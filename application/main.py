import json
import logging
import re
import subprocess
from threading import Event, Thread

import click
from colorama import Fore, Style
from docker.models.containers import Container
from packaging.version import parse
from rich.segment import Segment
from textual import on
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.logging import TextualHandler
from textual.strip import Strip
from textual.widget import Widget
from textual.widgets import (
    Button,
    Footer,
    Header,
    Input,
    Label,
    ListItem,
    ListView,
    RichLog,
)
from yaspin import yaspin

from application.config import Config, load_config
from application.docker_manager import DockerManager
from application.help import HelpScreen
from application.helper import (
    get_current_version,
    get_latest_version,
    read_changelog,
    read_latest_version_fetch,
    time_since_last_fetch,
    write_latest_version_fetch,
)

#### REFERENCES ####
logs = None
log_task_stop_event = Event()
config: Config = None
docker_manager: DockerManager = None

logging.basicConfig(
    level="INFO",
    handlers=[TextualHandler()],
)


def live_logs_task():
    docker_manager.live_container_logs(logs, log_task_stop_event)


def start_log_task():
    global log_task_stop_event
    log_task_stop_event.set()  # Signal any existing task to stop
    log_task_stop_event = Event()  # Create a new stop event for the new task
    Thread(target=live_logs_task, daemon=True).start()


def live_statistics_task():
    for stats in docker_manager.container(docker_manager.selected_container).stats(
        stream=True, decode=True
    ):
        try:
            cpu_usage = (
                stats["cpu_stats"]["cpu_usage"]["total_usage"]
                / stats["cpu_stats"]["system_cpu_usage"]
            )
            memory_usage_mb = stats["memory_stats"]["usage"] / (1024 * 1024)

            cpu = "{:.3f}%".format(cpu_usage * 100)
            memory = "{:.3f} MB".format(memory_usage_mb)
            logs.border_subtitle = (
                f"cpu: {cpu} | ram: {memory} | logs: {len(logs.lines)}"
            )
        except:
            pass


class PockerContainers(Widget):
    BORDER_TITLE: str = "Containers"
    current_index = 0

    def compose(self) -> ComposeResult:
        self.list_view = ListView(id="ContainersAndImagesListView")

        with self.list_view:
            container: Container
            for container in docker_manager.containers:
                status = "[U]"
                if container.status == "running":
                    status = "running"
                else:
                    status = "down"
                container_name = container.attrs["Names"][0].replace("/", "")
                listview_container = ListItem(
                    Label(container_name), id=container_name, classes=status
                )
                yield listview_container
        with Horizontal(id="startstopbuttons"):
            yield Button("Start all", id="startAllContainers")
            yield Button("Stop all", id="stopAllContainers")

    def on_mount(self) -> None:
        self.list_view.children[0].add_class("selected")
        self.list_view.sort_children(
            key=lambda listview_container: listview_container.has_class("running"),
            reverse=True,
        )
        self.log(self.tree)

    def on_list_view_selected(self):
        old_index = self.current_index
        new_index = self.list_view.index
        self.set_list_item_background(old_index, new_index)

    def set_list_item_background(self, old_index: int, new_index: int):
        old_container_list_item: ListItem = self.list_view.children[old_index]
        new_container_list_item: ListItem = self.list_view.children[new_index]

        deselect_classes = frozenset(
            set(old_container_list_item.classes) - {"selected"}
        )
        select_classes = frozenset(set(new_container_list_item.classes) | {"selected"})

        new_container_list_item.classes = select_classes
        old_container_list_item.classes = deselect_classes

        self.current_index = self.list_view.index

        docker_manager.selected_container = str(
            new_container_list_item.children[0].renderable
        )
        logs.border_title = docker_manager.selected_container
        start_log_task()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        id = str(event.button.id)
        if id == "stopAllContainers":
            for container in docker_manager.containers:
                container.stop()
        elif id == "startAllContainers":
            for container in docker_manager.containers:
                container.start()

    def live_status_events_task(self):
        event: dict[str, str]
        for event in docker_manager.client.events(decode=True):
            if event["Type"] == "container" and event["status"] in [
                "start",
                "stop",
                "die",
            ]:
                container_name = event.get("Actor").get("Attributes").get("name")
                container_list_item: ListItem = self.list_view.get_child_by_id(
                    container_name
                )
                status = ""
                was_selected: bool = container_list_item.has_class("selected")

                if event["status"] == "start":
                    status = "running"
                elif event["status"] == "stop":
                    status = "stopped"
                else:
                    status = "down"

                container_list_item.set_classes(status)
                if was_selected:
                    container_list_item.add_class("selected")


class PockerImages(Widget):
    BORDER_TITLE: str = "Images"

    def compose(self) -> ComposeResult:
        with ListView(id="ContainersAndImagesListView"):
            image: DockerManager
            for image in docker_manager.images:
                repo_tags = image.attrs.get("RepoTags")
                if len(repo_tags) != 0:
                    name = repo_tags[0].split(":")[0]
                    version = repo_tags[0].split(":")[1]
                    radio_button = ListItem(Label(str(f"{name}:{version}")))
                    yield radio_button

    def on_list_view_selected(self, item: ListItem):
        list_view: ListView = self.query_one(ListView)
        logs.write(list_view.index)


class ContentWindow(Widget):

    current_index = 0
    search_keyword = ""
    matches, indices = None, None

    def compose(self) -> ComposeResult:
        global logs

        search_logs_input = Input(placeholder="Search logs...", type="text")
        yield search_logs_input
        logs = RichLog(highlight=True, auto_scroll=True, name="Log")
        logs.border_title = docker_manager.selected_container
        logs.auto_scroll = True
        yield logs

    def search_logs(self, pattern):
        matches = []
        indices = []
        line: Strip
        for i, line in enumerate(logs.lines):
            if re.search(pattern, line.text):
                matches.append(line)
                indices.append(i)
        self.matches = matches
        self.indices = indices

    @on(Input.Submitted)
    def input_submitted(self, event: Input.Submitted) -> None:
        event.stop()
        keyword = str(event.value)

        if len(keyword) == 0:
            input = self.query_one("Input")
            input.border_title = None
            self.current_index = 0
            return

        if len(keyword) == 0 or keyword is not self.search_keyword:
            self.current_index = 0
            self.search_keyword = ""

        if self.current_index == 0:
            self.search_logs(keyword)
            self.current_index = len(self.indices) - 1
            self.search_keyword = keyword

        if len(self.indices) > 0:
            self.current_index -= 1
            self.update_input_border(str(self.indices[self.current_index + 1]))
            logs.scroll_to(
                y=self.indices[self.current_index], animate=True, duration=0.2
            )
            strip: Strip = self.matches[self.current_index]
            new_segments = [Segment(x.text, style="on yellow") for x in strip._segments]
            new_strip = Strip(new_segments)
            logs.lines[self.current_index] = new_strip
        else:
            input = self.query_one("Input")
            input.border_title = "No results"
            self.current_index = 0

    def update_input_border(self, line: str):
        input = self.query_one("Input")
        input.border_title = f"{(self.current_index + 1)}/{len(self.indices) - 1}"
        input.border_subtitle = f"line {line}"


class UI(App):
    CSS_PATH = "styles.tcss"
    SCREENS = {"helpscreen": HelpScreen()}
    BINDINGS = [
        Binding(key="q", action="quit", description="Quit the app"),
        Binding(
            key="question_mark",
            action="push_screen('helpscreen')",
            description="Show help screen",
            key_display="?",
        ),
        Binding(key="l", action="restore_logs", description="Show logs"),
        Binding(key="a", action="attributes", description="Show attributes"),
        Binding(key="f", action="toggle_content_full_screen", description="Fullscreen"),
        Binding(key="w", action="wrap_text", description="Wrap output to fit all"),
        Binding(key="s", action="toggle_auto_scroll", description="Toggle scroll"),
        Binding(key="/", action="toggle_search_log", description="Search log"),
    ]

    MODE = "LOGS"
    pocker_containers: PockerContainers
    pocker_images: PockerImages

    def compose(self) -> ComposeResult:
        global config, docker_manager

        config = load_config()
        docker_manager = DockerManager(config)

        header = Header()
        containers_and_images = Vertical(id="containers-and-images")
        self.pocker_containers = PockerContainers(id="PockerContainers")
        self.pocker_images = PockerImages(id="PockerImages")
        content_window = ContentWindow(id="ContentWindow")
        footer = Footer()

        yield header
        with containers_and_images:
            yield self.pocker_containers
            yield self.pocker_images

        yield content_window
        yield footer

    def on_mount(self) -> None:
        self._run_threads()
        self.title = "Pocker"

        if config.start_fullscreen:
            self.action_toggle_content_full_screen()
        if config.start_wrap:
            self.action_wrap_text()
        if not config.start_scroll:
            self.action_toggle_auto_scroll()

        self.set_header()

        current_version = parse(get_current_version())
        last_fetch = read_latest_version_fetch()

        if parse(last_fetch.version_fetched) > current_version:
            # Fetch latest version if more than 20 minutes ago.
            if time_since_last_fetch() > 20:
                latest_version = get_latest_version()
                if latest_version is not None:
                    if latest_version > current_version:
                        self._show_update_notification(current_version, latest_version)
                    write_latest_version_fetch(latest_version.base_version)

    def _show_update_notification(self, current_version, latest_version):
        self.notify(
            title=f"New version available! v{current_version} -> v{latest_version}",
            message=f"Update by running: 'pocker update",
            timeout=6,
        )

    def _run_threads(self):
        start_log_task()
        statistics_thread = Thread(target=live_statistics_task, daemon=True)
        status_events_thread = Thread(
            target=self.pocker_containers.live_status_events_task, daemon=True
        )
        statistics_thread.start()
        status_events_thread.start()

    def set_header(self):
        header_state = f"Mode: {self.MODE} ○ Containers: {len(docker_manager.containers)} ○ Wrap: {logs.wrap} ○ Scroll: {logs.auto_scroll}"
        self.sub_title = header_state

    def on_key(self, event: Input.Submitted) -> None:
        key = str(event.name)
        if self.query_one("Input").has_focus and key == "escape":
            self.action_toggle_search_log()

    def action_logs(self):
        self.MODE = "logs"
        logs.clear()
        logs.write(docker_manager.logs())
        self.set_header()

    def action_attributes(self):
        self.MODE = "attributes"
        logs.clear()
        logs.write(json.dumps(docker_manager.attributes(), indent=2))
        self.set_header()

    def action_restore_logs(self):
        logs.clear()
        logs.write(docker_manager.logs())

    def action_wrap_text(self):
        if logs.wrap == True:
            logs.wrap = False
        else:
            logs.wrap = True
        self.set_header()
        logs.clear()
        logs.write(docker_manager.logs())

    def action_toggle_content_full_screen(self):
        containers_and_images_styling = self.query_one(
            "#containers-and-images"
        ).styles.display
        if containers_and_images_styling == "block":
            self.query_one("#containers-and-images").styles.display = "none"
            self.query_one("ContentWindow").styles.width = "100%"
            self.query_one("RichLog").styles.width = "100%"
            self.query_one("RichLog").styles.border = ("blank", "transparent")
            self.query_one("Input").styles.width = "100%"
        else:
            self.query_one("#containers-and-images").styles.display = "block"
            self.query_one("RichLog").styles.width = "80%"
            self.query_one("RichLog").styles.border = ("round", "cornflowerblue")
            self.query_one("Input").styles.width = "80%"

    def action_toggle_auto_scroll(self):
        if logs.auto_scroll:
            logs.auto_scroll = False
        else:
            logs.auto_scroll = True
        self.set_header()

    def action_toggle_search_log(self):
        search_logs_input = self.query_one("Input")
        content_window = self.query_one("RichLog")

        if search_logs_input.styles.display == "block":
            search_logs_input.styles.display = "none"
            content_window.styles.height = "100%"
        else:
            search_logs_input.styles.display = "block"
            content_window.styles.height = "94%"
            content_window.scroll_end(animate=False)

        search_logs_input.focus()


def start():
    UI().run()


@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx):
    if ctx.invoked_subcommand is None:
        start()


@cli.command()
@click.option("--force", "-f", is_flag=True, help="Force update.")
def update(force):
    current_version = parse(get_current_version())
    latest_version = None

    if time_since_last_fetch() < 5 and not force:
        print(
            f"⚠️ {Fore.YELLOW}Updating too often might lead to being rate-limited.{Style.RESET_ALL}\n"
            "Pass --force or -f to force update."
        )
        return
    else:
        latest_version = get_latest_version()
        write_latest_version_fetch(latest_version.base_version)

    if latest_version is not None and latest_version > current_version:
        with yaspin(text=f"Updating to v{latest_version}", timer=True) as sp:
            result = subprocess.run(
                [
                    "pipx",
                    "install",
                    "git+https://github.com/pommee/Pocker@main",
                    "--force",
                ],
                text=True,
                capture_output=True,
                check=True,
            )
            sp.ok()
            if "installed package pocker" in result.stdout:
                click.echo(
                    f"Pocker is now updated from{Fore.LIGHTYELLOW_EX} v{current_version}{Style.RESET_ALL}{Fore.LIGHTGREEN_EX} -> v{latest_version}{Style.RESET_ALL}"
                )
                read_changelog(current_version)
            return
    if latest_version == current_version:
        print(
            f"{Fore.LIGHTGREEN_EX}Already running latest (v{latest_version}){Style.RESET_ALL}"
        )

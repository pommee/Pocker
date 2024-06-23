import logging
import re
import subprocess
from threading import Event, Thread

import click
import yaml
from colorama import Fore, Style
from docker.models.containers import Container
from docker.models.images import Image
from packaging.version import parse
from textual import on, work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.logging import TextualHandler
from textual.strip import Strip
from textual.widget import Widget
from textual.widgets import (
    Button,
    Footer,
    Input,
    Label,
    ListItem,
    ListView,
    RichLog,
    Rule,
    Static,
    TabbedContent,
    TabPane,
)
from yaspin import yaspin

from application.docker_manager import DockerManager
from application.util.config import load_config
from application.util.help import HelpScreen
from application.util.helper import (
    get_current_version,
    get_latest_version,
    read_changelog,
    read_latest_version_fetch,
    time_since_last_fetch,
    write_latest_version_fetch,
)
from application.widget.topbar import TopBar

#### REFERENCES ####
logs: RichLog
docker_manager: DockerManager
log_task_stop_event = Event()

logging.basicConfig(
    level="INFO",
    handlers=[TextualHandler()],
)


def live_logs_task():
    docker_manager.live_container_logs(logs, log_task_stop_event)


def run_log_task():
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

        yield Static("Containers", classes="containers-and-images-header")
        with self.list_view:
            container: Container
            for container in docker_manager.containers:
                container_name = container.attrs["Names"][0].replace("/", "")
                yield ListItem(
                    Label(container_name),
                    id=container_name,
                    classes=docker_manager.status(container),
                )
        with Horizontal(id="startstopbuttons"):
            yield Button("Start all", id="startAllContainers")
            yield Button("Stop all", id="stopAllContainers")

    async def on_mount(self) -> None:
        self.list_view.children[0].add_class("selected")
        self.list_view.sort_children(
            key=lambda listview_container: listview_container.has_class("running"),
            reverse=True,
        )

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
        run_log_task()

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
        yield Static("Images", classes="containers-and-images-header")
        with ListView(id="ContainersAndImagesListView"):
            image: Image
            for image in docker_manager.images:
                if image.tags:
                    name = image.tags[0].split(":")[0]
                    version = image.tags[0].split(":")[1]
                    yield ListItem(Label(f"{name}:{version}"))

    # TODO: Implement fetching relevant information regarding an image.
    def on_list_view_selected(self, item: ListItem):
        pass


class ContentWindow(Widget):

    current_index = 0
    search_keyword = ""
    matches, indices = None, None

    def compose(self) -> ComposeResult:
        global logs

        yield Input(placeholder="Search logs...", type="text")
        with TabbedContent():
            with TabPane("Logs", id="logpane"):
                logs = RichLog(id="logs", highlight=True, auto_scroll=True, name="Log")
                logs.border_title = docker_manager.selected_container
                logs.scroll_end(animate=False)
                yield logs
            with TabPane("Attributes", id="attributespane"):
                attributes = RichLog(
                    id="attributes_log",
                    highlight=True,
                    auto_scroll=True,
                    name="Attributes",
                )
                attributes.border_title = docker_manager.selected_container
                attributes.scroll_end(animate=False)
                yield attributes
            with TabPane("Environment", id="environmentpane"):
                environment = RichLog(
                    id="environment_log",
                    highlight=True,
                    auto_scroll=True,
                    name="Environment",
                )
                environment.border_title = docker_manager.selected_container
                environment.scroll_end(animate=False)
                yield environment
            with TabPane("Statistics", id="statisticspane"):
                statistics = RichLog(
                    id="statistics_log",
                    highlight=True,
                    auto_scroll=True,
                    name="Statistics",
                )
                statistics.border_title = docker_manager.selected_container
                statistics.scroll_end(animate=False)
                yield statistics

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
    def input_submitted(self, input=Input(validate_on=["submitted"])) -> None:
        keyword = input.value

        if len(keyword) == 0 or keyword is not self.search_keyword:
            self.current_index = 0
            self.search_keyword = ""

        if self.current_index == 0:
            self.search_logs(keyword)
            self.current_index = len(self.indices) - 1
            self.search_keyword = keyword

        if len(self.indices) > 0:
            self.current_index -= 1
            self.update_input_border()
            logs.scroll_to(
                y=self.indices[self.current_index], animate=True, duration=0.2
            )
        else:
            input.border_title = "No results"
            self.current_index = 0

    def update_input_border(self):
        line = str(self.indices[self.current_index + 1])
        input = self.query_one(Input)
        input.border_title = f"{self.current_index + 1}/{len(self.indices) - 1}"
        input.border_subtitle = f"line {line}"


class UI(App):

    CSS_PATH = "styles.tcss"
    SCREENS = {"helpscreen": HelpScreen()}
    TITLE = "Pocker"
    BINDINGS = [
        Binding(
            key="question_mark",
            action="push_screen('helpscreen')",
        ),
        Binding(key="/", action="toggle_search_log", description="Search"),
    ]

    def set_bindings_from_config_keymap(self) -> None:
        keymap = load_config().keymap
        self.bind(keymap.get("quit"), "quit", description="Quit")
        self.bind(keymap.get("logs"), "restore_logs", description="Logs")
        self.bind(
            keymap.get("attributes"),
            "attributes",
            description="Attributes",
        )
        self.bind(
            keymap.get("environment"),
            "environment",
            description="Environment",
        )
        self.bind(
            keymap.get("statistics"),
            "statistics",
            description="Statistics",
        )
        self.bind(
            keymap.get("fullscreen"),
            "toggle_content_full_screen",
            description="Fullscreen",
        )
        self.bind(
            keymap.get("wrap-logs"),
            "wrap_text",
            description="Wrap logs",
        )
        self.bind(
            keymap.get("toggle-scroll"),
            "toggle_auto_scroll",
            description="Wrap logs",
        )

    def compose(self) -> ComposeResult:
        global docker_manager

        self.config = load_config()
        docker_manager = DockerManager(self.config)
        self.set_bindings_from_config_keymap()

        yield TopBar(get_current_version())
        with Vertical(id="containers-and-images"):
            yield PockerContainers(id="PockerContainers")
            yield Rule("horizontal")
            yield PockerImages(id="PockerImages")
        yield ContentWindow(id="ContentWindow")
        yield Footer()

    async def on_mount(self) -> None:
        self._run_threads()
        self.set_header_statuses()
        self._look_for_update()

    def read_and_apply_config(self):
        logs.max_lines = self.config.max_log_lines

        if self.config.start_fullscreen:
            self.action_toggle_content_full_screen()
        if self.config.start_wrap:
            self.action_wrap_text()
        if not self.config.start_scroll:
            self.action_toggle_auto_scroll()

    @work(exclusive=True)
    async def _look_for_update(self):
        current_version = parse(get_current_version())
        last_fetch = parse(read_latest_version_fetch().version_fetched)

        if last_fetch > current_version:
            self.set_header_new_version_available(last_fetch)
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
            message=f"Update by running: 'pocker update'",
            timeout=6,
        )

    def _run_threads(self):
        run_log_task()
        statistics_thread = Thread(target=live_statistics_task, daemon=True)
        status_events_thread = Thread(
            target=self.query_one(PockerContainers).live_status_events_task, daemon=True
        )
        statistics_thread.start()
        status_events_thread.start()

    def set_header_statuses(self):
        self.query_one("#topbar_statuses").update(
            f"Wrap [{logs.wrap}]    Scroll [{logs.auto_scroll}]"
        )

    def set_header_new_version_available(self, new_version):
        self.query_one("#topbar_title").update(
            f" Pocker [b green]v{new_version} Available![/b green]"
        )

    def on_key(self, event: Input.Submitted) -> None:
        key = str(event.name)
        try:
            if self.query_one(Input).has_focus and key == "escape":
                self.action_toggle_search_log()
        except:
            pass

    @on(TabbedContent.TabActivated)
    def action_show_tab(self, tab: TabbedContent.TabActivated) -> None:
        selected_tab = tab.tab.id.replace("--content-tab-", "")
        match selected_tab:
            case "logpane":
                self.action_restore_logs()
            case "attributespane":
                self.action_attributes()
            case "environmentpane":
                self.action_environment()
            case "statisticspane":
                self.action_statistics()

    def action_restore_logs(self):
        self.query_one(TabbedContent).active = "logpane"
        logs.clear()
        logs.write(docker_manager.logs())
        self.set_header_statuses()

    def action_attributes(self):
        self.query_one(TabbedContent).active = "attributespane"
        attributes_log: RichLog = self.query_one("#attributes_log")
        attributes_log.clear()
        attributes_log.write(yaml.dump(docker_manager.attributes, indent=2))
        self.set_header_statuses()

    def action_environment(self):
        self.query_one(TabbedContent).active = "environmentpane"
        environment_log: RichLog = self.query_one("#environment_log")
        environment_log.clear()
        for entry in docker_manager.environment:
            key = entry.split("=")[0]
            value = entry.split("=")[1]
            environment_log.write(f"{key}: {value}")
        self.set_header_statuses()

    def action_statistics(self):
        self.query_one(TabbedContent).active = "statisticspane"
        statistics_log: RichLog = self.query_one("#statistics_log")
        statistics_log.clear()
        statistics_log.write(yaml.dump(docker_manager.statistics, indent=2))
        self.set_header_statuses()

    def action_wrap_text(self):
        if logs.wrap == True:
            logs.wrap = False
        else:
            logs.wrap = True
        self.set_header_statuses()
        logs.clear()
        logs.write(docker_manager.logs())

    def action_toggle_content_full_screen(self):
        tabbed_content = self.query_one(TabbedContent)
        containers_and_images = self.query_one("#containers-and-images")
        search_window = self.query_one(Input)

        containers_and_images_styling = self.query_one(
            "#containers-and-images"
        ).styles.display
        if containers_and_images_styling == "block":
            containers_and_images.styles.display = "none"
            self.query_one(ContentWindow).styles.width = "100%"
            tabbed_content.styles.width = "100%"
            search_window.styles.width = "100%"
        else:
            containers_and_images.styles.display = "block"
            tabbed_content.styles.width = "79%"
            search_window.styles.width = "79%"
        self.set_header_statuses()

    def action_toggle_auto_scroll(self):
        if logs.auto_scroll:
            logs.auto_scroll = False
        else:
            logs.auto_scroll = True
        self.set_header_statuses()

    def action_toggle_search_log(self):
        search_logs_input = self.query_one(Input)
        content_window = self.query_one(TabbedContent)

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

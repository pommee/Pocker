import asyncio
import logging
import subprocess
from threading import Thread

import click
import yaml
from colorama import Fore, Style
from packaging.version import parse
from textual import on, work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.events import DescendantFocus
from textual.logging import TextualHandler
from textual.widgets import (
    ContentSwitcher,
    Footer,
    Input,
    ListView,
    TabbedContent,
)
from yaspin import yaspin

from application.docker_manager import DockerManager, NoVisibleContainers
from application.util.config import CONFIG_PATH, load_config
from application.util.helper import (
    get_current_version,
    get_latest_version,
    read_changelog,
    read_latest_version_fetch,
    time_since_last_fetch,
    write_latest_version_fetch,
)
from application.widget.containers import PockerContainers
from application.widget.content import ContentWindow
from application.widget.help import HelpScreen
from application.widget.images import PockerImages
from application.widget.log_viewer import LogLines
from application.widget.settings import SettingsScreen
from application.widget.shell import ShellPane
from application.widget.startup_error_modal import StartupError
from application.widget.topbar import TopBar

#### REFERENCES ####
logs: LogLines
docker_manager: DockerManager

logging.basicConfig(
    level="INFO",
    handlers=[TextualHandler()],
)


class UI(App):
    CSS_PATH = "styles.tcss"
    SCREENS = {"helpscreen": HelpScreen(), "settingsscreen": SettingsScreen()}
    TITLE = "Pocker"
    BINDINGS = [
        Binding(
            key="question_mark",
            action="push_screen('helpscreen')",
        ),
        Binding(
            key="p",
            action="push_screen('settingsscreen')",
        ),
        Binding(key="TAB", action="NOT_VALID_ACTION", description="Cycle widget"),
        Binding(key="/", action="toggle_search_log", description="Search"),
        Binding(key="escape", action="dismiss_search_log"),
    ]
    current_index = 0
    _ERROR = None

    def set_bindings_from_config_keymap(self) -> None:
        keymap = load_config().keymap
        self.set_keybind(keymap.get("quit"), "quit", description="Quit")
        self.set_keybind(keymap.get("logs"), "restore_logs", description="Logs")
        self.set_keybind(
            keymap.get("attributes"),
            "attributes",
            description="Attributes",
        )
        self.set_keybind(
            keymap.get("environment"),
            "environment",
            description="Environment",
        )
        self.set_keybind(
            keymap.get("statistics"),
            "statistics",
            description="Statistics",
        )
        self.set_keybind(
            keymap.get("shell"),
            "shell",
            description="Shell",
        )
        self.set_keybind(
            keymap.get("fullscreen"),
            "toggle_content_full_screen",
            description="Fullscreen",
        )
        self.set_keybind(
            keymap.get("wrap-logs"),
            "wrap_text",
            description="Wrap logs",
        )
        self.set_keybind(
            keymap.get("toggle-scroll"),
            "toggle_auto_scroll",
            description="Auto scroll",
        )

    def set_keybind(self, key: str, action: str, description: str):
        try:
            self.bind(key, action, description=description)
        except AttributeError:
            self._show_keybind_error(description)
            self.bind("<Error>", action, description=description)

    def compose(self) -> ComposeResult:
        global docker_manager

        self.config = load_config()

        try:
            docker_manager = DockerManager(self.config)
        except NoVisibleContainers as ex:
            self._ERROR = ex
            return
        self.set_bindings_from_config_keymap()

        self.content_window = ContentWindow(
            id="ContentWindow", docker_manager=docker_manager
        )

        yield TopBar(get_current_version())
        with Vertical(id="containers-and-images"):
            yield PockerContainers(
                id="PockerContainers",
                docker_manager=docker_manager,
                classes="active-widget",
            )
            yield PockerImages(id="PockerImages", docker_manager=docker_manager)
        yield self.content_window
        yield Footer()

    async def on_mount(self) -> None:
        if self._ERROR:
            self.app.push_screen(StartupError(self._ERROR))
            return
        self._run_threads()
        self.set_header_statuses()
        self._look_for_update()
        self.list_view = self.query_one(PockerContainers).query_one(
            "#ContainersAndImagesListView"
        )
        self.currently_focused_widget = self.focused

    @on(DescendantFocus)
    def focus_switched(self, focus: DescendantFocus):
        widget = focus.widget

        try:
            self.currently_focused_widget.remove_class("active-widget")
        except AttributeError:
            pass  # Previous widget might not have a border.

        if type(widget) is ListView:
            next_focused_widget = widget.parent
            widget.parent.add_class("active-widget")
        elif "ContentTabs" in str(type(widget)):
            underline = widget.query_one("Underline")
            underline.add_class("active-widget")
            next_focused_widget = underline
        else:
            next_focused_widget = widget
            widget.add_class("active-widget")

        self.currently_focused_widget = next_focused_widget

    def read_and_apply_config(self):
        logs = self.query_one("#logs", LogLines)
        logs.max_lines = self.config.max_log_lines

        if self.config.start_fullscreen:
            self.action_toggle_content_full_screen()
        if self.config.start_wrap:
            self.action_wrap_text()
        if not self.config.start_scroll:
            self.action_toggle_auto_scroll()

    @work(exclusive=True)
    async def _look_for_update(self):
        fetched_version = get_current_version()  # can return None
        if not fetched_version:
            return
        current_version = parse(fetched_version)
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
            message="Update by running: 'pocker update'",
            timeout=6,
        )

    def _show_keybind_error(self, description: str):
        self.notify(
            title="Keybind error",
            message=f"Could not bind key for {description}\nKeymap can be found in config [b]{CONFIG_PATH}[/b]",
            severity="warning",
            timeout=6,
        )

    def _run_threads(self):
        self.content_window.run_log_task()
        loop = asyncio.get_event_loop()

        Thread(target=self.content_window.live_statistics_task, daemon=True).start()
        Thread(
            target=self.query_one(PockerContainers).live_status_events_task,
            args=(loop,),
            daemon=True,
        ).start()

    def set_header_statuses(self):
        logs = self.query_one("#logs", LogLines)
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
        except Exception:
            pass

    def on_list_view_selected(self):
        def _update_tab_content(self, tab_id: str):
            match tab_id:
                case "logpane":
                    self.action_restore_logs()
                case "attributespane":
                    self.action_attributes()
                case "environmentpane":
                    self.action_environment()
                case "statisticspane":
                    self.action_statistics()
                case "shellpane":
                    self.action_shell()

        old_index = self.current_index
        new_index = self.list_view.index

        if old_index == new_index:
            return

        docker_manager.selected_container = self.list_view.children[new_index].id
        self.set_list_item_background(old_index, new_index)
        self.content_window.run_log_task()

        current_tab = self.query_one(ContentSwitcher).current
        _update_tab_content(self, current_tab)

    def set_list_item_background(self, old_index: int, new_index: int):
        logs = self.query_one("#logs", LogLines)

        old_item = self.list_view.children[old_index]
        new_item = self.list_view.children[new_index]

        old_item.classes -= {"selected"}
        new_item.classes |= {"selected"}

        self.current_index = new_index
        docker_manager.selected_container = docker_manager.containers.get(
            str(new_item.children[0].renderable)
        )
        logs.border_title = docker_manager.selected_container.name

    @on(TabbedContent.TabActivated)
    def action_show_tab(self, tab: TabbedContent.TabActivated) -> None:
        selected_tab = tab.tab.id.replace("--content-tab-", "")
        if self.query_one(TabbedContent).active_pane == selected_tab:
            return
        match selected_tab:
            case "logpane":
                self.action_restore_logs()
            case "attributespane":
                self.action_attributes()
            case "environmentpane":
                self.action_environment()
            case "statisticspane":
                self.action_statistics()
            case "shellpane":
                self.action_shell()

    def action_restore_logs(self):
        logs = self.query_one("#logs", LogLines)

        self.query_one(TabbedContent).active = "logpane"
        logs.clear()
        logs.write(docker_manager.logs())
        self.set_header_statuses()

    def action_attributes(self):
        self.query_one(TabbedContent).active = "attributespane"
        attributes_log: LogLines = self.query_one("#attributes_log")
        attributes_log.clear()
        attributes_log.border_title = docker_manager.selected_container.name
        attributes_log.write(yaml.dump(docker_manager.attributes, indent=2))
        self.set_header_statuses()

    def action_environment(self):
        self.query_one(TabbedContent).active = "environmentpane"
        environment_log: LogLines = self.query_one("#environment_log")
        environment_log.clear()
        environment_log.border_title = docker_manager.selected_container.name
        for entry in docker_manager.environment:
            name_value = entry.split("=", maxsplit=2)
            key = name_value[0]
            if len(name_value) == 2:
                value = name_value[1]
            else:
                value = ""
            environment_log.write(f"{key}: {value}")
        self.set_header_statuses()

    def action_statistics(self):
        self.query_one(TabbedContent).active = "statisticspane"
        statistics_log: LogLines = self.query_one("#statistics_log")
        statistics_log.clear()
        statistics_log.border_title = docker_manager.selected_container.name
        statistics_log.write(yaml.dump(docker_manager.statistics, indent=2))
        self.set_header_statuses()

    def action_shell(self):
        self.query_one(TabbedContent).active = "shellpane"
        shell_log: LogLines = self.query_one("#shell-output")
        shell_log.clear()
        self.query_one(ShellPane).run_shell()
        shell_log.border_title = docker_manager.selected_container.name
        self.query_one("#shell-input", Input).focus()

    def action_wrap_text(self):
        logs = self.query_one("#logs", LogLines)

        if logs.wrap is True:
            logs.wrap = False
        else:
            logs.wrap = True
        self.set_header_statuses()
        logs.clear()
        logs.write(docker_manager.logs())

    def action_toggle_content_full_screen(self):
        tabbed_content = self.query_one(TabbedContent)
        containers_and_images = self.query_one("#containers-and-images")
        search_window = self.query_one("#search_log_input")

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
            tabbed_content.styles.width = "81%"
            search_window.styles.width = "81%"
        self.set_header_statuses()

    def action_toggle_auto_scroll(self):
        logs = self.query_one("#logs", LogLines)

        if logs.auto_scroll:
            logs.auto_scroll = False
        else:
            logs.auto_scroll = True
        self.set_header_statuses()

    def action_toggle_search_log(self):
        search_logs_input = self.query_one("#search_log_input")
        search_container = self.query_one(".container")
        content_window = self.query_one(TabbedContent)

        if search_container.styles.display == "block":
            search_container.styles.display = "none"
            content_window.styles.height = "100%"
        else:
            search_container.styles.display = "block"
            content_window.styles.height = "94%"
            content_window.scroll_end(animate=False)

        search_logs_input.focus()

    def action_dismiss_search_log(self):
        search_logs_input = self.query_one("#search_log_input", Input)
        search_container = self.query_one(".container")
        content_window = self.query_one(TabbedContent)

        search_container.styles.display = "none"
        search_logs_input.clear()
        search_logs_input.border_subtitle = ""
        search_logs_input.border_title = ""
        content_window.styles.height = "100%"
        content_window.scroll_end(animate=False)

        content_window.focus()

        log_lines = self.content_window.query_one("#logs", LogLines)
        log_lines.keyword = None
        log_lines.current_index = None


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

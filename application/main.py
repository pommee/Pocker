import logging
import re
from typing import Self
from cachetools import LRUCache
from docker.models.containers import Container
from threading import Event, Thread
from textual import on
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import (
    Footer,
    RadioButton,
    Header,
    Button,
    Input,
    Label,
    ListItem,
    ListView,
)
from textual.containers import Horizontal, Vertical
from textual.widget import Widget
from application.help import HelpScreen
from application.docker_manager import DockerManager
from textual.strip import Strip
from textual.logging import TextualHandler
from textual.geometry import Size
from textual.strip import Strip
from textual.scroll_view import ScrollView
from rich.highlighter import Highlighter, ReprHighlighter
from rich.console import RenderableType
from rich.protocol import is_renderable
from rich.pretty import Pretty
from rich.text import Text
from typing import cast
from textual.geometry import Region
from rich.segment import Segment
from rich.measure import measure_renderables

#### REFERENCES ####
logs = None
container_buttons: dict[str, RadioButton] = {}
docker_manager = DockerManager()
log_task_stop_event = Event()


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
    for x in docker_manager.container(docker_manager.selected_container).stats(
        stream=True, decode=True
    ):
        cpu_usage = (
            x["cpu_stats"]["cpu_usage"]["total_usage"]
            / x["cpu_stats"]["system_cpu_usage"]
        )
        memory_usage_mb = x["memory_stats"]["usage"] / (1024 * 1024)

        cpu = "{:.3f}%".format(cpu_usage * 100)
        memory = "{:.3f} MB".format(memory_usage_mb)
        # logs.border_subtitle = f"cpu: {cpu} | ram: {memory} | logs: {len(logs.lines)}"


def live_status_events_task():
    for event in docker_manager.client.events(decode=True):
        logging.info(str(event))
        if event["Type"] == "container" and event["status"] in [
            "start",
            "stop",
            "die",
        ]:
            status = ""
            container_name = event.get("Actor").get("Attributes").get("name")
            if event["status"] == "start":
                status = "running"
            elif event["status"] == "stop":
                status = "stopped"
            else:
                status = "down"
            container_buttons.get(
                docker_manager.container(event["id"]).name
            ).classes = status
            if (
                docker_manager.selected_container == container_name
                and status == "running"
            ):
                button = container_buttons.get(container_name)
                button.toggle()


class PockerContainers(Widget):
    BORDER_TITLE: str = "Containers"
    current_index = 0

    def compose(self) -> ComposeResult:
        docker_containers = docker_manager.containers

        self.list_view = ListView(id="ContainersAndImagesListView")

        with self.list_view:
            container: Container
            for container in docker_containers:
                is_running = container.attrs.get("State").get("Running")
                status = "[U]"
                if is_running is True:
                    status = "running"
                if not is_running:
                    status = "down"
                listview_container = ListItem(Label(container.name, classes=status))
                container_buttons[container.name] = listview_container
                yield listview_container
        with Horizontal(id="startstopbuttons"):
            yield Button("Start all", id="startAllContainers")
            yield Button("Stop all", id="stopAllContainers")

    def on_mount(self):

        # Style first container when started
        first_list_item: Label = self.list_view.children[0]
        new_classes = frozenset(set(first_list_item.classes) | {"selected"})
        first_list_item.classes = new_classes

    def on_list_view_selected(self, item):
        old_index = self.current_index
        new_index = self.list_view.index
        self.set_list_item_background(old_index, new_index)

    def set_border_title(self, text):
        # logs.border_title = text
        pass

    def set_list_item_background(self, old_index: int, new_index: bool):
        old_container_list_item: ListItem = self.list_view.children[old_index]
        new_container_list_item: ListItem = self.list_view.children[new_index]

        deselect_classes = frozenset(
            set(new_container_list_item.classes) - {"selected"}
        )
        select_classes = frozenset(set(new_container_list_item.classes) | {"selected"})

        new_container_list_item.classes = select_classes
        old_container_list_item.classes = deselect_classes

        self.current_index = self.list_view.index
        self.set_border_title(new_container_list_item.children[0].renderable)

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


class PockerImages(Widget):
    BORDER_TITLE: str = "Images"

    def compose(self) -> ComposeResult:
        with ListView(id="ContainersAndImagesListView"):
            for image in docker_manager.images:
                repo_tags = image.attrs.get("RepoTags")
                if len(repo_tags) != 0:
                    name = repo_tags[0].split(":")[0]
                    version = repo_tags[0].split(":")[1]
                    radio_button = ListItem(Label(str(f"{name}:{version}")))
                    yield radio_button

    def on_list_view_selected(self, item: ListItem):
        list_view: ListView = self.query_one(ListView)
        # logs.write(list_view.index)


class ContentWindow(ScrollView):
    """A widget for logging text."""

    DEFAULT_CSS = """
    RichLog{
        background: $surface;
        color: $text;
        overflow-y: scroll;
    }
    """

    def __init__(
        self,
        *,
        max_lines: int | None = None,
        min_width: int = 78,
        wrap: bool = False,
        highlight: bool = False,
        markup: bool = False,
        auto_scroll: bool = True,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
        disabled: bool = False,
    ) -> None:
        """Create a RichLog widget.

        Args:
            max_lines: Maximum number of lines in the log or `None` for no maximum.
            min_width: Minimum width of renderables.
            wrap: Enable word wrapping (default is off).
            highlight: Automatically highlight content.
            markup: Apply Rich console markup.
            auto_scroll: Enable automatic scrolling to end.
            name: The name of the text log.
            id: The ID of the text log in the DOM.
            classes: The CSS classes of the text log.
            disabled: Whether the text log is disabled or not.
        """
        super().__init__(name=name, id=id, classes=classes, disabled=disabled)
        self.max_lines = max_lines
        """Maximum number of lines in the log or `None` for no maximum."""
        self._start_line: int = 0
        self.lines: list[Strip] = []
        self._line_cache: LRUCache[tuple[int, int, int, int], Strip]
        self._line_cache = LRUCache(1024)
        self.max_width: int = 0
        self.min_width = min_width
        """Minimum width of renderables."""
        self.wrap = wrap
        """Enable word wrapping."""
        self.highlight = highlight
        """Automatically highlight content."""
        self.markup = markup
        """Apply Rich console markup."""
        self.auto_scroll = auto_scroll
        """Automatically scroll to the end on write."""
        self.highlighter: Highlighter = ReprHighlighter()
        """Rich Highlighter used to highlight content when highlight is True"""

        self._last_container_width: int = min_width
        """Record the last width we rendered content at."""

    def notify_style_update(self) -> None:
        self._line_cache.clear()

    def on_resize(self) -> None:
        self._last_container_width = self.scrollable_content_region.width

    def _make_renderable(self, content: RenderableType | object) -> RenderableType:
        """Make content renderable.

        Args:
            content: Content to render.

        Returns:
            A Rich renderable.
        """
        renderable: RenderableType
        if not is_renderable(content):
            renderable = Pretty(content)
        else:
            if isinstance(content, str):
                if self.markup:
                    renderable = Text.from_markup(content)
                else:
                    renderable = Text(content)
                if self.highlight:
                    renderable = self.highlighter(renderable)
            else:
                renderable = cast(RenderableType, content)

        if isinstance(renderable, Text):
            renderable.expand_tabs()

        return renderable

    def write(
        self,
        content: RenderableType | object,
        width: int | None = None,
        expand: bool = False,
        shrink: bool = True,
        scroll_end: bool | None = None,
    ) -> Self:
        """Write text or a rich renderable.

        Args:
            content: Rich renderable (or text).
            width: Width to render or `None` to use optimal width.
            expand: Enable expand to widget width, or `False` to use `width`.
            shrink: Enable shrinking of content to fit width.
            scroll_end: Enable automatic scroll to end, or `None` to use `self.auto_scroll`.

        Returns:
            The `RichLog` instance.
        """

        auto_scroll = self.auto_scroll if scroll_end is None else scroll_end

        console = self.app.console
        render_options = console.options

        renderable = self._make_renderable(content)

        if isinstance(renderable, Text) and not self.wrap:
            render_options = render_options.update(overflow="ignore", no_wrap=True)

        render_width = measure_renderables(
            console, render_options, [renderable]
        ).maximum

        container_width = (
            self.scrollable_content_region.width if width is None else width
        )

        # Use the container_width if it's available, otherwise use the last available width.
        container_width = (
            container_width if container_width else self._last_container_width
        )

        if expand and render_width < container_width:
            render_width = container_width
        if shrink and render_width > container_width:
            render_width = container_width

        render_width = max(render_width, self.min_width)

        segments = self.app.console.render(
            renderable, render_options.update_width(render_width)
        )
        lines = list(Segment.split_lines(segments))
        if not lines:
            self.lines.append(Strip.blank(render_width))
        else:
            self.max_width = max(
                self.max_width,
                max(sum([segment.cell_length for segment in _line]) for _line in lines),
            )
            strips = Strip.from_lines(lines)
            for strip in strips:
                strip.adjust_cell_length(render_width)
            self.lines.extend(strips)

            if self.max_lines is not None and len(self.lines) > self.max_lines:
                self._start_line += len(self.lines) - self.max_lines
                self.refresh()
                self.lines = self.lines[-self.max_lines :]
        self.virtual_size = Size(self.max_width, len(self.lines))
        if auto_scroll:
            self.scroll_end(animate=False)

        return self

    def clear(self) -> Self:
        """Clear the text log.

        Returns:
            The `RichLog` instance.
        """
        self.lines.clear()
        self._line_cache.clear()
        self._start_line = 0
        self.max_width = 0
        self.virtual_size = Size(self.max_width, len(self.lines))
        self.refresh()
        return self

    def render_line(self, y: int) -> Strip:
        scroll_x, scroll_y = self.scroll_offset
        line = self._render_line(scroll_y + y, scroll_x, self.size.width)
        strip = line.apply_style(self.rich_style)
        return strip

    def render_lines(self, crop: Region) -> list[Strip]:
        """Render the widget in to lines.

        Args:
            crop: Region within visible area to.

        Returns:
            A list of list of segments.
        """
        lines = self._styles_cache.render_widget(self, crop)
        return lines

    def _render_line(self, y: int, scroll_x: int, width: int) -> Strip:
        if y >= len(self.lines):
            return Strip.blank(width, self.rich_style)

        key = (y + self._start_line, scroll_x, width, self.max_width)
        if key in self._line_cache:
            return self._line_cache[key]

        line = self.lines[y].crop_extend(scroll_x, scroll_x + width, self.rich_style)

        self._line_cache[key] = line
        return line


class TestIt(Widget):

    current_index = 0
    search_keyword = ""
    matches, indices = None, None

    def compose(self) -> ComposeResult:
        global logs

        search_logs_input = Input(placeholder="Search logs...", type="text")
        yield search_logs_input
        logs = ContentWindow()
        for x in range(100):
            logs.write(x)
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

    def compose(self) -> ComposeResult:
        header = Header()
        containers_and_images = Vertical(id="containers-and-images")
        pocker_containers = PockerContainers(id="PockerContainers")
        pocker_images = PockerImages(id="PockerImages")
        content_window = TestIt(id="ContentWindow")
        footer = Footer()

        yield header
        with containers_and_images:
            yield pocker_containers
            yield pocker_images

        yield content_window
        yield footer

    def on_mount(self) -> None:
        self._run_threads()
        self.title = "Pocker"
        self.set_header()
        # self.notify(
        #    title="New version available!",
        #    message="Update to v1.2.1 by running: 'pocker update'",
        #    timeout=6,
        # )

    def _run_threads(self):
        start_log_task()
        statistics_thread = Thread(target=live_statistics_task, daemon=True)
        status_events_thread = Thread(target=live_status_events_task, daemon=True)
        statistics_thread.start()
        status_events_thread.start()

    def set_header(self):
        header_state = f"Mode: {self.MODE} ○ Containers: {len(docker_manager.containers)} ○ Scroll: {'logs.auto_scroll'}"
        self.sub_title = header_state

    def on_key(self, event: Input.Submitted) -> None:
        key = str(event.name)
        if self.query_one("Input").has_focus and key == "escape":
            self.action_toggle_search_log()

    def action_logs(self):
        self.MODE = "logs"
        # logs.clear()
        # logs.write(docker_manager.logs())
        self.set_header()

    def action_attributes(self):
        self.MODE = "attributes"
        # logs.clear()
        # logs.write(json.dumps(docker_manager.attributes(), indent=2))
        self.set_header()

    def action_restore_logs(self):
        # logs.clear()
        # logs.write(docker_manager.logs())
        pass

    def action_wrap_text(self):
        if logs.wrap == True:
            logs.wrap = False
        else:
            logs.wrap = True
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
        else:
            self.query_one("#containers-and-images").styles.display = "block"
            self.query_one("RichLog").styles.width = "80%"
            self.query_one("RichLog").styles.border = ("round", "cornflowerblue")

    def action_toggle_auto_scroll(self):
        if logs.auto_scroll:
            logs.auto_scroll = False
        else:
            logs.auto_scroll = True

    def action_toggle_search_log(self):
        search_logs_input = self.query_one("Input")
        content_window = self.query_one("TestIt")

        if search_logs_input.styles.display == "block":
            search_logs_input.styles.display = "none"
            content_window.styles.height = "100%"
        else:
            search_logs_input.styles.display = "block"
            content_window.styles.height = "94%"
            content_window.scroll_end(animate=False)

        search_logs_input.focus()


def start():
    ui = UI()
    ui.run()


if __name__ == "__main__":
    start()

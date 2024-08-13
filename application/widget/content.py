import re
from threading import Event, Thread
from typing import Any

from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.widget import Widget
from textual.widgets import (
    Input,
    Static,
    Switch,
    TabbedContent,
    TabPane,
)

from application.docker_manager import DockerManager
from application.widget.log_viewer import LogLines
from application.widget.shell import ShellPane


class ContentWindow(Widget):
    current_index = 0
    search_keyword = ""
    matches, indices = None, None
    log_task_stop_event = Event()

    def __init__(
        self,
        docker_manager: DockerManager,
        *children: Widget,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
        disabled: bool = False,
    ) -> None:
        self.docker_manager = docker_manager
        super().__init__(
            *children, name=name, id=id, classes=classes, disabled=disabled
        )

    def compose(self) -> ComposeResult:
        global logs

        yield Horizontal(
            Input(id="search_log_input", placeholder="Search logs...", type="text"),
            Horizontal(
                Static("case-sensitive", classes="label"),
                Switch(id="case-sensitive-switch", animate=True),
                classes="case-sensitive-switch",
            ),
            classes="container",
        )
        with TabbedContent():
            with TabPane("Logs", id="logpane"):
                logs = LogLines(id="logs", highlight=True, auto_scroll=True, name="Log")
                logs.border_title = self.docker_manager.selected_container.name
                logs.scroll_end(animate=False)
                yield logs
            with TabPane("Attributes", id="attributespane"):
                attributes = LogLines(
                    id="attributes_log",
                    highlight=True,
                    auto_scroll=True,
                    name="Attributes",
                )
                attributes.border_title = self.docker_manager.selected_container.name
                attributes.scroll_end(animate=False)
                yield attributes
            with TabPane("Environment", id="environmentpane"):
                environment = LogLines(
                    id="environment_log",
                    highlight=True,
                    auto_scroll=True,
                    name="Environment",
                )
                environment.border_title = self.docker_manager.selected_container.name
                environment.scroll_end(animate=False)
                yield environment
            with TabPane("Statistics", id="statisticspane"):
                statistics = LogLines(
                    id="statistics_log",
                    highlight=True,
                    auto_scroll=True,
                    name="Statistics",
                )
                statistics.border_title = self.docker_manager.selected_container.name
                statistics.scroll_end(animate=False)
                yield statistics
            yield ShellPane(
                title="Shell", id="shellpane", docker_manager=self.docker_manager
            )

    def search_logs(self, pattern):
        case_sensitive_switch = self.query_one("#case-sensitive-switch", Switch).value
        case_sensitive = 0 if case_sensitive_switch else re.IGNORECASE
        compiled_pattern = re.compile(pattern, case_sensitive)

        results = [
            (line, i)
            for i, line in enumerate(logs.lines)
            if compiled_pattern.search(line.text)
        ]

        if results:
            self.matches, self.indices = zip(*results)
            self.matches = list(self.matches)
            self.indices = list(self.indices)
        else:
            self.matches = []
            self.indices = []

    @on(Input.Changed)
    def input_changed(self, input=Input()) -> None:
        keyword = input.value
        case_sensitive_switch = self.query_one("#case-sensitive-switch", Switch).value
        logs.case_sensitive = 0 if case_sensitive_switch else re.IGNORECASE

        if not keyword or keyword != self.search_keyword:
            self.current_index = 0
            self.search_keyword = ""
            self.indices = []

        if self.current_index == 0 and keyword:
            self.search_logs(keyword)
            self.search_keyword = keyword
            self.current_index = len(self.indices) - 1

        if self.indices:
            self.current_index -= 1
            self.update_input_border()
            logs.scroll_to(
                y=self.indices[self.current_index], animate=False, duration=0
            )
            logs.keyword = keyword
            logs.current_index = self.indices[self.current_index] + 1
            logs.refresh()  # Force refresh, just to get rid of slow visual changes.
        else:
            input.border_title = "No results"
            self.current_index = 0

    @on(Input.Submitted)
    def input_submitted(self, input=Input()) -> None:
        keyword = input.value
        case_sensitive_switch = self.query_one("#case-sensitive-switch", Switch).value
        logs.case_sensitive = 0 if case_sensitive_switch else re.IGNORECASE

        if not keyword or keyword != self.search_keyword:
            self.current_index = 0
            self.search_keyword = ""
            self.indices = []

        if self.current_index == 0 and keyword:
            self.search_logs(keyword)
            self.search_keyword = keyword
            self.current_index = len(self.indices) - 1

        if self.indices:
            self.current_index -= 1
            self.update_input_border()
            logs.scroll_to(
                y=self.indices[self.current_index], animate=False, duration=0
            )
            logs.keyword = keyword
            logs.current_index = self.indices[self.current_index] + 1
            logs.refresh()  # Force refresh, just to get rid of slow visual changes.
        else:
            input.border_title = "No results"
            self.current_index = 0

    def update_input_border(self):
        line = str(self.indices[self.current_index + 1])
        input = self.query_one("#search_log_input")
        input.border_title = f"{self.current_index + 1}/{len(self.indices) - 1}"
        input.border_subtitle = f"line {line}"

    def live_logs_task(self):
        self.docker_manager.live_container_logs(logs, self.log_task_stop_event)

    def run_log_task(self):
        self.log_task_stop_event.set()  # Signal any existing task to stop
        self.log_task_stop_event = Event()  # Create a new stop event for the new task
        Thread(target=self.live_logs_task, daemon=True).start()

    def live_statistics_task(self):
        stop_event = Event()

        while not stop_event.is_set():
            try:
                stats = self._fetch_container_stats()
                cpu, memory = self._parse_stats(stats)
                self._update_logs(cpu, memory)
            except Exception:
                stop_event.set()
                self.live_logs_task()

    def _fetch_container_stats(self):
        return self.docker_manager.selected_container.stats(stream=False)

    def _parse_stats(self, stats: dict[Any, Any]):
        try:
            cpu_usage = (
                stats["cpu_stats"]["cpu_usage"]["total_usage"]
                / stats["cpu_stats"]["system_cpu_usage"]
            )
            memory_usage_mb = stats["memory_stats"]["usage"] / (1024 * 1024)
            cpu = f"{cpu_usage * 100:.3f}%"
            memory = f"{memory_usage_mb:.3f} MB"
            return cpu, memory
        except KeyError as e:
            self.log(f"Error parsing stats: {e}")
            return "N/A", "N/A"

    def _update_logs(self, cpu: str, memory: str):
        logs.border_subtitle = f"cpu: {cpu} | ram: {memory} | logs: {len(logs.lines)}"

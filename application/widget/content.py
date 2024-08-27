import re
import time
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
from application.widget.statistics import Statistics


class ContentWindow(Widget):
    current_list_index = None
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
                yield Statistics(label="CPU (%)", id="statistics_plot_cpu")
                yield Statistics(label="RAM (MB)", id="statistics_plot_memory")

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

        current_tab = self.query_one(TabbedContent).active
        self.current_content_window: LogLines = self.query_one(
            f"#{current_tab}"
        ).children[0]
        results = [
            (line, i)
            for i, line in enumerate(self.current_content_window.lines)
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
        if self._shell_tab_active():
            return  # No text to look for when inside shell

        keyword = input.value
        self._update_case_sensitivity()

        if not keyword or keyword != self.search_keyword:
            self._reset_search_state()

        if self.current_list_index is None and keyword:
            self._perform_search(keyword)

        if self.indices:
            self._update_input_display(keyword)
        else:
            self._show_no_results()

    @on(Input.Submitted)
    def input_submitted(self, input=Input()) -> None:
        if self._shell_tab_active():
            return  # No text to look for when inside shell

        keyword = input.value
        self._update_case_sensitivity()
        self._update_list_index()
        self._update_input_display(keyword)

    def _update_case_sensitivity(self) -> None:
        case_sensitive_switch = self.query_one("#case-sensitive-switch", Switch).value
        logs.case_sensitive = 0 if case_sensitive_switch else re.IGNORECASE

    def _reset_search_state(self) -> None:
        self.current_list_index = None
        self.search_keyword = ""
        self.indices = []

    def _perform_search(self, keyword: str) -> None:
        self.search_logs(keyword)
        self.search_keyword = keyword
        self.current_list_index = len(self.indices) - 1

    def _update_input_display(self, keyword: str) -> None:
        try:
            self.update_input_border()
        except IndexError:
            return  # No matches, don't update

        self.current_content_window.scroll_to(
            y=self._get_indices_list_value(), animate=False, duration=0
        )
        self.current_content_window.keyword = keyword
        self.current_content_window.current_index = self._get_indices_list_value()
        self.current_content_window.refresh()  # Force refresh, just to get rid of slow visual changes.

    def _show_no_results(self) -> None:
        input = self.query_one("#search_log_input")
        input.border_title = "No results"
        self.current_list_index = 0

    def _update_list_index(self) -> None:
        if self.current_list_index == 0:
            self.current_list_index = len(self.indices) - 1
        else:
            self.current_list_index -= 1

    def _get_indices_list_value(self):
        return self.indices[self.current_list_index]

    def update_input_border(self) -> None:
        line = str(self._get_indices_list_value())
        input = self.query_one("#search_log_input")
        input.border_title = f"{self.current_list_index + 1}/{len(self.indices)}"
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
                self._update_plots_if_visible(cpu, memory)
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
        except KeyError:
            # TODO: Correctly handle this case.
            return "N/A", "N/A"

    def _update_plots_if_visible(self, cpu: str, memory: str):
        if self.query_one(TabbedContent).active == "statisticspane":
            cpu = float(cpu.replace("%", ""))
            memory = float(memory.replace("MB", ""))
            current_time = time.strftime("%M:%S")
            self.query_one("#statistics_plot_cpu", Statistics).update(cpu, current_time)
            self.query_one("#statistics_plot_memory", Statistics).update(
                memory, current_time
            )

    def _update_logs(self, cpu: str, memory: str):
        logs.border_subtitle = f"cpu: {cpu} | ram: {memory} | logs: {len(logs.lines)}"

    def _shell_tab_active(self):
        return self.query_one(TabbedContent).active == "shellpane"

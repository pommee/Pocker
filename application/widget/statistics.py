from __future__ import annotations

from textual.reactive import var
from textual_plotext import PlotextPlot


class Statistics(PlotextPlot):
    cpu_marker: var[str] = var("braille")
    memory_marker: var[str] = var("braille")

    def __init__(
        self,
        *,
        name: str | None = None,
        classes: str | None = None,
        disabled: bool = False,
    ) -> None:
        super().__init__(
            name=name, id="statistics_plot", classes=classes, disabled=disabled
        )
        self._cpu_data: list[float] = []
        self._memory_data: list[float] = []
        self._time: list[str] = []

    def on_mount(self) -> None:
        """Initialize the plot."""
        self.plt.date_form("M:S")

    def replot(self) -> None:
        """Redraw the plot with updated CPU and memory usage data."""
        self.plt.clear_data()
        self.plt.plot(
            self._time, self._cpu_data, marker=self.cpu_marker, label="CPU (%)"
        )
        self.plt.plot(
            self._time,
            self._memory_data,
            marker=self.memory_marker,
            label="Memory (MB)",
        )
        self.refresh()

    def update(self, cpu_usage: str, memory: str, timestamp: str) -> None:
        """Update the data for the CPU and memory usage plot.

        Args:
            cpu_usage: The current CPU usage percentage.
            memory: The current memory usage in MB.
            timestamp: The current time as a string.
        """
        self._cpu_data.append(float(cpu_usage.replace("%", "")))
        self._memory_data.append(float(memory.replace("MB", "")))
        self._time.append(timestamp)
        self.replot()

    def _watch_marker(self) -> None:
        """React to the marker being changed."""
        self.replot()

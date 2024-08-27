from __future__ import annotations

from textual.reactive import var
from textual_plotext import PlotextPlot


class Statistics(PlotextPlot):
    marker: var[str] = var("braille")

    def __init__(
        self,
        label: str,
        *,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
        disabled: bool = False,
    ) -> None:
        super().__init__(name=name, id=id, classes=classes, disabled=disabled)
        self.label = label
        self._data: list[float] = []
        self._time: list[str] = []

    def on_mount(self) -> None:
        """Initialize the plot."""
        self.plt.date_form("M:S")

    def replot(self) -> None:
        """Redraw the plot with updated usage data."""
        self.plt.clear_data()
        self.plt.plot(self._time, self._data, marker=self.marker, label=self.label)
        self.refresh()

    def update(self, data: str, timestamp: str) -> None:
        """Update the data for the usage plot.

        Args:
            data: The current value for a specific measurement.
            timestamp: The current time as a string.
        """
        self._data.append(float(data))
        self._time.append(timestamp)
        self.replot()

    def _watch_marker(self) -> None:
        """React to the marker being changed."""
        self.replot()

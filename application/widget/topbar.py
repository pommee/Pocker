from textual.app import ComposeResult
from textual.containers import Container
from textual.widgets import Label


class TopBar(Container):
    HELP_TEXT = "[b yellow]?[/b yellow] Help  [b yellow]p[/b yellow] Settings "

    def __init__(self, app_version: str, statuses=""):
        super().__init__()

        self.topbar_title = Label(
            f" [b]Pocker[/b] v{app_version}",
            id="topbar_title",
        )
        self.topbar_statuses = Label(statuses, id="topbar_statuses")
        self.topbar_help = Label(self.HELP_TEXT, id="topbar_help")

    def compose(self) -> ComposeResult:
        yield self.topbar_title
        yield self.topbar_statuses
        yield self.topbar_help

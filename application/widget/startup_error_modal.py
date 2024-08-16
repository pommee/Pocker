from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import Footer, Markdown


class StartupError(ModalScreen):
    BINDINGS = [
        Binding(key="q", action="quit", description="Quit"),
    ]

    def __init__(
        self,
        error_reason: Exception,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        self.error_reason = error_reason
        super().__init__(name, id, classes)

    def compose(self) -> ComposeResult:
        ERROR_HEADER = "# ERROR"
        REASON_HEADER = "### Reason"

        with VerticalScroll():
            yield Markdown(ERROR_HEADER)
            yield Markdown(f"{REASON_HEADER}: {self.error_reason.REASON}")

            HELP_MARKDOWN = Markdown(id="help")
            HELP_MARKDOWN._markdown = self.error_reason.HELP
            HELP_MARKDOWN.border_title = "HELP"
            yield HELP_MARKDOWN

        yield Footer()

    async def action_quit(self):
        await self.app.action_quit()

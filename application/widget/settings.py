import webbrowser

from textual import on
from textual.app import ComposeResult
from textual.containers import Grid, Horizontal, Vertical, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import Markdown, Static, Switch

from application.util.config import load_config

HELP_MD = """
\n# Settings \n
Consult the [README](https://github.com/pommee/Pocker/blob/main/README.md) to get more information about certain settings.

Press **ESC** to close this window.

---

"""


class SettingsScreen(ModalScreen):
    BINDINGS = [
        ("escape", "dismiss"),
    ]

    def __init__(
        self, name: str | None = None, id: str | None = None, classes: str | None = None
    ) -> None:
        super().__init__(name, id, classes)

    def compose(self) -> ComposeResult:
        config = load_config()

        with VerticalScroll():
            yield Markdown(HELP_MD, id="help", classes="help")

            with Grid():
                with Horizontal(id="container-show-all-containers"):
                    with Vertical():
                        yield Static("Show all containers.", classes="label")
                        with Horizontal(classes="switch-with-status"):
                            yield Switch(
                                id="show-all-containers",
                                animate=True,
                                value=config.show_all_containers,
                            )
                            yield Static(
                                str(config.show_all_containers), classes="switch-status"
                            )

                with Horizontal(id="container-start-fullscreen"):
                    with Vertical():
                        yield Static(
                            "Start in fullscreen. Containers & images won't be visible.",
                            classes="label",
                        )
                        with Horizontal(classes="switch-with-status"):
                            yield Switch(
                                id="start-fullscreen",
                                animate=True,
                                value=config.start_fullscreen,
                            )
                            yield Static(
                                str(config.start_fullscreen), classes="switch-status"
                            )

                with Horizontal(id="container-start-scroll"):
                    with Vertical():
                        yield Static("Start with scrolling.", classes="label")
                        with Horizontal(classes="switch-with-status"):
                            yield Switch(
                                id="start-scroll",
                                animate=True,
                                value=config.start_scroll,
                            )
                            yield Static(
                                str(config.start_scroll), classes="switch-status"
                            )

                with Horizontal(id="container-start-wrap"):
                    with Vertical():
                        yield Static("Start with wrapped logs.", classes="label")
                        with Horizontal(classes="switch-with-status"):
                            yield Switch(
                                id="start-wrap", animate=True, value=config.start_wrap
                            )
                            yield Static(
                                str(config.start_wrap), classes="switch-status"
                            )

    def on_switch_changed(self, value: Switch.Changed):
        config = load_config()
        switch_id = value.switch.id
        new_value = value.value

        field_name = switch_id.replace("-", "_")
        setattr(config, field_name, new_value)
        config.save()

        container = self.query_one(f"#container-{switch_id}")

        if container:
            static_widget: Static = container.query(".switch-status").first()
            static_widget.update(str(new_value))

    @on(Markdown.LinkClicked)
    def on_markdown_link_clicked(self, event: Markdown.LinkClicked) -> None:
        self.action_go(event.href)

    def action_go(self, href: str) -> None:
        webbrowser.open(href)

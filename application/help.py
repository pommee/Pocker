import webbrowser

from rich.text import Text
from textual import on
from textual.app import ComposeResult
from textual.containers import Center, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import Footer, Markdown, Static

from application.helper import get_current_version

HELP_MD = """
Pocker is a tool for the terminal to do Docker related tasks.

Repository: [https://github.com/pommee/Pocker](https://github.com/pommee/Pocker)  
Author: [pommee](https://github.com/pommee)

---

- `esc` closes this window.

### Navigation

- `q` to quit pocker.
- `?` shows this help modal.
- `l` updates the content window with logs of selected container.
- `a` same as above but displays attributes.
- `f` display content window in full-size.
- `w` will wrap logs/attributes to avoid horizontal scrolling.

### Other keys

- `ctrl+f` or `/` Show find dialog.

"""

TITLE = rf"""
  _____   _____  _______ _     _ _______  ______
 |_____] |     | |       |____/  |______ |_____/
 |       |_____| |_____  |    \_ |______ |    \_  v{get_current_version()}

"""


def get_title() -> Text:
    lines = TITLE.splitlines(keepends=True)
    return Text.assemble(
        *zip(
            lines,
            [
                "#6076FF",
                "#0087FF",
                "#00888B",
                "#008157",
            ],
        )
    )


class HelpScreen(ModalScreen):
    BINDINGS = [
        ("escape", "dismiss"),
    ]

    def compose(self) -> ComposeResult:
        yield Footer()
        with VerticalScroll() as vertical_scroll:
            with Center():
                yield Static(get_title(), classes="title")
            yield Markdown(HELP_MD + self.read_changelog())
        vertical_scroll.border_title = "Help"

    @on(Markdown.LinkClicked)
    def on_markdown_link_clicked(self, event: Markdown.LinkClicked) -> None:
        self.action_go(event.href)

    def action_go(self, href: str) -> None:
        webbrowser.open(href)

    def read_changelog(self):
        file_path = "CHANGELOG.md"
        with open(file_path, "r") as file:
            return "---  \n### Changelog\n" + file.read()

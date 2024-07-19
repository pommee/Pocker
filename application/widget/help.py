import webbrowser

import requests
from rich.text import Text
from textual import on
from textual.app import ComposeResult
from textual.containers import Center, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import Markdown, Static

from application.util.helper import POCKER_CONFIG_BASE_PATH, get_current_version

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
- `/` search in the content window.
- `a` show container attributes.
- `e` show container environment variables.
- `f` display content window in full-size.
- `v` shell in the container.
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
        with VerticalScroll():
            with Center():
                yield Static(get_title(), id="title", classes="title")
            yield Markdown(HELP_MD, id="help", classes="help")
            yield Markdown(self.read_changelog(), id="changelog", classes="changelog")

    @on(Markdown.LinkClicked)
    def on_markdown_link_clicked(self, event: Markdown.LinkClicked) -> None:
        self.action_go(event.href)

    def action_go(self, href: str) -> None:
        webbrowser.open(href)

    def read_changelog(self):
        file_path = POCKER_CONFIG_BASE_PATH / "CHANGELOG.md"
        if not file_path.exists():
            response = requests.get(
                "https://raw.githubusercontent.com/pommee/Pocker/main/CHANGELOG.md"
            )
            if response.status_code == 200:
                with open(file_path, "w") as file:
                    file.write(response.text)
            else:
                return response.text

        with open(file_path, "r") as file:
            return "---  \n# Changelog  \n\n" + file.read()

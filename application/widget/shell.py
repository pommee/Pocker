from application.widget.terminal import Terminal


from rich.text import TextType
from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import (
    TabPane,
)

from application.docker_manager import DockerManager


class ShellPane(TabPane):
    def __init__(
        self,
        title: TextType,
        docker_manager: DockerManager,
        *children: Widget,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
        disabled: bool = False,
    ):
        self.docker_manager = docker_manager
        super().__init__(
            title, *children, name=name, id=id, classes=classes, disabled=disabled
        )

    def compose(self) -> ComposeResult:
        yield Terminal(id="shell-output")

    def initialize(self) -> None:
        cmd = f"docker exec -it {self.docker_manager.selected_container.name} /bin/bash"
        terminal: Terminal = self.query_one("#shell-output")
        terminal.start(cmd)

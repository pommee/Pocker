import os
import pty
import subprocess
from threading import Thread

from rich.text import Text, TextType
from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import (
    Input,
    RichLog,
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
        yield RichLog(
            id="shell-output",
            highlight=True,
            auto_scroll=True,
            name="ShellPaneLog",
        )
        yield Input(placeholder="Enter command...", id="shell-input")

    def run_shell(self) -> None:
        self.container = self.docker_manager.selected_container
        self.output_widget = self.query_one("#shell-output", RichLog)
        self.input_widget = self.query_one("#shell-input", Input)

        self.master_fd, slave_fd = pty.openpty()
        self.process = subprocess.Popen(
            ["docker", "exec", "-it", self.container.id, "bash"],
            stdin=slave_fd,
            stdout=slave_fd,
            stderr=slave_fd,
            preexec_fn=os.setsid,
        )

        def read_output(fd):
            while True:
                output = os.read(fd, 16384).decode()
                self.app.call_from_thread(self.write_output, output)

        self.read_thread = Thread(target=read_output, args=(self.master_fd,))
        self.read_thread.daemon = True
        self.read_thread.start()

    def write_output(self, output: str) -> None:
        self.output_widget.write(Text.from_ansi(output))

    async def on_input_submitted(self, message: Input.Submitted) -> None:
        self.send_command(message.value)
        self.input_widget.clear()

    def send_command(self, command: str) -> None:
        if self.process:
            os.write(self.master_fd, (command + "\n").encode())

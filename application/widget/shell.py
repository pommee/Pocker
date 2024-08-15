import os

import subprocess
from threading import Thread

if os.name == "nt":
    from winpty import PTY
else:
    import pty

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
        self.default_shell = "bash"

        if os.name == "nt":
            self.process = PTY(80, 25)
            if not self.process.spawn(
                f"docker exec -it {self.container.id} {self.default_shell}"
            ):
                raise Exception("Failed to spawn shell")
        else:
            self.master_fd, slave_fd = pty.openpty()
            self.process = subprocess.Popen(
                ["docker", "exec", "-it", self.container.id, self.default_shell],
                stdin=slave_fd,
                stdout=slave_fd,
                stderr=slave_fd,
                preexec_fn=os.setsid,
            )

        def read_output(fd):
            while True:
                if os.name == "nt":
                    output = fd.read(16384)
                    if not output:
                        continue
                else:
                    output = os.read(fd, 16384).decode()
                self.app.call_from_thread(self.write_output, output)

        if os.name == "nt":
            self.read_thread = Thread(target=read_output, args=(self.process,))
        else:
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
            if os.name == "nt":
                self.process.write(command + "\n")
            else:
                os.write(self.master_fd, (command + "\n").encode())

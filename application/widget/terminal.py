"""
Thanks to Mischa Schindowski for a good base to use:
https://github.com/mitosch/textual-terminal/blob/main/textual_terminal/_terminal.py
"""

from __future__ import annotations

import os
import signal
import shlex
import asyncio
from asyncio import Task
import pty
import struct
import termios
import re
from pathlib import Path

import pyte
from pyte.screens import Char

from rich.text import Text
from rich.style import Style
from rich.color import ColorParseError

from textual.widget import Widget
from textual import events

from textual import log


class TerminalPyteScreen(pyte.Screen):
    """Overrides the pyte.Screen class to be used with TERM=linux."""

    def set_margins(self, *args, **kwargs):
        kwargs.pop("private", None)
        return super().set_margins(*args, **kwargs)


class TerminalDisplay:
    """Rich display for the terminal."""

    def __init__(self, lines):
        self.lines = lines

    def __rich_console__(self, _console, _options):
        line: Text
        for line in self.lines:
            yield line


_re_ansi_sequence = re.compile(r"(\x1b\[\??[\d;]*[a-zA-Z])")
DECSET_PREFIX = "\x1b[?"


class Terminal(Widget, can_focus=True):
    """Terminal textual widget."""

    textual_colors: dict | None

    def __init__(
        self,
        default_colors: str | None = "system",
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        self.command = None
        self.default_colors = default_colors

        if default_colors == "textual":
            self.textual_colors = self.detect_textual_colors()

        # default size, will be adapted on_resize
        self.ncol = 80
        self.nrow = 24
        self.mouse_tracking = False

        # variables used when starting the emulator: self.start()
        self.emulator: TerminalEmulator = None
        self.send_queue: asyncio.Queue = None
        self.recv_queue: asyncio.Queue = None
        self.recv_task: Task = None

        self._display = self.initial_display()
        self._screen = TerminalPyteScreen(self.ncol, self.nrow)
        self.stream = pyte.Stream(self._screen)

        super().__init__(name=name, id=id, classes=classes)

    def start(self, command: str) -> None:
        if self.emulator is not None:
            return

        self.emulator = TerminalEmulator(command=command)
        self.emulator.start()
        self.send_queue = self.emulator.recv_queue
        self.recv_queue = self.emulator.send_queue
        self.recv_task = asyncio.create_task(self.recv())

    def stop(self) -> None:
        if self.emulator is None:
            return

        self._display = self.initial_display()

        self.recv_task.cancel()

        self.emulator.stop()
        self.emulator = None

    def render(self):
        return self._display

    async def on_key(self, event: events.Key) -> None:
        if self.emulator is None:
            return

        event.stop()

        if event.key == "tab":
            await self.send_queue.put(["stdin", "\t"])
            return

        if event.key == "backspace":
            await self.send_queue.put(["stdin", "\x08"])
            return

        if event.key == "enter":
            await self.send_queue.put(["stdin", "\r"])
            return

        if event.key == "up":
            await self.send_queue.put(["stdin", "\x1b[A"])
            return

        if event.key == "down":
            await self.send_queue.put(["stdin", "\x1b[B"])
            return

        if event.character:
            await self.send_queue.put(["stdin", event.character])

    async def on_resize(self, _event: events.Resize) -> None:
        if self.emulator is None:
            return

        self.ncol = self.size.width
        self.nrow = self.size.height
        await self.send_queue.put(["set_size", self.nrow, self.ncol])
        self._screen.resize(self.nrow, self.ncol)

    async def on_click(self, event: events.MouseEvent):
        if self.emulator is None:
            return

        if self.mouse_tracking is False:
            return

        await self.send_queue.put(["click", event.x, event.y, event.button])

    async def on_mouse_scroll_down(self, event: events.MouseScrollDown):
        if self.emulator is None:
            return

        if self.mouse_tracking is False:
            return

        await self.send_queue.put(["scroll", "down", event.x, event.y])

    async def on_mouse_scroll_up(self, event: events.MouseScrollUp):
        if self.emulator is None:
            return

        if self.mouse_tracking is False:
            return

        await self.send_queue.put(["scroll", "up", event.x, event.y])

    async def recv(self):
        try:
            while True:
                message = await self.recv_queue.get()
                cmd = message[0]
                if cmd == "setup":
                    await self.send_queue.put(["set_size", self.nrow, self.ncol])
                elif cmd == "stdout":
                    chars = message[1]

                    for sep_match in re.finditer(_re_ansi_sequence, chars):
                        sequence = sep_match.group(0)
                        if sequence.startswith(DECSET_PREFIX):
                            parameters = sequence.removeprefix(DECSET_PREFIX).split(";")
                            if "1000h" in parameters:
                                self.mouse_tracking = True
                            if "1000l" in parameters:
                                self.mouse_tracking = False

                    try:
                        self.stream.feed(chars)
                    except TypeError as error:
                        # pyte could get into errors here: Screen.cursor_position()
                        # is getting 4 args. Happens when TERM=linux and using
                        # w3m (default options).

                        # This also happened when TERM is not set to "linux" and w3m
                        # is started without the option "-no-mouse".
                        log.warning("could not feed:", error)

                    lines = []
                    last_char: Char
                    last_style: Style
                    for y in range(self._screen.lines):
                        line_text = Text()
                        line = self._screen.buffer[y]
                        style_change_pos: int = 0
                        for x in range(self._screen.columns):
                            char: Char = line[x]

                            line_text.append(char.data)

                            # if style changed, stylize it with rich
                            if x > 0:
                                last_char = line[x - 1]
                                if (
                                    not self.char_style_cmp(char, last_char)
                                    or x == self._screen.columns - 1
                                ):
                                    last_style = self.char_rich_style(last_char)
                                    line_text.stylize(
                                        last_style, style_change_pos, x + 1
                                    )
                                    style_change_pos = x

                            if (
                                self._screen.cursor.x == x
                                and self._screen.cursor.y == y
                            ):
                                line_text.stylize("reverse", x, x + 1)

                        lines.append(line_text)

                    self._display = TerminalDisplay(lines)
                    self.refresh()

                elif cmd == "disconnect":
                    self.stop()
        except asyncio.CancelledError:
            pass

    def char_rich_style(self, char: Char) -> Style:
        """Returns a rich.Style from the pyte.Char."""

        foreground = self.detect_color(char.fg)
        background = self.detect_color(char.bg)
        if self.default_colors == "textual":
            if background == "default":
                background = self.textual_colors["background"]
            if foreground == "default":
                foreground = self.textual_colors["foreground"]

        style: Style
        try:
            style = Style(
                color=foreground,
                bgcolor=background,
                bold=char.bold,
            )
        except ColorParseError as error:
            log.warning("color parse error:", error)
            style = None

        return style

    def char_style_cmp(self, given: Char, other: Char) -> bool:
        """Compares two pyte.Chars and returns if these are the same.

        Returns:
            True    if char styles are the same
            False   if char styles differ
        """

        if (
            given.fg == other.fg
            and given.bg == other.bg
            and given.bold == other.bold
            and given.italics == other.italics
            and given.underscore == other.underscore
            and given.strikethrough == other.strikethrough
            and given.reverse == other.reverse
            and given.blink == other.blink
        ):
            return True

        return False

    def char_style_default(self, char: Char) -> bool:
        """Returns True if the given char has a default style."""

        if (
            char.fg == "default"
            and char.bg == "default"
            and char.bold is False
            and char.italics is False
            and char.underscore is False
            and char.strikethrough is False
            and char.reverse is False
            and char.blink is False
        ):
            return True

        return False

    def detect_color(self, color: str) -> str:
        """Tries to detect the correct Rich-Color based on a color name.

        * Returns #<color> if <color> is a hex-definition without "#"
        * Fixes wrong ANSI color names.
        """

        if re.match("[0-9a-f]{6}", color, re.IGNORECASE):
            return f"#{color}"

        return color

    def detect_textual_colors(self) -> dict:
        """Returns the currently used colors of textual depending on dark-mode."""

        return self.app.current_theme.to_color_system().generate()

    def initial_display(self) -> TerminalDisplay:
        """Returns the display when initially creating the terminal or clearing it."""

        return TerminalDisplay([Text()])


class TerminalEmulator:
    def __init__(self, command: str):
        self.ncol = 80
        self.nrow = 24
        self.data_or_disconnect = None
        self.run_task: asyncio.Task = None
        self.send_task: asyncio.Task = None

        self.fd = self.open_terminal(command=command)
        self.p_out = os.fdopen(self.fd, "w+b", 0)
        self.recv_queue = asyncio.Queue()
        self.send_queue = asyncio.Queue()
        self.event = asyncio.Event()

    def start(self):
        self.run_task = asyncio.create_task(self._run())
        self.send_task = asyncio.create_task(self._send_data())

    def stop(self):
        self.run_task.cancel()
        self.send_task.cancel()

        os.kill(self.pid, signal.SIGTERM)
        os.waitpid(self.pid, 0)

    def open_terminal(self, command: str):
        self.pid, fd = pty.fork()
        if self.pid == 0:
            argv = shlex.split(command)
            # OPTIMIZE: do not use a fixed LC_ALL
            env = dict(TERM="xterm", LC_ALL="en_US.UTF-8", HOME=str(Path.home()))
            os.execvpe(argv[0], argv, env)

        return fd

    async def _run(self):
        loop = asyncio.get_running_loop()

        def on_output():
            try:
                self.data_or_disconnect = self.p_out.read(65536).decode()
                self.event.set()
            except UnicodeDecodeError as error:
                # NOTE: this happens sometimes, eg in w3m browsing wrongly decoded docs
                # OPTIMIZE: here a screen refresh could be needed. some chars are
                #   left in the buffer when scrolling
                log.warning("decode error:", error)
            except Exception:
                # this exception tell's us to end the emulator:
                # throwed when exiting the command
                loop.remove_reader(self.p_out)
                self.data_or_disconnect = None
                self.event.set()

        loop.add_reader(self.p_out, on_output)
        await self.send_queue.put(["setup", {}])
        try:
            while True:
                msg = await self.recv_queue.get()
                if msg[0] == "stdin":
                    self.p_out.write(msg[1].encode())
                elif msg[0] == "set_size":
                    import fcntl

                    winsize = struct.pack("HH", msg[1], msg[2])
                    fcntl.ioctl(self.fd, termios.TIOCSWINSZ, winsize)
                elif msg[0] == "click":
                    x = msg[1] + 1
                    y = msg[2] + 1
                    button = msg[3]

                    if button == 1:
                        self.p_out.write(f"\x1b[<0;{x};{y}M".encode())
                        self.p_out.write(f"\x1b[<0;{x};{y}m".encode())
                elif msg[0] == "scroll":
                    x = msg[2] + 1
                    y = msg[3] + 1

                    if msg[1] == "up":
                        self.p_out.write(f"\x1b[<64;{x};{y}M".encode())
                    if msg[1] == "down":
                        self.p_out.write(f"\x1b[<65;{x};{y}M".encode())
        except asyncio.CancelledError:
            pass

    async def _send_data(self):
        try:
            while True:
                await self.event.wait()
                self.event.clear()
                if self.data_or_disconnect is not None:
                    await self.send_queue.put(["stdout", self.data_or_disconnect])
                else:
                    await self.send_queue.put(["disconnect", 1])
        except asyncio.CancelledError:
            pass

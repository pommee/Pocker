from __future__ import annotations

import re
from typing import TYPE_CHECKING, Optional, cast

from rich.console import RenderableType
from rich.highlighter import Highlighter, ReprHighlighter
from rich.measure import measure_renderables
from rich.pretty import Pretty
from rich.protocol import is_renderable
from rich.segment import Segment
from rich.text import Text
from textual.cache import LRUCache
from textual.geometry import Region, Size
from textual.reactive import var
from textual.scroll_view import ScrollView
from textual.strip import Strip

if TYPE_CHECKING:
    from typing_extensions import Self


class LogLines(ScrollView, can_focus=True):
    COMPONENT_CLASSES = {
        "loglines--filter-highlight",
        "loglines--filter-highlight-selected",
    }

    max_lines: var[int | None] = var[Optional[int]](None)
    min_width: var[int] = var(78)
    wrap: var[bool] = var(False)
    highlight: var[bool] = var(False)
    markup: var[bool] = var(False)
    auto_scroll: var[bool] = var(True)

    def __init__(
        self,
        *,
        max_lines: int | None = None,
        min_width: int = 78,
        wrap: bool = False,
        highlight: bool = False,
        markup: bool = False,
        auto_scroll: bool = True,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
        disabled: bool = False,
    ) -> None:
        super().__init__(name=name, id=id, classes=classes, disabled=disabled)
        self.max_lines = max_lines
        self.keyword = None
        self.current_index = None
        self.case_sensitive = False
        self._start_line: int = 0
        self.lines: list[Strip] = []
        self._line_cache: LRUCache[tuple[int, int, int, int], Strip]
        self._line_cache = LRUCache(1024)
        self.max_width: int = 0
        self.min_width = min_width
        self.wrap = wrap
        self.highlight = highlight
        self.markup = markup
        self.auto_scroll = auto_scroll
        self.highlighter: Highlighter = ReprHighlighter()
        self._last_container_width: int = min_width

    def notify_style_update(self) -> None:
        self._line_cache.clear()

    def on_resize(self) -> None:
        self._last_container_width = self.scrollable_content_region.width

    def _make_renderable(self, content: RenderableType | object) -> RenderableType:
        renderable: RenderableType
        if not is_renderable(content):
            renderable = Pretty(content)
        else:
            if isinstance(content, str):
                if self.markup:
                    renderable = Text.from_markup(content)
                else:
                    renderable = Text(content)
                if self.highlight:
                    renderable = self.highlighter(renderable)
            else:
                renderable = cast(RenderableType, content)

        if isinstance(renderable, Text):
            renderable.expand_tabs()

        return renderable

    def write(
        self,
        content: RenderableType | object,
        width: int | None = None,
        expand: bool = False,
        shrink: bool = True,
        scroll_end: bool | None = None,
    ) -> Self:
        auto_scroll = self.auto_scroll if scroll_end is None else scroll_end

        console = self.app.console
        render_options = console.options

        renderable = self._make_renderable(content)

        if isinstance(renderable, Text) and not self.wrap:
            render_options = render_options.update(overflow="ignore", no_wrap=True)

        render_width = measure_renderables(
            console, render_options, [renderable]
        ).maximum

        container_width = (
            self.scrollable_content_region.width if width is None else width
        )

        container_width = (
            container_width if container_width else self._last_container_width
        )

        if expand and render_width < container_width:
            render_width = container_width
        if shrink and render_width > container_width:
            render_width = container_width

        render_width = max(render_width, self.min_width)

        segments = self.app.console.render(
            renderable, render_options.update_width(render_width)
        )
        lines = list(Segment.split_lines(segments))
        if not lines:
            self.lines.append(Strip.blank(render_width))
        else:
            self.max_width = max(
                self.max_width,
                max(sum([segment.cell_length for segment in _line]) for _line in lines),
            )
            strips = Strip.from_lines(lines)
            for strip in strips:
                strip.adjust_cell_length(render_width)
            self.lines.extend(strips)

            if self.max_lines is not None and len(self.lines) > self.max_lines:
                self._start_line += len(self.lines) - self.max_lines
                self.refresh()
                self.lines = self.lines[-self.max_lines :]
        self.virtual_size = Size(self.max_width, len(self.lines))
        if auto_scroll:
            self.scroll_end(animate=False)

        return self

    def clear(self) -> Self:
        self.lines.clear()
        self._line_cache.clear()
        self._start_line = 0
        self.max_width = 0
        self.virtual_size = Size(self.max_width, len(self.lines))
        self.refresh()
        return self

    def render_line(self, y: int) -> Strip:
        filter_style_line = self.get_component_rich_style("loglines--filter-highlight")
        filter_style_word = self.get_component_rich_style(
            "loglines--filter-highlight-selected"
        )
        scroll_x, scroll_y = self.scroll_offset
        line = self._render_line(scroll_y + y, scroll_x, self.size.width)
        text = Text.from_ansi(line.text)

        if self.keyword:
            matches = list(
                re.finditer(
                    self.keyword,
                    line.text,
                    flags=self.case_sensitive,
                )
            )

            if self.current_index == scroll_y + y:
                text.stylize(filter_style_line, 0, text.cell_len)

            if matches:
                for match in matches:
                    text.stylize(filter_style_word, *match.span())
            else:
                text.stylize("dim")

            strip = Strip(text.render(self.app.console), text.cell_len)

        else:
            strip = line.apply_style(self.rich_style)

        return strip

    def render_lines(self, crop: Region) -> list[Strip]:
        lines = self._styles_cache.render_widget(self, crop)
        return lines

    def _render_line(self, y: int, scroll_x: int, width: int) -> Strip:
        if y >= len(self.lines):
            return Strip.blank(width, self.rich_style)

        key = (y + self._start_line, scroll_x, width, self.max_width)
        if key in self._line_cache:
            return self._line_cache[key]

        line = self.lines[y].crop_extend(scroll_x, scroll_x + width, self.rich_style)

        self._line_cache[key] = line
        return line

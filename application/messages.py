from dataclasses import dataclass

from textual.message import Message
from textual.widgets import ListItem


@dataclass
class ContainersAndImagesExpaned(Message, bubble=True):
    pass


@dataclass
class ClickedContainer(Message, bubble=True):
    clicked_container: ListItem

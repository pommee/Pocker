from dataclasses import dataclass

from docker.models.images import Image
from textual import on
from textual.app import ComposeResult
from textual.message import Message
from textual.widget import Widget
from textual.widgets import (
    Label,
    ListItem,
    ListView,
)

from application.docker_manager import DockerManager


class PockerImages(Widget):
    BORDER_TITLE: str = "Images"

    def __init__(
        self,
        docker_manager: DockerManager,
        *children: Widget,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
        disabled: bool = False,
    ) -> None:
        self.docker_manager = docker_manager
        super().__init__(
            *children, name=name, id=id, classes=classes, disabled=disabled
        )

    def compose(self) -> ComposeResult:
        with ListView(id="ContainersAndImagesListView"):
            image: Image
            for image in self.docker_manager.images:
                if image.tags:
                    name = image.tags[0].split(":")[0]
                    version = image.tags[0].split(":")[1]
                    yield ListItem(Label(f"{name}:{version}"))

    @dataclass
    class ClickedImage(Message, bubble=True):
        clicked_image: ListItem

    # TODO: Implement fetching relevant information regarding an image.
    def on_list_view_selected(self, selected: ListView.Selected):
        self.notify(
            title="Not implemented",
            message="Viewing images will be supported in future releases.",
            timeout=6,
        )
        # self.post_message(PockerImages.ClickedImage(selected.item))

    @on(ClickedImage)
    def _update_selected_container(self, new_selected_image: ClickedImage):
        selected_image = new_selected_image.clicked_image
        images = self.query_one(ListView)
        image: ListItem
        for image in images.children:
            if image.has_class("selected"):
                image.remove_class("selected")

        selected_image.add_class("selected")

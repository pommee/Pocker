from docker.models.images import Image
from textual.app import ComposeResult
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

    # TODO: Implement fetching relevant information regarding an image.
    def on_list_view_selected(self, item: ListItem):
        pass

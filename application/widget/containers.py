from docker.models.containers import Container
from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import (
    Label,
    ListItem,
    ListView,
)

from application.docker_manager import DockerManager


class PockerContainers(Widget):
    BORDER_TITLE: str = "Containers"

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
        self.highlighted_child_index = 0
        self.first_run = True
        super().__init__(
            *children, name=name, id=id, classes=classes, disabled=disabled
        )

    def compose(self) -> ComposeResult:
        self.list_view = ListView(id="ContainersAndImagesListView")

        with self.list_view:
            container: Container
            for name, container in self.docker_manager.containers.items():
                yield ListItem(
                    Label(name),
                    id=name,
                    classes=self.docker_manager.status(container),
                )

    def on_list_view_highlighted(self, highlighted: ListView.Highlighted):
        if self.first_run:
            self.first_run = False
            return

        list_view = highlighted.list_view
        list_item = highlighted.item

        list_item.add_class("selected")
        list_view.children[self.highlighted_child_index].remove_class("selected")
        self.highlighted_child_index = list_view.index

    async def on_mount(self) -> None:
        self.list_view.children[0].add_class("selected")
        self.list_view.sort_children(
            key=lambda listview_container: listview_container.has_class("running"),
            reverse=True,
        )

    def live_status_events_task(self):
        event: dict[str, str]
        for event in self.docker_manager.client.events(decode=True):
            if event["Type"] == "container" and event["status"] in [
                "start",
                "stop",
                "die",
            ]:
                container_name = event.get("Actor").get("Attributes").get("name")
                container_list_item: ListItem = self.list_view.get_child_by_id(
                    container_name
                )
                status = ""
                was_selected: bool = container_list_item.has_class("selected")

                if event["status"] == "start":
                    status = "running"
                elif event["status"] == "stop":
                    status = "stopped"
                else:
                    status = "down"

                container_list_item.set_classes(status)
                if was_selected:
                    container_list_item.add_class("selected")

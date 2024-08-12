import asyncio

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

    async def _validate_if_any_container_selected(self):
        for child in self.list_view.walk_children():
            if child.has_class("selected"):
                return

        first_child = self.list_view.query()[0]
        first_child.add_class("selected")

    def live_status_events_task(self, loop: asyncio.AbstractEventLoop):
        event: dict[str, str]
        for event in self.docker_manager.client.events(decode=True):
            if event["Type"] == "container":
                container_name = event.get("Actor").get("Attributes").get("name")
                match event["status"]:
                    case "start":
                        asyncio.run_coroutine_threadsafe(
                            self._container_started(container_name), loop
                        )
                    case "stop":
                        asyncio.run_coroutine_threadsafe(
                            self._container_status_changed(container_name, "stopping"),
                            loop,
                        )
                    case "die":
                        asyncio.run_coroutine_threadsafe(
                            self._container_status_changed(container_name, "down"), loop
                        )
                    case "destroy":
                        asyncio.run_coroutine_threadsafe(
                            self._container_destroyed(container_name), loop
                        )

    async def _container_started(self, container_name: str):
        for child in self.list_view.walk_children():
            if child.id == container_name:
                child.remove_class("down")
                child.set_class(True, "running")
                await self._validate_if_any_container_selected()
                return

        self.docker_manager.append_container(container_name)
        await self.list_view.append(
            ListItem(Label(container_name), id=container_name, classes="running")
        )
        await self._validate_if_any_container_selected()

    async def _container_status_changed(self, container_name: str, status: str):
        container_list_item: ListItem = self.list_view.get_child_by_id(container_name)
        was_selected: bool = container_list_item.has_class("selected")

        container_list_item.set_classes(status)
        if was_selected:
            container_list_item.add_class("selected")

    async def _container_destroyed(self, container_name: str):
        for x in self.list_view.walk_children():
            if x.id == container_name:
                self.list_view.remove_children(f"#{container_name}")
                break

        await self._validate_if_any_container_selected()

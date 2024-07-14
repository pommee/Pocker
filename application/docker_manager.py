import logging
import time
from threading import Event

import docker
from docker.models.containers import Container
from docker.models.images import Image, ImageCollection
from textual.logging import TextualHandler
from textual.widgets import RichLog

from application.util.config import CONFIG_PATH, Config

logging.basicConfig(
    level="INFO",
    handlers=[TextualHandler()],
)


class DockerManager:
    def __init__(self, config: Config) -> None:
        self.client = docker.from_env()
        self.containers = {
            container.name: container
            for container in self.client.containers.list(all=config.show_all_containers)
        }
        self.images: ImageCollection = self.client.images.list(all=True)
        try:
            self.selected_container: Container = list(self.containers.values())[0]
        except IndexError:
            raise SystemExit(
                "No containers to display. Set 'show_all_containers' to true in config to display exited containers.\n"
                f"Config can be found at {CONFIG_PATH}"
            )
        self.config = config

    @property
    def attributes(self) -> Container:
        return self.selected_container.attrs

    @property
    def environment(self) -> dict:
        return self.selected_container.attrs.get("Config").get("Env")

    @property
    def statistics(self) -> Image:
        return self.selected_container.stats(stream=False)

    def logs(self):
        logs: bytes = self.selected_container.logs(
            tail=self.config.log_tail, follow=False, stream=False
        )
        return logs.decode("utf-8").strip()

    def status(self, container: Container):
        status = "[U]"
        if container.status == "running":
            status = "running"
        else:
            status = "down"

        return status

    def live_container_logs(self, logs: RichLog, stop_event: Event):
        logs.clear()
        last_fetch = time.time()

        while not stop_event.is_set():
            new_logs = self.selected_container.logs(since=last_fetch)

            if new_logs:
                last_fetch = time.time()
                logs.write(new_logs.decode("utf-8").rstrip())

            time.sleep(1)

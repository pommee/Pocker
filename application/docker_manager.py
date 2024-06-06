import logging
import time
from threading import Event

import docker
from docker.models.containers import Container, ContainerCollection
from docker.models.images import ImageCollection
from textual.logging import TextualHandler
from textual.widgets import RichLog

from application.config import Config

logging.basicConfig(
    level="INFO",
    handlers=[TextualHandler()],
)


class DockerManager:
    def __init__(self, config: Config) -> None:
        self.client = docker.from_env()
        self.containers: ContainerCollection = self.client.containers.list(
            all=True, sparse=True
        )
        self.images: ImageCollection = self.client.images.list(all=True)
        self.selected_container = self.containers[0].attrs["Names"][0].replace("/", "")
        self.config = config

    def container(self, container_name: str) -> Container:
        return self.client.containers.get(container_name)

    def curr_container(self):
        return self.container(self.selected_container)

    def logs(self):
        logs: bytes = self.curr_container().logs(
            tail=self.config.log_tail, follow=False, stream=False
        )
        return logs.decode("utf-8").strip()

    def attributes(self):
        return self.container(self.selected_container).attrs

    def status(self, container_name: str):
        is_running = self.container(container_name).attrs.get("State").get("Running")

        status = "[U]"
        if is_running is True:
            status = "running"
        if not is_running:
            status = "down"
        return status

    def live_container_logs(self, logs: RichLog, stop_event: Event):
        logs.clear()

        while not stop_event.is_set():
            if len(logs.lines) == 0:
                last_fetch = time.time()
                # If logs are empty, write initial logs
                logs.write(self.logs())

            new_logs = (
                self.container(self.selected_container)
                .logs(since=last_fetch)
                .decode("utf-8")
            )

            if len(new_logs) > 0:
                last_fetch = time.time()
                logs.write(new_logs.rstrip())

            time.sleep(0.6)

import logging
from threading import Event
import time
import docker
from docker.models.containers import Container, ContainerCollection
from textual.widgets import RichLog
from textual.logging import TextualHandler

logging.basicConfig(
    level="INFO",
    handlers=[TextualHandler()],
)


class DockerManager:
    def __init__(self) -> None:
        self.client = docker.from_env()
        self.containers: ContainerCollection = self.client.containers.list(all=True)
        self.images = self.client.images.list(all=True)
        self.selected_container = self.containers[0].name

    def container(self, container_name: str) -> Container:
        return self.client.containers.get(container_name)

    def curr_container(self):
        return self.container(self.selected_container)

    def logs(self):
        return (
            self.container(self.selected_container)
            .logs(follow=False)
            .decode("utf-8")
            .strip()
        )

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

    def live_container_logs(self, logs, stop_event: Event):
        logging.info("#STATE# test %s", logs)
        logs.clear()

        while not stop_event.is_set():
            if len(logs.lines) == 0:
                last_fetch = time.time()
                # If logs are empty, write initial logs
                logs.write(
                    self.container(self.selected_container)
                    .logs()
                    .decode("utf-8")
                    .strip()
                )

            new_logs = (
                self.container(self.selected_container)
                .logs(since=last_fetch)
                .decode("utf-8")
            )

            if len(new_logs) > 0:
                last_fetch = time.time()
                logs.write(new_logs.rstrip())

            time.sleep(0.2)

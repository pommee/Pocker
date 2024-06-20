import logging
import time
from threading import Event, Thread

import docker
from docker.models.containers import Container, ContainerCollection
from docker.models.images import ImageCollection
from textual.logging import TextualHandler
from textual.widgets import RichLog

from application.util.config import Config

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
        log_task_stop_event = Event()

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
        logs.write(self.logs())

        while not stop_event.is_set():
            new_logs = (
                self.container(self.selected_container)
                .logs(since=last_fetch)
                .decode("utf-8")
            )

            if new_logs:
                last_fetch = time.time()
                logs.write(new_logs.rstrip())

            time.sleep(1)

    def run_log_task(self):
        global log_task_stop_event
        log_task_stop_event.set()  # Signal any existing task to stop
        log_task_stop_event = Event()  # Create a new stop event for the new task
        Thread(target=self.live_logs_task, daemon=True).start()

    def live_logs_task(self, logs):
        self.live_container_logs(logs, log_task_stop_event)

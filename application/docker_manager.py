import logging
from threading import Event

import docker
from docker.models.containers import Container
from docker.models.images import Image, ImageCollection
from textual.logging import TextualHandler

from application.util.config import CONFIG_PATH, Config
from application.widget.log_viewer import LogLines

logging.basicConfig(
    level="INFO",
    handlers=[TextualHandler()],
)


class NoVisibleContainers(Exception):
    REASON = "No container(s) to display"
    HELP = f"""
- No containers are running.
- Set `show_all_containers` to true in config to display exited containers.  

Config can be found at `{CONFIG_PATH}`
"""
    pass


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
            raise NoVisibleContainers()
        self.selected_image = None
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

    def append_container(self, container_name: str):
        self.containers[container_name] = self.client.containers.get(container_name)

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

    def live_container_logs(self, logs: LogLines, stop_event: Event):
        logs.clear()

        try:
            log_stream = self.selected_container.logs(stream=True, follow=True)

            for log in log_stream:
                if stop_event.is_set():
                    break
                logs.write(log.decode("utf-8").rstrip())

        except Exception:
            stop_event.set()  # Handle exceptions, for example, if the container is removed

        finally:
            log_stream.close()  # Clean up or close resources if needed

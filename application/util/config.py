from pydantic import BaseModel
from yaml import dump, safe_load

from application.util.helper import POCKER_CONFIG_BASE_PATH

CONFIG_PATH = POCKER_CONFIG_BASE_PATH / "config.yaml"


class Config(BaseModel):
    log_tail: int = 2000
    max_log_lines: int = 2000
    start_wrap: bool = False
    show_all_containers: bool = False
    start_fullscreen: bool = False
    start_scroll: bool = True
    keymap: dict[str, str] = {
        "quit": "q",
        "logs": "l",
        "attributes": "a",
        "environment": "e",
        "statistics": "d",
        "shell": "v",
        "fullscreen": "f",
        "wrap-logs": "w",
        "toggle-scroll": "s",
    }

    def __repr__(self) -> str:
        return super().__repr__(self.start_wrap)

    def create_default_config(self):
        default_config = {
            "log_tail": self.log_tail,
            "max_log_lines": self.max_log_lines,
            "start_wrap": self.start_wrap,
            "show_all_containers": self.show_all_containers,
            "start_fullscreen": self.start_fullscreen,
            "start_scroll": self.start_scroll,
            "keymap": self.keymap,
        }
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with CONFIG_PATH.open("w") as file:
            dump(default_config, file)

    def save(self):
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with CONFIG_PATH.open("w") as file:
            dump(self.model_dump(), file)


def load_config():
    if not CONFIG_PATH.exists():
        Config().create_default_config()
    with CONFIG_PATH.open() as file:
        config_dict = safe_load(file)
        return Config(**config_dict)

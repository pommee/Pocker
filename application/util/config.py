import os

from pydantic import BaseModel
from yaml import dump, safe_load

from application.util.helper import POCKER_CONFIG_BASE_PATH

CONFIG_PATH = POCKER_CONFIG_BASE_PATH / "config.yaml"


class Config(BaseModel):
    log_tail: int
    max_log_lines: int
    start_wrap: bool
    start_fullscreen: bool
    start_scroll: bool
    keymap: dict[str, str]

    def __repr__(self) -> str:
        return super().__repr__(self.start_wrap)


def create_default_config():
    default_config = {
        "log_tail": 2000,
        "max_log_lines": 2000,
        "start_wrap": False,
        "start_fullscreen": False,
        "start_scroll": True,
        "keymap": {
            "quit": "q",
            "logs": "l",
            "attributes": "a",
            "environment": "e",
            "statistics": "d",
            "fullscreen": "f",
            "wrap-logs": "w",
            "toggle-scroll": "s",
        },
    }
    with open(CONFIG_PATH, "w") as file:
        dump(default_config, file)


def load_config():
    if not os.path.exists(CONFIG_PATH):
        create_default_config()
    with open(CONFIG_PATH, "r") as file:
        config_dict = safe_load(file)
        return Config(**config_dict)

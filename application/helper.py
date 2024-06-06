import datetime
import os
import subprocess
from pydantic import BaseModel
import requests
from packaging.version import parse as version_parse
import yaml


def get_latest_version():
    response = requests.get(
        "https://api.github.com/repos/pommee/Pocker/tags?per_page=1"
    )

    if response.status_code == 200:
        response: dict = response.json()[0]
        latest_version = response.get("name")
        return version_parse(latest_version)
    else:
        return None


def get_current_version():
    try:
        result = subprocess.run(
            ["pipx", "list", "--short"], text=True, capture_output=True, check=True
        )

        for line in result.stdout.splitlines():
            if "pocker" in line:
                version = line.split()[1]
                return version

    except subprocess.CalledProcessError as e:
        print(f"An error occurred: {e}")
        return None


class Version_Fetch(BaseModel):
    time_fetched: datetime.datetime
    version_fetched: str


def write_latest_version_fetch(version):
    version_fetch_dict = {
        "time_fetched": datetime.datetime.now(),
        "version_fetched": version,
    }

    with open("latest_version_fetch.yaml", "w") as file:
        yaml.safe_dump(version_fetch_dict, file)


def read_latest_version_fetch():
    if not os.path.exists("latest_version_fetch.yaml"):
        current_version = version_parse(get_current_version())
        write_latest_version_fetch(current_version.base_version)
    with open("latest_version_fetch.yaml", "r") as file:
        fetch_dict = yaml.safe_load(file)
        return Version_Fetch(**fetch_dict)


def time_since_last_fetch():
    return (
        datetime.datetime.now() - read_latest_version_fetch().time_fetched
    ).total_seconds() / 60

import datetime
import os
import re
import subprocess
from pathlib import Path

import requests
import yaml
from colorama import Fore, Style
from packaging.version import parse as version_parse
from pydantic import BaseModel

POCKER_CONFIG_BASE_PATH = Path.home() / ".config/pocker"


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

    except subprocess.CalledProcessError:
        return None


class Version_Fetch(BaseModel):
    time_fetched: datetime.datetime
    version_fetched: str


def write_latest_version_fetch(version):
    version_fetch_dict = {
        "time_fetched": datetime.datetime.now(),
        "version_fetched": version,
    }
    if not os.path.exists(POCKER_CONFIG_BASE_PATH):
        POCKER_CONFIG_BASE_PATH.mkdir()

    with open(POCKER_CONFIG_BASE_PATH / "latest_version_fetch.yaml", "w") as file:
        yaml.safe_dump(version_fetch_dict, file)


def read_latest_version_fetch():
    if not os.path.exists(POCKER_CONFIG_BASE_PATH / "latest_version_fetch.yaml"):
        latest_version = get_latest_version()
        write_latest_version_fetch(latest_version.base_version)
    with open(POCKER_CONFIG_BASE_PATH / "latest_version_fetch.yaml", "r") as file:
        fetch_dict = yaml.safe_load(file)
        return Version_Fetch(**fetch_dict)


def time_since_last_fetch():
    return (
        datetime.datetime.now() - read_latest_version_fetch().time_fetched
    ).total_seconds() / 60


commit_and_link_pattern = (
    r"\[([a-f0-9]+)\]\((https://github\.com/pommee/Pocker/commit/[a-f0-9]+)\)"
)
changed_line = r"\(\[([a-f0-9]+)\]\(([^)]+)\)\)"


def bright_text(text):
    return f"{Style.BRIGHT}{text}{Style.RESET_ALL}"


class Release:
    def __init__(self, unparsed_text: dict) -> None:
        self.unparsed_text = unparsed_text
        self.version = None
        self.features = None
        self.bug_fixes = None

    def extract_version(self):
        version_pattern = r"# \[(\d+\.\d+\.\d+)\]"
        version_match = re.search(version_pattern, self.unparsed_text)
        self.version = version_match.group(1) if version_match else None

    def extract_features(self):
        features_pattern = r"### Features\n\n((?:\* .+\n?)+)"
        features_match = re.search(features_pattern, self.unparsed_text)
        self.features = (
            features_match.group(1).strip().split("\n") if features_match else []
        )

    def extract_bug_fixes(self):
        bug_fixes_pattern = r"### Bug Fixes\n\n((?:\* .+\n?)+)"
        bug_fixes_match = re.search(bug_fixes_pattern, self.unparsed_text)
        self.bug_fixes = (
            bug_fixes_match.group(1).strip().split("\n") if bug_fixes_match else []
        )

    def extract_headers(self):
        self.extract_version()
        self.extract_features()
        self.extract_bug_fixes()

    def print_changelog_header(self):
        print(bright_text(f"\nv{self.version} Changelog\n"))

    def print_features(self):
        if len(self.features) == 0:
            return
        print(bright_text("Features:\n"))
        for feature in self.features:
            processed_text = re.sub(changed_line, r"[\1](\2)", feature).replace("*", "")
            match = re.search(commit_and_link_pattern, processed_text)
            if match:
                commit_hash = f"[{match.group(1)}]"
                url = match.group(2)
                print(
                    f" - {Fore.YELLOW}{commit_hash}{Style.RESET_ALL} {processed_text.replace(commit_hash, '').replace(f'({url})', '')}"
                )

    def print_bug_fixes(self):
        if len(self.bug_fixes) == 0:
            return
        print(bright_text("\nBug Fixes:\n"))
        for bug_fix in self.bug_fixes:
            processed_text = re.sub(changed_line, r"[\1](\2)", bug_fix).replace("*", "")
            match = re.search(commit_and_link_pattern, processed_text)
            if match:
                commit_hash = f"[{match.group(1)}]"
                url = match.group(2)
                print(
                    f" - {Fore.YELLOW}{commit_hash}{Style.RESET_ALL} {processed_text.replace(commit_hash, '').replace(f'({url})', '')}"
                )


def read_changelog(previously_installed_version):
    response = requests.get("https://api.github.com/repos/pommee/Pocker/releases")
    changelog: dict = response.json()
    releases: list[Release] = []

    for change in changelog:
        change_text = change.get("body")
        release = Release(change_text)

        release.extract_headers()
        releases.append(release)

    for release in releases:
        current_release_version = version_parse(release.version)

        if current_release_version > previously_installed_version:
            release.print_changelog_header()
            release.print_features()
            release.print_bug_fixes()

    print("")

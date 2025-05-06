# TODO: Code hard to read / violent error, need refactor

import logging
from pathlib import Path
from dataclasses import dataclass
import os
import sys

from anime_sama_api.langs import Lang, lang2ids

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PlayersConfig:
    prefers: list[str]
    bans: list[str]


@dataclass(frozen=True)
class Config:
    prefer_languages: list[Lang]
    download_path: Path
    download: bool
    show_players: bool
    max_retry_time: int
    format: str
    format_sort: str
    internal_player_command: list[str]
    url: str
    players: PlayersConfig  # Deprecated
    concurrent_downloads: dict[str, int]


# Load default config
exemple_config = Path(__file__).parent / "config.toml"
if not exemple_config.exists():
    raise FileNotFoundError(
        "There is an issues with the installation of the package.\nThe exemple config cannot be found."
    )
with open(exemple_config, "rb") as file:
    default_config = tomllib.load(file)


# Load user config
possible_path = ["."]
possible_path.append(
    "~/AppData/Local/anime-sama_api" if os.name == "nt" else "~/.config/anime-sama_cli"
)
possible_path = [Path(path).expanduser() for path in possible_path]

user_config = {}
for path in possible_path:
    config_file = path / "config.toml"
    if config_file.is_file():
        with open(config_file, "rb") as config_file:
            user_config = tomllib.load(config_file)
            break
else:
    from shutil import copy

    possible_path[1].mkdir(parents=True, exist_ok=True)
    copy(exemple_config, possible_path[1])
    logger.info("Default config created at %s", possible_path[1])

# Update the default values by values set by the user
config = default_config | user_config

# Check if value respect the type
for index, lang in enumerate(config["prefer_languages"]):
    # Backward compatibility
    if lang == "VO":
        config["prefer_languages"][index] = "VOSTFR"
        lang = "VOSTFR"

    assert lang in lang2ids, (
        f"{lang} is not a valid languages for prefer_languages\nOnly the following are acceptable: {list(lang2ids.keys())}"
    )

# Convert type
config["download_path"] = (
    Path(config["download_path"]) if config.get("download_path") is not None else ""
)
config["internal_player_command"] = (
    config["internal_player_command"].split()
    if config.get("internal_player_command") is not None
    else ""
)
config["players"] = (
    PlayersConfig(**config["players"])
    if config.get("players") is not None
    else PlayersConfig([], [])
)
config = Config(**config)

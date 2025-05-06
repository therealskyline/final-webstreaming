#!/usr/bin/env python3

import os
import tomli
import logging
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, List

from .langs import Lang

logger = logging.getLogger(__name__)

@dataclass
class PlayersConfig:
    prefers: List[str]
    bans: List[str]

@dataclass
class Config:
    prefer_languages: List[str]
    download_path: Path
    download: bool
    show_players: bool
    max_retry_time: int
    format: str
    format_sort: str
    internal_player_command: List[str]
    url: str
    players: PlayersConfig  # Deprecated
    concurrent_downloads: Dict[str, int]

config_defaults = {
    "prefer_languages": ["VF", "VOSTFR"],  # Priorité sur le français
    "download_path": None,
    "download": False,
    "show_players": False,
    "max_retry_time": 512,
    "format": "",
    "format_sort": "",
    "internal_player_command": [],
    "url": "https://anime-sama.fr",
    "players": {
        "prefers": [],
        "bans": []
    },
    "concurrent_downloads": {
        "episodes": 1,
        "fragments": 3
    }
}

# Global config
config = Config(**config_defaults)

def find_config() -> Path:
    """Find config toml file"""
    if os.getenv("ANIME_SAMA_CONFIG"):
        return Path(os.getenv("ANIME_SAMA_CONFIG"))
    if Path("config.toml").exists():
        return Path("config.toml")
    if Path("~/.config/anime-sama/config.toml").expanduser().exists():
        return Path("~/.config/anime-sama/config.toml").expanduser()
    if Path("~/.anime-sama.toml").expanduser().exists():
        return Path("~/.anime-sama.toml").expanduser()
    if Path("/etc/anime-sama.toml").exists():
        return Path("/etc/anime-sama.toml")
    
    # Pas de fichier de configuration trouvé, création d'un fichier par défaut
    config_path = Path("config.toml")
    logger.info(f"Aucun fichier de configuration trouvé, création de {config_path}")
    
    # Écrire le fichier de configuration par défaut
    with open(config_path, "w") as f:
        f.write("""# Configuration Anime-Sama
# Priorité sur le français (VF) puis sous-titres (VOSTFR)
prefer_languages = ["VF", "VOSTFR"]
download = false
show_players = false
url = "https://anime-sama.fr"

[players]
prefers = []
bans = []

[concurrent_downloads]
episodes = 1
fragments = 3
""")
    
    return config_path

def load_config() -> Config:
    """Load config from toml file"""
    global config
    
    try:
        config_path = find_config()
        with open(config_path, "rb") as f:
            config_toml = tomli.load(f)
        
        # Merge config
        for key, value in config_toml.items():
            if hasattr(config, key):
                setattr(config, key, value)
        
        # Ensure prefer_languages is a list and has VF as priority
        if not isinstance(config.prefer_languages, list):
            config.prefer_languages = config_defaults["prefer_languages"]
        elif len(config.prefer_languages) == 0:
            config.prefer_languages = config_defaults["prefer_languages"]
        elif config.prefer_languages[0] != "VF":
            # Assurer que VF est en première position
            if "VF" in config.prefer_languages:
                config.prefer_languages.remove("VF")
            config.prefer_languages.insert(0, "VF")
            logger.info(f"Configuration ajustée pour priorité VF: {config.prefer_languages}")
                
        # Ensure players is a PlayersConfig
        if not isinstance(config.players, PlayersConfig):
            config.players = PlayersConfig(**config.players)
        
        # If download_path is None or "", use default path
        if not config.download_path:
            config.download_path = Path("~/Downloads/anime-sama").expanduser()
        
        # If download_path is a string, convert to Path
        if isinstance(config.download_path, str):
            config.download_path = Path(config.download_path).expanduser()
        
        # Create download directory if it doesn't exist and download is enabled
        if config.download and not config.download_path.exists():
            config.download_path.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Configuration chargée depuis {config_path}")
        logger.info(f"Langues préférées: {config.prefer_languages}")
        
    except Exception as e:
        logger.error(f"Erreur lors du chargement de la configuration: {e}")
        logger.info("Utilisation de la configuration par défaut")
    
    return config

# Load config
load_config()

if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    # Print config
    print(f"Config: {config}")
    # Print config path
    print(f"Config path: {find_config()}")
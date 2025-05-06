# This file marks cli as a Python package
# Import important modules for easy access

from .config import Config, config, load_config
from .langs import Lang, LangId, VF, FR, VOSTFR

# Imports pour éviter les erreurs
from .downloader import download, multi_download
from .internal_player import play_episode, play_file, open_silent_process
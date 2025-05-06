import time
import logging
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import urlparse

from yt_dlp import YoutubeDL, DownloadError
from rich import print, get_console
from rich.live import Live
from rich.console import Group
from rich.table import Column
from rich.progress import (
    BarColumn,
    Progress,
    TextColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
    MofNCompleteColumn,
    TaskID,
    TotalFileSizeColumn,
    ProgressColumn,
)

from .error_handeling import YDL_log_filter, reaction_to
from .episode import Episode
from .langs import Lang
from .config import config

logger = logging.getLogger(__name__)
logger.addFilter(YDL_log_filter)

console = get_console()
download_progress_list: list[str | ProgressColumn] = [
    "[bold blue]{task.fields[episode_name]}",
    BarColumn(bar_width=None),
    "[progress.percentage]{task.percentage:>3.1f}%",
    TransferSpeedColumn(),
    TotalFileSizeColumn(),
    TimeRemainingColumn(compact=True, elapsed_when_finished=True),
]
if config.show_players:
    download_progress_list.insert(
        1,
        TextColumn(
            "[green]{task.fields[site]}",
            table_column=Column(max_width=12),
            justify="right",
        ),
    )

download_progress = Progress(*download_progress_list, console=console)

total_progress = Progress(
    TextColumn("[bold cyan]{task.description}"),
    BarColumn(bar_width=None),
    MofNCompleteColumn(),
    TimeRemainingColumn(elapsed_when_finished=True),
    console=console,
)
progress = Group(total_progress, download_progress)

def download(
    episode: Episode,
    path: Path,
    prefer_languages: list[Lang] = ["VF", "VOSTFR", "VJ"],
    concurrent_fragment_downloads=3,
    max_retry_time=1024,
    format="bestvideo[height<=720]+bestaudio/best[height<=720]",
    format_sort="",
):
    cookies_file = Path("attached_assets/vidmoly.me_cookies (1).txt")

    option = {
        "outtmpl": {"default": f"{path}/{episode.serie_name}/{episode.season_name}/Episode {episode.index}.%(ext)s"},
        "concurrent_fragment_downloads": concurrent_fragment_downloads,
        "format": "best",
        "format_sort": format_sort,
        "quiet": True,
        "socket_timeout": 30,
        "retries": 10,
        "fragment_retries": 10,
        "http_headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "fr,fr-FR;q=0.8,en-US;q=0.5,en;q=0.3",
            "Referer": "https://anime-sama.fr/",
            "Origin": "https://anime-sama.fr",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        }
    }

    if not any(episode.languages.values()):
        print("[red]Aucun lecteur disponible")
        return False

    me = download_progress.add_task(
        "download", episode_name=episode.name, site="", total=None
    )
    task = download_progress.tasks[me]

    full_path = (
        path / episode.serie_name / episode.season_name / f"Episode {episode.index}"
    ).expanduser()

    def hook(data: dict):
        if data.get("status") != "downloading":
            return

        task.total = data.get("total_bytes") or data.get("total_bytes_estimate")
        download_progress.update(me, completed=data.get("downloaded_bytes", 0))

    option["progress_hooks"] = [hook]
    option["logger"] = logger

    # Removed logging of available players
    logger.info(f"Tentative de téléchargement de {episode.name}")
    
    # Réorganiser les lecteurs pour essayer vidmoly en premier, puis oneupload et sendvid
    players = list(episode.consume_player(prefer_languages))
    reordered_players = []

    # Mettre vidmoly en premier
    for player in players:
        if "vidmoly" in player:
            reordered_players.append(player)

    # Mettre oneupload et sendvid ensuite
    for player in players:
        if "oneupload" in player or "sendvid" in player:
            reordered_players.append(player)

    # Ajouter les autres lecteurs
    for player in players:
        if "vidmoly" not in player and "oneupload" not in player and "sendvid" not in player:
            reordered_players.append(player)

    downloaded = False
    for player in reordered_players:
        if downloaded:
            break

        retry_time = 1
        download_progress.update(me, site=urlparse(player).hostname)

        while True:
            try:
                with YoutubeDL(option) as ydl:
                    error_code = ydl.download([player])
                    if not error_code:
                        downloaded = True
                        break
                    else:
                        logger.info(
                            "Protection détectée sur %s, tentative avec une autre source...",
                            urlparse(player).hostname
                        )
                        break
            except DownloadError as execption:
                error_msg = execption.msg.lower()

                if "socket" in error_msg or "timeout" in error_msg:
                    logger.warning(f"Timeout sur {urlparse(player).hostname}, nouvelle tentative...")
                    time.sleep(retry_time)
                    retry_time *= 2
                    if retry_time < max_retry_time:
                        continue

                match reaction_to(execption.msg):
                    case "continue":
                        break
                    case "retry":
                        if retry_time >= max_retry_time:
                            logger.warning(f"Nombre maximum de tentatives atteint pour {urlparse(player).hostname}")
                            break
                        logger.info(
                            f"Nouvelle tentative pour {episode.name} dans %ss...", retry_time
                        )
                        time.sleep(retry_time)
                        retry_time *= 2
                    case "crash":
                        raise execption
                    case _:
                        logger.warning(
                            f"Erreur non gérée pour {urlparse(player).hostname}, passage au suivant..."
                        )
                        break

        if downloaded:
            break

    download_progress.update(me, visible=False)
    if total_progress.tasks:
        total_progress.update(TaskID(0), advance=1)

def multi_download(
    episodes: list[Episode],
    path: Path,
    concurrent_downloads={"video": 1, "fragment": 3},
    prefer_languages: list[Lang] = ["VF", "VOSTFR"],
    max_retry_time=1024,
    format="",
    format_sort="",
):
    total_progress.add_task("Downloaded", total=len(episodes))
    with Live(progress, console=console):
        with ThreadPoolExecutor(
            max_workers=concurrent_downloads.get("video", 1)
        ) as executor:
            for episode in episodes:
                executor.submit(
                    download,
                    episode,
                    path,
                    prefer_languages,
                    concurrent_downloads.get("fragment", 3),
                    max_retry_time,
                    format,
                    format_sort,
                )
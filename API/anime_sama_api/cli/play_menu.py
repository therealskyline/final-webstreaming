import subprocess
import time
import sys
import logging
from typing import Optional, Callable, Any

from rich import print
from rich.console import Console
from rich.prompt import Prompt

from anime_sama_api.episode import Episode
from anime_sama_api.langs import Lang

from .config import config
from .internal_player import play_episode


logger = logging.getLogger(__name__)
console = Console()


class EpisodesManager:
    def __init__(self, episodes: list[Episode], current_index=0) -> None:
        self.episodes = episodes
        self.current_index = current_index

    def __next__(self):
        if self.current_index < len(self.episodes) - 1:
            self.current_index += 1
            return self.episodes[self.current_index]

        raise StopIteration

    def previous(self):
        if self.current_index > 0:
            self.current_index -= 1
            return self.episodes[self.current_index]

        raise StopIteration

    @property
    def current(self):
        return self.episodes[self.current_index]


class PlayMenu:
    """Interactive menu for playing episodes with controls for navigation"""
    
    def __init__(self, episodes_manager: EpisodesManager, prefer_languages: list[Lang] = None):
        self.episodes_manager = episodes_manager
        self.prefer_languages = prefer_languages or config.prefer_languages
        self.player_process: Optional[subprocess.Popen] = None
        self.is_running = True
        
    def print_menu(self):
        """Display menu options for controlling playback"""
        print("[bold cyan]Playback Controls:[/]")
        print(" [green]n[/] - Next episode")
        print(" [green]p[/] - Previous episode")
        print(" [green]r[/] - Replay current episode")
        print(" [green]i[/] - Episode information")
        print(" [green]q[/] - Quit")
        
    def kill_player(self):
        """Terminate the current player process if it's running"""
        if self.player_process and self.player_process.poll() is None:
            self.player_process.terminate()
            try:
                self.player_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.player_process.kill()
            self.player_process = None
            
    def play_current(self):
        """Play the current episode"""
        current_episode = self.episodes_manager.current
        print(f"[blue]Playing: {current_episode.name}[/]")
        
        # First stop any running player
        self.kill_player()
        
        # Start new player
        self.player_process = play_episode(
            current_episode,
            self.prefer_languages
        )
        
        if not self.player_process:
            print("[red]Failed to play episode. No compatible player found.[/]")
            
    def show_episode_info(self):
        """Display detailed information about the current episode"""
        episode = self.episodes_manager.current
        print(f"\n[bold blue]Episode Information:[/]")
        print(f"[yellow]Name:[/] {episode.name}")
        print(f"[yellow]Series:[/] {episode.serie_name}")
        print(f"[yellow]Season:[/] {episode.season_name}")
        print(f"[yellow]Available Languages:[/]")
        
        for lang, players in episode.languages.items():
            if players:
                print(f"  [green]{lang.upper()}[/]: {len(players)} source(s)")
                
    def run(self):
        """Run the interactive menu loop"""
        try:
            self.play_current()
            
            while self.is_running:
                self.print_menu()
                choice = Prompt.ask("Enter command", default="").lower()
                
                if choice == 'n':
                    try:
                        next_episode = next(self.episodes_manager)
                        self.play_current()
                    except StopIteration:
                        print("[yellow]This is the last episode.[/]")
                        
                elif choice == 'p':
                    try:
                        prev_episode = self.episodes_manager.previous()
                        self.play_current()
                    except StopIteration:
                        print("[yellow]This is the first episode.[/]")
                        
                elif choice == 'r':
                    self.play_current()
                    
                elif choice == 'i':
                    self.show_episode_info()
                    
                elif choice == 'q':
                    self.is_running = False
                    
                elif not choice:
                    # Check if player has exited naturally
                    if self.player_process and self.player_process.poll() is not None:
                        try:
                            next_episode = next(self.episodes_manager)
                            self.play_current()
                        except StopIteration:
                            print("[yellow]Reached end of episodes.[/]")
                            self.is_running = False
                            
                time.sleep(0.5)
                
        except KeyboardInterrupt:
            print("\n[yellow]Playback interrupted.[/]")
        finally:
            self.kill_player()

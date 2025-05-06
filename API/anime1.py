#!/usr/bin/env python3

"""
Anime1.py - Version modifiée de l'API Anime-Sama avec priorité sur la version française (VF)
Cette version reprend directement les fichiers de l'API originale et modifie la langue prioritaire
"""

import sys
import os
import logging
import json
from pathlib import Path
import asyncio

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.spinner import Spinner
    from rich.prompt import Prompt
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    print("Module 'rich' non disponible. Installation recommandée pour une meilleure interface:")
    print("pip install rich")

# Configuration de base du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Création d'une console rich si disponible, sinon utiliser print standard
if RICH_AVAILABLE:
    console = Console()
else:
    # Créer un remplacement simple pour console.print
    class SimpleConsole:
        def print(self, text, *args, **kwargs):
            # Supprimer les balises Rich pour l'affichage texte
            import re
            text = re.sub(r'\[.*?\]', '', text)
            print(text)
    console = SimpleConsole()

# Fonction pour vérifier et corriger la configuration
def setup_config():
    """Vérifie et corrige le fichier de configuration pour priorité VF"""
    config_path = Path("config.toml")

    if not config_path.exists():
        # Créer le fichier de configuration s'il n'existe pas
        console.print("[yellow]Fichier de configuration non trouvé, création...[/yellow]")
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
        console.print(f"[green]✓ Fichier de configuration créé: {config_path}[/green]")
    else:
        # Vérifier la configuration existante
        try:
            import tomli

            with open(config_path, "rb") as f:
                config = tomli.load(f)

            # Vérifier les langues préférées
            if "prefer_languages" in config:
                languages = config["prefer_languages"]
                if not languages or languages[0] != "VF":
                    # Créer une copie modifiée de la configuration
                    with open(config_path, "r") as f:
                        config_text = f.read()

                    # Modifier la préférence de langue
                    import re
                    if "prefer_languages" in config_text:
                        new_config = re.sub(
                            r'prefer_languages\s*=\s*\[[^\]]*\]',
                            'prefer_languages = ["VF", "VOSTFR"]',
                            config_text
                        )
                        with open(config_path, "w") as f:
                            f.write(new_config)
                        console.print("[green]✓ Configuration mise à jour avec priorité VF[/green]")
                    else:
                        # Ajouter la préférence si elle n'existe pas
                        with open(config_path, "a") as f:
                            f.write('\nprefer_languages = ["VF", "VOSTFR"]\n')
                        console.print("[green]✓ Préférence de langue ajoutée à la configuration[/green]")
                else:
                    console.print("[green]✓ Configuration déjà correcte avec priorité VF[/green]")
            else:
                # Ajouter la préférence si elle n'existe pas
                with open(config_path, "a") as f:
                    f.write('\nprefer_languages = ["VF", "VOSTFR"]\n')
                console.print("[green]✓ Préférence de langue ajoutée à la configuration[/green]")

        except Exception as e:
            console.print(f"[red]❌ Erreur lors de la vérification de la configuration: {e}[/red]")
            # Créer un nouveau fichier de configuration par défaut
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
            console.print(f"[yellow]⚠️ Configuration réinitialisée avec priorité VF[/yellow]")

    return config_path

def print_welcome():
    """Affiche un message de bienvenue"""
    if RICH_AVAILABLE:
        console.print(Panel.fit(
            "[bold cyan]Anime-Sama API - VERSION FRANÇAISE PRIORITAIRE[/bold cyan]\n"
            "Cette application utilise l'API Anime-Sama avec priorité sur les versions françaises (VF)",
            title="Bienvenue", border_style="green"
        ))
    else:
        print("=" * 70)
        print("Anime-Sama API - VERSION FRANÇAISE PRIORITAIRE")
        print("Cette application utilise l'API Anime-Sama avec priorité sur les versions françaises (VF)")
        print("=" * 70)

from anime_sama_api.top_level import AnimeSama

def run_api():
    try:
        return 0
    except Exception as e:
        console.print(f"[red]Erreur: {e}[/red]")
        return 1

from anime_sama_api.downloader import multi_download as api_multi_download

def multi_download(episodes, download_path, concurrent_downloads, prefer_languages):
    """Télécharge les épisodes sélectionnés"""
    try:
        api_multi_download(
            episodes=episodes,
            path=download_path,
            concurrent_downloads=concurrent_downloads,
            prefer_languages=prefer_languages
        )
    except Exception as e:
        console.print(f"[red]Erreur de téléchargement: {e}[/red]")



async def main():
    config_path = setup_config()
    console.print(f"[blue]Configuration utilisée: {config_path}[/blue]")

    # Boucle principale de recherche
    while True:
        try:
            query = input("\nRechercher un anime (ou 'q' pour quitter): ")
            if query.lower() in ('q', 'quit', 'exit'):
                break

            if not query.strip():
                continue

            console.print("[yellow]Recherche en cours...[/yellow]")

            # Utiliser l'API pour la recherche avec gestion d'erreur
            try:
                api = AnimeSama("https://anime-sama.fr/")
                results = await api.search(query)
            except Exception as e:
                console.print(f"[red]Erreur de connexion: {e}[/red]")
                console.print("[yellow]Vérification de la connexion...[/yellow]")
                continue

            if not results:
                console.print("[yellow]Aucun résultat trouvé[/yellow]")
                continue

            # Afficher les résultats
            console.print(f"\n[green]Résultats pour '{query}':[/green]")
            for i, anime in enumerate(results, 1):
                # Si pas de langue spécifiée, on affiche [VOSTFR]
                langs = anime.languages if anime.languages else ["VOSTFR"]
                console.print(f"{i}. [cyan]{anime.name}[/cyan] [{', '.join(langs)}]")

            # Permettre la sélection
            choice = input("\nChoisir un numéro (ou Entrée pour continuer): ")
            if choice.isdigit() and 1 <= int(choice) <= len(results):
                selected = results[int(choice)-1]
                console.print(f"\n[bold]Détails de {selected.name}[/bold]")

                # Utiliser l'URL de base pour toutes les langues
                base_url = "https://anime-sama.fr"
                api = AnimeSama(f"{base_url}/")
                
                if not selected.languages:
                    selected.languages = ["VOSTFR"]

                console.print(f"Langues: {', '.join(selected.languages)}")
                # Récupérer les saisons depuis le catalogue
                try:
                    catalogue = await api.search(selected.name)
                    catalogue = await api.search(selected.name)
                    if catalogue:
                        seasons_data = await catalogue[0].seasons()
                        seasons = seasons_data
                    else:
                        # Si pas de saisons trouvées, considérer comme une seule saison en VJ
                        seasons = ["Saison 1"]
                except:
                    # En cas d'erreur, considérer comme une seule saison en VJ
                    seasons = ["Saison 1"]

                # Afficher les saisons disponibles ou message scan
                if not seasons:
                    console.print("\n[red]Cet anime ne possède que des scans, pas de saisons animées disponibles.[/red]")
                else:
                    console.print("\nSaisons disponibles:")
                    for i, season in enumerate(seasons, 1):
                        console.print(f"{i}. {season.name}")

                season_choice = input("\nChoisir une saison (numéro ou 'full' pour tout): ")
                if season_choice.lower() == 'full':
                    # Télécharger toutes les saisons
                    for season in seasons:
                        console.print(f"\nTraitement de: {season.name}")
                        try:
                            episodes_data = await season.episodes()
                            # Télécharger tous les épisodes de la saison
                            if episodes_data:
                                console.print("\n[yellow]Démarrage du téléchargement...[/yellow]")
                                download_path = Path("downloads")
                                download_path.mkdir(exist_ok=True)
                                # Télécharger les épisodes par groupes de 2
                                for i in range(0, len(episodes_data), 2):
                                    batch = episodes_data[i:i+2]
                                    # Déterminer les langues préférées selon disponibilité
                                    prefer_langs = []
                                    if "VF" in selected.languages:
                                        prefer_langs = ["VF", "VOSTFR"]
                                    elif "VOSTFR" in selected.languages:
                                        prefer_langs = ["VOSTFR"]
                                    else:
                                        prefer_langs = ["VJ"]

                                    multi_download(
                                        batch,
                                        download_path,
                                        concurrent_downloads={"video": 2, "fragment": 3},
                                        prefer_languages=prefer_langs,
                                    )
                                    console.print(f"\n[green]Groupe d'épisodes {i+1}-{min(i+2, len(episodes_data))} terminé ![/green]")
                        except Exception as e:
                            console.print(f"[red]Erreur lors du téléchargement de la saison {season.name}: {e}[/red]")


                else:
                    try:
                        season_num = int(season_choice)
                        if 1 <= season_num <= len(seasons):
                            selected_season = seasons[season_num - 1]
                            console.print(f"\nSaison sélectionnée: {selected_season.name}")

                            # Récupérer les épisodes depuis le catalogue
                            try:
                                episodes_data = await selected_season.episodes()
                                nb_episodes = len(episodes_data)
                            except:
                                nb_episodes = 12  # Par défaut 12 épisodes

                            console.print("\nÉpisodes disponibles:")

                            # Afficher les épisodes en liste numérotée
                            for i in range(1, nb_episodes + 1):
                                # Simuler les langues disponibles pour l'exemple
                                langs = []
                                if "VF" in selected.languages:
                                    langs.append("VF")
                                if "VOSTFR" in selected.languages:
                                    langs.append("VOSTFR")

                                langs_str = f" [{', '.join(langs)}]" if langs else ""
                                console.print(f"{i}. Episode {i}{langs_str}")

                            ep_range = input("\nSélectionner les épisodes: ")

                            # Créer le dossier downloads s'il n'existe pas
                            download_path = Path("downloads")
                            download_path.mkdir(exist_ok=True)

                            # Préparer la liste des épisodes à télécharger
                            episodes_to_download = []
                            if '-' in ep_range:
                                start, end = map(int, ep_range.split('-'))
                                console.print(f"\nÉpisodes sélectionnés: {start} à {end}")

                                # Récupérer les épisodes dans la plage
                                for i in range(start, end + 1):
                                    if i <= len(episodes_data):
                                        episodes_to_download.append(episodes_data[i-1])
                            else:
                                try:
                                    ep_num = int(ep_range)
                                    if ep_num <= len(episodes_data):
                                        episodes_to_download.append(episodes_data[ep_num-1])
                                    console.print(f"\nÉpisode sélectionné: {ep_range}")
                                except ValueError:
                                    console.print("[red]Numéro d'épisode invalide[/red]")
                                    continue

                            # Lancer le téléchargement par lots de 2 épisodes
                            if episodes_to_download:
                                console.print("\n[yellow]Démarrage du téléchargement par lots de 2 épisodes...[/yellow]")
                                for i in range(0, len(episodes_to_download), 2):
                                    batch = episodes_to_download[i:i+2]
                                    console.print(f"\n[cyan]Téléchargement des épisodes {i+1}-{min(i+2, len(episodes_to_download))}[/cyan]")
                                    # Déterminer les langues préférées selon disponibilité
                                    prefer_langs = []
                                    if "VF" in selected.languages:
                                        prefer_langs = ["VF", "VOSTFR"]
                                    elif "VOSTFR" in selected.languages:
                                        prefer_langs = ["VOSTFR"]
                                    else:
                                        prefer_langs = ["VJ"]

                                    multi_download(
                                        batch,
                                        download_path,
                                        concurrent_downloads={"video": 2, "fragment": 3},
                                        prefer_languages=prefer_langs,
                                    )
                                console.print("\n[green]Téléchargement terminé ![/green]")

                            input("\nAppuyez sur Entrée pour continuer...")

                    except ValueError:
                        console.print("\nSélection invalide")

        except KeyboardInterrupt:
            break
        except Exception as e:
            console.print(f"[red]Erreur: {e}[/red]")
            continue

    console.print("\n[green]Au revoir ![/green]")
    return 0

if __name__ == "__main__":
    asyncio.run(main())
# Anime-Sama avec Priorité Française (VF)

Ce projet est une modification de l'API Anime-Sama pour privilégier les versions françaises (VF) des animes avec fallback sur les versions sous-titrées (VOSTFR) quand les VF ne sont pas disponibles.

## Caractéristiques

- 🇫🇷 **Priorité au français**: Configuration par défaut qui privilégie la VF puis la VOSTFR
- 🔍 **Recherche simplifiée**: Interface conviviale pour trouver facilement vos animes préférés
- 📱 **Interface web**: Visualisez les animes disponibles avec badges colorés par langue (VF/VOSTFR)
- 🎬 **Simulation de téléchargement**: Avec priorité automatique sur les versions françaises
- 📋 **Extraction de données**: Outil pour récupérer le catalogue complet depuis le site Anime-Sama

## Installation

1. Clonez ce dépôt:
   ```
   git clone https://github.com/votrenom/anime-sama-vf.git
   cd anime-sama-vf
   ```

2. Installez les dépendances nécessaires:
   ```
   pip install httpx rich tomli yt-dlp flask
   ```

## Utilisation

### Deux versions disponibles:

1. **anime1.py** - Version complète qui utilise l'API d'origine modifiée:
   ```bash
   python anime1.py
   ```
   Cette version modifie l'API originale pour prioriser la VF et utilise toutes les fonctionnalités de l'API.

2. **anime2.py** - Version simplifiée en console avec simulation:
   ```bash
   python anime2.py
   ```
   Cette version offre une interface console légère avec un catalogue intégré d'animes populaires.

### Autres modes disponibles

Pour la version simplifiée avec un ensemble d'animes pré-chargés:
```bash
python simple_demo.py
```

Pour extraire la liste complète des animes depuis le site:
```bash
python anime_data_extractor.py --extract
```

Pour lancer l'interface web:
```bash
python main.py
```
Puis ouvrez votre navigateur à l'adresse `http://localhost:5000/`.

## Configuration

La configuration par défaut privilégie déjà la VF. Si vous souhaitez personnaliser davantage, modifiez le fichier `config.toml` à la racine du projet:

```toml
# Configuration Anime-Sama
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
```

## Remarques

Ce projet est une adaptation de l'API d'origine pour faciliter l'accès aux versions françaises. Il n'est pas affilié au site officiel Anime-Sama.
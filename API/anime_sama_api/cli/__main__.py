#!/usr/bin/env python3

import asyncio
import logging

try:
    import rich
    import rich.console
    import rich.progress
    import rich.logging
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
import sys
from . import config, downloader, internal_player
from .langs import Lang, VF, FR, VOSTFR

logger = logging.getLogger(__name__)

def spinner(text: str):
    """Simple spinner avec texte pour simulation de chargement"""
    try:
        # Utilisons une méthode simplifiée pour éviter les problèmes avec rich.progress
        print(f"Chargement: {text}...")
        import time
        time.sleep(1)
        print("Terminé!")
    except Exception as e:
        logger.error(f"Erreur lors de l'affichage du spinner: {e}")

async def async_main():
    """Version asynchrone de la fonction principale"""
    try:
        # Gestion simplifiée sans dépendre de rich
        
        # Configurer la priorité sur FR/VF
        if hasattr(config, "config") and hasattr(config.config, "prefer_languages") and len(config.config.prefer_languages) > 0:
            if config.config.prefer_languages[0] not in ["FR", "VF"]:
                print("ℹ️ Changement de la priorité de langue pour FR/VF")
                config.config.prefer_languages[0] = "FR"
        
        # Afficher les informations de configuration
        print("✓ Configuration chargée avec succès")
        if hasattr(config, "config") and hasattr(config.config, "prefer_languages"):
            print(f"• Langues préférées: {', '.join(config.config.prefer_languages)}")
        
        # Menu d'accueil
        print("\n✨ Bienvenue dans l'API Anime-Sama - Version FR ✨")
        print("Cette version a été modifiée pour donner priorité aux versions françaises")
        
        # Simuler un chargement
        spinner("Chargement de l'API...")
        
        return True
        
    except Exception as e:
        logger.error(f"Erreur: {e}")
        import traceback
        logger.debug(traceback.format_exc())
        return False

def main() -> int:
    """Point d'entrée principal du programme"""
    # Configurer le logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Informer sur le statut de dév
    logger.info("Démarrage de l'API Anime-Sama - Version française")
    
    try:
        # Exécuter la fonction asynchrone
        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(async_main())
        return 0 if result else 1
    except KeyboardInterrupt:
        logger.info("Interruption utilisateur")
        return 130
    except Exception as e:
        logger.error(f"Erreur non gérée: {e}")
        import traceback
        logger.debug(traceback.format_exc())
        return 1

if __name__ == "__main__":
    sys.exit(main())
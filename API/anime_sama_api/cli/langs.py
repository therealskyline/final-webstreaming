#!/usr/bin/env python3

import re
import logging
from enum import Enum, auto
from dataclasses import dataclass

logger = logging.getLogger(__name__)

class LangId(Enum):
    VOSTFR = auto()
    VF = auto()
    FR = auto()  # Alias pour VF
    MANGA = auto()
    RAW = auto()

# Constantes pour les langues - définies directement
VF = "VF"
VOSTFR = "VOSTFR"
FR = "FR"  # Alias pour VF
MANGA = "MANGA"
RAW = "RAW"

# Décorateur pour créer des constantes
def lang(cls):
    for lang_id in LangId:
        setattr(cls, lang_id.name, lang_id.name)
    return cls

@lang
class Lang:
    """
    Constantes pour les langues
    L'énumération est disponible comme Lang.VOSTFR, Lang.VF, etc.
    """
    pass

LANG_LINK_PATTERN = {
    LangId.VOSTFR: re.compile(r"<a href=\"([^\"]*)\"><img src=\"img\/vostfr\.png\" alt=\"VOSTFR\" \/><\/a>"),
    LangId.VF: re.compile(r"<a href=\"([^\"]*)\"><img src=\"img\/vf\.png\" alt=\"VF\" \/><\/a>"),
    LangId.MANGA: re.compile(r"<a href=\"([^\"]*)\"><img src=\"img\/manga\.png\" alt=\"MANGA\" \/><\/a>"),
    LangId.RAW: re.compile(r"<a href=\"([^\"]*)\"><img src=\"img\/raw\.png\" alt=\"RAW\" \/><\/a>"),
}

ANIME_SAMA_URL = "https://anime-sama.fr"

# Fonction dummy pour rendre le module importable
async def main():
    logger.info(f"Module de langues chargé: {Lang.VF}, {Lang.VOSTFR}")
    return True

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
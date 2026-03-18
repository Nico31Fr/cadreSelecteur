# -*- coding: utf-8 -*-
"""Charge la configuration depuis le fichier JSON situé dans le dossier resources.
Ce module vit en dehors du dossier `resources` afin que `resources/` reste non-modulaire
comme demandé.

Exporte des constantes : WINDOWS_SIZE, THUMBNAIL_H, THUMBNAIL_L, TEMPLATE_NAME,
TEMPLATE_NAME_STD, CADRE_NAME_1, CADRE_NAME_4
"""
from pathlib import Path
import json
import logging
import sys
from typing import Any

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent
# En mode PyInstaller, tenter de lire CONFIG depuis _MEIPASS
MEIPASS_DIR = None
if getattr(sys, 'frozen', False):
    MEIPASS_DIR = Path(getattr(sys, '_MEIPASS', ''))

if MEIPASS_DIR:
    # essayer plusieurs emplacements plausibles
    possible = [
        MEIPASS_DIR / 'CadreSelecteur' / 'resources',
        MEIPASS_DIR / 'resources',
        MEIPASS_DIR,
    ]
    RESOURCES_DIR = None
    for p in possible:
        if p.exists():
            RESOURCES_DIR = p
            break
    # fallback sur le répertoire resources du package si aucun des chemins MEIPASS n'existe
    if RESOURCES_DIR is None:
        RESOURCES_DIR = BASE_DIR / 'resources'
else:
    RESOURCES_DIR = BASE_DIR / 'resources'

CONFIG_PATH = RESOURCES_DIR / 'config.json'

# Defaults in case the file is missing or invalid
_defaults = {
    "WINDOWS_SIZE": "1000x600",
    "THUMBNAIL_H": 128,
    "THUMBNAIL_L": 85,
    "TEMPLATE_NAME": "template.xml",
    "TEMPLATE_NAME_STD": "template_1.xml",
    "CADRE_NAME_1": "cadre_1.png",
    "CADRE_NAME_4": "cadre_4.png",
    # langue par défaut (français)
    "LANGUAGE": "fr",
}

_config: dict[str, Any] = _defaults.copy()

try:
    if CONFIG_PATH.exists():
        with CONFIG_PATH.open("r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, dict):
                _config.update(data)
            else:
                logger.warning("config.json does not contain a JSON object; using defaults")
    else:
        logger.info(f"config.json not found at {CONFIG_PATH}; using defaults")
except Exception as e:
    logger.exception(f"Failed to load config.json: {e}; using defaults")

WINDOWS_SIZE: str = str(_config.get("WINDOWS_SIZE", _defaults["WINDOWS_SIZE"]))
THUMBNAIL_H: int = int(_config.get("THUMBNAIL_H", _defaults["THUMBNAIL_H"]))
THUMBNAIL_L: int = int(_config.get("THUMBNAIL_L", _defaults["THUMBNAIL_L"]))
TEMPLATE_NAME: str = str(_config.get("TEMPLATE_NAME", _defaults["TEMPLATE_NAME"]))
TEMPLATE_NAME_STD: str = str(_config.get("TEMPLATE_NAME_STD", _defaults["TEMPLATE_NAME_STD"]))
CADRE_NAME_1: str = str(_config.get("CADRE_NAME_1", _defaults["CADRE_NAME_1"]))
CADRE_NAME_4: str = str(_config.get("CADRE_NAME_4", _defaults["CADRE_NAME_4"]))
# Exposer la langue choisie dans 'config.json' (fallback sur la valeur par défaut)
LANGUAGE: str = str(_config.get("LANGUAGE", _defaults["LANGUAGE"]))

__all__ = [
    "WINDOWS_SIZE",
    "THUMBNAIL_H",
    "THUMBNAIL_L",
    "TEMPLATE_NAME",
    "TEMPLATE_NAME_STD",
    "CADRE_NAME_1",
    "CADRE_NAME_4",
    "LANGUAGE",
    "RESOURCES_DIR",
]

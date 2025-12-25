# -*- coding: utf-8 -*-
"""Simple translator module.
Charge les fichiers JSON `i18n/{lang}.json` et expose _t(key, **kwargs),
set_language(lang) et get_language().

Le chargement est conçu pour fonctionner avec PyInstaller :
- lecture directe depuis le dossier i18n (mode développement)
- lecture via importlib.resources ou pkgutil (mode bundle / exe)
"""
from __future__ import annotations

from pathlib import Path
import json
import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent
I18N_DIR = BASE_DIR

# Chargement paresseux de la langue pour éviter les import cycles
_current_lang = 'fr'
_translations: Dict[str, Any] = {}


def _load_translations(lang: str) -> None:
    """Charge les traductions pour la langue donnée.

    Stratégie :
    1. Si le fichier existe sur le système de fichiers (mode dev), le lire.
    2. Sinon, tenter importlib.resources.read_text() (fonctionne quand les
       fichiers sont inclus dans le package, p.ex. via PyInstaller --add-data
       ou en package wheel).
    3. Sinon, tenter pkgutil.get_data() (fallback).
    4. En dernier recours, retomber sur 'fr' ou dictionnaire vide.
    """
    global _translations, _current_lang

    # 1) tentative lecture fichier direct
    try:
        lang_file = I18N_DIR / f"{lang}.json"
        if lang_file.exists():
            with lang_file.open('r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, dict):
                    _translations = data
                    _current_lang = lang
                    return
                else:
                    logger.warning(f"Translation file {lang_file} does not contain a JSON object; using empty dict")
                    _translations = {}
                    _current_lang = lang
                    return
    except Exception as e:
        logger.debug(f"Filesystem load of translations failed for {lang}: {e}")

    # 2) tentative importlib.resources (meilleur pour packaging)
    try:
        try:
            # Python 3.9+: importlib.resources.files / read_text
            import importlib.resources as importlib_resources
            pkg = __package__  # 'CadreSelecteur.i18n'
            text = importlib_resources.read_text(pkg, f"{lang}.json", encoding='utf-8')
            data = json.loads(text)
            if isinstance(data, dict):
                _translations = data
                _current_lang = lang
                return
            else:
                logger.warning(f"Resource {lang}.json does not contain a JSON object; using empty dict")
                _translations = {}
                _current_lang = lang
                return
        except Exception:
            # fallback to older APIs
            import pkgutil
            raw = pkgutil.get_data(__package__, f"{lang}.json")
            if raw:
                text = raw.decode('utf-8')
                data = json.loads(text)
                if isinstance(data, dict):
                    _translations = data
                    _current_lang = lang
                    return
                else:
                    logger.warning(f"Resource {lang}.json (pkgutil) does not contain a JSON object; using empty dict")
                    _translations = {}
                    _current_lang = lang
                    return
    except Exception as e:
        logger.debug(f"Package resource load of translations failed for {lang}: {e}")

    # Si aucune méthode n'a fonctionné, essayer de charger le fallback 'fr'
    try:
        lang_file = I18N_DIR / "fr.json"
        if lang_file.exists():
            with lang_file.open('r', encoding='utf-8') as f:
                data = json.load(f)
                _translations = data if isinstance(data, dict) else {}
                _current_lang = 'fr'
                logger.warning('Falling back to \'fr\' translations (filesystem)')
                return
    except Exception as e:
        logger.debug(f"Failed to load fallback fr.json from filesystem: {e}")

    # dernier recours : translations vides
    _translations = {}
    _current_lang = lang
    logger.warning(f"No translations available for '{lang}' and fallback failed; using empty translations")


def get_language() -> str:
    return _current_lang


def set_language(lang: str) -> bool:
    """Change la langue et recharge les traductions.

    Retourne True si la langue a été chargée (ou False en cas d'erreur).
    """
    try:
        _load_translations(lang)
        return True
    except Exception:
        return False


def _t(key: str, **kwargs) -> str:
    """Retourne la traduction pour la clé. Si non trouvé, retourne la clé.

    Supporte le formatage Python via str.format(**kwargs).
    """
    parts = key.split('.')
    node = _translations

    try:
        for p in parts:
            if isinstance(node, dict) and p in node:
                node = node[p]
            else:
                # clé manquante
                return key

        if isinstance(node, str):
            if kwargs:
                try:
                    return node.format(**kwargs)
                except Exception as e:
                    logger.exception(f"Formatting error for key {key}: {e}")
                    return node
            return node
        else:
            return key
    except Exception as e:
        logger.exception(f"Error in _t for key {key}: {e}")
        return key


# Initial load: try to read configuration language from config_loader
try:
    # Importer localement pour réduire le risque de circular import
    from ..config_loader import LANGUAGE as _cfg_lang  # type: ignore
    _load_translations(_cfg_lang)
except Exception:
    # fallback
    _load_translations('fr')


__all__ = ["_t", "set_language", "get_language"]

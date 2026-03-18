# -*- coding: utf-8 -*-
"""Simple translator module.
Charge les fichiers JSON `resources/{lang}.json` ou `i18n/{lang}.json` et expose _t(key, **kwargs),
set_language(lang) et get_language().

Le chargement est conçu pour fonctionner avec PyInstaller via path_resolver centralisé.
"""
from __future__ import annotations

import json
import logging
from typing import Any, Dict

from ..path_resolver import resolve_i18n_file

logger = logging.getLogger(__name__)

# Chargement paresseux de la langue pour éviter les import cycles
_current_lang = 'fr'
_translations: Dict[str, Any] = {}


def _load_translations(lang: str) -> None:
    """Charge les traductions pour la langue donnée.

    Stratégie (via path_resolver centralisé):
    1. resources/{lang}.json (priorité)
    2. i18n/{lang}.json (fallback)
    3. Si PyInstaller, chemins MEIPASS gérés par path_resolver
    """
    global _translations, _current_lang

    try:
        # Utiliser path_resolver pour trouver le fichier de langue
        lang_file = resolve_i18n_file(lang)
        logger.debug(f"Attempting to load translations from: {lang_file}")

        if not lang_file.exists():
            logger.warning(f"Translation file not found: {lang_file}. Attempting fallback to 'fr'.")
            # Fallback à français si la langue demandée n'existe pas
            if lang != 'fr':
                _load_translations('fr')
            else:
                _translations = {}
                _current_lang = lang
            return

        try:
            with lang_file.open('r', encoding='utf-8') as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            logger.warning(f"Translation file {lang_file} is malformed (JSON error): {e}. Using empty translations.")
            _translations = {}
            _current_lang = lang
            return
        except Exception as e:
            logger.warning(f"Failed to read translation file {lang_file}: {e}. Using empty translations.")
            _translations = {}
            _current_lang = lang
            return

        if isinstance(data, dict):
            _translations = data
            _current_lang = lang
            logger.info(f"Loaded translations for '{lang}' from: {lang_file}")
        else:
            logger.warning(f"Translation file {lang_file} does not contain a JSON object. Using empty dict.")
            _translations = {}
            _current_lang = lang

    except Exception as e:
        logger.exception(f"Unexpected error loading translations for '{lang}': {e}")
        # Fallback à français en cas d'erreur inattendue
        if lang != 'fr':
            logger.info(f"Falling back to 'fr' after error loading '{lang}'")
            _load_translations('fr')
        else:
            _translations = {}
            _current_lang = lang


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

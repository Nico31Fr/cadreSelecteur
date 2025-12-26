# -*- coding: utf-8 -*-
"""Simple translator module.
Charge les fichiers JSON `resources/{lang}.json` ou `i18n/{lang}.json` et expose _t(key, **kwargs),
set_language(lang) et get_language().

Le chargement est conçu pour fonctionner avec PyInstaller :
- lecture directe depuis le dossier resources (mode développement)
- lecture via importlib.resources ou pkgutil (mode bundle / exe)
"""
from __future__ import annotations

from pathlib import Path
import json
import logging
import sys
from typing import Any, Dict

logger = logging.getLogger(__name__)

# `BASE_DIR` = dossier du package `CadreSelecteur/i18n/..` -> dossier du package CadreSelecteur
BASE_DIR = Path(__file__).resolve().parent.parent
# Dossier non-modulaire `resources/` demandé par l'utilisateur
RESOURCES_DIR = BASE_DIR / "resources"
# Ancien emplacement possible (fallback)
I18N_DIR = Path(__file__).resolve().parent

# If running from a PyInstaller bundle, _MEIPASS contains the temp extraction path.
MEIPASS_DIR = None
if getattr(sys, 'frozen', False):
    MEIPASS_DIR = Path(getattr(sys, '_MEIPASS', ''))

# Chargement paresseux de la langue pour éviter les import cycles
_current_lang = 'fr'
_translations: Dict[str, Any] = {}


def _try_load_from_meipass(lang: str) -> bool:
    """Si on est dans PyInstaller, tente plusieurs emplacements sous _MEIPASS.
    Retourne True si un fichier a été chargé (même vide), False sinon.
    """
    global _translations, _current_lang
    if not MEIPASS_DIR:
        return False
    candidates = [
        MEIPASS_DIR / 'CadreSelecteur' / 'resources' / f"{lang}.json",
        MEIPASS_DIR / 'resources' / f"{lang}.json",
        MEIPASS_DIR / f"{lang}.json",
    ]
    for p in candidates:
        try:
            if p.exists():
                try:
                    with p.open('r', encoding='utf-8') as f:
                        data = json.load(f)
                except Exception as e:
                    logger.warning(f"Translation file {p} is malformed: {e}; using empty translations for '{lang}'")
                    _translations = {}
                    _current_lang = lang
                    return True
                if isinstance(data, dict):
                    _translations = data
                    _current_lang = lang
                    return True
                else:
                    logger.warning(f"Translation file {p} does not contain a JSON object; using empty dict")
                    _translations = {}
                    _current_lang = lang
                    return True
        except Exception as e:
            logger.debug(f"Failed checking MEIPASS path {p} for translations: {e}")
    return False


def _load_translations(lang: str) -> None:
    """Charge les traductions pour la langue donnée.

    Stratégie :
    1. Si le fichier existe dans `resources/`, le lire.
    2. Sinon, si le fichier existe dans `i18n/` (ancien emplacement), le lire.
    3. Si PyInstaller bundle (MEIPASS), essayer les emplacements extraits.
    4. Sinon, tenter importlib.resources (en ciblant d'abord `resources/` dans le package racine),
       puis pkgutil.
    5. En dernier recours, retomber sur 'fr' (depuis resources ou i18n) ou dictionnaire vide.
    """
    global _translations, _current_lang

    # 0) Si PyInstaller, tenter d'abord le MEIPASS (prioritaire pour bundle)
    try:
        if _try_load_from_meipass(lang):
            return
    except Exception:
        # ne pas planter si cette stratégie échoue
        pass

    # 1) tentative lecture fichier direct dans resources/
    try:
        res_file = RESOURCES_DIR / f"{lang}.json"
        if res_file.exists():
            try:
                with res_file.open('r', encoding='utf-8') as f:
                    data = json.load(f)
            except Exception as e:
                logger.warning(f"Translation file {res_file} is malformed: {e}; using empty translations for '{lang}'")
                _translations = {}
                _current_lang = lang
                return

            if isinstance(data, dict):
                _translations = data
                _current_lang = lang
                return
            else:
                logger.warning(f"Translation file {res_file} does not contain a JSON object; using empty dict")
                _translations = {}
                _current_lang = lang
                return
    except Exception as e:
        logger.debug(f"Filesystem load of translations from resources failed for {lang}: {e}")

    # 2) tentative lecture fichier direct dans i18n/ (fallback)
    try:
        lang_file = I18N_DIR / f"{lang}.json"
        if lang_file.exists():
            try:
                with lang_file.open('r', encoding='utf-8') as f:
                    data = json.load(f)
            except Exception as e:
                logger.warning(f"Translation file {lang_file} is malformed: {e}; using empty translations for '{lang}'")
                _translations = {}
                _current_lang = lang
                return

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
        logger.debug(f"Filesystem load of translations from i18n failed for {lang}: {e}")

    # 3) tentative importlib.resources (meilleur pour packaging)
    try:
        import importlib.resources as importlib_resources
        # Package racine (p.ex. 'CadreSelecteur')
        root_pkg = __package__.split('.')[0] if __package__ else None

        # 3.a) essai : resources/{lang}.json in package root
        if root_pkg:
            try:
                files = importlib_resources.files(root_pkg)
                res_node = files.joinpath('resources', f"{lang}.json")
                if res_node.is_file():
                    text = res_node.read_text(encoding='utf-8')
                    data = json.loads(text)
                    if isinstance(data, dict):
                        _translations = data
                        _current_lang = lang
                        return
                    else:
                        logger.warning(f"Resource resources/{lang}.json does not contain a JSON object;"
                                       f" using empty dict")
                        _translations = {}
                        _current_lang = lang
                        return
            except Exception:
                # on continue vers d'autres stratégies
                pass

        # 3.b) essai : lecture directe dans le package i18n (ancien comportement)
        try:
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
            # fallback to pkgutil below
            pass

        # 3.c) fallback pkgutil: essayer resources/ dans le package racine, puis i18n/
        import pkgutil
        if root_pkg:
            raw = pkgutil.get_data(root_pkg, f"resources/{lang}.json")
            if raw:
                try:
                    text = raw.decode('utf-8')
                    data = json.loads(text)
                    if isinstance(data, dict):
                        _translations = data
                        _current_lang = lang
                        return
                    else:
                        logger.warning(f"Resource resources/{lang}.json (pkgutil) does not contain a JSON object;"
                                       f" using empty dict")
                        _translations = {}
                        _current_lang = lang
                        return
                except Exception:
                    logger.warning(f"Resource resources/{lang}.json (pkgutil) is malformed;"
                                   f" using empty translations for '{lang}'")
                    _translations = {}
                    _current_lang = lang
                    return

        # encore fallback to pkgutil for current package
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

    # 4) Si aucune méthode n'a fonctionné, essayer de charger le fallback 'fr' depuis resources puis i18n
    try:
        fr_file = RESOURCES_DIR / "fr.json"
        if fr_file.exists():
            with fr_file.open('r', encoding='utf-8') as f:
                data = json.load(f)
                _translations = data if isinstance(data, dict) else {}
                _current_lang = 'fr'
                logger.warning('Falling back to \'fr\' translations (resources)')
                return
    except Exception as e:
        logger.debug(f"Failed to load fallback fr.json from resources: {e}")

    try:
        fr_file = I18N_DIR / "fr.json"
        if fr_file.exists():
            with fr_file.open('r', encoding='utf-8') as f:
                data = json.load(f)
                _translations = data if isinstance(data, dict) else {}
                _current_lang = 'fr'
                logger.warning('Falling back to \'fr\' translations (i18n)')
                return
    except Exception as e:
        logger.debug(f"Failed to load fallback fr.json from i18n: {e}")

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

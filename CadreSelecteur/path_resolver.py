# -*- coding: utf-8 -*-
"""
Résoluteur de chemins centralisé pour CadreSelecteur.

Gère les 3 contextes d'exécution:
1. Mode développement: CadreSelecteur/resources/
2. Mode PyInstaller: _MEIPASS/CadreSelecteur/resources/ ou _MEIPASS/resources/
3. Mode bundle: tempdir/CadreSelecteur/

Cette centralisation évite la duplication de logique path dans 5+ fichiers.
"""

import sys
import logging
from pathlib import Path
from typing import Optional, List

logger = logging.getLogger(__name__)


class PathResolver:
    """Résout les chemins pour les 3 contextes d'exécution."""

    # Cache pour ne résoudre qu'une fois
    _cache = {}

    # Chemins candidats pour chaque contexte
    _BASE_DIR = Path(__file__).resolve().parent

    @classmethod
    def is_frozen(cls) -> bool:
        """Détecte si on exécute depuis un bundle PyInstaller."""
        return getattr(sys, 'frozen', False)

    @classmethod
    def get_meipass(cls) -> Optional[Path]:
        """Retourne le répertoire _MEIPASS de PyInstaller s'il existe."""
        meipass = getattr(sys, '_MEIPASS', None)
        if meipass:
            return Path(meipass)
        return None

    @classmethod
    def resolve_resources_dir(cls) -> Path:
        """
        Résout le répertoire resources de CadreSelecteur.

        Stratégie:
        1. Si PyInstaller: chercher dans _MEIPASS (3 emplacements possibles)
        2. Sinon: utiliser le répertoire resources/ du package
        3. Fallback: répertoire temporaire

        Returns:
            Path absolue au répertoire resources/
        """
        cache_key = 'resources_dir'
        if cache_key in cls._cache:
            logger.debug(f"Using cached resources_dir: {cls._cache[cache_key]}")
            return cls._cache[cache_key]

        meipass = cls.get_meipass()
        if meipass:
            # Mode PyInstaller: essayer 3 emplacements
            candidates = [
                meipass / 'CadreSelecteur' / 'resources',
                meipass / 'resources',
                meipass,
            ]
            logger.debug(f"PyInstaller mode detected. Checking candidates: {candidates}")

            for candidate in candidates:
                if candidate.exists() and candidate.is_dir():
                    logger.info(f"Found resources_dir at: {candidate}")
                    cls._cache[cache_key] = candidate
                    return candidate

            logger.warning(f"No resources directory found in PyInstaller paths. Using package default.")

        # Mode développement: utiliser le chemin du package
        resources_dir = cls._BASE_DIR / 'resources'
        if resources_dir.exists():
            logger.debug(f"Using package resources_dir: {resources_dir}")
            cls._cache[cache_key] = resources_dir
            return resources_dir

        # Fallback ultime: créer dans tempdir
        import tempfile
        fallback = Path(tempfile.gettempdir()) / 'CadreSelecteur' / 'resources'
        logger.warning(f"Fallback to tempdir resources: {fallback}")
        cls._cache[cache_key] = fallback
        return fallback

    @classmethod
    def resolve_file_in_resources(cls, filename: str) -> Path:
        """
        Résout le chemin complet d'un fichier dans resources/.

        Args:
            filename: nom du fichier (ex: 'config.json', 'fr.json')

        Returns:
            Path absolue au fichier

        Example:
            >>> config_path = PathResolver.resolve_file_in_resources('config.json')
        """
        resources_dir = cls.resolve_resources_dir()
        file_path = resources_dir / filename
        logger.debug(f"Resolved file: {filename} → {file_path}")
        return file_path

    @classmethod
    def resolve_file_in_package(cls, relative_path: str) -> Path:
        """
        Résout un chemin relatif au package CadreSelecteur (pas dans resources).

        Utile pour Fonts/, Templates/, Cadres/, etc.

        Args:
            relative_path: chemin relatif au package (ex: 'Fonts/Arial.ttf')

        Returns:
            Path absolue

        Example:
            >>> fonts_dir = PathResolver.resolve_file_in_package('Fonts')
        """
        cache_key = f'package:{relative_path}'
        if cache_key in cls._cache:
            return cls._cache[cache_key]

        # Mode développement ou PyInstaller (si les fichiers sont bundlés)
        package_path = cls._BASE_DIR / relative_path

        if package_path.exists():
            logger.debug(f"Found package file: {relative_path} → {package_path}")
            cls._cache[cache_key] = package_path
            return package_path

        # Mode PyInstaller: chercher dans _MEIPASS
        meipass = cls.get_meipass()
        if meipass:
            meipass_path = meipass / 'CadreSelecteur' / relative_path
            if meipass_path.exists():
                logger.debug(f"Found in MEIPASS: {relative_path} → {meipass_path}")
                cls._cache[cache_key] = meipass_path
                return meipass_path

        logger.warning(f"Could not find package file: {relative_path}")
        # Retourner le chemin attendu même s'il n'existe pas (pour messages d'erreur clairs)
        cls._cache[cache_key] = package_path
        return package_path

    @classmethod
    def resolve_i18n_dir(cls) -> Path:
        """
        Résout le répertoire i18n/.

        Retour:
            Path au répertoire i18n/
        """
        return cls.resolve_file_in_package('i18n')

    @classmethod
    def resolve_i18n_file(cls, lang: str) -> Path:
        """
        Résout le chemin d'un fichier de langue.

        Stratégie:
        1. resources/{lang}.json (priorité)
        2. i18n/{lang}.json (fallback)

        Args:
            lang: code de langue (ex: 'fr', 'en')

        Returns:
            Path au fichier de langue
        """
        # Priorité 1: resources/
        resources_file = cls.resolve_file_in_resources(f'{lang}.json')
        if resources_file.exists():
            logger.debug(f"Found i18n in resources: {lang}.json")
            return resources_file

        # Priorité 2: i18n/
        i18n_file = cls.resolve_i18n_dir() / f'{lang}.json'
        logger.debug(f"Falling back to i18n/{lang}.json")
        return i18n_file

    @classmethod
    def clear_cache(cls):
        """Vide le cache. Utile pour les tests."""
        cls._cache.clear()
        logger.debug("Path resolver cache cleared")


# API publique simple
def resolve_resources_dir() -> Path:
    """Résout le répertoire resources/ (API publique)."""
    return PathResolver.resolve_resources_dir()


def resolve_file_in_resources(filename: str) -> Path:
    """Résout un fichier dans resources/ (API publique)."""
    return PathResolver.resolve_file_in_resources(filename)


def resolve_file_in_package(relative_path: str) -> Path:
    """Résout un fichier dans le package (API publique)."""
    return PathResolver.resolve_file_in_package(relative_path)


def resolve_i18n_file(lang: str) -> Path:
    """Résout un fichier de langue (API publique)."""
    return PathResolver.resolve_i18n_file(lang)


__all__ = [
    'PathResolver',
    'resolve_resources_dir',
    'resolve_file_in_resources',
    'resolve_file_in_package',
    'resolve_i18n_file',
]


# -*- coding: utf-8 -*-
"""
Gestionnaire centralisé de références PhotoImage.

Tkinter garbage-collect les PhotoImage si on ne garde pas de référence.
Ce module fournit une API propre pour gérer ces références sans les
disperser partout dans le code (plus de `_image_refs.append()` partout).
"""

import logging
from typing import Dict, List
from PIL.ImageTk import PhotoImage

logger = logging.getLogger(__name__)


class ImageRefManager:
    """Gère les références PhotoImage pour éviter le garbage collection."""

    def __init__(self):
        """Initialise le manager."""
        # Dictionnaire des listes de références par catégorie
        self._refs: Dict[str, List[PhotoImage]] = {}

    def add_ref(self, ref: PhotoImage, category: str = 'default') -> None:
        """
        Ajoute une référence à une catégorie.

        Args:
            ref: PhotoImage à conserver
            category: catégorie pour grouper les références (ex: 'thumbnails', 'icons', 'backgrounds')
        """
        if category not in self._refs:
            self._refs[category] = []
        self._refs[category].append(ref)
        logger.debug(f"Added PhotoImage ref to category '{category}' (total: {len(self._refs[category])})")

    def clear_category(self, category: str) -> int:
        """
        Efface toutes les références d'une catégorie.

        Args:
            category: catégorie à effacer

        Returns:
            Nombre de références effacées
        """
        if category not in self._refs:
            return 0
        count = len(self._refs[category])
        self._refs[category].clear()
        logger.debug(f"Cleared {count} PhotoImage refs from category '{category}'")
        return count

    def clear_all(self) -> int:
        """
        Efface TOUTES les références.

        Returns:
            Nombre total de références effacées
        """
        total = sum(len(refs) for refs in self._refs.values())
        self._refs.clear()
        logger.debug(f"Cleared all {total} PhotoImage refs")
        return total

    def get_count(self, category: str = None) -> int:
        """
        Retourne le nombre de références.

        Args:
            category: catégorie (None = tous)

        Returns:
            Nombre de références
        """
        if category is None:
            return sum(len(refs) for refs in self._refs.values())
        return len(self._refs.get(category, []))

    def get_categories(self) -> list:
        """Retourne les catégories existantes."""
        return list(self._refs.keys())

    def __repr__(self) -> str:
        details = ", ".join(f"{cat}: {len(refs)}" for cat, refs in self._refs.items())
        return f"ImageRefManager({details})"


__all__ = ['ImageRefManager']


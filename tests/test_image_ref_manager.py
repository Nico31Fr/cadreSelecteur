# -*- coding: utf-8 -*-
"""
Tests pour ImageRefManager.

Valide que:
1. Les références sont conservées correctement
2. Le caching par catégorie fonctionne
3. Les opérations clear fonctionnent
"""

import pytest
import tkinter as tk
from PIL import Image, ImageTk

from CadreSelecteur.image_ref_manager import ImageRefManager


@pytest.fixture(scope="session")
def tk_root():
    """Créer une fenêtre Tk pour la session (nécessaire pour PhotoImage)."""
    root = tk.Tk()
    root.withdraw()  # Cacher la fenêtre
    yield root
    root.destroy()


@pytest.fixture
def simple_image():
    """Crée une simple image de test."""
    img = Image.new('RGB', (100, 100), color='red')
    return img


@pytest.fixture
def photoimage(tk_root, simple_image):
    """Crée une PhotoImage de test."""
    return ImageTk.PhotoImage(simple_image, master=tk_root)


@pytest.fixture
def manager():
    """Crée un manager frais pour chaque test."""
    return ImageRefManager()


class TestImageRefManager:
    """Tests du gestionnaire de références."""

    def test_add_ref_default_category(self, manager, photoimage):
        """Ajouter une référence dans la catégorie par défaut."""
        manager.add_ref(photoimage)
        assert manager.get_count('default') == 1
        assert manager.get_count() == 1

    def test_add_ref_custom_category(self, manager, photoimage):
        """Ajouter une référence dans une catégorie custom."""
        manager.add_ref(photoimage, 'thumbnails')
        assert manager.get_count('thumbnails') == 1
        assert manager.get_count('default') == 0
        assert manager.get_count() == 1

    def test_multiple_refs_same_category(self, manager, photoimage):
        """Ajouter plusieurs références dans la même catégorie."""
        img1 = photoimage
        img2 = photoimage
        img3 = photoimage
        manager.add_ref(img1, 'icons')
        manager.add_ref(img2, 'icons')
        manager.add_ref(img3, 'icons')
        assert manager.get_count('icons') == 3
        assert manager.get_count() == 3

    def test_multiple_categories(self, manager, photoimage):
        """Ajouter des références dans plusieurs catégories."""
        manager.add_ref(photoimage, 'thumbnails')
        manager.add_ref(photoimage, 'icons')
        manager.add_ref(photoimage, 'dest_canvas')
        assert manager.get_count('thumbnails') == 1
        assert manager.get_count('icons') == 1
        assert manager.get_count('dest_canvas') == 1
        assert manager.get_count() == 3

    def test_clear_category(self, manager, photoimage):
        """Effacer une catégorie spécifique."""
        manager.add_ref(photoimage, 'temp')
        manager.add_ref(photoimage, 'persistent')
        assert manager.get_count() == 2
        
        cleared = manager.clear_category('temp')
        assert cleared == 1
        assert manager.get_count('temp') == 0
        assert manager.get_count('persistent') == 1
        assert manager.get_count() == 1

    def test_clear_nonexistent_category(self, manager):
        """Effacer une catégorie inexistante."""
        cleared = manager.clear_category('nonexistent')
        assert cleared == 0

    def test_clear_all(self, manager, photoimage):
        """Effacer toutes les références."""
        manager.add_ref(photoimage, 'cat1')
        manager.add_ref(photoimage, 'cat2')
        manager.add_ref(photoimage, 'cat3')
        assert manager.get_count() == 3
        
        cleared = manager.clear_all()
        assert cleared == 3
        assert manager.get_count() == 0

    def test_get_categories(self, manager, photoimage):
        """Récupérer la liste des catégories."""
        assert len(manager.get_categories()) == 0
        
        manager.add_ref(photoimage, 'cat1')
        manager.add_ref(photoimage, 'cat2')
        
        categories = manager.get_categories()
        assert set(categories) == {'cat1', 'cat2'}

    def test_repr(self, manager, photoimage):
        """Test la représentation textuelle."""
        manager.add_ref(photoimage, 'icons')
        manager.add_ref(photoimage, 'thumbnails')
        
        repr_str = repr(manager)
        assert 'ImageRefManager' in repr_str
        assert 'icons' in repr_str
        assert 'thumbnails' in repr_str

    def test_manager_workflow(self, manager, photoimage):
        """Test d'un workflow complet."""
        # Ajouter des références
        manager.add_ref(photoimage, 'thumbnails')
        assert manager.get_count('thumbnails') == 1
        
        # Ajouter plus
        manager.add_ref(photoimage, 'thumbnails')
        manager.add_ref(photoimage, 'thumbnails')
        assert manager.get_count('thumbnails') == 3
        
        # Effacer et vérifier
        manager.clear_category('thumbnails')
        assert manager.get_count('thumbnails') == 0
        
        # Ajouter une autre catégorie
        manager.add_ref(photoimage, 'icons')
        assert manager.get_count('icons') == 1
        
        # Effacer tout
        manager.clear_all()
        assert manager.get_count() == 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])


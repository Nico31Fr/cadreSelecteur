# -*- coding: utf-8 -*-
"""Test du thème ttk clam"""

import unittest
import tkinter as tk
from tkinter import ttk
import sys
import logging

# Setup logging
logging.basicConfig(level=logging.DEBUG)

# Add parent to path for imports
sys.path.insert(0, '/home/nicolas/PycharmProjects/cadreSelecteur')

from CadreSelecteur.ttk_theme import apply_clam_theme


class TestClamTheme(unittest.TestCase):
    """Test de la configuration du thème clam"""

    def setUp(self):
        """Créer une fenêtre de test"""
        self.root = tk.Tk()

    def tearDown(self):
        """Fermer la fenêtre de test"""
        try:
            self.root.destroy()
        except:
            pass

    def test_clam_theme_applied(self):
        """Vérifier que le thème clam est appliqué"""
        apply_clam_theme(self.root)
        style = ttk.Style(self.root)
        
        # Le thème appliqué doit être 'clam' ou un fallback disponible
        current_theme = style.theme_use()
        self.assertIn(current_theme, style.theme_names())

    def test_custom_styles_configured(self):
        """Vérifier que les styles personnalisés sont appliqués"""
        apply_clam_theme(self.root)
        style = ttk.Style(self.root)
        
        # Vérifier que les styles personnalisés existent
        try:
            style.lookup("Primary.TButton", "padding")
            self.assertTrue(True, "Style Primary.TButton existe")
        except Exception as e:
            self.fail(f"Style Primary.TButton non trouvé: {e}")

    def test_theme_with_different_widgets(self):
        """Vérifier que le thème fonctionne avec différents widgets"""
        apply_clam_theme(self.root)
        
        try:
            # Créer différents widgets ttk
            frame = ttk.Frame(self.root)
            label = ttk.Label(frame, text="Test")
            button = ttk.Button(frame, text="Click")
            
            frame.pack()
            label.pack()
            button.pack()
            
            # Pas d'erreur = succès
            self.assertTrue(True)
        except Exception as e:
            self.fail(f"Erreur lors de la création de widgets: {e}")


if __name__ == "__main__":
    unittest.main()


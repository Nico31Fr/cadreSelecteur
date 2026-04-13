# -*- coding: utf-8 -*-
"""Configuration du thème ttk pour l'application CadreSelecteur

Module centralisé pour configurer le thème ttk avec des personnalisations
pour assurer une cohérence visuelle dans toute l'application.

Utilisation:
    from CadreSelecteur.ttk_theme import apply_clam_theme
    
    root = tk.Tk()
    apply_clam_theme(root)
    # ... rest of app setup
"""

from tkinter import ttk
import logging

from .config_loader import TTK_THEME

logger = logging.getLogger(__name__)


def apply_clam_theme(root):
    """
    Configure le thème ttk spécifié dans config.json pour la fenêtre racine.
    
    Args:
        root: La fenêtre Tk racine
        
    Note:
        Le thème peut être configuré dans resources/config.json via la clé "TTK_THEME".
        Si le thème spécifié n'est pas disponible, utilise le premier thème disponible.
    """
    try:
        style = ttk.Style(root)
        
        # Lister les thèmes disponibles
        available_themes = style.theme_names()
        logger.debug(f"Thèmes ttk disponibles: {available_themes}")
        
        # Appliquer le thème configuré s'il est disponible
        if TTK_THEME in available_themes:
            style.theme_use(TTK_THEME)
            logger.info(f"Thème ttk '{TTK_THEME}' appliqué avec succès")
        else:
            # Fallback sur le premier thème disponible
            if available_themes:
                logger.warning(f"Thème '{TTK_THEME}' non disponible. Utilisation de '{available_themes[0]}'")
                style.theme_use(available_themes[0])
            else:
                logger.warning("Aucun thème ttk disponible")
                return
        
        # Personnalisations supplémentaires du thème
        configure_clam_styles(style)
        
    except Exception as e:
        logger.error(f"Erreur lors de la configuration du thème ttk: {e}")


def configure_clam_styles(style):
    """
    Configure des styles personnalisés pour le thème clam.
    
    Args:
        style: L'objet ttk.Style()
    """
    try:
        # Exemple: personnaliser les couleurs des boutons
        # (à adapter selon les besoins visuels du projet)
        
        # Style pour les boutons primaires
        style.configure(
            "Primary.TButton",
            padding=10,
            font=("TkDefaultFont", 10)
        )
        
        # Style pour les labels importants
        style.configure(
            "Header.TLabel",
            font=("TkDefaultFont", 12, "bold")
        )
        
        # Style pour les labels secondaires
        style.configure(
            "Secondary.TLabel",
            font=("TkDefaultFont", 9)
        )
        
        logger.debug("Styles personnalisés appliqués")
        
    except Exception as e:
        logger.warning(f"Erreur lors de la configuration des styles: {e}")


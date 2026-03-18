# -*- coding: utf-8 -*-
"""
Module d'exceptions personnalisées pour CadreSelecteur.

Définit une hiérarchie claire d'exceptions par domaine :
- FileOperationError : opérations fichier/répertoire
- ImageProcessingError : chargement/traitement d'images
- ProjectError : sauvegarde/chargement de projets JSON
- UIError : erreurs Tkinter
- ConfigurationError : problèmes de config
- ValidationError : données invalides
"""

from typing import Optional


class CadreSelecteurError(Exception):
    """Exception parent de CadreSelecteur."""

    def __init__(self, message: str, context: Optional[dict] = None):
        """
        Args:
            message: clé i18n ou message d'erreur
            context: dict avec infos additionnelles pour logging/debugging
                    Exemple: {'path': '/some/file', 'reason': 'permission denied'}
        """
        super().__init__(message)
        self.message = message
        self.context = context or {}


class FileOperationError(CadreSelecteurError):
    """Erreur lors d'opérations fichier (copie, lecture, écriture, suppression)."""

    pass


class ImageProcessingError(CadreSelecteurError):
    """Erreur lors du chargement ou traitement d'images (PIL/Pillow)."""

    pass


class ProjectError(CadreSelecteurError):
    """Erreur lors de sauvegarde/chargement de projets (JSON)."""

    pass


class UIError(CadreSelecteurError):
    """Erreur Tkinter ou de widget."""

    pass


class ConfigurationError(CadreSelecteurError):
    """Erreur de configuration (fichier malformé, valeur invalide)."""

    pass


class ValidationError(CadreSelecteurError):
    """Erreur de validation de données (chemin traversal, type invalide, etc.)."""

    pass


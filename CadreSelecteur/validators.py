# -*- coding: utf-8 -*-
"""
Module de validation centralisé pour CadreSelecteur.

Valide les données utilisateur et les inputs avant traitement :
- Noms de fichiers (chemin traversal prevention)
- Couleurs hex
- Positions et tailles (nombres positifs)
- Chemins (sécurité)
- Structures JSON/XML
"""

import logging
import re
from pathlib import Path
from typing import Any, Union, Optional

logger = logging.getLogger(__name__)


class ValidationError(ValueError):
    """Exception levée lors d'une validation échouée."""
    pass


class Validators:
    """Collecte de validateurs pour les données du projet."""

    # Regex pour nom de fichier sûr (pas de chemin traversal)
    SAFE_FILENAME_REGEX = re.compile(r'^[a-zA-Z0-9_\-. ]+$')
    
    # Regex pour couleur hex
    HEX_COLOR_REGEX = re.compile(r'^#[0-9A-Fa-f]{6}$')
    
    # Caractères interdits dans les noms de fichiers
    FORBIDDEN_CHARS = {'/', '\\', ':', '*', '?', '"', '<', '>', '|', '\0'}

    @staticmethod
    def validate_filename(filename: str, allow_subdirs: bool = False) -> str:
        """
        Valide un nom de fichier pour éviter chemin traversal et caractères invalides.

        Args:
            filename: nom du fichier à valider
            allow_subdirs: autoriser les sous-répertoires (ex: "folder/file.txt")

        Returns:
            Nom validé

        Raises:
            ValidationError: si le nom est invalide
        """
        if not filename:
            raise ValidationError("Filename cannot be empty")

        if not isinstance(filename, str):
            raise ValidationError(f"Filename must be string, got {type(filename)}")

        # Vérifier la longueur
        if len(filename) > 255:
            raise ValidationError(f"Filename too long (max 255 chars, got {len(filename)})")

        # Vérifier les chemins traversal
        if '..' in filename or filename.startswith('/'):
            raise ValidationError(f"Path traversal detected in filename: {filename}")

        # Vérifier les caractères interdits
        forbidden = Validators.FORBIDDEN_CHARS - ({'/'}  if allow_subdirs else set())
        for char in forbidden:
            if char in filename:
                raise ValidationError(f"Forbidden character in filename: {repr(char)}")

        # Vérifier les caractères valides (sauf '/' si allow_subdirs)
        if allow_subdirs:
            # Vérifier chaque partie du chemin
            for part in filename.split('/'):
                if part and not Validators.SAFE_FILENAME_REGEX.match(part):
                    raise ValidationError(f"Invalid characters in path component: {part}")
        else:
            if not Validators.SAFE_FILENAME_REGEX.match(filename):
                raise ValidationError(f"Invalid filename format: {filename}")

        logger.debug(f"Filename validated: {filename}")
        return filename

    @staticmethod
    def validate_hex_color(color: str) -> str:
        """
        Valide une couleur hexadécimale (#RRGGBB).

        Args:
            color: couleur en format hex

        Returns:
            Couleur validée (normalisée en majuscules)

        Raises:
            ValidationError: si la couleur est invalide
        """
        if not color:
            raise ValidationError("Color cannot be empty")

        if not isinstance(color, str):
            raise ValidationError(f"Color must be string, got {type(color)}")

        # Normaliser (enlever espaces, convertir en majuscules)
        color = color.strip().upper()

        if not Validators.HEX_COLOR_REGEX.match(color):
            raise ValidationError(f"Invalid hex color format: {color}. Expected #RRGGBB")

        logger.debug(f"Color validated: {color}")
        return color

    @staticmethod
    def is_valid_hex_color(color: str) -> bool:
        """
        Vérifie si une couleur hex est valide (sans lever d'exception).
        
        Args:
            color: couleur en format hex
            
        Returns:
            True si valide, False sinon
        """
        if not color or not isinstance(color, str):
            return False
        return bool(Validators.HEX_COLOR_REGEX.match(color.strip().upper()))

    @staticmethod
    def validate_positive_number(value: Union[int, float], 
                                 name: str = "value",
                                 allow_zero: bool = False) -> Union[int, float]:
        """
        Valide qu'un nombre est positif (et entier ou float).

        Args:
            value: nombre à valider
            name: nom du champ (pour messages d'erreur)
            allow_zero: accepter zéro?

        Returns:
            Nombre validé

        Raises:
            ValidationError: si le nombre est invalide
        """
        if not isinstance(value, (int, float)):
            raise ValidationError(f"{name} must be number, got {type(value)}")

        if value < 0 or (value == 0 and not allow_zero):
            raise ValidationError(f"{name} must be positive, got {value}")

        logger.debug(f"{name} validated: {value}")
        return value

    @staticmethod
    def validate_position(x: Union[int, float], y: Union[int, float]) -> tuple:
        """
        Valide une position (x, y).

        Args:
            x: coordonnée x
            y: coordonnée y

        Returns:
            Tuple (x, y) validé

        Raises:
            ValidationError: si la position est invalide
        """
        x_val = Validators.validate_positive_number(x, name="x", allow_zero=True)
        y_val = Validators.validate_positive_number(y, name="y", allow_zero=True)
        return (x_val, y_val)

    @staticmethod
    def validate_size(width: Union[int, float], height: Union[int, float], 
                     min_size: int = 1) -> tuple:
        """
        Valide une taille (width, height).

        Args:
            width: largeur
            height: hauteur
            min_size: taille minimale (défaut: 1)

        Returns:
            Tuple (width, height) validé

        Raises:
            ValidationError: si la taille est invalide
        """
        if not isinstance(width, (int, float)):
            raise ValidationError(f"width must be number, got {type(width)}")
        if not isinstance(height, (int, float)):
            raise ValidationError(f"height must be number, got {type(height)}")

        if width < min_size:
            raise ValidationError(f"width must be >= {min_size}, got {width}")
        if height < min_size:
            raise ValidationError(f"height must be >= {min_size}, got {height}")

        logger.debug(f"Size validated: {width}x{height}")
        return (width, height)

    @staticmethod
    def validate_path(path_str: Union[str, Path], must_exist: bool = False) -> Path:
        """
        Valide un chemin (prévention chemin traversal, existence optionnelle).

        Args:
            path_str: chemin à valider
            must_exist: doit le chemin exister?

        Returns:
            Path validé

        Raises:
            ValidationError: si le chemin est invalide
        """
        try:
            p = Path(path_str)
        except (TypeError, ValueError) as e:
            raise ValidationError(f"Invalid path: {e}")

        # Résoudre le chemin pour éviter chemin traversal
        try:
            p = p.resolve()
        except (OSError, RuntimeError) as e:
            raise ValidationError(f"Cannot resolve path: {e}")

        if must_exist and not p.exists():
            raise ValidationError(f"Path does not exist: {p}")

        logger.debug(f"Path validated: {p}")
        return p

    @staticmethod
    def validate_project_name(name: str) -> str:
        """
        Valide un nom de projet.

        Args:
            name: nom du projet

        Returns:
            Nom validé

        Raises:
            ValidationError: si le nom est invalide
        """
        if not name or not name.strip():
            raise ValidationError("Project name cannot be empty")

        if not isinstance(name, str):
            raise ValidationError(f"Project name must be string, got {type(name)}")

        # Utiliser le validateur filename mais sans '.png' etc
        name = name.strip()
        if len(name) > 100:
            raise ValidationError(f"Project name too long (max 100 chars)")

        # Caractères valides pour nom de projet
        if not re.match(r'^[a-zA-Z0-9_\-. ]+$', name):
            raise ValidationError(f"Project name contains invalid characters: {name}")

        logger.debug(f"Project name validated: {name}")
        return name

    @staticmethod
    def validate_layer_data(layer_dict: dict) -> dict:
        """
        Valide la structure de données d'une couche.

        Args:
            layer_dict: dictionnaire de données couche

        Returns:
            Dictionnaire validé

        Raises:
            ValidationError: si la structure est invalide
        """
        if not isinstance(layer_dict, dict):
            raise ValidationError(f"Layer data must be dict, got {type(layer_dict)}")

        # Champs obligatoires
        required_fields = {'layer_type', 'name', 'visible', 'locked'}
        missing = required_fields - set(layer_dict.keys())
        if missing:
            raise ValidationError(f"Layer data missing fields: {missing}")

        # Valider les champs
        layer_type = layer_dict.get('layer_type')
        if layer_type not in {'Image', 'Texte', 'ZoneEx'}:
            raise ValidationError(f"Invalid layer type: {layer_type}")

        name = layer_dict.get('name')
        if not isinstance(name, str) or not name:
            raise ValidationError(f"Layer name must be non-empty string")

        if not isinstance(layer_dict.get('visible'), bool):
            raise ValidationError(f"visible must be boolean")

        if not isinstance(layer_dict.get('locked'), bool):
            raise ValidationError(f"locked must be boolean")

        logger.debug(f"Layer data validated: {layer_type} '{name}'")
        return layer_dict

    @staticmethod
    def validate_json_structure(data: Any, expected_type: type = dict) -> Any:
        """
        Valide la structure de données JSON.

        Args:
            data: données à valider
            expected_type: type attendu (dict, list, etc.)

        Returns:
            Données validées

        Raises:
            ValidationError: si la structure est invalide
        """
        if not isinstance(data, expected_type):
            raise ValidationError(f"Expected {expected_type.__name__}, got {type(data).__name__}")

        logger.debug(f"JSON structure validated: {expected_type.__name__}")
        return data

    @staticmethod
    def validate_project_filename(filepath: str) -> str:
        """
        Valide un chemin de fichier de projet (.json).
        
        Args:
            filepath: chemin du fichier
            
        Returns:
            Chemin validé
            
        Raises:
            ValidationError: si invalide
        """
        if not filepath:
            raise ValidationError("Project filepath cannot be empty")
        
        p = Path(filepath)
        
        # Vérifier extension
        if p.suffix.lower() != '.json':
            raise ValidationError(f"Project file must be .json, got {p.suffix}")
        
        # Valider nom
        Validators.validate_filename(p.name)
        
        logger.debug(f"Project filename validated: {filepath}")
        return filepath


__all__ = ['Validators', 'ValidationError']


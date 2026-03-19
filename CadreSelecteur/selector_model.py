# -*- coding: utf-8 -*-
"""
Modèle métier pour le sélecteur de cadres (séparé de Tkinter)
Gère: listing cadres, sélection, opérations fichier
"""

import logging
from pathlib import Path
from typing import List, Optional, Dict, Tuple
from shutil import copy, rmtree

from PIL import Image

from CadreSelecteur.exceptions import FileOperationError, UIError
from CadreSelecteur.validators import Validators, ValidationError

logger = logging.getLogger(__name__)


class SelectorModel:
    """
    Modèle métier pour le sélecteur de cadres.
    Contient TOUTE la logique métier sans dépendance Tkinter.
    
    Responsabilités:
    - Listing cadres/templates
    - Sélection et copie de cadres
    - Génération thumbnails
    - Gestion opérations fichier
    """

    def __init__(self,
                 template_dir: str,
                 frames_dir: str,
                 thumbnail_height: int = 60):
        """
        Initialise le modèle sélecteur.
        
        Args:
            template_dir: Chemin vers répertoire des templates
            frames_dir: Chemin vers répertoire des cadres sélectionnés
            thumbnail_height: Hauteur des thumbnails (pixels)
        """
        self.template_dir = Path(template_dir)
        self.frames_dir = Path(frames_dir)
        self.thumbnail_height = thumbnail_height
        
        # Ensure directories exist
        self.template_dir.mkdir(parents=True, exist_ok=True)
        self.frames_dir.mkdir(parents=True, exist_ok=True)
        
        # Cache templates (filename → PIL Image)
        self._template_cache: Dict[str, Image.Image] = {}
        self._thumbnail_cache: Dict[str, Image.Image] = {}

    # ---- Listing ----
    
    def list_available_templates(self) -> List[Tuple[str, Path]]:
        """
        Liste tous les templates disponibles.
        
        Returns:
            Liste de (nom, path) pour les fichiers template_*.png
        """
        try:
            templates = sorted(self.template_dir.glob('template_*.png'))
            return [(t.name, t) for t in templates]
        except Exception as e:
            logger.error(f"Erreur listing templates: {e}")
            return []

    def list_installed_frames(self) -> List[Tuple[str, Path]]:
        """
        Liste les cadres sélectionnés/installés.
        
        Returns:
            Liste de (nom, path) pour les fichiers cadre_*.png dans frames_dir
        """
        try:
            frames = sorted(self.frames_dir.glob('cadre_*.png'))
            return [(f.name, f) for f in frames]
        except Exception as e:
            logger.error(f"Erreur listing cadres: {e}")
            return []

    def get_template_xml(self, template_name: str) -> Optional[Path]:
        """Récupère le fichier XML correspondant à un template."""
        xml_name = Path(template_name).with_suffix('.xml')
        xml_path = self.template_dir / xml_name
        
        if xml_path.exists():
            return xml_path
        return None

    # ---- Sélection de cadres ----
    
    def select_frame(self, template_path: Path, frame_type: str = "1") -> None:
        """
        Sélectionne un template comme cadre actif.
        
        Args:
            template_path: Path du template PNG
            frame_type: "1" pour cadre_1.png, "4" pour cadre_4.png
            
        Raises:
            FileOperationError: En cas d'erreur copie
            ValidationError: Si frame_type invalide
        """
        # Valider frame_type
        if frame_type not in ("1", "4"):
            raise ValidationError(f"Type cadre invalide: {frame_type}")
        
        if not template_path.exists():
            raise FileOperationError(f"Template non trouvé: {template_path}")
        
        try:
            dest_name = f"cadre_{frame_type}.png"
            dest_path = self.frames_dir / dest_name
            
            # Copier template → cadre
            copy(str(template_path), str(dest_path))
            logger.info(f"Cadre sélectionné: {template_path.name} → {dest_name}")
            
            # Invalider cache thumbnails pour ce cadre
            self._thumbnail_cache.pop(dest_name, None)
        
        except (OSError, Exception) as e:
            raise FileOperationError(f"Erreur sélection cadre: {e}") from e

    def copy_frame(self, src_name: str, dest_name: str) -> None:
        """
        Copie un cadre vers une nouvelle destination.
        
        Args:
            src_name: Nom source (ex: "cadre_1.png")
            dest_name: Nom destination
            
        Raises:
            FileOperationError: En cas d'erreur copie
        """
        # Valider noms
        src_name = Validators.validate_filename(src_name)
        dest_name = Validators.validate_filename(dest_name)
        
        src_path = self.frames_dir / src_name
        dest_path = self.frames_dir / dest_name
        
        if not src_path.exists():
            raise FileOperationError(f"Cadre source non trouvé: {src_name}")
        
        try:
            copy(str(src_path), str(dest_path))
            logger.info(f"Cadre copié: {src_name} → {dest_name}")
            self._thumbnail_cache.pop(dest_name, None)
        
        except (OSError, Exception) as e:
            raise FileOperationError(f"Erreur copie cadre: {e}") from e

    def delete_frame(self, frame_name: str) -> None:
        """
        Supprime un cadre.
        
        Args:
            frame_name: Nom du cadre (ex: "cadre_1.png")
            
        Raises:
            FileOperationError: En cas d'erreur suppression
        """
        # Valider nom
        frame_name = Validators.validate_filename(frame_name)
        
        frame_path = self.frames_dir / frame_name
        
        if not frame_path.exists():
            raise FileOperationError(f"Cadre non trouvé: {frame_name}")
        
        try:
            frame_path.unlink()
            logger.info(f"Cadre supprimé: {frame_name}")
            self._thumbnail_cache.pop(frame_name, None)
        
        except (OSError, Exception) as e:
            raise FileOperationError(f"Erreur suppression cadre: {e}") from e

    def delete_frame_directory(self, frame_name: str) -> None:
        """
        Supprime un répertoire de cadre (ex: "cadre_1/").
        
        Args:
            frame_name: Nom du répertoire
            
        Raises:
            FileOperationError: En cas d'erreur suppression
        """
        # Valider nom
        frame_name = Validators.validate_filename(frame_name)
        
        frame_dir = self.frames_dir / frame_name
        
        if not frame_dir.exists():
            raise FileOperationError(f"Répertoire cadre non trouvé: {frame_name}")
        
        try:
            rmtree(frame_dir)
            logger.info(f"Répertoire cadre supprimé: {frame_name}")
            # Invalider cache de tous les thumbnails de ce répertoire
            self._thumbnail_cache.clear()
        
        except (OSError, Exception) as e:
            raise FileOperationError(f"Erreur suppression répertoire: {e}") from e

    # ---- Thumbnails ----
    
    def get_thumbnail(self, image_path: Path) -> Optional[Image.Image]:
        """
        Génère (ou récupère du cache) un thumbnail.
        
        Args:
            image_path: Path de l'image source
            
        Returns:
            PIL Image resizée, ou None si erreur
        """
        cache_key = image_path.name
        
        # Vérifier cache
        if cache_key in self._thumbnail_cache:
            return self._thumbnail_cache[cache_key]
        
        try:
            if not image_path.exists():
                logger.warning(f"Image non trouvée: {image_path}")
                return None
            
            image = Image.open(image_path)
            
            # Resize proportionnel
            ratio = self.thumbnail_height / image.height
            new_width = int(image.width * ratio)
            thumbnail = image.resize((new_width, self.thumbnail_height), Image.Resampling.LANCZOS)
            
            # Cacher
            self._thumbnail_cache[cache_key] = thumbnail
            return thumbnail
        
        except Exception as e:
            logger.warning(f"Erreur génération thumbnail: {e}")
            return None

    def clear_thumbnail_cache(self) -> None:
        """Vide le cache des thumbnails."""
        self._thumbnail_cache.clear()
        logger.debug("Cache thumbnails vidé")

    # ---- Introspection ----
    
    def get_frame_info(self, frame_name: str) -> Optional[Dict[str, any]]:
        """Récupère les infos d'un cadre."""
        frame_path = self.frames_dir / frame_name
        
        if not frame_path.exists():
            return None
        
        try:
            image = Image.open(frame_path)
            return {
                "name": frame_name,
                "path": str(frame_path),
                "size": image.size,
                "format": image.format,
            }
        except Exception as e:
            logger.warning(f"Erreur infos cadre: {e}")
            return None

    def get_selected_frame(self, layout: str = "1") -> Optional[Path]:
        """Récupère le chemin du cadre sélectionné."""
        frame_name = f"cadre_{layout}.png"
        frame_path = self.frames_dir / frame_name
        return frame_path if frame_path.exists() else None


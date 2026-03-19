# -*- coding: utf-8 -*-
"""
Modèle métier pour l'éditeur de cadre (séparé de Tkinter)
Gère: couches, sauvegarde/chargement projets, export images
"""

import json
import logging
from pathlib import Path
from shutil import copy
from typing import List, Dict, Any, Optional, Tuple

from PIL import Image

from CadreSelecteur.exceptions import ProjectError, FileOperationError
from CadreSelecteur.validators import Validators, ValidationError

logger = logging.getLogger(__name__)


class EditorModel:
    """
    Modèle métier pour l'éditeur de cadre.
    Contient TOUTE la logique métier sans dépendance Tkinter.
    
    Responsabilités:
    - Gestion pile de calques (add, delete, move, select)
    - Sauvegarde/chargement projets JSON
    - Export images PNG
    - Gestion templates XML
    """

    def __init__(self,
                 template_dir: str,
                 destination_dir: str,
                 canvas_width: int = 600,
                 canvas_height: int = 400,
                 image_width: int = 1800,
                 image_height: int = 1200):
        """
        Initialise le modèle éditeur.
        
        Args:
            template_dir: Chemin vers répertoire des templates
            destination_dir: Chemin vers répertoire de sortie
            canvas_width: Largeur canvas d'édition (pixels display)
            canvas_height: Hauteur canvas d'édition
            image_width: Largeur image exportée (pixels réels)
            image_height: Hauteur image exportée
        """
        self.template_dir = Path(template_dir)
        self.destination_dir = Path(destination_dir)
        
        self.CANVA_W = canvas_width
        self.CANVA_H = canvas_height
        self.IMAGE_W = image_width
        self.IMAGE_H = image_height
        self.RATIO = int(self.IMAGE_W // self.CANVA_W)
        
        # État de la pile de calques
        self.layers_1photo: List[Dict[str, Any]] = []
        self.layers_4photo: List[Dict[str, Any]] = []
        self.active_layer_idx_1: int = -1
        self.active_layer_idx_4: int = -1
        
        # État couleur de fond
        self.background_color_1: str = "#FFFFFF"
        self.background_color_4: str = "#FFFFFF"
        
        # Template sélectionné
        self.selected_template: str = "template_1.xml"
        
        # Cache zones d'exclusion
        self.exclusion_zones: Dict[str, List[Tuple[int, int, int, int]]] = {}

    # ---- Gestion pile calques (vue-agnostique) ----
    
    def get_layers(self, layout: str = "1") -> List[Dict[str, Any]]:
        """Récupère la pile de calques pour le layout donné."""
        if layout == "1":
            return self.layers_1photo
        elif layout == "4":
            return self.layers_4photo
        raise ValueError(f"Layout invalide: {layout}")

    def get_active_layer_idx(self, layout: str = "1") -> int:
        """Récupère l'index du calque actif."""
        if layout == "1":
            return self.active_layer_idx_1
        elif layout == "4":
            return self.active_layer_idx_4
        raise ValueError(f"Layout invalide: {layout}")

    def set_active_layer_idx(self, idx: int, layout: str = "1") -> None:
        """Définit le calque actif."""
        layers = self.get_layers(layout)
        if idx < -1 or idx >= len(layers):
            raise IndexError(f"Index calque invalide: {idx}")
        
        if layout == "1":
            self.active_layer_idx_1 = idx
        elif layout == "4":
            self.active_layer_idx_4 = idx
        else:
            raise ValueError(f"Layout invalide: {layout}")

    def add_layer(self, layer_data: Dict[str, Any], layout: str = "1") -> int:
        """
        Ajoute un calque à la pile.
        
        Args:
            layer_data: Dictionnaire avec données du calque (type, position, etc.)
            layout: "1" ou "4"
        
        Returns:
            Index du calque ajouté
        """
        layers = self.get_layers(layout)
        layers.append(layer_data)
        idx = len(layers) - 1
        self.set_active_layer_idx(idx, layout)
        layer_type = layer_data.get("type", "unknown")
        logger.info(f"Layer ajouté: {layer_type} (layout={layout}, idx={idx})")
        return idx

    def delete_layer(self, layout: str = "1") -> bool:
        """
        Supprime le calque actif.
        
        Returns:
            True si suppression réussie, False sinon
        """
        layers = self.get_layers(layout)
        idx = self.get_active_layer_idx(layout)
        
        if idx < 0 or idx >= len(layers):
            logger.warning(f"Impossible de supprimer: index invalide {idx}")
            return False
        
        layer_type = layers[idx].get("type", "unknown")
        layers.pop(idx)
        
        # Ajuster index actif
        if len(layers) > 0:
            new_idx = min(idx, len(layers) - 1)
            self.set_active_layer_idx(new_idx, layout)
        else:
            self.set_active_layer_idx(-1, layout)
        
        logger.info(f"Layer supprimé: {layer_type} (layout={layout})")
        return True

    def move_layer(self, direction: int, layout: str = "1") -> bool:
        """
        Déplace un calque dans la pile (z-order).
        
        Args:
            direction: -1 pour monter, +1 pour descendre
            layout: "1" ou "4"
            
        Returns:
            True si déplacement réussi
        """
        layers = self.get_layers(layout)
        idx = self.get_active_layer_idx(layout)
        new_idx = idx + direction
        
        if new_idx < 0 or new_idx >= len(layers):
            logger.warning(f"Impossible de déplacer calque: hors limites")
            return False
        
        # Swap
        layers[idx], layers[new_idx] = layers[new_idx], layers[idx]
        self.set_active_layer_idx(new_idx, layout)
        logger.info(f"Layer déplacé: idx {idx} → {new_idx}")
        return True

    def clean_editable_layers(self, layout: str = "1") -> None:
        """Supprime tous les calques NON-exclusion pour un layout."""
        layers = self.get_layers(layout)
        to_remove = [i for i, layer in enumerate(layers)
                     if layer.layer_type != 'ZoneEx']
        
        for i in reversed(to_remove):
            layers.pop(i)
        
        self.set_active_layer_idx(-1 if not layers else 0, layout)
        logger.info(f"Calques éditables supprimés (layout={layout})")

    # ---- Gestion couleur fond ----
    
    def get_background_color(self, layout: str = "1") -> str:
        """Récupère la couleur de fond."""
        if layout == "1":
            return self.background_color_1
        elif layout == "4":
            return self.background_color_4
        raise ValueError(f"Layout invalide: {layout}")

    def set_background_color(self, color: str, layout: str = "1") -> None:
        """
        Définit la couleur de fond (validation hex).
        
        Args:
            color: Couleur hex "#RRGGBB"
            layout: "1" ou "4"
        """
        # Valider format hex
        if not Validators.is_valid_hex_color(color):
            raise ValidationError(f"Couleur hex invalide: {color}")
        
        if layout == "1":
            self.background_color_1 = color
        elif layout == "4":
            self.background_color_4 = color
        else:
            raise ValueError(f"Layout invalide: {layout}")
        
        logger.debug(f"Couleur fond mise à jour: {color} (layout={layout})")

    # ---- Sauvegarde/Chargement projets ----
    
    def save_project(self, file_path: str) -> None:
        """
        Sauvegarde le projet actuel en JSON.
        
        Args:
            file_path: Chemin du fichier .json
            
        Raises:
            FileOperationError: En cas d'erreur d'écriture
        """
        try:
            # Valider nom fichier
            file_path = Validators.validate_project_filename(file_path)
            
            project_data = {
                "version": "1.0",
                "template": self.selected_template,
                "app1": {
                    "layers": self.layers_1photo,  # Stockées comme dicts
                    "background_color": self.background_color_1,
                },
                "app4": {
                    "layers": self.layers_4photo,  # Stockées comme dicts
                    "background_color": self.background_color_4,
                },
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(project_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Projet sauvegardé: {file_path}")
        
        except ValidationError as e:
            raise FileOperationError(f"Nom fichier invalide: {e}") from e
        except (IOError, OSError) as e:
            raise FileOperationError(f"Erreur écriture projet: {e}") from e

    def load_project(self, file_path: str) -> None:
        """
        Charge un projet depuis un fichier JSON.
        
        Args:
            file_path: Chemin du fichier .json
            
        Raises:
            FileOperationError: En cas d'erreur de lecture
            ProjectError: Si format projet invalide
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                project_data = json.load(f)
            
            # Valider structure
            if "app1" not in project_data or "app4" not in project_data:
                raise ProjectError("Format projet invalide (app1/app4 manquants)")
            
            # Charger template
            self.selected_template = project_data.get("template", "template_1.xml")
            
            # Charger calques et couleurs
            self._load_layout(project_data["app1"], layout="1")
            self._load_layout(project_data["app4"], layout="4")
            
            logger.info(f"Projet chargé: {file_path}")
        
        except (IOError, OSError) as e:
            raise FileOperationError(f"Erreur lecture projet: {e}") from e
        except json.JSONDecodeError as e:
            raise ProjectError(f"JSON invalide: {e}") from e

    def _load_layout(self, layout_data: Dict[str, Any], layout: str) -> None:
        """
        Charge les données d'un layout (app1 ou app4).
        NOTE: Retourne juste les données brutes (dicts) - la vue Tkinter les convertira en Layer objets
        """
        # Valider structure
        layer_dicts = layout_data.get("layers", [])
        if not isinstance(layer_dicts, list):
            logger.warning("layers must be a list")
            layer_dicts = []
        
        # NOTE: On stocke les dicts bruts, pas les objets Layer
        # Les couches seront créées par ImageEditor avec les params Tkinter
        
        if layout == "1":
            self.layers_1photo = layer_dicts  # Stockage simplifié pour maintenant
            self.background_color_1 = layout_data.get("background_color", "#FFFFFF")
            self.active_layer_idx_1 = 0 if layer_dicts else -1
        elif layout == "4":
            self.layers_4photo = layer_dicts
            self.background_color_4 = layout_data.get("background_color", "#FFFFFF")
            self.active_layer_idx_4 = 0 if layer_dicts else -1


    # ---- Export images ----
    
    def get_frame_data_for_export(self, layout: str = "1") -> Tuple[List[Dict[str, Any]], str]:
        """
        Récupère les données d'un frame prêtes pour export par la vue.
        
        Args:
            layout: "1" ou "4"
            
        Returns:
            Tuple (layers_dicts, background_color)
        """
        if layout == "1":
            return self.layers_1photo, self.background_color_1
        elif layout == "4":
            return self.layers_4photo, self.background_color_4
        else:
            raise ValueError(f"Layout invalide: {layout}")

    def _export_frame(self, layers: List[Dict[str, Any]], output_path: str, bg_color: str) -> None:
        """
        Note: Cette fonction est un placeholder. L'export réel doit être fait par ImageEditor
        qui a accès aux objets Layer Tkinter complets.
        """
        raise NotImplementedError(
            "Export doit être fait par la vue (ImageEditor) qui a les objets Layer Tkinter"
        )

    def export_template_xml(self, output_path: str) -> None:
        """
        Copie le XML template vers le dossier de sortie.
        
        Args:
            output_path: Chemin fichier XML de sortie
            
        Raises:
            FileOperationError: En cas d'erreur copie
        """
        try:
            source_xml = self.template_dir / self.selected_template
            if not source_xml.exists():
                raise FileNotFoundError(f"Template XML manquant: {source_xml}")
            
            dest_xml = Path(output_path).with_suffix('.xml')
            copy(str(source_xml), str(dest_xml))
            logger.info(f"Template XML copié: {dest_xml}")
        
        except FileNotFoundError as e:
            raise FileOperationError(f"Template XML introuvable: {e}") from e
        except (OSError, Exception) as e:
            raise FileOperationError(f"Erreur copie template: {e}") from e

    # ---- Introspection ----
    
    def get_layer_info(self, layout: str = "1", idx: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """Récupère les infos du calque (ou du calque actif si idx=None)."""
        layers = self.get_layers(layout)
        if idx is None:
            idx = self.get_active_layer_idx(layout)
        
        if idx < 0 or idx >= len(layers):
            return None
        
        layer = layers[idx]
        return {
            "type": layer.layer_type,
            "visible": layer.visible,
            "locked": layer.locked,
            "position": (layer.canva_x, layer.canva_y),
            "size": (layer.canva_w, layer.canva_h),
        }

    def list_templates(self) -> List[str]:
        """Récupère la liste des templates disponibles."""
        try:
            templates = list(self.template_dir.glob('template_*.xml'))
            return sorted([t.name for t in templates])
        except Exception as e:
            logger.warning(f"Erreur lecture templates: {e}")
            return []


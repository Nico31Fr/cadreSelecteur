# -*- coding: utf-8 -*-
"""
Tests pour les modèles métier (sans Tkinter).
Démontre que la logique fonctionne indépendamment de la GUI.
"""

import pytest
import json
import tempfile
from pathlib import Path

from CadreSelecteur.CadreEditeur.editor_model import EditorModel
from CadreSelecteur.selector_model import SelectorModel
from CadreSelecteur.validators import Validators, ValidationError
from CadreSelecteur.exceptions import FileOperationError, ProjectError


class TestEditorModel:
    """Tests pour le modèle éditeur (pure métier, pas de Tkinter)."""

    @pytest.fixture
    def model(self):
        """Crée un modèle pour les tests."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield EditorModel(
                template_dir=tmpdir,
                destination_dir=tmpdir,
            )

    def test_init(self, model):
        """Vérifie l'initialisation."""
        assert model.CANVA_W == 600
        assert model.IMAGE_W == 1800
        assert model.RATIO == 3
        assert len(model.layers_1photo) == 0
        assert len(model.layers_4photo) == 0

    def test_add_layer(self, model):
        """Test ajout de calque."""
        layer_data = {
            "type": "text",
            "content": "Hello",
            "position": (10, 10)
        }
        idx = model.add_layer(layer_data, layout="1")
        
        assert idx == 0
        assert len(model.layers_1photo) == 1
        assert model.get_active_layer_idx("1") == 0

    def test_delete_layer(self, model):
        """Test suppression de calque."""
        layer1 = {"type": "text", "content": "A"}
        layer2 = {"type": "text", "content": "B"}
        
        model.add_layer(layer1, layout="1")
        model.add_layer(layer2, layout="1")
        
        assert len(model.layers_1photo) == 2
        
        model.delete_layer(layout="1")
        assert len(model.layers_1photo) == 1
        assert model.layers_1photo[0]["content"] == "A"

    def test_move_layer(self, model):
        """Test réordonnage de calques."""
        layer1 = {"type": "text", "content": "A"}
        layer2 = {"type": "text", "content": "B"}
        layer3 = {"type": "text", "content": "C"}
        
        model.add_layer(layer1, layout="1")
        model.add_layer(layer2, layout="1")
        model.add_layer(layer3, layout="1")
        
        # Activer le dernier
        model.set_active_layer_idx(2, layout="1")
        
        # Monter d'un cran
        assert model.move_layer(direction=-1, layout="1")
        assert model.get_active_layer_idx("1") == 1
        assert model.layers_1photo[1]["content"] == "C"

    def test_background_color(self, model):
        """Test gestion couleur fond."""
        # Couleur valide
        model.set_background_color("#FF0000", layout="1")
        assert model.get_background_color("1") == "#FF0000"
        
        # Couleur invalide
        with pytest.raises(ValidationError):
            model.set_background_color("INVALID", layout="1")

    def test_save_project(self, model):
        """Test sauvegarde projet."""
        layer1 = {"type": "text", "content": "Test"}
        model.add_layer(layer1, layout="1")
        model.set_background_color("#FF0000", layout="1")
        
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "project.json"
            
            model.save_project(str(filepath))
            assert filepath.exists()
            
            # Vérifier contenu
            with open(filepath) as f:
                data = json.load(f)
            
            assert data["app1"]["background_color"] == "#FF0000"
            assert len(data["app1"]["layers"]) == 1
            assert data["app1"]["layers"][0]["content"] == "Test"

    def test_load_project(self, model):
        """Test chargement projet."""
        # Créer un projet
        filepath = Path(tempfile.gettempdir()) / "test_project.json"
        project_data = {
            "version": "1.0",
            "template": "template_1.xml",
            "app1": {
                "layers": [{"type": "text", "content": "Loaded"}],
                "background_color": "#00FF00",
            },
            "app4": {
                "layers": [],
                "background_color": "#FFFFFF",
            }
        }
        
        with open(filepath, 'w') as f:
            json.dump(project_data, f)
        
        # Charger
        model.load_project(str(filepath))
        
        assert model.background_color_1 == "#00FF00"
        assert len(model.layers_1photo) == 1
        assert model.layers_1photo[0]["content"] == "Loaded"
        
        # Cleanup
        filepath.unlink()

    def test_invalid_layout(self, model):
        """Test validation layout invalide."""
        with pytest.raises(ValueError):
            model.get_layers(layout="invalid")
        
        with pytest.raises(ValueError):
            model.set_active_layer_idx(0, layout="invalid")


class TestSelectorModel:
    """Tests pour le modèle sélecteur."""

    @pytest.fixture
    def model(self):
        """Crée un modèle pour les tests."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Créer structure
            template_dir = Path(tmpdir) / "Templates"
            frames_dir = Path(tmpdir) / "Frames"
            template_dir.mkdir()
            frames_dir.mkdir()
            
            # Créer template PNG fictif
            from PIL import Image
            img = Image.new('RGB', (100, 100), color='red')
            template_path = template_dir / "template_1.png"
            img.save(template_path)
            
            yield SelectorModel(
                template_dir=str(template_dir),
                frames_dir=str(frames_dir),
            )

    def test_list_templates(self, model):
        """Test listing templates."""
        templates = model.list_available_templates()
        assert len(templates) >= 1
        assert any("template_1.png" in name for name, _ in templates)

    def test_select_frame(self, model):
        """Test sélection de cadre."""
        templates = model.list_available_templates()
        if templates:
            template_path = templates[0][1]
            
            # Sélectionner
            model.select_frame(template_path, frame_type="1")
            
            # Vérifier
            frame_path = model.get_selected_frame("1")
            assert frame_path is not None
            assert frame_path.exists()

    def test_delete_frame(self, model):
        """Test suppression de cadre."""
        templates = model.list_available_templates()
        if templates:
            template_path = templates[0][1]
            model.select_frame(template_path, frame_type="1")
            
            # Supprimer
            model.delete_frame("cadre_1.png")
            
            # Vérifier suppression
            frame_path = model.get_selected_frame("1")
            assert frame_path is None

    def test_copy_frame(self, model):
        """Test copie de cadre."""
        templates = model.list_available_templates()
        if templates:
            template_path = templates[0][1]
            model.select_frame(template_path, frame_type="1")
            
            # Copier
            model.copy_frame("cadre_1.png", "custom_frame.png")
            
            # Vérifier
            custom_path = model.frames_dir / "custom_frame.png"
            assert custom_path.exists()

    def test_thumbnail_cache(self, model):
        """Test cache de thumbnails."""
        templates = model.list_available_templates()
        if templates:
            template_path = templates[0][1]
            
            # Première génération
            thumb1 = model.get_thumbnail(template_path)
            
            # Deuxième génération (du cache)
            thumb2 = model.get_thumbnail(template_path)
            
            assert thumb1 is not None
            assert thumb2 is not None
            # Vérifier cache
            assert template_path.name in model._thumbnail_cache


class TestValidators:
    """Tests pour les validateurs."""

    def test_validate_filename(self):
        """Test validation nom de fichier."""
        # Valide
        assert Validators.validate_filename("document.txt")
        assert Validators.validate_filename("my_file-123.json")
        
        # Invalide (chemin traversal)
        with pytest.raises(ValidationError):
            Validators.validate_filename("../etc/passwd")
        
        # Invalide (caractères interdits)
        with pytest.raises(ValidationError):
            Validators.validate_filename("file*/name.txt")

    def test_validate_hex_color(self):
        """Test validation couleur hex."""
        # Valide
        assert Validators.validate_hex_color("#FF0000")
        assert Validators.validate_hex_color("#00ff00")
        
        # Invalide
        with pytest.raises(ValidationError):
            Validators.validate_hex_color("#FF00")  # Trop court
        
        with pytest.raises(ValidationError):
            Validators.validate_hex_color("FF0000")  # Sans #

    def test_is_valid_hex_color(self):
        """Test vérification hex color (sans exception)."""
        assert Validators.is_valid_hex_color("#FF0000")
        assert Validators.is_valid_hex_color("#00ff00")
        assert not Validators.is_valid_hex_color("#FF00")
        assert not Validators.is_valid_hex_color("INVALID")

    def test_validate_project_name(self):
        """Test validation nom de projet."""
        # Valide
        assert Validators.validate_project_name("my_project")
        assert Validators.validate_project_name("Cadre 2024")
        
        # Invalide
        with pytest.raises(ValidationError):
            Validators.validate_project_name("")
        
        with pytest.raises(ValidationError):
            Validators.validate_project_name("../evil")

    def test_validate_positive_number(self):
        """Test validation nombres positifs."""
        # Valide
        assert Validators.validate_positive_number(10) == 10
        assert Validators.validate_positive_number(0, allow_zero=True) == 0
        
        # Invalide
        with pytest.raises(ValidationError):
            Validators.validate_positive_number(-5)
        
        with pytest.raises(ValidationError):
            Validators.validate_positive_number(0, allow_zero=False)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])


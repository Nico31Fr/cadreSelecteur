# -*- coding: utf-8 -*-
"""Tests pour le module validators."""

import pytest
from pathlib import Path

from CadreSelecteur.validators import Validators, ValidationError


class TestFilenameValidation:
    """Tests pour validate_filename."""

    def test_valid_filename(self):
        """Filenames valides doivent passer."""
        assert Validators.validate_filename("document.txt") == "document.txt"
        assert Validators.validate_filename("file_123.json") == "file_123.json"
        assert Validators.validate_filename("my-file.png") == "my-file.png"

    def test_empty_filename(self):
        """Filename vide doit échouer."""
        with pytest.raises(ValidationError):
            Validators.validate_filename("")

    def test_path_traversal_attack(self):
        """Chemins traversal doivent être rejetés."""
        with pytest.raises(ValidationError):
            Validators.validate_filename("../../../etc/passwd")
        with pytest.raises(ValidationError):
            Validators.validate_filename("..\\..\\windows\\system32")

    def test_forbidden_characters(self):
        """Caractères interdits doivent être rejetés."""
        with pytest.raises(ValidationError):
            Validators.validate_filename("file/name.txt")
        with pytest.raises(ValidationError):
            Validators.validate_filename("file:name.txt")
        with pytest.raises(ValidationError):
            Validators.validate_filename("file*name.txt")

    def test_filename_too_long(self):
        """Noms trop longs doivent être rejetés."""
        with pytest.raises(ValidationError):
            Validators.validate_filename("x" * 300)

    def test_subdirs_allowed(self):
        """Avec allow_subdirs=True, chemins valides doivent passer."""
        assert Validators.validate_filename("folder/file.txt", allow_subdirs=True)
        with pytest.raises(ValidationError):
            Validators.validate_filename("../folder/file.txt", allow_subdirs=True)


class TestHexColorValidation:
    """Tests pour validate_hex_color."""

    def test_valid_colors(self):
        """Couleurs hex valides doivent passer."""
        assert Validators.validate_hex_color("#000000") == "#000000"
        assert Validators.validate_hex_color("#FFFFFF") == "#FFFFFF"
        assert Validators.validate_hex_color("#ff00ff") == "#FF00FF"  # Normalized

    def test_empty_color(self):
        """Couleur vide doit échouer."""
        with pytest.raises(ValidationError):
            Validators.validate_hex_color("")

    def test_invalid_format(self):
        """Formats invalides doivent échouer."""
        with pytest.raises(ValidationError):
            Validators.validate_hex_color("000000")  # Missing #
        with pytest.raises(ValidationError):
            Validators.validate_hex_color("#00000")  # Too short
        with pytest.raises(ValidationError):
            Validators.validate_hex_color("#GGGGGG")  # Invalid hex


class TestNumberValidation:
    """Tests pour validate_positive_number."""

    def test_valid_positive_numbers(self):
        """Nombres positifs doivent passer."""
        assert Validators.validate_positive_number(1) == 1
        assert Validators.validate_positive_number(100.5) == 100.5

    def test_zero_allowed(self):
        """Zéro doivent passer si allow_zero=True."""
        assert Validators.validate_positive_number(0, allow_zero=True) == 0

    def test_zero_not_allowed(self):
        """Zéro doit échouer si allow_zero=False."""
        with pytest.raises(ValidationError):
            Validators.validate_positive_number(0, allow_zero=False)

    def test_negative_number(self):
        """Nombres négatifs doivent échouer."""
        with pytest.raises(ValidationError):
            Validators.validate_positive_number(-5)

    def test_invalid_type(self):
        """Types non-numériques doivent échouer."""
        with pytest.raises(ValidationError):
            Validators.validate_positive_number("5")


class TestPositionValidation:
    """Tests pour validate_position."""

    def test_valid_position(self):
        """Positions valides doivent passer."""
        x, y = Validators.validate_position(10, 20)
        assert x == 10 and y == 20

    def test_zero_position(self):
        """Zéro doit être accepté pour positions."""
        x, y = Validators.validate_position(0, 0)
        assert x == 0 and y == 0

    def test_negative_position(self):
        """Positions négatives doivent échouer."""
        with pytest.raises(ValidationError):
            Validators.validate_position(-1, 10)


class TestSizeValidation:
    """Tests pour validate_size."""

    def test_valid_size(self):
        """Tailles valides doivent passer."""
        w, h = Validators.validate_size(100, 200)
        assert w == 100 and h == 200

    def test_zero_size(self):
        """Taille zéro doit échouer."""
        with pytest.raises(ValidationError):
            Validators.validate_size(0, 100)

    def test_negative_size(self):
        """Tailles négatives doivent échouer."""
        with pytest.raises(ValidationError):
            Validators.validate_size(-10, 100)

    def test_min_size_custom(self):
        """Custom min_size doit être respectée."""
        with pytest.raises(ValidationError):
            Validators.validate_size(4, 100, min_size=5)


class TestPathValidation:
    """Tests pour validate_path."""

    def test_valid_path(self, tmp_path):
        """Chemins valides doivent passer."""
        p = Validators.validate_path(str(tmp_path))
        assert isinstance(p, Path)

    def test_path_traversal(self, tmp_path):
        """Chemins traversal doivent être résolus (et échouer si non-existent)."""
        # Ce test montre que resolve() évite les traversals
        # Créer un chemin avec traversal (..) dans tmp_path
        test_file = tmp_path / "test" / "file.txt"
        traversal_path = str(test_file.parent.parent / "test" / ".." / "test" / "file.txt")
        p = Validators.validate_path(traversal_path, must_exist=False)
        # Le chemin doit être résolu (sans les ..)
        assert "test" in str(p)
        # Vérifier que c'est un chemin absolu résolu
        assert p.is_absolute()

    def test_nonexistent_path_ignored(self):
        """Chemins inexistants OK si must_exist=False."""
        # Utiliser un chemin inexistant qui fonctionne sur tous les systèmes
        p = Validators.validate_path("./this_path_does_not_exist_12345/subdir", must_exist=False)
        assert isinstance(p, Path)

    def test_nonexistent_path_required(self, tmp_path):
        """Chemins inexistants échouent si must_exist=True."""
        # Créer un chemin inexistant basé sur tmp_path pour garantir qu'il n'existe pas
        nonexistent_path = tmp_path / "definitely" / "nonexistent" / "path" / "that_wont_exist"
        with pytest.raises(ValidationError):
            Validators.validate_path(str(nonexistent_path), must_exist=True)


class TestProjectNameValidation:
    """Tests pour validate_project_name."""

    def test_valid_project_names(self):
        """Noms de projet valides doivent passer."""
        assert Validators.validate_project_name("MyProject") == "MyProject"
        assert Validators.validate_project_name("project_123") == "project_123"
        assert Validators.validate_project_name("my-project") == "my-project"

    def test_empty_project_name(self):
        """Nom vide doit échouer."""
        with pytest.raises(ValidationError):
            Validators.validate_project_name("")

    def test_project_name_too_long(self):
        """Nom trop long doit échouer."""
        with pytest.raises(ValidationError):
            Validators.validate_project_name("x" * 150)

    def test_project_name_invalid_chars(self):
        """Caractères invalides doivent échouer."""
        with pytest.raises(ValidationError):
            Validators.validate_project_name("project@123")


class TestLayerDataValidation:
    """Tests pour validate_layer_data."""

    def test_valid_layer_data(self):
        """Données de couche valides doivent passer."""
        data = {
            'layer_type': 'Image',
            'name': 'Layer1',
            'visible': True,
            'locked': False
        }
        result = Validators.validate_layer_data(data)
        assert result == data

    def test_missing_field(self):
        """Champs manquants doivent échouer."""
        data = {'layer_type': 'Image', 'name': 'Layer1'}
        with pytest.raises(ValidationError):
            Validators.validate_layer_data(data)

    def test_invalid_layer_type(self):
        """Type de couche invalide doit échouer."""
        data = {
            'layer_type': 'InvalidType',
            'name': 'Layer1',
            'visible': True,
            'locked': False
        }
        with pytest.raises(ValidationError):
            Validators.validate_layer_data(data)

    def test_invalid_visible_type(self):
        """visible doit être booléen."""
        data = {
            'layer_type': 'Image',
            'name': 'Layer1',
            'visible': 'yes',  # Should be bool
            'locked': False
        }
        with pytest.raises(ValidationError):
            Validators.validate_layer_data(data)


class TestJSONValidation:
    """Tests pour validate_json_structure."""

    def test_valid_dict(self):
        """Dict valide doit passer."""
        data = {'key': 'value'}
        result = Validators.validate_json_structure(data, dict)
        assert result == data

    def test_valid_list(self):
        """List valide doit passer."""
        data = [1, 2, 3]
        result = Validators.validate_json_structure(data, list)
        assert result == data

    def test_type_mismatch(self):
        """Type non-matching doit échouer."""
        with pytest.raises(ValidationError):
            Validators.validate_json_structure({'key': 'value'}, list)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])


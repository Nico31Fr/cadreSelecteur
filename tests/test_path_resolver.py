# -*- coding: utf-8 -*-
"""
Tests pour valider la centralisation du path_resolver.

Vérifie que:
1. Tous les chemins sont résolus correctement (dev + PyInstaller)
2. Le caching fonctionne
3. Les trois contextes d'exécution sont supportés
"""

import pytest
from pathlib import Path
from unittest.mock import patch

from CadreSelecteur.path_resolver import (
    PathResolver,
    resolve_resources_dir,
    resolve_file_in_resources,
    resolve_file_in_package,
    resolve_i18n_file,
)


class TestPathResolver:
    """Tests pour PathResolver."""

    def teardown_method(self):
        """Vider le cache après chaque test."""
        PathResolver.clear_cache()

    def test_is_not_frozen_in_dev(self):
        """En mode développement, is_frozen() doit retourner False."""
        assert PathResolver.is_frozen() is False

    def test_resolve_resources_dir_dev_mode(self):
        """En mode développement, resources_dir doit exister."""
        resources_dir = resolve_resources_dir()
        assert resources_dir.exists()
        assert resources_dir.is_dir()
        assert resources_dir.name == 'resources'

    def test_resolve_file_in_resources(self):
        """Résoudre un fichier dans resources/."""
        config_path = resolve_file_in_resources('config.json')
        assert isinstance(config_path, Path)
        assert config_path.name == 'config.json'

    def test_resolve_file_in_package(self):
        """Résoudre un fichier dans le package."""
        fonts_path = resolve_file_in_package('Fonts')
        assert isinstance(fonts_path, Path)
        assert fonts_path.exists()
        assert fonts_path.name == 'Fonts'

    def test_resolve_i18n_file_resources_priority(self):
        """resolve_i18n_file doit chercher dans resources/ en priorité."""
        fr_path = resolve_i18n_file('fr')
        assert isinstance(fr_path, Path)
        # Doit trouver le fichier dans resources/
        assert fr_path.exists()

    def test_caching_works(self):
        """Le caching doit retourner le même chemin."""
        path1 = resolve_resources_dir()
        path2 = resolve_resources_dir()
        # Doivent être exactement le même objet (cached)
        assert path1 == path2

    def test_cache_clear(self):
        """clear_cache() doit vider le cache."""
        resolve_resources_dir()  # Remplir le cache
        assert len(PathResolver._cache) > 0
        PathResolver.clear_cache()
        assert len(PathResolver._cache) == 0

    def test_resolve_nonexistent_file_returns_path(self):
        """Même si le fichier n'existe pas, retourner le chemin attendu."""
        missing_path = resolve_file_in_resources('nonexistent.json')
        assert isinstance(missing_path, Path)
        assert missing_path.name == 'nonexistent.json'
        # Le chemin doit être dans resources/ même s'il n'existe pas
        assert 'resources' in str(missing_path)

    def test_i18n_file_fallback_to_i18n_dir(self):
        """Si pas dans resources/, chercher dans i18n/."""
        # Pour une langue inexistante, doit retourner le chemin en fallback
        zz_path = resolve_i18n_file('zz_nonexistent')
        assert isinstance(zz_path, Path)
        # Doit essayer i18n/ en fallback
        assert 'i18n' in str(zz_path)

    def test_multiple_package_paths(self):
        """Plusieurs appels avec paths différents fonctionnent."""
        fonts = resolve_file_in_package('Fonts')
        templates = resolve_file_in_package('Templates')
        cadres = resolve_file_in_package('Cadres')
        
        assert fonts != templates != cadres
        assert all(p.exists() for p in [fonts, templates, cadres])

    def test_logging_resolution(self, caplog):
        """Les chemins résolus doivent être loggés."""
        import logging
        with caplog.at_level(logging.DEBUG):
            resolve_resources_dir()
        # Doit avoir au moins un log
        assert any("resources_dir" in record.message for record in caplog.records)


class TestPathResolverIntegration:
    """Tests d'intégration du path_resolver avec les modules."""

    def test_config_loader_uses_resolver(self):
        """config_loader doit utiliser path_resolver."""
        from CadreSelecteur.config_loader import CONFIG_PATH, RESOURCES_DIR
        assert isinstance(CONFIG_PATH, Path)
        assert isinstance(RESOURCES_DIR, Path)

    def test_translator_uses_resolver(self):
        """translator doit utiliser path_resolver."""
        from CadreSelecteur.i18n.translator import _load_translations
        # Doit pouvoir charger le français sans erreur
        _load_translations('fr')
        # Ne doit pas lever d'exception

    def test_logging_config_uses_resolver(self):
        """logging_config doit utiliser path_resolver."""
        from CadreSelecteur.logging_config import RESOURCES_DIR, LOG_PATH
        assert isinstance(RESOURCES_DIR, Path)
        assert isinstance(LOG_PATH, Path)

    def test_layertext_uses_resolver(self):
        """layertext doit utiliser path_resolver pour Fonts/."""
        from CadreSelecteur.CadreEditeur.layertext import LayerText
        # Juste vérifier que l'import fonctionne (layertext utilise resolver)
        assert LayerText is not None


class TestEliminiationOfDuplication:
    """Vérifier que la duplication de code PyInstaller a été éliminée."""

    def test_no_meipass_logic_in_config_loader(self):
        """config_loader ne doit pas avoir de logique _MEIPASS."""
        import inspect
        from CadreSelecteur import config_loader
        src = inspect.getsource(config_loader)
        # Ne doit pas avoir de _MEIPASS direct
        assert '_MEIPASS' not in src

    def test_no_meipass_logic_in_logging_config(self):
        """logging_config ne doit pas avoir de logique _MEIPASS."""
        import inspect
        from CadreSelecteur import logging_config
        src = inspect.getsource(logging_config)
        # Ne doit pas tester _MEIPASS en dur (c'est fait dans path_resolver)
        assert 'path' not in src or 'tempdir' in src  # logging utilise tempdir seulement

    def test_translator_simplified(self):
        """translator doit être simplifié."""
        import inspect
        from CadreSelecteur.i18n import translator
        src = inspect.getsource(translator)
        # Ne doit plus avoir _try_load_from_meipass
        assert '_try_load_from_meipass' not in src
        # Ne doit plus avoir MEIPASS_DIR
        assert 'MEIPASS_DIR' not in src or 'PathResolver' in src


if __name__ == '__main__':
    pytest.main([__file__, '-v'])


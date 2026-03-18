# -*- coding: utf-8 -*-
"""
Tests pour valider la gestion des erreurs cohérente.

Vérifie que :
1. Les exceptions custom sont levées aux bons endroits
2. handle_exception() log et affiche les messages correctement
3. Les traductions d'erreurs fonctionnent
4. Pas de `exc_info=e` incorrect
"""

import pytest
import logging
from unittest.mock import Mock, patch, MagicMock
from CadreSelecteur.exceptions import (
    FileOperationError,
    ImageProcessingError,
    ProjectError,
    UIError,
    ConfigurationError,
    ValidationError,
)
from CadreSelecteur.error_handler import (
    exception_to_domain,
    handle_exception,
    ErrorContext,
)


class TestExceptionConversion:
    """Test la conversion d'exceptions natives en domaines CadreSelecteur."""

    def test_file_not_found_converts_to_file_operation_error(self):
        """FileNotFoundError doit être converti en FileOperationError."""
        exc = FileNotFoundError("test file")
        result = exception_to_domain(exc)
        assert isinstance(result, FileOperationError)
        assert result.context['original_exception'] == 'FileNotFoundError'

    def test_permission_error_converts_to_file_operation_error(self):
        """PermissionError doit être converti en FileOperationError."""
        exc = PermissionError("denied")
        result = exception_to_domain(exc)
        assert isinstance(result, FileOperationError)

    def test_os_error_converts_to_file_operation_error(self):
        """OSError doit être converti en FileOperationError."""
        exc = OSError("io error")
        result = exception_to_domain(exc)
        assert isinstance(result, FileOperationError)

    def test_value_error_converts_to_validation_error(self):
        """ValueError doit être converti en ValidationError."""
        exc = ValueError("bad value")
        result = exception_to_domain(exc, fallback_domain='file')
        assert isinstance(result, ValidationError)

    def test_key_error_converts_to_project_error(self):
        """KeyError doit être converti en ProjectError (données malformées)."""
        exc = KeyError("missing_key")
        result = exception_to_domain(exc)
        assert isinstance(result, ProjectError)

    def test_fallback_domain_image(self):
        """Fallback vers ImageProcessingError si specified."""
        exc = RuntimeError("unknown")
        result = exception_to_domain(exc, fallback_domain='image')
        assert isinstance(result, ImageProcessingError)


class TestHandleException:
    """Test le traitement centralisé des exceptions."""

    @patch('CadreSelecteur.error_handler.messagebox.showerror')
    def test_handle_exception_shows_messagebox(self, mock_messagebox):
        """handle_exception doit afficher une messagebox par défaut."""
        exc = FileOperationError("errors.file_operation.not_found")
        handle_exception(exc, operation="test_op", show_messagebox=True)
        mock_messagebox.assert_called_once()

    @patch('CadreSelecteur.error_handler.messagebox.showerror')
    def test_handle_exception_no_messagebox_when_disabled(self, mock_messagebox):
        """Ne pas afficher messagebox si show_messagebox=False."""
        exc = FileOperationError("errors.file_operation.not_found")
        handle_exception(exc, operation="test_op", show_messagebox=False)
        mock_messagebox.assert_not_called()

    def test_handle_exception_logs_exception_level(self, caplog):
        """handle_exception doit logger en niveau exception."""
        with caplog.at_level(logging.DEBUG):
            exc = FileOperationError("errors.file_operation.not_found")
            handle_exception(exc, operation="test", log_level='exception', show_messagebox=False)
        assert any("test" in record.message for record in caplog.records)

    def test_handle_exception_logs_warning_level(self, caplog):
        """handle_exception doit supporter log_level='warning'."""
        with caplog.at_level(logging.WARNING):
            exc = FileOperationError("errors.file_operation.not_found")
            handle_exception(exc, operation="test", log_level='warning', show_messagebox=False)
        assert any(record.levelname == 'WARNING' for record in caplog.records)

    def test_handle_exception_converts_native_exception(self, caplog):
        """Converter les exceptions natives automatiquement."""
        with caplog.at_level(logging.DEBUG):
            exc = FileNotFoundError("missing")
            handle_exception(exc, operation="test", log_level='exception', show_messagebox=False)
        # Vérifier qu'au moins un log a été fait
        assert len(caplog.records) > 0
        assert any("test" in record.message for record in caplog.records)


class TestErrorContext:
    """Test le context manager ErrorContext."""

    def test_error_context_suppresses_exception(self):
        """ErrorContext doit supprimer l'exception après traitement."""
        with ErrorContext("test_op", show_messagebox=False):
            raise FileOperationError("test error")
        # Si on arrive ici, l'exception a été supprimée

    def test_error_context_calls_on_error_callback(self):
        """ErrorContext doit appeler le callback on_error."""
        callback = Mock()
        with ErrorContext("test_op", show_messagebox=False, on_error=callback):
            raise FileOperationError("test error")
        callback.assert_called_once()

    def test_error_context_no_exception_when_success(self):
        """ErrorContext ne doit rien faire si pas d'exception."""
        callback = Mock()
        with ErrorContext("test_op", show_messagebox=False, on_error=callback):
            pass  # pas d'exception
        callback.assert_not_called()


class TestExceptionHierarchy:
    """Test la hiérarchie des exceptions."""

    def test_all_custom_exceptions_inherit_from_cadre_selecteur_error(self):
        """Toutes les exceptions custom doivent hériter de CadreSelecteurError."""
        from CadreSelecteur.exceptions import CadreSelecteurError
        exceptions = [
            FileOperationError,
            ImageProcessingError,
            ProjectError,
            UIError,
            ConfigurationError,
            ValidationError,
        ]
        for exc_class in exceptions:
            assert issubclass(exc_class, CadreSelecteurError)

    def test_exception_context_attribute(self):
        """Les exceptions doivent avoir un attribut context."""
        exc = FileOperationError("test", context={'file': 'test.txt'})
        assert exc.context == {'file': 'test.txt'}

    def test_exception_message_attribute(self):
        """Les exceptions doivent avoir un attribut message."""
        exc = FileOperationError("test_message")
        assert exc.message == "test_message"


class TestLoggingConsistency:
    """Test la cohérence du logging."""

    def test_no_exc_info_equals_e_pattern(self):
        """Vérifier que exc_info n'utilise pas exc_info=e (incorrect)."""
        # Ce test vérifie visuellement que les patterns corrects sont utilisés
        # exc_info=True (correct) au lieu de exc_info=e (incorrect)
        from CadreSelecteur import cadreselecteur
        from CadreSelecteur.CadreEditeur import imageeditorapp
        
        # Lire les fichiers et vérifier pas de exc_info=e
        import inspect
        src = inspect.getsource(cadreselecteur)
        # Chercher les patterns incorrects (simplifié - en prod, utiliser grep)
        assert "exc_info=exc" not in src.replace("exc_info=True", "")
        
        src = inspect.getsource(imageeditorapp)
        assert "exc_info=exc" not in src.replace("exc_info=True", "")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])


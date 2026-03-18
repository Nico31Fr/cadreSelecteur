# -*- coding: utf-8 -*-
"""
Helper centralisé pour la gestion des erreurs.

Responsabilités :
- Convertir les exceptions natives (OSError, PIL) en exceptions CadreSelecteur
- Router vers logging approprié + messagebox
- Supporter i18n pour messages utilisateur
"""

import logging
import tkinter as tk
from tkinter import messagebox
from typing import Optional, Callable

from .exceptions import (
    CadreSelecteurError,
    FileOperationError,
    ImageProcessingError,
    ProjectError,
    ConfigurationError,
    ValidationError,
)
from .i18n.translator import _t

logger = logging.getLogger(__name__)


def exception_to_domain(exc: Exception, fallback_domain: str = 'file') -> CadreSelecteurError:
    """
    Convertit une exception native en exception CadreSelecteur spécifique.

    Args:
        exc: Exception native (OSError, ValueError, etc.)
        fallback_domain: domaine par défaut si ne peut pas déduire

    Returns:
        Instance de CadreSelecteurError ou sous-classe appropriée
    """
    context = {'original_exception': type(exc).__name__, 'message': str(exc)}

    if isinstance(exc, FileNotFoundError):
        return FileOperationError(f"errors.file_operation.not_found", context)
    elif isinstance(exc, PermissionError):
        return FileOperationError(f"errors.file_operation.permission_denied", context)
    elif isinstance(exc, IsADirectoryError):
        return FileOperationError(f"errors.file_operation.is_directory", context)
    elif isinstance(exc, OSError):
        return FileOperationError(f"errors.file_operation.io_error", context)
    elif isinstance(exc, ValueError):
        return ValidationError(f"errors.validation.invalid_value", context)
    elif isinstance(exc, (KeyError, AttributeError)):
        return ProjectError(f"errors.project.malformed_data", context)
    elif isinstance(exc, tk.TclError):
        return UIError(f"errors.ui.tkinter_error", context)
    else:
        # Fallback: créer exception du domaine demandé
        if fallback_domain == 'image':
            return ImageProcessingError(f"errors.image_processing.unknown", context)
        elif fallback_domain == 'project':
            return ProjectError(f"errors.project.unknown", context)
        elif fallback_domain == 'config':
            return ConfigurationError(f"errors.configuration.unknown", context)
        else:
            return FileOperationError(f"errors.file_operation.unknown", context)


def handle_exception(
    exc: Exception,
    operation: str = "operation",
    show_messagebox: bool = True,
    context: Optional[dict] = None,
    log_level: str = 'exception'
) -> None:
    """
    Gère une exception de manière centralisée :
    1. Logging approprié (debug/warning/exception)
    2. Affichage messagebox (si show_messagebox=True)
    3. Support i18n

    Args:
        exc: Exception à gérer
        operation: description de l'opération (pour le log)
        show_messagebox: afficher messagebox utilisateur ?
        context: contexte additionnel pour le log
        log_level: 'debug', 'warning', 'exception' (défaut)
    """
    # Enrichir le contexte
    full_context = context or {}
    full_context['operation'] = operation

    # Convertir en exception CadreSelecteur si nécessaire
    if not isinstance(exc, CadreSelecteurError):
        try:
            cadre_exc = exception_to_domain(exc)
            cadre_exc.context.update(full_context)
        except Exception:
            cadre_exc = CadreSelecteurError(str(exc), full_context)
    else:
        cadre_exc = exc
        cadre_exc.context.update(full_context)

    # Logging (exc_info=True pour exception(), False pour debug/warning)
    if log_level == 'exception':
        logger.exception(f"Error during {operation}: {cadre_exc.message}", exc_info=True)
    elif log_level == 'warning':
        logger.warning(f"Warning during {operation}: {cadre_exc.message}")
    else:  # 'debug'
        logger.debug(f"Debug during {operation}: {cadre_exc.message}")

    # Messagebox utilisateur (si applicable)
    if show_messagebox and isinstance(cadre_exc, CadreSelecteurError):
        try:
            # Tenter de traiter la clé i18n
            user_message = _t(cadre_exc.message)
            error_title = _t('errors.general.title', operation=operation)
        except Exception:
            # Fallback si traduction échoue
            user_message = f"{operation}: {str(exc)}"
            error_title = "Error"

        messagebox.showerror(error_title, user_message)


class ErrorContext:
    """Context manager pour capturer et gérer les erreurs."""

    def __init__(
        self,
        operation: str,
        show_messagebox: bool = True,
        on_error: Optional[Callable[[Exception], None]] = None
    ):
        """
        Args:
            operation: description de l'opération
            show_messagebox: afficher messagebox en cas d'erreur ?
            on_error: callback optionnel appelé en cas d'exception
        """
        self.operation = operation
        self.show_messagebox = show_messagebox
        self.on_error = on_error

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            handle_exception(
                exc_val,
                operation=self.operation,
                show_messagebox=self.show_messagebox
            )
            if self.on_error:
                self.on_error(exc_val)
            # Ne pas propager l'exception (on l'a gérée)
            return True
        return False


__all__ = [
    'exception_to_domain',
    'handle_exception',
    'ErrorContext',
]



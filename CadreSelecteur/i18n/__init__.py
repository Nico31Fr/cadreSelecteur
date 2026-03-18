# -*- coding: utf-8 -*-
"""Package i18n wrapper
Expose a small public API that proxies to translator._t but avoids importing
protected names elsewhere in the codebase.

Public API:
- t(key, **kwargs): translate key
- set_language(lang)
- get_language()
"""
from .translator import _t as _translator_t
from .translator import set_language as set_language
from .translator import get_language as get_language


def t(key: str, **kwargs) -> str:
    """Public translation function.

    Wraps translator._t to avoid referencing a protected member outside the
    package.
    """
    return _translator_t(key, **kwargs)


__all__ = ["t", "set_language", "get_language"]

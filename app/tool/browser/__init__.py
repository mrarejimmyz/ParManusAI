"""
Browser Module Init

Modular browser tool components.
"""

from .actions import (
    BrowserActionHandler,
    ExtractionHandler,
    InteractionHandler,
    NavigationHandler,
    ScrollHandler,
    TabHandler,
)
from .router import BrowserActionRouter
from .state import BrowserStateManager

__all__ = [
    "BrowserActionHandler",
    "BrowserActionRouter",
    "BrowserStateManager",
    "NavigationHandler",
    "InteractionHandler",
    "ScrollHandler",
    "TabHandler",
    "ExtractionHandler",
]

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
from .modern_tool import ModernBrowserTool
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
    "ModernBrowserTool",
]

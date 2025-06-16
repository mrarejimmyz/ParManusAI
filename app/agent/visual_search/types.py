"""
Visual Search Types and Data Models
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional


class SearchStrategy(Enum):
    """Available search strategies"""

    DIRECT_URL = "direct_url"
    WEB_SEARCH = "web_search"
    MANUAL_INTERACTION = "manual_interaction"
    LLM_GUIDED = "llm_guided"


class NavigationStatus(Enum):
    """Navigation status indicators"""

    SUCCESS = "success"
    FAILED = "failed"
    RETRY_NEEDED = "retry_needed"
    CAPTCHA_DETECTED = "captcha_detected"


@dataclass
class SearchResult:
    """Structured search result"""

    title: str
    url: str
    snippet: str
    rank: Optional[int] = None
    confidence: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class NavigationResult:
    """Result of navigation attempt"""

    success: bool
    status: NavigationStatus
    error: Optional[str] = None
    page_content: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class SearchContext:
    """Context for search operations"""

    query: str
    max_results: int = 10
    preferred_strategy: Optional[SearchStrategy] = None
    retry_attempts: int = 3
    timeout: float = 30.0
    filters: Optional[Dict[str, Any]] = None


@dataclass
class ExtractionConfig:
    """Configuration for content extraction"""

    target_elements: List[str]
    extraction_method: str = "llm_guided"
    structured_output: bool = True
    include_metadata: bool = False
    max_content_length: int = 5000


@dataclass
class CryptoData:
    """Cryptocurrency data structure"""

    name: str
    symbol: str
    price: Optional[str] = None
    rank: Optional[str] = None
    market_cap: Optional[str] = None
    change_24h: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

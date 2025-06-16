"""
Multi-Engine Search Implementation - NOW USING OPTIMIZED BULLETPROOF SEARCH
Uses verified APIs that actually work: DuckDuckGo API and real news sources
"""

# Import the optimized bulletproof implementation
from app.tool.optimized_bulletproof_search import OptimizedBulletproofSearch


# Redirect to optimized bulletproof search for backward compatibility
class MultiEngineSearch(OptimizedBulletproofSearch):
    """Backward compatibility wrapper for optimized bulletproof search"""

    pass


# Alias for backward compatibility
NodriverGoogleSearch = MultiEngineSearch

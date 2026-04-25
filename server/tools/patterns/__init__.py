"""
Patterns module for air-mold design prompt enhancement.
移植自 PneumatCraft + GenPilot 机制
"""

from .database import PatternDatabase, get_pattern_database, load_pattern_database
from .matcher import PatternMatcher, MatchedPattern
from .enhancer import PromptEnhancer, EnhancementResult

__all__ = [
    "PatternDatabase",
    "get_pattern_database",
    "load_pattern_database",
    "PatternMatcher",
    "MatchedPattern",
    "PromptEnhancer",
    "EnhancementResult",
]
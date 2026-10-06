"""Analytics package for SmartStudy AI."""
from .progress import (
    calculate_study_streak,
    get_progress_overview,
    get_subject_wise_analytics,
    analyze_weak_and_strong_topics,
)

__all__ = [
    "calculate_study_streak",
    "get_progress_overview",
    "get_subject_wise_analytics",
    "analyze_weak_and_strong_topics",
]

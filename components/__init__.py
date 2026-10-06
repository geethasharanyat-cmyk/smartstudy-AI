"""Components package for SmartStudy AI."""
from .ui import apply_theme, render_header, render_kpi, get_difficulty_badge, get_priority_badge, get_status_badge
from .charts import render_progress_donut, render_subject_progress_bar, render_difficulty_priority_breakdown, render_study_time_comparison
from .dashboard import render_dashboard_view, seed_sample_student_data

__all__ = [
    "apply_theme",
    "render_header",
    "render_kpi",
    "get_difficulty_badge",
    "get_priority_badge",
    "get_status_badge",
    "render_progress_donut",
    "render_subject_progress_bar",
    "render_difficulty_priority_breakdown",
    "render_study_time_comparison",
    "render_dashboard_view",
    "seed_sample_student_data",
]

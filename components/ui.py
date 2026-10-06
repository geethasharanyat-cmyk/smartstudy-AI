"""
Modern UI styling, theme management (Light/Dark mode), custom CSS,
and reusable UI components for SmartStudy AI.
"""

import streamlit as st
from typing import Optional


LIGHT_THEME_CSS = """
<style>
:root {
    --bg-main: #f8fafc;
    --card-bg: #ffffff;
    --card-border: #e2e8f0;
    --text-primary: #0f172a;
    --text-secondary: #475569;
    --accent: #4f46e5;
    --accent-light: #e0e7ff;
    --success: #10b981;
    --warning: #f59e0b;
    --danger: #ef4444;
}
.stApp {
    background-color: #f8fafc;
    color: #0f172a;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}
.card {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 20px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    margin-bottom: 16px;
}
.kpi-card {
    background: linear-gradient(135deg, #ffffff 0%, #f1f5f9 100%);
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 18px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.04);
}
.kpi-number {
    font-size: 2rem;
    font-weight: 700;
    color: #1e1b4b;
    line-height: 1.2;
}
.kpi-label {
    font-size: 0.85rem;
    font-weight: 600;
    color: #64748b;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-bottom: 4px;
}
.badge {
    display: inline-block;
    padding: 4px 10px;
    border-radius: 9999px;
    font-size: 0.75rem;
    font-weight: 600;
}
.badge-easy { background: #dcfce7; color: #166534; }
.badge-med { background: #fef3c7; color: #92400e; }
.badge-hard { background: #fee2e2; color: #991b1b; }
.badge-low { background: #e0f2fe; color: #075985; }
.badge-high { background: #fae8ff; color: #86198f; }
.session-card {
    background: #ffffff;
    border-left: 5px solid #4f46e5;
    border-radius: 8px;
    padding: 14px 18px;
    margin-bottom: 12px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06);
}
</style>
"""

DARK_THEME_CSS = """
<style>
:root {
    --bg-main: #0b0f19;
    --card-bg: #111827;
    --card-border: #1f2937;
    --text-primary: #f9fafb;
    --text-secondary: #9ca3af;
    --accent: #6366f1;
    --accent-light: #1e1b4b;
    --success: #34d399;
    --warning: #fbbf24;
    --danger: #f87171;
}
.stApp {
    background-color: #0b0f19;
    color: #f9fafb;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}
.card {
    background: #111827;
    border: 1px solid #1f2937;
    border-radius: 12px;
    padding: 20px;
    box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    margin-bottom: 16px;
}
.kpi-card {
    background: linear-gradient(135deg, #111827 0%, #1f2937 100%);
    border: 1px solid #374151;
    border-radius: 12px;
    padding: 18px;
    box-shadow: 0 4px 6px rgba(0,0,0,0.25);
}
.kpi-number {
    font-size: 2rem;
    font-weight: 700;
    color: #e0e7ff;
    line-height: 1.2;
}
.kpi-label {
    font-size: 0.85rem;
    font-weight: 600;
    color: #9ca3af;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-bottom: 4px;
}
.badge {
    display: inline-block;
    padding: 4px 10px;
    border-radius: 9999px;
    font-size: 0.75rem;
    font-weight: 600;
}
.badge-easy { background: #064e3b; color: #a7f3d0; }
.badge-med { background: #78350f; color: #fde68a; }
.badge-hard { background: #7f1d1d; color: #fecaca; }
.badge-low { background: #0c4a6e; color: #bae6fd; }
.badge-high { background: #581c87; color: #f5d0fe; }
.session-card {
    background: #111827;
    border-left: 5px solid #6366f1;
    border: 1px solid #1f2937;
    border-left-width: 5px;
    border-radius: 8px;
    padding: 14px 18px;
    margin-bottom: 12px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.3);
}
</style>
"""


def apply_theme():
    """Applies either Light Mode or Dark Mode CSS according to session state."""
    current_theme = st.session_state.get("theme", "dark")
    if current_theme == "dark":
        st.markdown(DARK_THEME_CSS, unsafe_allow_html=True)
    else:
        st.markdown(LIGHT_THEME_CSS, unsafe_allow_html=True)


def render_header(title: str, subtitle: Optional[str] = None, badge_text: Optional[str] = None):
    """Renders a clean modern page header with optional subtitle and tag badge."""
    badge_html = f'<span style="background: rgba(99, 102, 241, 0.15); color: #818cf8; padding: 4px 12px; border-radius: 20px; font-size: 0.8rem; font-weight: 600; margin-left: 10px; border: 1px solid rgba(99, 102, 241, 0.3);">{badge_text}</span>' if badge_text else ""
    st.markdown(
        f"""
        <div style="margin-bottom: 24px;">
            <h1 style="margin: 0; font-size: 2.1rem; font-weight: 800; display: inline-flex; align-items: center; letter-spacing: -0.02em;">
                {title} {badge_html}
            </h1>
            {f'<p style="margin: 6px 0 0 0; color: #64748b; font-size: 1.05rem;">{subtitle}</p>' if subtitle else ''}
        </div>
        """,
        unsafe_allow_html=True
    )


def render_kpi(label: str, value: str, icon: str = "📊", hint: str = ""):
    """Renders an attractive KPI metric tile."""
    st.markdown(
        f"""
        <div class="kpi-card">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div class="kpi-label">{label}</div>
                <span style="font-size: 1.3rem;">{icon}</span>
            </div>
            <div class="kpi-number">{value}</div>
            {f'<div style="font-size: 0.8rem; color: #64748b; margin-top: 4px;">{hint}</div>' if hint else ''}
        </div>
        """,
        unsafe_allow_html=True
    )


def get_difficulty_badge(difficulty: str) -> str:
    """Returns styled HTML badge for difficulty."""
    d = (difficulty or "Medium").lower()
    if d == "easy":
        return '<span class="badge badge-easy">🟢 Easy</span>'
    elif d == "hard":
        return '<span class="badge badge-hard">🔴 Hard</span>'
    else:
        return '<span class="badge badge-med">🟡 Medium</span>'


def get_priority_badge(priority: str) -> str:
    """Returns styled HTML badge for priority."""
    p = (priority or "Medium").lower()
    if p == "high":
        return '<span class="badge badge-high">🔥 High</span>'
    elif p == "low":
        return '<span class="badge badge-low">💤 Low</span>'
    else:
        return '<span class="badge badge-med">⚡ Medium</span>'


def get_status_badge(status: str) -> str:
    """Returns styled HTML badge for completion status."""
    s = (status or "Not Started")
    if s == "Completed":
        return '<span style="background: #10b981; color: white; padding: 3px 8px; border-radius: 6px; font-size: 0.75rem; font-weight: 600;">✓ Completed</span>'
    elif s == "In Progress":
        return '<span style="background: #3b82f6; color: white; padding: 3px 8px; border-radius: 6px; font-size: 0.75rem; font-weight: 600;">⏳ In Progress</span>'
    elif s == "Missed":
        return '<span style="background: #ef4444; color: white; padding: 3px 8px; border-radius: 6px; font-size: 0.75rem; font-weight: 600;">⚠️ Missed</span>'
    else:
        return '<span style="background: #64748b; color: white; padding: 3px 8px; border-radius: 6px; font-size: 0.75rem; font-weight: 600;">⚪ Not Started</span>'

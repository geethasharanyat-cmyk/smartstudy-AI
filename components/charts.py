"""
Chart and visualization components using Matplotlib and Seaborn.
Renders responsive, theme-aware visualizations for study analytics.
"""

from typing import List, Dict, Any
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st


def set_plot_theme(is_dark: bool = True):
    """Configures matplotlib style parameters according to the active theme."""
    if is_dark:
        plt.style.use("dark_background")
        text_color = "#f3f4f6"
        grid_color = "#374151"
        face_color = "#111827"
    else:
        plt.style.use("default")
        text_color = "#1e293b"
        grid_color = "#e2e8f0"
        face_color = "#ffffff"

    plt.rcParams["text.color"] = text_color
    plt.rcParams["axes.labelcolor"] = text_color
    plt.rcParams["xtick.color"] = text_color
    plt.rcParams["ytick.color"] = text_color
    plt.rcParams["figure.facecolor"] = face_color
    plt.rcParams["axes.facecolor"] = face_color
    plt.rcParams["grid.color"] = grid_color


def render_progress_donut(completion_pct: float, is_dark: bool = True):
    """Renders an attractive donut chart showing overall completion rate."""
    set_plot_theme(is_dark)
    fig, ax = plt.subplots(figsize=(4, 4))

    completed = max(0.0, min(100.0, completion_pct))
    remaining = 100.0 - completed

    colors = ["#4f46e5", "#1f2937" if is_dark else "#e2e8f0"]
    if completed == 100:
        colors = ["#10b981", "#1f2937" if is_dark else "#e2e8f0"]

    wedges, _ = ax.pie(
        [completed, remaining],
        colors=colors,
        startangle=90,
        wedgeprops=dict(width=0.28, edgecolor="none")
    )

    # Center label
    center_color = "#ffffff" if is_dark else "#0f172a"
    ax.text(
        0, 0, f"{completed:.0f}%",
        ha="center", va="center",
        fontsize=22, fontweight="bold",
        color=center_color
    )
    ax.set_title("Overall Progress", fontsize=12, pad=10, fontweight="600")
    plt.tight_layout()
    return fig


def render_subject_progress_bar(subjects_data: List[Dict[str, Any]], is_dark: bool = True):
    """Renders a horizontal bar chart showing completion % per subject."""
    if not subjects_data:
        return None

    set_plot_theme(is_dark)
    names = [s["subject_name"] for s in subjects_data]
    pcts = [s["completion_percentage"] for s in subjects_data]
    colors = [s.get("color", "#6366f1") for s in subjects_data]

    fig, ax = plt.subplots(figsize=(6, max(2.5, len(names) * 0.75)))
    y_pos = range(len(names))

    bars = ax.barh(y_pos, pcts, color=colors, height=0.55, edgecolor="none", alpha=0.85)

    ax.set_yticks(y_pos)
    ax.set_yticklabels(names, fontsize=10, fontweight="500")
    ax.set_xlim(0, 105)
    ax.set_xlabel("Completion (%)", fontsize=10)
    ax.grid(axis="x", linestyle="--", alpha=0.3)

    # Add data labels
    for bar in bars:
        width = bar.get_width()
        ax.text(
            width + 2, bar.get_y() + bar.get_height() / 2,
            f"{width:.0f}%",
            ha="left", va="center", fontsize=9, fontweight="bold"
        )

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    plt.tight_layout()
    return fig


def render_difficulty_priority_breakdown(
    topics: List[Dict[str, Any]],
    is_dark: bool = True
):
    """Renders a two-panel bar plot comparing Difficulty and Priority distributions."""
    if not topics:
        return None

    set_plot_theme(is_dark)
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(8, 3.2))

    # Difficulty counts
    diff_counts = {"Easy": 0, "Medium": 0, "Hard": 0}
    prio_counts = {"Low": 0, "Medium": 0, "High": 0}

    for t in topics:
        d = t.get("difficulty", "Medium")
        p = t.get("priority", "Medium")
        if d in diff_counts:
            diff_counts[d] += 1
        if p in prio_counts:
            prio_counts[p] += 1

    diff_colors = ["#10b981", "#f59e0b", "#ef4444"]
    prio_colors = ["#0284c7", "#f59e0b", "#9333ea"]

    ax1.bar(list(diff_counts.keys()), list(diff_counts.values()), color=diff_colors, width=0.5)
    ax1.set_title("Topics by Difficulty", fontsize=11, fontweight="600")
    ax1.spines["top"].set_visible(False)
    ax1.spines["right"].set_visible(False)
    ax1.grid(axis="y", linestyle="--", alpha=0.3)

    ax2.bar(list(prio_counts.keys()), list(prio_counts.values()), color=prio_colors, width=0.5)
    ax2.set_title("Topics by Priority", fontsize=11, fontweight="600")
    ax2.spines["top"].set_visible(False)
    ax2.spines["right"].set_visible(False)
    ax2.grid(axis="y", linestyle="--", alpha=0.3)

    plt.tight_layout()
    return fig


def render_study_time_comparison(planned_hours: float, actual_hours: float, is_dark: bool = True):
    """Renders a comparison bar chart of planned vs actual study hours."""
    set_plot_theme(is_dark)
    fig, ax = plt.subplots(figsize=(5, 3))

    categories = ["Planned Time", "Actual Completed"]
    values = [planned_hours, actual_hours]
    colors = ["#6366f1", "#10b981"]

    bars = ax.bar(categories, values, color=colors, width=0.45)
    ax.set_ylabel("Hours", fontsize=10)
    ax.set_title("Study Time Investment", fontsize=11, fontweight="600")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(axis="y", linestyle="--", alpha=0.3)

    for bar in bars:
        height = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width() / 2, height + 0.1,
            f"{height:.1f}h",
            ha="center", va="bottom", fontsize=10, fontweight="bold"
        )

    plt.tight_layout()
    return fig

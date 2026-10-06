"""
Dashboard UI view for SmartStudy AI.
Displays KPI metric cards, today's time-slot schedule with one-click completion,
rescheduling notifications, and first-time user empty state.
"""

from datetime import date, datetime
from typing import Dict, Any, List
import streamlit as st
from components.ui import render_header, render_kpi, get_difficulty_badge, get_priority_badge
from components.charts import render_progress_donut, render_subject_progress_bar
from analytics.progress import get_progress_overview, get_subject_wise_analytics, analyze_weak_and_strong_topics
from planner.scheduler import (
    get_user_schedule_for_date,
    detect_and_reschedule_missed_sessions,
    complete_study_session
)
from database.models import Subject, Topic, StudySession
from database.db import get_db


def seed_sample_student_data(user_id: int):
    """
    Populates sample subjects, topics, and an initial schedule for demo and testing purposes.
    Allows quick evaluation without manual data entry.
    """
    with get_db() as db:
        # Check if already seeded
        if db.query(Subject).filter(Subject.user_id == user_id).first():
            return False

        # Add Subjects
        cs = Subject(user_id=user_id, name="Computer Science", code="CS101", color="#4F46E5", description="Core CS and Programming")
        db_sub = Subject(user_id=user_id, name="Database Systems", code="DBMS201", color="#06B6D4", description="Relational & NoSQL Databases")
        math = Subject(user_id=user_id, name="Discrete Mathematics", code="MATH150", color="#EC4899", description="Logic, Sets, and Probability")

        db.add_all([cs, db_sub, math])
        db.flush()

        # Add Topics
        t1 = Topic(
            subject_id=cs.id,
            name="Object Oriented Programming",
            difficulty="Hard",
            priority="High",
            knowledge_level="Beginner",
            status="In Progress",
            estimated_duration_hours=2.0,
            exam_date=date.today() + date.resolution * 5
        )
        t2 = Topic(
            subject_id=cs.id,
            name="Variables & Data Types",
            difficulty="Easy",
            priority="Medium",
            knowledge_level="Advanced",
            status="Completed",
            estimated_duration_hours=1.0,
            completed_at=datetime.now()
        )
        t3 = Topic(
            subject_id=db_sub.id,
            name="Normalization (1NF, 2NF, 3NF, BCNF)",
            difficulty="Hard",
            priority="High",
            knowledge_level="Intermediate",
            status="Not Started",
            estimated_duration_hours=2.5,
            exam_date=date.today() + date.resolution * 8
        )
        t4 = Topic(
            subject_id=db_sub.id,
            name="ER Modeling & Relational Schema",
            difficulty="Medium",
            priority="Medium",
            knowledge_level="Advanced",
            status="Completed",
            estimated_duration_hours=1.5,
            completed_at=datetime.now()
        )
        t5 = Topic(
            subject_id=math.id,
            name="Probability & Bayes Theorem",
            difficulty="Medium",
            priority="High",
            knowledge_level="Intermediate",
            status="In Progress",
            estimated_duration_hours=2.0,
            exam_date=date.today() + date.resolution * 12
        )

        db.add_all([t1, t2, t3, t4, t5])

    return True


def render_dashboard_view(user: Dict[str, Any], navigate_to):
    """Renders the comprehensive, modern dashboard page."""
    user_id = user["id"]
    today = date.today()
    is_dark = st.session_state.get("theme", "dark") == "dark"

    # Auto-detect and reschedule missed sessions on dashboard load
    rescheduled_count, notifications = detect_and_reschedule_missed_sessions(user_id)
    if notifications:
        for note in notifications:
            st.warning(note, icon="⚠️")

    overview = get_progress_overview(user_id)
    total_topics = overview["total_topics"]

    # Welcome Header
    greeting = "Good afternoon" if datetime.now().hour >= 12 and datetime.now().hour < 17 else ("Good evening" if datetime.now().hour >= 17 else "Good morning")
    student_name = user.get("full_name") or user.get("username")
    render_header(f"👋 {greeting}, {student_name}!", "Here is your personalized academic control center.")

    # First-time empty state check
    if total_topics == 0:
        st.markdown(
            """
            <div class="card" style="text-align: center; padding: 40px 20px;">
                <div style="font-size: 3rem; margin-bottom: 12px;">📚</div>
                <h2 style="margin: 0; font-weight: 700;">Welcome to SmartStudy AI 👋</h2>
                <p style="color: #64748b; font-size: 1.1rem; max-width: 550px; margin: 10px auto 25px auto;">
                    Let's create your first intelligent study plan. Add your enrolled subjects and topics, or load our quick demo dataset to explore right away!
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            if st.button("➕ Add Subject", use_container_width=True, type="primary"):
                navigate_to("Subjects & Topics")
        with col2:
            if st.button("📅 Create Study Plan", use_container_width=True):
                navigate_to("Study Planner")
        with col3:
            if st.button("📄 Upload Material", use_container_width=True):
                navigate_to("Study Materials")
        with col4:
            if st.button("🚀 Load Sample Study Data", use_container_width=True):
                if seed_sample_student_data(user_id):
                    st.success("Sample curriculum loaded! Refreshing dashboard...")
                    st.rerun()
        return

    # Top KPI Cards
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        render_kpi("Overall Progress", f"{overview['completion_percentage']}%", "📈", f"{overview['completed_topics']}/{total_topics} topics done")
    with col2:
        render_kpi("Today's Study", f"{overview['today_study_hours']} hrs", "⏱️", f"Planned: {overview['planned_hours']} hrs total")
    with col3:
        streak_icon = "🔥" if overview['study_streak'] > 0 else "❄️"
        render_kpi("Study Streak", f"{overview['study_streak']} Days", streak_icon, "Keep consistent daily!")
    with col4:
        exam_info = overview["upcoming_exam"]
        if exam_info:
            render_kpi("Upcoming Exam", f"{exam_info['days_left']} Days", "🎯", f"{exam_info['subject_name']}: {exam_info['date']}")
        else:
            render_kpi("Upcoming Exam", "None set", "🎯", "Set exam dates in Topics")

    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

    # Today's Study Schedule Section
    today_sessions = get_user_schedule_for_date(user_id, today)

    st.markdown(f"### 📅 Today's Time-Slot Schedule ({today.strftime('%A, %b %d')})")

    if not today_sessions:
        st.info("No study sessions scheduled for today. Head to the **Study Planner** to generate a balanced schedule!")
        if st.button("Go to Study Planner ➡️", type="primary"):
            navigate_to("Study Planner")
    else:
        for s in today_sessions:
            status_style = "border-left: 5px solid #10b981;" if s["status"] == "Completed" else ("border-left: 5px solid #ef4444;" if s["status"] == "Missed" else "border-left: 5px solid #6366f1;")
            with st.container():
                st.markdown(
                    f"""
                    <div class="session-card" style="{status_style}">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                            <strong style="font-size: 1.05rem; color: #6366f1;">⏰ {s['start_time']} – {s['end_time']} ({s['duration']} mins)</strong>
                            <span style="font-weight: 600; font-size: 0.85rem; color: {s['subject_color']};">{s['subject_name']}</span>
                        </div>
                        <div style="font-size: 1.15rem; font-weight: 700; margin-bottom: 4px;">{s['topic_name']}</div>
                        <div style="display: flex; gap: 8px; align-items: center; margin-top: 6px;">
                            {get_difficulty_badge(s['difficulty'])}
                            {get_priority_badge(s['priority'])}
                            <span style="font-size: 0.8rem; color: #64748b;">Status: <b>{s['status']}</b></span>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                if s["status"] == "Planned":
                    btn_col1, btn_col2 = st.columns([1, 4])
                    with btn_col1:
                        if st.button(f"Mark Complete ✓", key=f"dash_done_{s['id']}"):
                            success, msg = complete_study_session(s["id"])
                            if success:
                                st.toast(msg, icon="🎉")
                                st.rerun()

    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)

    # Visual Analytics & Weak Topics Row
    row_col1, row_col2 = st.columns([1, 1])

    with row_col1:
        st.markdown("### 📊 Subject Progress Breakdown")
        subjects_data = get_subject_wise_analytics(user_id)
        if subjects_data:
            bar_fig = render_subject_progress_bar(subjects_data, is_dark=is_dark)
            if bar_fig:
                st.pyplot(bar_fig)
        else:
            st.info("No subjects added yet.")

    with row_col2:
        st.markdown("### ⚠️ Topics Needing Revision")
        analysis = analyze_weak_and_strong_topics(user_id)
        weak_topics = analysis.get("weak_topics", [])

        if not weak_topics:
            st.success("🎉 Excellent! No weak topics detected at this time. All topics are on track!")
        else:
            for wt in weak_topics[:3]:
                st.markdown(
                    f"""
                    <div class="card" style="padding: 12px 16px; margin-bottom: 8px; border-left: 4px solid #f59e0b;">
                        <div style="font-weight: 700; font-size: 1rem;">⚠️ {wt['topic_name']} <span style="font-weight: normal; color: #64748b; font-size: 0.85rem;">({wt['subject_name']})</span></div>
                        <div style="color: #ef4444; font-size: 0.85rem; margin-top: 3px;"><b>Reason:</b> {wt['reason']}</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            if len(weak_topics) > 3:
                st.caption(f"+ {len(weak_topics) - 3} more topics need attention. See full report on Progress page.")

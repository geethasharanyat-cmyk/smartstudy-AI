"""
SmartStudy AI - Your Intelligent Personal Study Planner
A complete, production-quality AI-powered study companion.
Built with Streamlit, SQLAlchemy, Google Gemini, and Scikit-learn.
"""

import os
import sys
from datetime import date, datetime, timedelta, time
import streamlit as st
import pandas as pd
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Add workspace directory to path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# Database & Authentication
from database.db import init_db, get_db
from database.models import User, Subject, Topic, StudySession, ProgressLog, UploadedMaterial, ChatMessage
from auth.authentication import (
    register_user,
    authenticate_user,
    get_user_profile,
    update_user_profile,
    update_user_password,
)

# Planner & Analytics
from planner.scheduler import (
    generate_balanced_study_plan,
    detect_and_reschedule_missed_sessions,
    complete_study_session,
    get_user_schedule_for_date,
    PRESET_SLOT_TIMES,
)
from analytics.progress import (
    get_progress_overview,
    get_subject_wise_analytics,
    analyze_weak_and_strong_topics,
)

# AI & Document Processing
from ai.chatbot import (
    ask_study_assistant,
    get_chat_history,
    clear_chat_history,
    get_configured_api_key,
    get_student_context,
)
from ai.document_qa import (
    ask_document_question,
    summarize_document,
    generate_exam_questions_from_doc,
)
from ai.planner_ai import get_ai_study_recommendations
from documents.processor import process_uploaded_document

# UI Components & Visualizations
from components.ui import (
    apply_theme,
    render_header,
    render_kpi,
    get_difficulty_badge,
    get_priority_badge,
    get_status_badge,
)
from components.charts import (
    render_progress_donut,
    render_subject_progress_bar,
    render_difficulty_priority_breakdown,
    render_study_time_comparison,
)
from components.dashboard import render_dashboard_view, seed_sample_student_data

# Page configuration
st.set_page_config(
    page_title="SmartStudy AI - Intelligent Study Planner",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize database schema
init_db()

# Session State Initialization
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
if "user" not in st.session_state:
    st.session_state["user"] = None
if "current_page" not in st.session_state:
    st.session_state["current_page"] = "Dashboard"
if "theme" not in st.session_state:
    st.session_state["theme"] = "dark"
if "custom_api_key" not in st.session_state:
    st.session_state["custom_api_key"] = ""
if "ai_mode" not in st.session_state:
    st.session_state["ai_mode"] = "Simple"

# Apply theme CSS
apply_theme()


def navigate_to(page_name: str):
    """Callback to switch current page."""
    st.session_state["current_page"] = page_name
    st.rerun()


# ==============================================================================
# AUTHENTICATION SCREEN (LOGIN / REGISTER)
# ==============================================================================
def render_auth_view():
    """Renders the login and registration portal."""
    col_center, _ = st.columns([1, 1])

    with col_center:
        st.markdown(
            """
            <div style="text-align: left; margin-bottom: 24px;">
                <div style="font-size: 2.5rem; margin-bottom: 6px;">🎓 <span style="font-weight: 800; color: #6366f1;">SmartStudy AI</span></div>
                <p style="color: #64748b; font-size: 1.1rem; margin: 0;">
                    Your Intelligent Personal Study Planner & AI Learning Assistant
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )

        tab_login, tab_register, tab_demo = st.tabs(["🔐 Sign In", "📝 Create Account", "🚀 Quick Demo"])

        # LOGIN TAB
        with tab_login:
            st.markdown("### Welcome Back")
            login_id = st.text_input("Username or Email", key="login_id", placeholder="student@example.com")
            login_pass = st.text_input("Password", type="password", key="login_pass", placeholder="••••••••")

            if st.button("Sign In to SmartStudy", type="primary", use_container_width=True):
                success, msg, user_data = authenticate_user(login_id, login_pass)
                if success and user_data:
                    st.session_state["authenticated"] = True
                    st.session_state["user"] = user_data
                    st.session_state["current_page"] = "Dashboard"
                    st.toast(msg, icon="🎉")
                    st.rerun()
                else:
                    st.error(msg)

        # REGISTER TAB
        with tab_register:
            st.markdown("### Create Student Account")
            reg_user = st.text_input("Username", key="reg_user", placeholder="alex_dev")
            reg_email = st.text_input("Email Address", key="reg_email", placeholder="alex@university.edu")
            reg_pass = st.text_input("Password (min 6 chars)", type="password", key="reg_pass")
            reg_name = st.text_input("Full Name", key="reg_name", placeholder="Alex Chen")

            col_sub1, col_sub2 = st.columns(2)
            with col_sub1:
                reg_course = st.text_input("Course / Major", key="reg_course", placeholder="Computer Science")
            with col_sub2:
                reg_year = st.selectbox("Year of Study", ["1st Year", "2nd Year", "3rd Year", "4th Year", "Postgraduate", "High School"], key="reg_year")

            if st.button("Register Account", type="primary", use_container_width=True):
                success, msg, new_user = register_user(
                    username=reg_user,
                    email=reg_email,
                    password=reg_pass,
                    full_name=reg_name,
                    course=reg_course,
                    year_of_study=reg_year
                )
                if success and new_user:
                    st.session_state["authenticated"] = True
                    st.session_state["user"] = new_user
                    st.session_state["current_page"] = "Dashboard"
                    # Seed demo data for instant delight
                    seed_sample_student_data(new_user["id"])
                    st.success("Account created successfully with introductory curriculum!")
                    st.rerun()
                else:
                    st.error(msg)

        # DEMO TAB
        with tab_demo:
            st.markdown("### Instant Demo Access")
            st.info("Explore SmartStudy AI instantly with a pre-configured sample account.")
            if st.button("Launch Demo Student Experience 🚀", type="primary", use_container_width=True):
                # Ensure demo user exists
                with get_db() as db:
                    demo = db.query(User).filter(User.username == "demo_student").first()
                    if not demo:
                        register_user(
                            username="demo_student",
                            email="demo@smartstudy.ai",
                            password="password123",
                            full_name="Sarah Miller",
                            course="Computer Science",
                            year_of_study="3rd Year"
                        )
                _, _, demo_user = authenticate_user("demo_student", "password123")
                if demo_user:
                    st.session_state["authenticated"] = True
                    st.session_state["user"] = demo_user
                    st.session_state["current_page"] = "Dashboard"
                    seed_sample_student_data(demo_user["id"])
                    st.rerun()


# ==============================================================================
# SUBJECTS & TOPICS VIEW
# ==============================================================================
def render_subjects_topics_view(user_id: int):
    """Subjects and Topics Management view."""
    render_header("📚 Subjects & Topics", "Manage your curriculum, topic difficulties, priorities, and exam dates.")

    tab_topics, tab_subjects = st.tabs(["📑 Topics Management", "🏷️ Enrolled Subjects"])

    # --- TOPICS MANAGEMENT ---
    with tab_topics:
        with get_db() as db:
            subjects = db.query(Subject).filter(Subject.user_id == user_id).all()

        if not subjects:
            st.warning("You haven't added any subjects yet. Please switch to the **Enrolled Subjects** tab to add your first subject.")
            return

        subject_dict = {s.name: s.id for s in subjects}

        with st.expander("➕ Add New Topic", expanded=False):
            with st.form("add_topic_form", clear_on_submit=True):
                t_col1, t_col2 = st.columns(2)
                with t_col1:
                    topic_subject = st.selectbox("Subject", options=list(subject_dict.keys()))
                    topic_name = st.text_input("Topic Name", placeholder="e.g. Dynamic Programming")
                    topic_difficulty = st.selectbox("Difficulty", ["Easy", "Medium", "Hard"], index=1)
                    topic_duration = st.number_input("Estimated Study Duration (Hours)", min_value=0.5, max_value=20.0, value=1.5, step=0.5)

                with t_col2:
                    topic_priority = st.selectbox("Priority", ["Low", "Medium", "High"], index=1)
                    topic_knowledge = st.selectbox("Knowledge Level", ["Beginner", "Intermediate", "Advanced"], index=0)
                    topic_status = st.selectbox("Status", ["Not Started", "In Progress", "Completed"], index=0)
                    topic_exam_date = st.date_input("Optional Exam / Deadline Date", value=None)

                topic_notes = st.text_area("Notes / Key Sub-topics", placeholder="Optional reminders, textbook chapters, or exam focus points...")
                submit_topic = st.form_submit_button("Add Topic", type="primary")

                if submit_topic:
                    if not topic_name.strip():
                        st.error("Topic name cannot be empty.")
                    else:
                        with get_db() as db:
                            new_t = Topic(
                                subject_id=subject_dict[topic_subject],
                                name=topic_name.strip(),
                                difficulty=topic_difficulty,
                                priority=topic_priority,
                                knowledge_level=topic_knowledge,
                                status=topic_status,
                                estimated_duration_hours=float(topic_duration),
                                exam_date=topic_exam_date,
                                notes=topic_notes.strip(),
                                completed_at=datetime.now() if topic_status == "Completed" else None
                            )
                            db.add(new_t)
                        st.success(f"Topic '{topic_name}' added successfully!")
                        st.rerun()

        # --- BULK UPLOAD ---
        with st.expander("📂 Bulk Upload from CSV / Excel", expanded=False):
            st.markdown(
                """
                Upload a **CSV** or **Excel (.xlsx)** file with the following columns:

                | Column | Required | Values |
                |--------|----------|--------|
                | `subject_name` | ✅ | Any text |
                | `topic_name` | ✅ | Any text |
                | `difficulty` | optional | Easy / Medium / Hard |
                | `priority` | optional | Low / Medium / High |
                | `knowledge_level` | optional | Beginner / Intermediate / Advanced |
                | `status` | optional | Not Started / In Progress / Completed |
                | `estimated_duration_hours` | optional | Number (e.g. 1.5) |
                """
            )

            upload_col, download_col = st.columns([3, 1])
            with download_col:
                sample_csv = (
                    "subject_name,topic_name,difficulty,priority,knowledge_level,status,estimated_duration_hours\n"
                    "Python,Decorators,Medium,High,Intermediate,Not Started,1.5\n"
                    "Machine Learning,Neural Networks,Hard,High,Advanced,Not Started,3.0\n"
                )
                st.download_button(
                    "⬇️ Download Sample CSV",
                    data=sample_csv,
                    file_name="sample_topics.csv",
                    mime="text/csv"
                )

            with upload_col:
                uploaded_file = st.file_uploader(
                    "Choose file",
                    type=["csv", "xlsx"],
                    key="bulk_topics_upload",
                    label_visibility="collapsed"
                )

            if uploaded_file is not None:
                try:
                    if uploaded_file.name.endswith(".xlsx"):
                        bulk_df = pd.read_excel(uploaded_file)
                    else:
                        bulk_df = pd.read_csv(uploaded_file)

                    # Normalise column names
                    bulk_df.columns = [c.strip().lower().replace(" ", "_") for c in bulk_df.columns]
                    required_cols = {"subject_name", "topic_name"}
                    missing_cols = required_cols - set(bulk_df.columns)
                    if missing_cols:
                        st.error(f"Missing required columns: {', '.join(missing_cols)}")
                    else:
                        bulk_df = bulk_df.dropna(subset=["subject_name", "topic_name"])
                        st.info(f"Preview: **{len(bulk_df)} rows** detected.")
                        st.dataframe(bulk_df.head(10), use_container_width=True)

                        if st.button("💾 Import All Rows", type="primary", key="bulk_import_btn"):
                            VALID_DIFFICULTY   = {"Easy", "Medium", "Hard"}
                            VALID_PRIORITY     = {"Low", "Medium", "High"}
                            VALID_KNOWLEDGE    = {"Beginner", "Intermediate", "Advanced"}
                            VALID_STATUS       = {"Not Started", "In Progress", "Completed"}
                            SUBJECT_COLORS     = ["#4F46E5", "#10B981", "#F59E0B", "#EF4444", "#8B5CF6",
                                                  "#3B82F6", "#EC4899", "#14B8A6", "#F97316", "#6366F1"]

                            added_subjects = 0
                            added_topics   = 0
                            skipped        = 0

                            with get_db() as db:
                                # Build a cache of existing subjects for this user
                                existing_subs = {
                                    s.name.lower(): s.id
                                    for s in db.query(Subject).filter(Subject.user_id == user_id).all()
                                }
                                color_idx = len(existing_subs) % len(SUBJECT_COLORS)

                                for _, row in bulk_df.iterrows():
                                    sub_name   = str(row["subject_name"]).strip()
                                    topic_name = str(row["topic_name"]).strip()
                                    if not sub_name or not topic_name:
                                        skipped += 1
                                        continue

                                    # Create subject if it doesn't exist yet
                                    sub_key = sub_name.lower()
                                    if sub_key not in existing_subs:
                                        new_sub = Subject(
                                            user_id=user_id,
                                            name=sub_name,
                                            color=SUBJECT_COLORS[color_idx % len(SUBJECT_COLORS)],
                                        )
                                        db.add(new_sub)
                                        db.flush()
                                        existing_subs[sub_key] = new_sub.id
                                        color_idx += 1
                                        added_subjects += 1

                                    sub_id = existing_subs[sub_key]

                                    # Parse optional fields
                                    def _safe(col, valid, default):
                                        if col in row.index and pd.notna(row[col]):
                                            v = str(row[col]).strip().title()
                                            return v if v in valid else default
                                        return default

                                    difficulty   = _safe("difficulty",              VALID_DIFFICULTY, "Medium")
                                    priority     = _safe("priority",               VALID_PRIORITY,   "Medium")
                                    knowledge    = _safe("knowledge_level",        VALID_KNOWLEDGE,  "Beginner")
                                    status_val   = _safe("status",                 VALID_STATUS,     "Not Started")
                                    try:
                                        dur = float(row["estimated_duration_hours"]) if "estimated_duration_hours" in row.index and pd.notna(row.get("estimated_duration_hours")) else 1.0
                                    except (ValueError, TypeError):
                                        dur = 1.0

                                    new_topic = Topic(
                                        subject_id=sub_id,
                                        name=topic_name,
                                        difficulty=difficulty,
                                        priority=priority,
                                        knowledge_level=knowledge,
                                        status=status_val,
                                        estimated_duration_hours=max(0.5, dur),
                                    )
                                    db.add(new_topic)
                                    added_topics += 1

                            st.success(
                                f"✅ Import complete! "
                                f"**{added_subjects}** new subject(s) created, "
                                f"**{added_topics}** topic(s) added"
                                + (f", {skipped} row(s) skipped." if skipped else ".")
                            )
                            st.rerun()

                except Exception as bulk_err:
                    st.error(f"Error reading file: {bulk_err}")

        # Filter & List Topics
        filter_col1, filter_col2, filter_col3 = st.columns([2, 1, 1])
        with filter_col1:
            subject_filter = st.selectbox("Filter by Subject", ["All Subjects"] + list(subject_dict.keys()))
        with filter_col2:
            status_filter = st.selectbox("Filter by Status", ["All Statuses", "Not Started", "In Progress", "Completed"])
        with filter_col3:
            difficulty_filter = st.selectbox("Filter by Difficulty", ["All Difficulties", "Easy", "Medium", "Hard"])

        with get_db() as db:
            query = db.query(Topic).join(Subject).filter(Subject.user_id == user_id)
            if subject_filter != "All Subjects":
                query = query.filter(Subject.name == subject_filter)
            if status_filter != "All Statuses":
                query = query.filter(Topic.status == status_filter)
            if difficulty_filter != "All Difficulties":
                query = query.filter(Topic.difficulty == difficulty_filter)

            topics_raw = query.order_by(Topic.created_at.desc()).all()
            topics = [
                {
                    "id": t.id,
                    "name": t.name,
                    "subject_name": t.subject.name if t.subject else "General",
                    "subject_color": t.subject.color if t.subject else "#4F46E5",
                    "difficulty": t.difficulty,
                    "priority": t.priority,
                    "knowledge_level": t.knowledge_level,
                    "status": t.status,
                    "estimated_duration_hours": t.estimated_duration_hours,
                    "exam_date": t.exam_date,
                    "notes": t.notes,
                }
                for t in topics_raw
            ]

        if not topics:
            st.info("No topics found matching your filter criteria.")
        else:
            st.markdown(f"**Found {len(topics)} topic{'s' if len(topics) != 1 else ''}:**")
            for t in topics:
                with st.container():
                    st.markdown(
                        f"""
                        <div class="card" style="padding: 16px 20px; margin-bottom: 12px;">
                            <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                                <div>
                                    <span style="font-weight: 700; font-size: 1.15rem;">{t['name']}</span>
                                    <span style="font-size: 0.85rem; color: {t['subject_color']}; margin-left: 10px; font-weight: 600;">{t['subject_name']}</span>
                                </div>
                                <div>
                                    {get_status_badge(t['status'])}
                                </div>
                            </div>
                            <div style="display: flex; gap: 8px; align-items: center; margin-top: 8px; flex-wrap: wrap;">
                                {get_difficulty_badge(t['difficulty'])}
                                {get_priority_badge(t['priority'])}
                                <span class="badge" style="background: rgba(147, 51, 234, 0.15); color: #a855f7;">Knowledge: {t['knowledge_level']}</span>
                                <span class="badge" style="background: rgba(100, 116, 139, 0.15); color: #94a3b8;">Est: {t['estimated_duration_hours']}h</span>
                                {f'<span class="badge" style="background: rgba(239, 68, 68, 0.15); color: #f87171;">Exam: {t["exam_date"].strftime("%b %d, %Y")}</span>' if t.get('exam_date') else ''}
                            </div>
                            {f'<div style="margin-top: 8px; font-size: 0.85rem; color: #94a3b8;">{t["notes"]}</div>' if t.get('notes') else ''}
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                    action_c1, action_c2, action_c3, action_c4 = st.columns([1, 1, 1, 3])
                    with action_c1:
                        if t["status"] != "Completed":
                            if st.button("Mark Completed ✓", key=f"top_done_{t['id']}"):
                                with get_db() as db:
                                    topic_rec = db.query(Topic).filter(Topic.id == t["id"]).first()
                                    if topic_rec:
                                        topic_rec.status = "Completed"
                                        topic_rec.completed_at = datetime.now()
                                st.toast(f"'{t['name']}' marked completed!", icon="🎉")
                                st.rerun()
                        else:
                            if st.button("Mark In Progress", key=f"top_reopen_{t['id']}"):
                                with get_db() as db:
                                    topic_rec = db.query(Topic).filter(Topic.id == t["id"]).first()
                                    if topic_rec:
                                        topic_rec.status = "In Progress"
                                st.rerun()

                    with action_c2:
                        edit_key = f"edit_topic_{t['id']}"
                        if st.button("Edit ✏️", key=f"top_edit_btn_{t['id']}"):
                            st.session_state[edit_key] = not st.session_state.get(edit_key, False)
                            st.rerun()

                    with action_c3:
                        if st.button("Delete 🗑️", key=f"top_del_{t['id']}"):
                            with get_db() as db:
                                db.query(Topic).filter(Topic.id == t["id"]).delete()
                            st.toast("Topic deleted.")
                            # clear edit state if open
                            st.session_state.pop(f"edit_topic_{t['id']}", None)
                            st.rerun()

                    # --- Inline Edit Form ---
                    if st.session_state.get(f"edit_topic_{t['id']}", False):
                        with st.form(f"edit_topic_form_{t['id']}"):
                            st.markdown("**✏️ Edit Topic**")
                            ec1, ec2 = st.columns(2)
                            with ec1:
                                e_name = st.text_input("Topic Name", value=t["name"])
                                e_diff = st.selectbox(
                                    "Difficulty", ["Easy", "Medium", "Hard"],
                                    index=["Easy", "Medium", "Hard"].index(t["difficulty"]) if t["difficulty"] in ["Easy", "Medium", "Hard"] else 1
                                )
                                e_dur = st.number_input(
                                    "Estimated Duration (Hours)",
                                    min_value=0.5, max_value=20.0,
                                    value=float(t["estimated_duration_hours"]),
                                    step=0.5
                                )
                                e_notes = st.text_area("Notes", value=t["notes"] or "")
                            with ec2:
                                e_priority = st.selectbox(
                                    "Priority", ["Low", "Medium", "High"],
                                    index=["Low", "Medium", "High"].index(t["priority"]) if t["priority"] in ["Low", "Medium", "High"] else 1
                                )
                                e_knowledge = st.selectbox(
                                    "Knowledge Level", ["Beginner", "Intermediate", "Advanced"],
                                    index=["Beginner", "Intermediate", "Advanced"].index(t["knowledge_level"]) if t["knowledge_level"] in ["Beginner", "Intermediate", "Advanced"] else 0
                                )
                                e_status = st.selectbox(
                                    "Status", ["Not Started", "In Progress", "Completed"],
                                    index=["Not Started", "In Progress", "Completed"].index(t["status"]) if t["status"] in ["Not Started", "In Progress", "Completed"] else 0
                                )
                                e_exam = st.date_input("Exam / Deadline Date", value=t["exam_date"] if t.get("exam_date") else None)

                            save_col, cancel_col = st.columns([1, 1])
                            save_edit = save_col.form_submit_button("Save Changes", type="primary")
                            cancel_edit = cancel_col.form_submit_button("Cancel")

                            if save_edit:
                                if not e_name.strip():
                                    st.error("Topic name cannot be empty.")
                                else:
                                    with get_db() as db:
                                        tr = db.query(Topic).filter(Topic.id == t["id"]).first()
                                        if tr:
                                            tr.name = e_name.strip()
                                            tr.difficulty = e_diff
                                            tr.priority = e_priority
                                            tr.knowledge_level = e_knowledge
                                            tr.status = e_status
                                            tr.estimated_duration_hours = float(e_dur)
                                            tr.exam_date = e_exam if e_exam else None
                                            tr.notes = e_notes.strip()
                                            if e_status == "Completed" and not tr.completed_at:
                                                tr.completed_at = datetime.now()
                                            elif e_status != "Completed":
                                                tr.completed_at = None
                                    st.toast(f"'{e_name.strip()}' updated!", icon="✅")
                                    st.session_state.pop(f"edit_topic_{t['id']}", None)
                                    st.rerun()
                            if cancel_edit:
                                st.session_state.pop(f"edit_topic_{t['id']}", None)
                                st.rerun()

    # --- SUBJECTS MANAGEMENT ---
    with tab_subjects:
        with st.expander("➕ Add New Subject", expanded=False):
            with st.form("add_subject_form", clear_on_submit=True):
                sub_col1, sub_col2 = st.columns(2)
                with sub_col1:
                    new_sub_name = st.text_input("Subject Name", placeholder="e.g. Computer Networks")
                    new_sub_code = st.text_input("Subject Code", placeholder="e.g. CS302")
                with sub_col2:
                    new_sub_color = st.color_picker("Subject Theme Color", "#4F46E5")
                    new_sub_desc = st.text_input("Description", placeholder="e.g. OSI model, TCP/IP protocols, routing")

                if st.form_submit_button("Add Subject", type="primary"):
                    if not new_sub_name.strip():
                        st.error("Subject name cannot be empty.")
                    else:
                        with get_db() as db:
                            new_sub = Subject(
                                user_id=user_id,
                                name=new_sub_name.strip(),
                                code=new_sub_code.strip(),
                                color=new_sub_color,
                                description=new_sub_desc.strip()
                            )
                            db.add(new_sub)
                        st.success(f"Subject '{new_sub_name}' added successfully!")
                        st.rerun()

        with get_db() as db:
            user_subjects_raw = db.query(Subject).filter(Subject.user_id == user_id).all()
            user_subjects = [
                {
                    "id": sub.id,
                    "name": sub.name,
                    "code": sub.code,
                    "color": sub.color,
                    "description": sub.description,
                    "topic_count": len(sub.topics),
                    "done_count": sum(1 for top in sub.topics if top.status == "Completed")
                }
                for sub in user_subjects_raw
            ]

        if not user_subjects:
            st.info("No subjects enrolled yet.")
        else:
            for sub in user_subjects:
                topic_count = sub["topic_count"]
                done_count = sub["done_count"]
                sub_c1, sub_c2 = st.columns([5, 1])
                with sub_c1:
                    st.markdown(
                        f"""
                        <div class="card" style="border-left: 6px solid {sub['color']}; padding: 14px 18px; margin-bottom: 8px;">
                            <div style="font-weight: 700; font-size: 1.15rem;">
                                {sub['name']} <span style="font-size: 0.85rem; color: #64748b;">({sub['code'] or 'No Code'})</span>
                            </div>
                            <div style="font-size: 0.9rem; color: #64748b; margin-top: 4px;">{sub['description'] or 'No description'}</div>
                            <div style="font-size: 0.8rem; margin-top: 6px; font-weight: 600;">
                                Topics: {topic_count} total | {done_count} completed ({round(done_count/topic_count*100 if topic_count else 0)}%)
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                with sub_c2:
                    if st.button("Delete 🗑️", key=f"del_sub_{sub['id']}"):
                        with get_db() as db:
                            db.query(Subject).filter(Subject.id == sub["id"]).delete()
                        st.toast("Subject and its topics deleted.")
                        st.rerun()


# ==============================================================================
# STUDY PLANNER VIEW
# ==============================================================================
def render_study_planner_view(user_id: int):
    """Study Planner with time-slot generation and auto-rescheduling."""
    render_header("📅 Intelligent Study Planner", "Generate balanced, time-slot-based study schedules with interleaving and auto-rescheduling.")

    with get_db() as db:
        user_prof = db.query(User).filter(User.id == user_id).first()
        default_hours = user_prof.preferred_study_hours if user_prof else 3.0
        default_preset = user_prof.preferred_study_time if user_prof else "Evening (6:00 PM - 10:00 PM)"

    # Missed Session Notification Banner
    rescheduled_count, notes = detect_and_reschedule_missed_sessions(user_id)
    if notes:
        st.warning("### ⚠️ Study Plan Automatically Rescheduled", icon="⚠️")
        for n in notes:
            st.markdown(n)

    # Schedule Generator Form
    with st.expander("⚡ Schedule Generator Configuration", expanded=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            days_to_plan = st.slider("Schedule Horizon (Days)", min_value=1, max_value=14, value=7)
            daily_hours = st.slider("Daily Study Hours", min_value=1.0, max_value=8.0, value=float(default_hours), step=0.5)

        with col2:
            time_preset = st.selectbox(
                "Preferred Study Window",
                options=list(PRESET_SLOT_TIMES.keys()) + ["Custom Start Time"],
                index=list(PRESET_SLOT_TIMES.keys()).index(default_preset) if default_preset in PRESET_SLOT_TIMES else 2
            )
            custom_time = None
            if time_preset == "Custom Start Time":
                custom_time = st.time_input("Choose Start Time", value=time(18, 0))

        with col3:
            session_len = st.selectbox("Slot Duration", [30, 45, 60], index=1, format_func=lambda x: f"{x} Minutes")
            break_len = st.selectbox("Break Between Slots", [5, 10, 15], index=2, format_func=lambda x: f"{x} Minutes")

        if st.button("🚀 Generate Balanced Time-Slot Schedule", type="primary", use_container_width=True):
            with st.spinner("Analyzing curriculum priorities, difficulties, and interleaving time slots..."):
                res = generate_balanced_study_plan(
                    user_id=user_id,
                    days_to_plan=days_to_plan,
                    daily_study_hours=daily_hours,
                    preferred_time_preset=time_preset,
                    custom_start_time=custom_time,
                    session_duration_minutes=session_len,
                    break_minutes=break_len
                )
                if res["success"]:
                    st.success(res["message"])
                    st.rerun()
                else:
                    st.error(res["message"])

    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

    # View Schedule by Date
    today = date.today()
    date_options = [today + timedelta(days=i) for i in range(14)]
    date_labels = [d.strftime("%a, %b %d") + (" (Today)" if d == today else "") for d in date_options]

    selected_date_idx = st.selectbox(
        "Select Schedule Date to View:",
        range(len(date_options)),
        format_func=lambda i: date_labels[i]
    )
    view_date = date_options[selected_date_idx]

    sessions = get_user_schedule_for_date(user_id, view_date)

    if not sessions:
        st.info(f"No study sessions planned for {view_date.strftime('%B %d, %Y')}. Generate a schedule above to populate.")
    else:
        st.markdown(f"### Study Slots for {view_date.strftime('%A, %B %d, %Y')}")
        for s in sessions:
            status_style = "border-left: 5px solid #10b981;" if s["status"] == "Completed" else ("border-left: 5px solid #ef4444;" if s["status"] == "Missed" else "border-left: 5px solid #6366f1;")
            with st.container():
                st.markdown(
                    f"""
                    <div class="session-card" style="{status_style}">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <span style="font-size: 1.1rem; font-weight: 700; color: #6366f1;">⏰ {s['start_time']} – {s['end_time']} ({s['duration']} mins)</span>
                            <span style="font-weight: 600; color: {s['subject_color']};">{s['subject_name']}</span>
                        </div>
                        <div style="font-size: 1.2rem; font-weight: 700; margin-top: 4px;">{s['topic_name']}</div>
                        <div style="display: flex; gap: 8px; align-items: center; margin-top: 6px;">
                            {get_difficulty_badge(s['difficulty'])}
                            {get_priority_badge(s['priority'])}
                            {get_status_badge(s['status'])}
                            {f'<span class="badge" style="background: rgba(245, 158, 11, 0.15); color: #f59e0b;">Auto-Rescheduled</span>' if s.get("rescheduled_from_id") else ''}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                if s["status"] == "Planned":
                    c_done, c_miss, _ = st.columns([1, 1, 4])
                    with c_done:
                        if st.button("Mark Completed ✓", key=f"plan_done_{s['id']}"):
                            success, msg = complete_study_session(s["id"])
                            if success:
                                st.toast(msg, icon="🎉")
                                st.rerun()
                    with c_miss:
                        if st.button("Mark Missed ⚠️", key=f"plan_miss_{s['id']}"):
                            with get_db() as db:
                                sess = db.query(StudySession).filter(StudySession.id == s["id"]).first()
                                if sess:
                                    sess.status = "Missed"
                            detect_and_reschedule_missed_sessions(user_id)
                            st.toast("Session marked missed and automatically rescheduled!", icon="⚠️")
                            st.rerun()

    # AI Study Coach Coaching Card
    st.markdown("---")
    st.markdown("### 🤖 AI Study Coach Recommendations")
    with st.spinner("Generating personalized study tips..."):
        advice = get_ai_study_recommendations(user_id, custom_api_key=st.session_state.get("custom_api_key"))
        st.markdown(
            f"""
            <div class="card" style="border-left: 4px solid #10b981;">
                {advice}
            </div>
            """,
            unsafe_allow_html=True
        )


# ==============================================================================
# PROGRESS & ANALYTICS VIEW
# ==============================================================================
def render_progress_view(user_id: int):
    """Dedicated Progress, Analytics, and Weak Topic Detection view."""
    render_header("📊 Progress & Analytics", "Real-time metrics, subject completion, and intelligent weak topic detection.")

    overview = get_progress_overview(user_id)
    is_dark = st.session_state.get("theme", "dark") == "dark"

    # KPI Row
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        render_kpi("Completion Rate", f"{overview['completion_percentage']}%", "🎯", f"{overview['completed_topics']} of {overview['total_topics']} topics")
    with c2:
        render_kpi("Study Time Invested", f"{overview['actual_hours']} hrs", "⌛", f"Planned: {overview['planned_hours']} hrs")
    with c3:
        render_kpi("Current Streak", f"{overview['study_streak']} Days", "🔥", "Study consistency")
    with c4:
        render_kpi("Remaining Topics", f"{overview['remaining_topics']}", "📝", f"{overview['in_progress_topics']} in progress")

    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)

    # Charts Row
    chart_c1, chart_c2 = st.columns([1, 1.4])
    with chart_c1:
        donut_fig = render_progress_donut(overview["completion_percentage"], is_dark=is_dark)
        st.pyplot(donut_fig)

    with chart_c2:
        subjects_data = get_subject_wise_analytics(user_id)
        if subjects_data:
            bar_fig = render_subject_progress_bar(subjects_data, is_dark=is_dark)
            if bar_fig:
                st.pyplot(bar_fig)
        else:
            st.info("No subjects found.")

    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)

    # Secondary Charts Row
    with get_db() as db:
        topics_db = db.query(Topic).join(Subject).filter(Subject.user_id == user_id).all()
        topic_dicts = [{"difficulty": t.difficulty, "priority": t.priority} for t in topics_db]

    sub_chart1, sub_chart2 = st.columns([1.5, 1])
    with sub_chart1:
        diff_fig = render_difficulty_priority_breakdown(topic_dicts, is_dark=is_dark)
        if diff_fig:
            st.pyplot(diff_fig)
    with sub_chart2:
        time_fig = render_study_time_comparison(overview["planned_hours"], overview["actual_hours"], is_dark=is_dark)
        st.pyplot(time_fig)

    st.markdown("---")

    # WEAK AND STRONG TOPICS SECTION
    analysis = analyze_weak_and_strong_topics(user_id)
    weak_topics = analysis.get("weak_topics", [])
    strong_topics = analysis.get("strong_topics", [])

    weak_col, strong_col = st.columns(2)

    with weak_col:
        st.markdown("### ⚠️ Topics Needing More Revision")
        st.caption("Intelligently flagged based on difficulty, knowledge level, missed sessions, and upcoming exam dates.")

        if not weak_topics:
            st.success("🎉 No critical weak topics detected. Keep up the consistent study habits!")
        else:
            for wt in weak_topics:
                st.markdown(
                    f"""
                    <div class="card" style="border-left: 4px solid #ef4444; padding: 14px 18px; margin-bottom: 10px;">
                        <div style="font-weight: 700; font-size: 1.05rem;">
                            ⚠️ {wt['topic_name']} <span style="font-weight: normal; color: #64748b; font-size: 0.85rem;">({wt['subject_name']})</span>
                        </div>
                        <div style="margin-top: 4px; font-size: 0.9rem; color: #ef4444;">
                            <b>Reason:</b> {wt['reason']}
                        </div>
                        <div style="margin-top: 6px; display: flex; gap: 8px;">
                            {get_difficulty_badge(wt['difficulty'])}
                            {get_priority_badge(wt['priority'])}
                            <span class="badge" style="background: rgba(100, 116, 139, 0.15); color: #94a3b8;">Level: {wt['knowledge_level']}</span>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

    with strong_col:
        st.markdown("### ✓ Strong Mastered Topics")
        st.caption("Topics where you have demonstrated mastery and completed study objectives.")

        if not strong_topics:
            st.info("Complete topics with Intermediate or Advanced knowledge level to build your strong topics list!")
        else:
            for st_top in strong_topics:
                st.markdown(
                    f"""
                    <div class="card" style="border-left: 4px solid #10b981; padding: 14px 18px; margin-bottom: 10px;">
                        <div style="font-weight: 700; font-size: 1.05rem; color: #10b981;">
                            ✓ {st_top['topic_name']} <span style="font-weight: normal; color: #64748b; font-size: 0.85rem;">({st_top['subject_name']})</span>
                        </div>
                        <div style="margin-top: 4px; font-size: 0.9rem; color: #64748b;">
                            <b>Status:</b> {st_top['reason']}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )


# ==============================================================================
# ASK AI ASSISTANT VIEW
# ==============================================================================
def render_ask_ai_view(user_id: int):
    """Interactive AI Study Assistant with Simple, Teacher, and Exam modes."""
    render_header("🤖 AI Study Assistant", "Ask questions, explore concepts, and prepare for exams with your personalized AI tutor.")

    # Mode Selector
    mode_col, context_col = st.columns([1.5, 1])
    with mode_col:
        selected_mode = st.radio(
            "Select AI Tutoring Mode:",
            ["Simple", "Teacher", "Exam"],
            index=["Simple", "Teacher", "Exam"].index(st.session_state.get("ai_mode", "Simple")),
            horizontal=True
        )
        st.session_state["ai_mode"] = selected_mode

    with context_col:
        with st.expander("👤 View Student Context Sent to AI", expanded=False):
            ctx_text = get_student_context(user_id)
            st.code(ctx_text or "No enrolled subjects or weak topics yet.", language="text")

    # Mode Description Card
    mode_descriptions = {
        "Simple": "💡 **Simple Mode:** Clear, intuitive explanations using relatable everyday analogies with minimal jargon.",
        "Teacher": "🧑‍🏫 **Teacher Mode:** Step-by-step breakdown with concrete examples, guidance, and quick self-check questions.",
        "Exam": "🎯 **Exam Mode:** High-yield definitions, exam-oriented notes, high-scoring keywords, and sample test questions."
    }
    st.info(mode_descriptions[selected_mode])

    # API Key status banner
    api_key = get_configured_api_key(custom_key=st.session_state.get("custom_api_key"))
    if not api_key:
        st.warning(
            "🔑 **Google Gemini API Key Not Configured:** Operating in intelligent offline mode. "
            "To activate live Google Gemini responses, add your free key in the **Settings** tab or `.env`.",
            icon="💡"
        )

    # Chat History Container
    chat_history = get_chat_history(user_id)

    chat_box = st.container()
    with chat_box:
        if not chat_history:
            st.markdown(
                """
                <div style="text-align: center; padding: 30px; color: #64748b;">
                    <div style="font-size: 2.5rem; margin-bottom: 8px;">💬</div>
                    <h4>No messages yet</h4>
                    <p>Ask any academic question or pick from the suggested prompts below.</p>
                </div>
                """,
                unsafe_allow_html=True
            )
        else:
            for msg in chat_history:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])
                    time_str = msg["timestamp"].strftime("%I:%M %p") if msg.get("timestamp") else ""
                    st.caption(f"Mode: {msg.get('mode', 'General')} • {time_str}")

    # Suggested Prompts
    st.markdown("**Suggested Prompts:**")
    prompt_c1, prompt_c2, prompt_c3, prompt_c4 = st.columns(4)
    quick_query = None

    with prompt_c1:
        if st.button("Explain Inheritance", use_container_width=True):
            quick_query = "Explain object-oriented inheritance in Python with a clear example."
    with prompt_c2:
        if st.button("Normalization Guide", use_container_width=True):
            quick_query = "Explain database normalization (1NF, 2NF, 3NF) simply."
    with prompt_c3:
        if st.button("Exam Revision Quiz", use_container_width=True):
            quick_query = "Give me 3 high-yield exam questions on my weakest subject."
    with prompt_c4:
        if st.button("Study Plan Advice", use_container_width=True):
            quick_query = "What should I focus on studying today based on my weak topics?"

    # Chat Input
    user_prompt = st.chat_input("Ask your study assistant anything...") or quick_query

    if user_prompt:
        with st.chat_message("user"):
            st.markdown(user_prompt)

        with st.chat_message("assistant"):
            with st.spinner(f"Thinking in {selected_mode} mode..."):
                response = ask_study_assistant(
                    user_id=user_id,
                    user_query=user_prompt,
                    mode=selected_mode,
                    custom_api_key=st.session_state.get("custom_api_key"),
                    save_to_history=True
                )
                st.markdown(response)
        st.rerun()

    # Clear Chat Button
    if chat_history:
        if st.button("🗑️ Clear Chat History", type="secondary"):
            clear_chat_history(user_id)
            st.toast("Chat history cleared.")
            st.rerun()


# ==============================================================================
# STUDY MATERIALS & DOCUMENT QA VIEW
# ==============================================================================
def render_study_materials_view(user_id: int):
    """Upload study materials (PDF, DOCX, TXT, Images) and perform Retrieval-Based Q&A."""
    render_header("📄 Study Materials & Document AI", "Upload lecture notes, textbooks, and past papers. Ask questions with semantic retrieval.")

    with get_db() as db:
        subjects = db.query(Subject).filter(Subject.user_id == user_id).all()
        subject_options = {s.name: s.id for s in subjects}
        materials_raw = db.query(UploadedMaterial).filter(UploadedMaterial.user_id == user_id).order_by(UploadedMaterial.created_at.desc()).all()
        materials = [
            {
                "id": m.id,
                "filename": m.filename,
                "file_type": m.file_type,
                "file_size_kb": m.file_size_kb,
                "created_at": m.created_at
            }
            for m in materials_raw
        ]

    # Upload Section
    with st.expander("📤 Upload New Study Material", expanded=len(materials) == 0):
        up_col1, up_col2 = st.columns([2, 1])
        with up_col1:
            uploaded_file = st.file_uploader(
                "Choose a document or image",
                type=["pdf", "docx", "txt", "md", "png", "jpg", "jpeg"]
            )
        with up_col2:
            sel_subject = st.selectbox("Associate with Subject (Optional)", ["None"] + list(subject_options.keys()))

        if uploaded_file is not None:
            if st.button("Process & Save Material", type="primary"):
                file_bytes = uploaded_file.read()
                file_size_kb = round(len(file_bytes) / 1024.0, 1)

                with st.spinner("Extracting text and indexing document..."):
                    success, extracted_text, file_type, msg = process_uploaded_document(
                        uploaded_file.name,
                        file_bytes
                    )

                if success:
                    sub_id = subject_options[sel_subject] if sel_subject != "None" else None
                    with get_db() as db:
                        mat = UploadedMaterial(
                            user_id=user_id,
                            subject_id=sub_id,
                            filename=uploaded_file.name,
                            file_type=file_type,
                            file_size_kb=file_size_kb,
                            extracted_text=extracted_text,
                            summary=""
                        )
                        db.add(mat)
                    st.success(f"File '{uploaded_file.name}' processed successfully ({file_size_kb} KB, {len(extracted_text.split())} words)!")
                    st.rerun()
                else:
                    st.error(f"Error processing file: {msg}")

    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

    # Document Q&A Section
    if not materials:
        st.info("No study materials uploaded yet. Upload your PDF notes or textbook chapters above to ask questions!")
        return

    st.markdown("### 🔍 Document-Based AI Q&A")
    mat_dict = {f"{m['filename']} ({m['file_type'].upper()}, {m['file_size_kb']} KB)": m['id'] for m in materials}
    selected_mat_label = st.selectbox("Select Document to Query:", list(mat_dict.keys()))
    selected_mat_id = mat_dict[selected_mat_label]

    q_col1, q_col2 = st.columns(2)
    with q_col1:
        if st.button("📝 Summarize Document", use_container_width=True):
            with st.spinner("Generating document summary using semantic retrieval..."):
                summary_text = summarize_document(selected_mat_id, custom_api_key=st.session_state.get("custom_api_key"))
                st.markdown("#### Document Summary:")
                st.markdown(summary_text)

    with q_col2:
        if st.button("🎯 Generate Practice Exam Questions", use_container_width=True):
            with st.spinner("Extracting high-yield exam questions..."):
                questions_text = generate_exam_questions_from_doc(selected_mat_id, custom_api_key=st.session_state.get("custom_api_key"))
                st.markdown("#### Practice Questions:")
                st.markdown(questions_text)

    # Custom Document Question
    doc_query = st.text_input("Ask a specific question about this document:", placeholder="e.g. What is the difference between TCP and UDP in this chapter?")
    if st.button("Ask Document Question", type="primary") and doc_query:
        with st.spinner("Searching document chunks and answering..."):
            ans = ask_document_question(
                material_id=selected_mat_id,
                user_query=doc_query,
                custom_api_key=st.session_state.get("custom_api_key")
            )
            st.markdown("#### Answer:")
            st.markdown(ans)

    # Uploaded Materials List
    st.markdown("---")
    st.markdown("### 📚 Your Uploaded Library")
    for mat in materials:
        m_c1, m_c2 = st.columns([5, 1])
        with m_c1:
            st.markdown(
                f"""
                <div class="card" style="padding: 12px 18px; margin-bottom: 8px;">
                    <div style="font-weight: 700; font-size: 1.05rem;">📄 {mat['filename']}</div>
                    <div style="font-size: 0.85rem; color: #64748b; margin-top: 2px;">
                        Type: {mat['file_type'].upper()} | Size: {mat['file_size_kb']} KB | Uploaded: {mat['created_at'].strftime('%b %d, %Y')}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
        with m_c2:
            if st.button("Delete", key=f"mat_del_{mat['id']}"):
                with get_db() as db:
                    db.query(UploadedMaterial).filter(UploadedMaterial.id == mat['id']).delete()
                st.toast(f"Deleted {mat['filename']}")
                st.rerun()


# ==============================================================================
# USER PROFILE VIEW
# ==============================================================================
def render_profile_view(user: Dict[str, Any]):
    """Student profile viewing and updating."""
    render_header("👤 Student Profile", "Update your academic details, study preferences, and credentials.")

    user_id = user["id"]
    prof = get_user_profile(user_id) or user

    p_col1, p_col2 = st.columns(2)

    with p_col1:
        st.markdown("### Academic Information")
        with st.form("profile_form"):
            name = st.text_input("Full Name", value=prof.get("full_name", ""))
            course = st.text_input("Course / Major", value=prof.get("course", ""))
            year = st.selectbox(
                "Year of Study",
                ["1st Year", "2nd Year", "3rd Year", "4th Year", "Postgraduate", "High School"],
                index=["1st Year", "2nd Year", "3rd Year", "4th Year", "Postgraduate", "High School"].index(prof.get("year_of_study", "1st Year")) if prof.get("year_of_study") in ["1st Year", "2nd Year", "3rd Year", "4th Year", "Postgraduate", "High School"] else 0
            )
            hours = st.number_input("Target Daily Study Hours", min_value=0.5, max_value=12.0, value=float(prof.get("preferred_study_hours", 3.0)), step=0.5)
            study_time = st.selectbox(
                "Preferred Study Window",
                list(PRESET_SLOT_TIMES.keys()),
                index=list(PRESET_SLOT_TIMES.keys()).index(prof.get("preferred_study_time")) if prof.get("preferred_study_time") in PRESET_SLOT_TIMES else 2
            )

            if st.form_submit_button("Save Profile Changes", type="primary"):
                success, msg = update_user_profile(user_id, name, course, year, hours, study_time)
                if success:
                    st.session_state["user"]["full_name"] = name
                    st.session_state["user"]["course"] = course
                    st.session_state["user"]["year_of_study"] = year
                    st.session_state["user"]["preferred_study_hours"] = hours
                    st.session_state["user"]["preferred_study_time"] = study_time
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)

    with p_col2:
        st.markdown("### Change Password")
        with st.form("pwd_form"):
            old_p = st.text_input("Current Password", type="password")
            new_p = st.text_input("New Password (min 6 chars)", type="password")
            conf_p = st.text_input("Confirm New Password", type="password")

            if st.form_submit_button("Update Password"):
                if new_p != conf_p:
                    st.error("New passwords do not match.")
                else:
                    success, msg = update_user_password(user_id, old_p, new_p)
                    if success:
                        st.success(msg)
                    else:
                        st.error(msg)


# ==============================================================================
# SETTINGS VIEW
# ==============================================================================
def render_settings_view(user_id: int):
    """Application settings, API key management, theme switcher, and demo tools."""
    render_header("⚙️ Settings", "Configure your AI credentials, theme preference, and database tools.")

    s_col1, s_col2 = st.columns(2)

    with s_col1:
        st.markdown("### 🔑 Google Gemini API Configuration")
        st.write("SmartStudy AI uses Google Gemini for conversational tutoring and document synthesis.")

        current_key = st.session_state.get("custom_api_key") or os.getenv("GOOGLE_API_KEY", "")
        entered_key = st.text_input("Google Gemini API Key", value=current_key, type="password", help="Get your free key at https://aistudio.google.com/")

        if st.button("Save API Key", type="primary"):
            st.session_state["custom_api_key"] = entered_key.strip()
            st.success("API Key saved for this session!")

        if current_key:
            st.success("🟢 Google Gemini API Key is configured and ready.")
        else:
            st.info("🟡 No API key active. SmartStudy AI will operate in intelligent offline mode.")

        st.markdown("---")
        st.markdown("### 🎨 Appearance & Theme")
        cur_theme = st.session_state.get("theme", "dark")
        new_theme = st.radio("Application Theme", ["Dark Mode 🌙", "Light Mode ☀️"], index=0 if cur_theme == "dark" else 1)
        selected_theme = "dark" if "Dark" in new_theme else "light"
        if selected_theme != cur_theme:
            st.session_state["theme"] = selected_theme
            st.rerun()

    with s_col2:
        st.markdown("### 🧪 Demo & Sample Data Management")
        st.write("Quickly populate or reset sample subjects, topics, and schedule for demonstration.")

        if st.button("🚀 Load Sample Curriculum & Topics", use_container_width=True):
            if seed_sample_student_data(user_id):
                st.success("Sample curriculum loaded!")
                st.rerun()
            else:
                st.warning("You already have subjects added.")

        st.markdown("---")
        st.markdown("### ℹ️ System Information")
        st.json({
            "Application": "SmartStudy AI",
            "Version": "1.0.0",
            "Python": sys.version.split()[0],
            "Database": "SQLite + SQLAlchemy 2.0",
            "UI Framework": "Streamlit",
            "AI Integration": "Google Gemini 2.5 / 1.5 Flash",
            "Status": "Production Ready"
        })


# ==============================================================================
# MAIN APPLICATION CONTROLLER
# ==============================================================================
def main():
    if not st.session_state["authenticated"] or not st.session_state["user"]:
        render_auth_view()
        return

    user = st.session_state["user"]
    user_id = user["id"]

    # Sidebar Navigation
    with st.sidebar:
        st.markdown(
            """
            <div style="padding: 10px 0 20px 0; border-bottom: 1px solid #374151; margin-bottom: 15px;">
                <div style="font-size: 1.6rem; font-weight: 800; color: #6366f1;">🎓 SmartStudy AI</div>
                <div style="font-size: 0.8rem; color: #9ca3af;">Intelligent Personal Study Planner</div>
            </div>
            """,
            unsafe_allow_html=True
        )

        # Student Profile Card in Sidebar
        student_display_name = user.get("full_name") or user.get("username")
        st.markdown(
            f"""
            <div style="background: rgba(99, 102, 241, 0.1); border: 1px solid rgba(99, 102, 241, 0.25); border-radius: 8px; padding: 10px 14px; margin-bottom: 16px;">
                <div style="font-weight: 700; font-size: 0.95rem;">👤 {student_display_name}</div>
                <div style="font-size: 0.8rem; color: #94a3b8;">{user.get('course') or 'Student'} • {user.get('year_of_study') or 'Enrolled'}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

        # Navigation Options
        pages = [
            ("Dashboard", "🏠 Dashboard"),
            ("Subjects & Topics", "📚 Subjects & Topics"),
            ("Study Planner", "📅 Study Planner"),
            ("Progress", "📊 Progress & Analytics"),
            ("Ask AI", "🤖 Ask AI Assistant"),
            ("Study Materials", "📄 Study Materials"),
            ("Profile", "👤 Profile"),
            ("Settings", "⚙️ Settings")
        ]

        current = st.session_state.get("current_page", "Dashboard")
        page_names = [p[0] for p in pages]
        selected_page = st.radio(
            "Navigation",
            options=page_names,
            format_func=lambda x: dict(pages).get(x, x),
            index=page_names.index(current) if current in page_names else 0,
            label_visibility="collapsed"
        )

        if selected_page != current:
            st.session_state["current_page"] = selected_page
            st.rerun()

        st.markdown("---")

        # Theme quick toggle in sidebar
        current_theme = st.session_state.get("theme", "dark")
        theme_toggle_label = "☀️ Switch to Light Mode" if current_theme == "dark" else "🌙 Switch to Dark Mode"
        if st.button(theme_toggle_label, use_container_width=True):
            st.session_state["theme"] = "light" if current_theme == "dark" else "dark"
            st.rerun()

        # Logout button
        if st.button("🚪 Logout", use_container_width=True, type="secondary"):
            st.session_state["authenticated"] = False
            st.session_state["user"] = None
            st.session_state["current_page"] = "Dashboard"
            st.rerun()

    # Route Page
    page = st.session_state.get("current_page", "Dashboard")

    if page == "Dashboard":
        render_dashboard_view(user, navigate_to)
    elif page == "Subjects & Topics":
        render_subjects_topics_view(user_id)
    elif page == "Study Planner":
        render_study_planner_view(user_id)
    elif page == "Progress":
        render_progress_view(user_id)
    elif page == "Ask AI":
        render_ask_ai_view(user_id)
    elif page == "Study Materials":
        render_study_materials_view(user_id)
    elif page == "Profile":
        render_profile_view(user)
    elif page == "Settings":
        render_settings_view(user_id)
    else:
        render_dashboard_view(user, navigate_to)


if __name__ == "__main__":
    main()

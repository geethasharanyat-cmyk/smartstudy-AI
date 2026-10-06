"""
Analytics, Progress Tracking, and Weak Topic Detection Engine.
Analyzes student completion rates, study streaks, subject breakdown,
and uses multi-factor analysis to identify weak topics with clear human-readable explanations.
"""

from datetime import datetime, date, timedelta
from typing import Dict, Any, List
from sqlalchemy import func
from database.models import Topic, Subject, StudySession, ProgressLog, User
from database.db import get_db


def calculate_study_streak(user_id: int) -> int:
    """
    Calculates current consecutive day streak of study activity
    from ProgressLog and completed StudySession.
    """
    today = date.today()
    with get_db() as db:
        # Get all distinct dates where user completed study sessions or logged study progress
        logged_dates = set(
            row[0] for row in db.query(ProgressLog.log_date)
            .filter(ProgressLog.user_id == user_id, ProgressLog.minutes_studied > 0)
            .distinct().all()
        )
        completed_session_dates = set(
            row[0] for row in db.query(StudySession.session_date)
            .filter(StudySession.user_id == user_id, StudySession.status == "Completed")
            .distinct().all()
        )

        all_active_dates = logged_dates.union(completed_session_dates)

        if not all_active_dates:
            return 0

        # Check if active today or yesterday
        streak = 0
        check_date = today

        # If didn't study yet today, see if streak continues from yesterday
        if check_date not in all_active_dates:
            check_date = today - timedelta(days=1)
            if check_date not in all_active_dates:
                return 0

        while check_date in all_active_dates:
            streak += 1
            check_date -= timedelta(days=1)

        return streak


def get_progress_overview(user_id: int) -> Dict[str, Any]:
    """
    Computes overall statistics:
    - Total, completed, in-progress, not-started topics
    - Overall completion percentage
    - Total planned study minutes vs actual studied minutes
    - Study streak
    - Next upcoming exam
    """
    today = date.today()
    with get_db() as db:
        topics = (
            db.query(Topic)
            .join(Subject)
            .filter(Subject.user_id == user_id)
            .all()
        )

        total_topics = len(topics)
        completed_topics = sum(1 for t in topics if t.status == "Completed")
        in_progress_topics = sum(1 for t in topics if t.status == "In Progress")
        not_started_topics = sum(1 for t in topics if t.status == "Not Started")

        completion_pct = (completed_topics / total_topics * 100.0) if total_topics > 0 else 0.0

        # Planned vs actual minutes
        planned_minutes = db.query(func.sum(StudySession.duration_minutes)).filter(
            StudySession.user_id == user_id
        ).scalar() or 0

        actual_minutes_sessions = db.query(func.sum(StudySession.duration_minutes)).filter(
            StudySession.user_id == user_id,
            StudySession.status == "Completed"
        ).scalar() or 0

        actual_minutes_logs = db.query(func.sum(ProgressLog.minutes_studied)).filter(
            ProgressLog.user_id == user_id
        ).scalar() or 0

        actual_minutes = max(actual_minutes_sessions, actual_minutes_logs)

        # Today's study time
        today_minutes = db.query(func.sum(StudySession.duration_minutes)).filter(
            StudySession.user_id == user_id,
            StudySession.session_date == today,
            StudySession.status == "Completed"
        ).scalar() or 0

        # Upcoming exam
        upcoming_exam_topic = (
            db.query(Topic)
            .join(Subject)
            .filter(Subject.user_id == user_id, Topic.exam_date >= today)
            .order_by(Topic.exam_date.asc())
            .first()
        )

        upcoming_exam_info = None
        if upcoming_exam_topic and upcoming_exam_topic.exam_date:
            days_left = (upcoming_exam_topic.exam_date - today).days
            upcoming_exam_info = {
                "topic_name": upcoming_exam_topic.name,
                "subject_name": upcoming_exam_topic.subject.name,
                "date": upcoming_exam_topic.exam_date.strftime("%b %d, %Y"),
                "days_left": days_left
            }

        streak = calculate_study_streak(user_id)

        return {
            "total_topics": total_topics,
            "completed_topics": completed_topics,
            "in_progress_topics": in_progress_topics,
            "not_started_topics": not_started_topics,
            "remaining_topics": total_topics - completed_topics,
            "completion_percentage": round(completion_pct, 1),
            "planned_hours": round(planned_minutes / 60.0, 1),
            "actual_hours": round(actual_minutes / 60.0, 1),
            "today_study_hours": round(today_minutes / 60.0, 1),
            "study_streak": streak,
            "upcoming_exam": upcoming_exam_info
        }


def get_subject_wise_analytics(user_id: int) -> List[Dict[str, Any]]:
    """
    Computes breakdown for each subject:
    - Subject Name & Color
    - Total topics, Completed topics, % Completion
    - Estimated vs spent study hours
    """
    results = []
    with get_db() as db:
        subjects = db.query(Subject).filter(Subject.user_id == user_id).all()

        for s in subjects:
            total_t = len(s.topics)
            completed_t = sum(1 for t in s.topics if t.status == "Completed")
            pct = (completed_t / total_t * 100.0) if total_t > 0 else 0.0

            total_est_hrs = sum(t.estimated_duration_hours for t in s.topics)

            results.append({
                "subject_id": s.id,
                "subject_name": s.name,
                "color": s.color,
                "total_topics": total_t,
                "completed_topics": completed_t,
                "remaining_topics": total_t - completed_t,
                "completion_percentage": round(pct, 1),
                "estimated_hours": round(total_est_hrs, 1)
            })

    return results


def analyze_weak_and_strong_topics(user_id: int) -> Dict[str, List[Dict[str, Any]]]:
    """
    Intelligently analyzes topics to categorize into:
    - Weak Topics (Needing revision) with human-readable rationale
    - Strong Topics (Mastered or solid grasp)

    Multi-factor heuristics evaluate:
    - Difficulty (Hard / Medium)
    - Knowledge level (Beginner / Intermediate)
    - Completion status (In Progress / Not Started)
    - Missed study sessions
    - Proximity to exam date
    """
    today = date.today()
    weak_topics = []
    strong_topics = []

    with get_db() as db:
        topics = (
            db.query(Topic)
            .join(Subject)
            .filter(Subject.user_id == user_id)
            .all()
        )

        for topic in topics:
            subject_name = topic.subject.name if topic.subject else "General"

            # Check missed sessions for this topic
            missed_count = db.query(StudySession).filter(
                StudySession.topic_id == topic.id,
                StudySession.status == "Missed"
            ).count()

            # Reasons generator
            reasons = []
            is_weak = False
            urgency_score = 0

            # Rule 1: Completed with Advanced knowledge level -> Strong topic
            if topic.status == "Completed" and topic.knowledge_level == "Advanced":
                strong_topics.append({
                    "id": topic.id,
                    "topic_name": topic.name,
                    "subject_name": subject_name,
                    "difficulty": topic.difficulty,
                    "knowledge_level": topic.knowledge_level,
                    "reason": "Completed topic with Advanced mastery level"
                })
                continue
            elif topic.status == "Completed" and topic.knowledge_level == "Intermediate":
                strong_topics.append({
                    "id": topic.id,
                    "topic_name": topic.name,
                    "subject_name": subject_name,
                    "difficulty": topic.difficulty,
                    "knowledge_level": topic.knowledge_level,
                    "reason": "Completed topic with good understanding"
                })
                continue

            # Check weaknesses
            if topic.difficulty == "Hard":
                reasons.append("Challenging topic")
                urgency_score += 2

            if topic.knowledge_level == "Beginner":
                reasons.append("Beginner knowledge level")
                urgency_score += 2
            elif topic.knowledge_level == "Intermediate" and topic.difficulty == "Hard":
                reasons.append("Needs more practice to reach mastery")
                urgency_score += 1

            if topic.priority == "High":
                reasons.append("High exam priority")
                urgency_score += 2

            if missed_count > 0:
                reasons.append(f"{missed_count} missed study session{'s' if missed_count > 1 else ''}")
                urgency_score += 3
                is_weak = True

            if topic.exam_date:
                days_to_exam = (topic.exam_date - today).days
                if days_to_exam <= 7:
                    reasons.append(f"Exam in {days_to_exam} day{'s' if days_to_exam != 1 else ''}")
                    urgency_score += 3
                    is_weak = True
                elif days_to_exam <= 14:
                    reasons.append(f"Exam in {days_to_exam} days")
                    urgency_score += 1

            if topic.status == "Not Started" and (topic.priority == "High" or topic.difficulty == "Hard"):
                reasons.append("Not yet started")
                urgency_score += 1

            # Decide if weak
            if is_weak or urgency_score >= 3:
                weak_topics.append({
                    "id": topic.id,
                    "topic_name": topic.name,
                    "subject_name": subject_name,
                    "difficulty": topic.difficulty,
                    "priority": topic.priority,
                    "knowledge_level": topic.knowledge_level,
                    "status": topic.status,
                    "missed_count": missed_count,
                    "urgency_score": urgency_score,
                    "reason": " + ".join(reasons) if reasons else "Incomplete topic requiring revision"
                })
            elif topic.status != "Completed":
                # Fair/moderate topic
                pass

        # Sort weak topics by urgency score descending
        weak_topics.sort(key=lambda x: x["urgency_score"], reverse=True)

    return {
        "weak_topics": weak_topics,
        "strong_topics": strong_topics
    }

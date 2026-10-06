"""
Intelligent Time-Slot-Based Study Scheduler and Rescheduling Engine.
Balances topic difficulty, priority, knowledge level, exam urgency, and subject interleaving.
Automatically detects and reschedules missed study sessions.
"""

from datetime import datetime, date, timedelta, time
from typing import List, Dict, Any, Tuple, Optional
import math
from sqlalchemy.orm import Session
from database.models import Topic, Subject, StudySession, ProgressLog, User
from database.db import get_db


# Scoring weights for scheduling priority
DIFFICULTY_SCORES = {"Easy": 1.0, "Medium": 2.0, "Hard": 3.5}
PRIORITY_SCORES = {"Low": 1.0, "Medium": 2.2, "High": 3.8}
KNOWLEDGE_DEFICIT = {"Advanced": 1.0, "Intermediate": 2.0, "Beginner": 3.2}
STATUS_WEIGHT = {"Not Started": 1.0, "In Progress": 1.25, "Completed": 0.0}

# Standard time presets (start hour, start minute)
PRESET_SLOT_TIMES = {
    "Morning (7:00 AM - 11:00 AM)": (7, 0),
    "Afternoon (1:00 PM - 5:00 PM)": (13, 0),
    "Evening (6:00 PM - 10:00 PM)": (18, 0),
    "Night (8:00 PM - 12:00 AM)": (20, 0),
}


def calculate_topic_urgency_score(topic: Topic, target_date: date) -> float:
    """
    Computes a deterministic priority score for a topic based on:
    - Difficulty (Hard > Medium > Easy)
    - Priority (High > Medium > Low)
    - Knowledge Deficit (Beginner > Intermediate > Advanced)
    - Exam Urgency (Closer exam dates receive higher multiplier)
    - Current completion status
    """
    if topic.status == "Completed":
        return 0.0

    diff_score = DIFFICULTY_SCORES.get(topic.difficulty, 2.0)
    prio_score = PRIORITY_SCORES.get(topic.priority, 2.0)
    know_score = KNOWLEDGE_DEFICIT.get(topic.knowledge_level, 2.0)
    status_factor = STATUS_WEIGHT.get(topic.status, 1.0)

    # Base score
    base_score = (diff_score * 0.3) + (prio_score * 0.4) + (know_score * 0.3)

    # Exam urgency multiplier
    urgency_multiplier = 1.0
    if topic.exam_date:
        days_until_exam = (topic.exam_date - target_date).days
        if days_until_exam <= 0:
            urgency_multiplier = 3.5
        elif days_until_exam <= 3:
            urgency_multiplier = 3.0
        elif days_until_exam <= 7:
            urgency_multiplier = 2.4
        elif days_until_exam <= 14:
            urgency_multiplier = 1.8
        elif days_until_exam <= 30:
            urgency_multiplier = 1.3
        else:
            urgency_multiplier = 1.0

    return round(base_score * urgency_multiplier * status_factor, 2)


def generate_time_slots(
    start_hour: int,
    start_minute: int,
    session_duration_minutes: int,
    break_minutes: int,
    total_study_minutes: int
) -> List[Tuple[str, str, int]]:
    """
    Generates discrete, human-readable time slots (e.g., '06:00 PM - 06:45 PM')
    accounting for pomodoro breaks and maximum study duration for the day.
    Returns: List of (formatted_start, formatted_end, duration_minutes)
    """
    slots = []
    current_minutes = start_hour * 60 + start_minute
    accumulated_study = 0

    while accumulated_study + session_duration_minutes <= total_study_minutes:
        slot_start_hour = (current_minutes // 60) % 24
        slot_start_min = current_minutes % 60

        slot_end_minutes = current_minutes + session_duration_minutes
        slot_end_hour = (slot_end_minutes // 60) % 24
        slot_end_min = slot_end_minutes % 60

        start_time_str = datetime.strptime(f"{slot_start_hour:02d}:{slot_start_min:02d}", "%H:%M").strftime("%I:%M %p")
        end_time_str = datetime.strptime(f"{slot_end_hour:02d}:{slot_end_min:02d}", "%H:%M").strftime("%I:%M %p")

        slots.append((start_time_str, end_time_str, session_duration_minutes))

        accumulated_study += session_duration_minutes
        current_minutes = slot_end_minutes + break_minutes

    return slots


def generate_balanced_study_plan(
    user_id: int,
    days_to_plan: int = 7,
    daily_study_hours: float = 3.0,
    preferred_time_preset: str = "Evening (6:00 PM - 10:00 PM)",
    custom_start_time: Optional[time] = None,
    session_duration_minutes: int = 45,
    break_minutes: int = 15,
    clear_existing_future: bool = True
) -> Dict[str, Any]:
    """
    Generates a smart, time-slot-based study schedule balancing:
    - Subject distribution (interleaving prevents mental burnout)
    - Topic difficulty and knowledge deficit
    - Exam dates and urgent deadlines
    - Available daily hours

    Persists generated study sessions into the database.
    """
    today = date.today()

    with get_db() as db:
        # Fetch user's active topics and subjects
        subjects = db.query(Subject).filter(Subject.user_id == user_id).all()
        if not subjects:
            return {"success": False, "message": "No subjects found. Please add subjects first."}

        topics = (
            db.query(Topic)
            .join(Subject)
            .filter(Subject.user_id == user_id, Topic.status != "Completed")
            .all()
        )

        if not topics:
            return {
                "success": False,
                "message": "All topics are currently completed! Add new topics or mark existing topics for revision."
            }

        # Clear existing planned sessions in the target date range if requested
        if clear_existing_future:
            db.query(StudySession).filter(
                StudySession.user_id == user_id,
                StudySession.session_date >= today,
                StudySession.status == "Planned"
            ).delete()

        # Determine start time for each day
        if custom_start_time:
            start_h, start_m = custom_start_time.hour, custom_start_time.minute
        else:
            start_h, start_m = PRESET_SLOT_TIMES.get(preferred_time_preset, (18, 0))

        daily_study_minutes = int(daily_study_hours * 60)
        daily_slots = generate_time_slots(
            start_hour=start_h,
            start_minute=start_m,
            session_duration_minutes=session_duration_minutes,
            break_minutes=break_minutes,
            total_study_minutes=daily_study_minutes
        )

        if not daily_slots:
            # Fallback to at least one 45 min slot if daily_study_minutes was too low
            daily_slots = [("06:00 PM", "06:45 PM", 45)]

        # Group topics by subject and calculate scores
        subject_topic_map: Dict[int, List[Tuple[Topic, float]]] = {}
        for topic in topics:
            score = calculate_topic_urgency_score(topic, today)
            if topic.subject_id not in subject_topic_map:
                subject_topic_map[topic.subject_id] = []
            subject_topic_map[topic.subject_id].append((topic, score))

        # Sort topics within each subject by priority score descending
        for sub_id in subject_topic_map:
            subject_topic_map[sub_id].sort(key=lambda x: x[1], reverse=True)

        active_subject_ids = list(subject_topic_map.keys())
        total_sessions_created = 0
        scheduled_sessions_info = []

        # Round-robin balanced topic assignment across days and time slots
        subject_idx = 0
        topic_pointers = {sub_id: 0 for sub_id in active_subject_ids}

        for day_offset in range(days_to_plan):
            plan_date = today + timedelta(days=day_offset)

            for slot_start, slot_end, duration in daily_slots:
                # Find the next topic to schedule using subject interleaving
                topic_to_schedule = None
                attempts = 0

                while attempts < len(active_subject_ids):
                    current_sub_id = active_subject_ids[subject_idx % len(active_subject_ids)]
                    sub_topics = subject_topic_map[current_sub_id]
                    ptr = topic_pointers[current_sub_id]

                    if sub_topics:
                        topic_to_schedule, _ = sub_topics[ptr % len(sub_topics)]
                        topic_pointers[current_sub_id] = ptr + 1
                        subject_idx += 1
                        break
                    subject_idx += 1
                    attempts += 1

                if not topic_to_schedule and topics:
                    # Fallback pick any topic
                    topic_to_schedule = topics[total_sessions_created % len(topics)]

                if topic_to_schedule:
                    new_session = StudySession(
                        user_id=user_id,
                        topic_id=topic_to_schedule.id,
                        session_date=plan_date,
                        start_time=slot_start,
                        end_time=slot_end,
                        duration_minutes=duration,
                        status="Planned",
                        notes=f"Scheduled for {topic_to_schedule.name} ({topic_to_schedule.subject.name})"
                    )
                    db.add(new_session)
                    total_sessions_created += 1

                    scheduled_sessions_info.append({
                        "date": plan_date.strftime("%Y-%m-%d"),
                        "slot": f"{slot_start} - {slot_end}",
                        "subject": topic_to_schedule.subject.name,
                        "topic": topic_to_schedule.name,
                        "difficulty": topic_to_schedule.difficulty,
                        "priority": topic_to_schedule.priority
                    })

    return {
        "success": True,
        "message": f"Successfully created {total_sessions_created} balanced study sessions across {days_to_plan} days!",
        "count": total_sessions_created,
        "sessions": scheduled_sessions_info
    }


def detect_and_reschedule_missed_sessions(user_id: int) -> Tuple[int, List[str]]:
    """
    Scans for overdue study sessions that were marked 'Planned' but whose date/time
    has passed without completion.
    Automatically reschedules them into the nearest available future slot
    without exceeding the user's daily study hours limit.

    Returns: (count_of_rescheduled, list_of_notification_messages)
    """
    today = date.today()
    now_time = datetime.now().time()
    notifications = []
    rescheduled_count = 0

    with get_db() as db:
        user = db.query(User).filter(User.id == user_id).first()
        daily_hours = user.preferred_study_hours if user else 3.0
        preferred_preset = user.preferred_study_time if user else "Evening (6:00 PM - 10:00 PM)"

        # Find all uncompleted sessions where session_date < today
        # OR session_date == today and end time has already elapsed
        past_planned = (
            db.query(StudySession)
            .filter(
                StudySession.user_id == user_id,
                StudySession.status == "Planned",
                StudySession.session_date <= today
            )
            .all()
        )

        missed_sessions: List[StudySession] = []
        for s in past_planned:
            if s.session_date < today:
                missed_sessions.append(s)
            elif s.session_date == today:
                try:
                    # Parse end_time e.g., "06:45 PM"
                    end_dt = datetime.strptime(s.end_time, "%I:%M %p").time()
                    if now_time > end_dt:
                        missed_sessions.append(s)
                except Exception:
                    pass

        if not missed_sessions:
            return 0, []

        start_h, start_m = PRESET_SLOT_TIMES.get(preferred_preset, (18, 0))
        standard_slots = generate_time_slots(
            start_hour=start_h,
            start_minute=start_m,
            session_duration_minutes=45,
            break_minutes=15,
            total_study_minutes=int(daily_hours * 60)
        )

        # For each missed session, mark it 'Missed' and find the next open future slot
        for missed in missed_sessions:
            missed.status = "Missed"
            topic = missed.topic
            topic_name = topic.name if topic else "Study Topic"
            subject_name = topic.subject.name if (topic and topic.subject) else "Subject"

            # Search future days starting from today or tomorrow
            rescheduled = False
            for day_offset in range(0, 14):
                candidate_date = today + timedelta(days=day_offset)

                # Get existing sessions on candidate_date
                existing_on_date = (
                    db.query(StudySession)
                    .filter(
                        StudySession.user_id == user_id,
                        StudySession.session_date == candidate_date,
                        StudySession.status == "Planned"
                    )
                    .all()
                )

                booked_times = {s.start_time for s in existing_on_date}
                total_duration = sum(s.duration_minutes for s in existing_on_date)

                # Check if there is room for another session
                if total_duration + missed.duration_minutes <= int(daily_hours * 60):
                    for slot_start, slot_end, dur in standard_slots:
                        if slot_start not in booked_times:
                            # Found an available slot!
                            new_session = StudySession(
                                user_id=user_id,
                                topic_id=missed.topic_id,
                                session_date=candidate_date,
                                start_time=slot_start,
                                end_time=slot_end,
                                duration_minutes=dur,
                                status="Planned",
                                rescheduled_from_id=missed.id,
                                notes=f"Auto-rescheduled from {missed.session_date}"
                            )
                            db.add(new_session)
                            rescheduled_count += 1
                            rescheduled = True

                            formatted_date = candidate_date.strftime("%b %d, %Y")
                            notifications.append(
                                f"⚠️ You missed **{topic_name}** ({subject_name}) on {missed.session_date.strftime('%b %d')}. "
                                f"Your study plan has been automatically adjusted to **{formatted_date} at {slot_start} - {slot_end}**."
                            )
                            break

                if rescheduled:
                    break

    return rescheduled_count, notifications


def complete_study_session(session_id: int, notes: str = "") -> Tuple[bool, str]:
    """
    Marks a planned study session as 'Completed' and logs the progress.
    Also updates topic progress status.
    """
    with get_db() as db:
        session = db.query(StudySession).filter(StudySession.id == session_id).first()
        if not session:
            return False, "Session not found."

        session.status = "Completed"
        if notes:
            session.notes = notes

        # Log into progress_logs
        log = ProgressLog(
            user_id=session.user_id,
            topic_id=session.topic_id,
            log_date=session.session_date,
            minutes_studied=session.duration_minutes,
            notes=notes or f"Completed scheduled session for {session.topic.name if session.topic else 'topic'}"
        )
        db.add(log)

        # Update topic status to 'In Progress' or check if completed
        if session.topic and session.topic.status == "Not Started":
            session.topic.status = "In Progress"

        return True, "Great job! Study session marked as completed."


def get_user_schedule_for_date(user_id: int, target_date: date) -> List[Dict[str, Any]]:
    """Fetches all study sessions scheduled for a particular date."""
    with get_db() as db:
        sessions = (
            db.query(StudySession)
            .filter(
                StudySession.user_id == user_id,
                StudySession.session_date == target_date
            )
            .order_by(StudySession.start_time)
            .all()
        )

        results = []
        for s in sessions:
            results.append({
                "id": s.id,
                "date": s.session_date,
                "start_time": s.start_time,
                "end_time": s.end_time,
                "duration": s.duration_minutes,
                "status": s.status,
                "notes": s.notes,
                "topic_id": s.topic_id,
                "topic_name": s.topic.name if s.topic else "General Study",
                "subject_name": s.topic.subject.name if (s.topic and s.topic.subject) else "General",
                "subject_color": s.topic.subject.color if (s.topic and s.topic.subject) else "#4F46E5",
                "difficulty": s.topic.difficulty if s.topic else "Medium",
                "priority": s.topic.priority if s.topic else "Medium",
                "rescheduled_from_id": s.rescheduled_from_id
            })
        return results

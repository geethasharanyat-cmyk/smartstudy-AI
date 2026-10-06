"""
AI Study Advice and Smart Revision Planner.
Generates personalized study tips, revision recommendations, and schedule coaching.
"""

from typing import Optional, List, Dict, Any
from ai.chatbot import get_configured_api_key, query_gemini
from analytics.progress import analyze_weak_and_strong_topics, get_progress_overview


def get_ai_study_recommendations(user_id: int, custom_api_key: Optional[str] = None) -> str:
    """
    Generates personalized study coaching advice based on the student's
    current progress, weak topics, and upcoming exam schedule.
    """
    analysis = analyze_weak_and_strong_topics(user_id)
    overview = get_progress_overview(user_id)
    weak_topics = analysis.get("weak_topics", [])
    strong_topics = analysis.get("strong_topics", [])

    weak_desc = "\n".join([f"- {w['topic_name']} ({w['subject_name']}): {w['reason']}" for w in weak_topics]) or "None identified yet!"
    strong_desc = "\n".join([f"- {s['topic_name']} ({s['subject_name']})" for s in strong_topics]) or "None completed yet."

    upcoming_exam_str = "None"
    if overview.get("upcoming_exam"):
        e = overview["upcoming_exam"]
        upcoming_exam_str = f"{e['subject_name']} - {e['topic_name']} ({e['days_left']} days left)"

    prompt = (
        "As an elite academic study coach, analyze this student's learning profile and provide 3-4 specific, actionable study recommendations:\n\n"
        f"Overall Completion: {overview.get('completion_percentage', 0)}%\n"
        f"Study Streak: {overview.get('study_streak', 0)} days\n"
        f"Upcoming Exam: {upcoming_exam_str}\n\n"
        f"Weak Topics Needing Revision:\n{weak_desc}\n\n"
        f"Strong Mastered Topics:\n{strong_desc}\n\n"
        "Provide your recommendations in an encouraging, practical bulleted format, highlighting which weak topic to prioritize and how to interleave revision."
    )

    api_key = get_configured_api_key(custom_key=custom_api_key)
    if api_key:
        try:
            return query_gemini(
                prompt=prompt,
                system_instruction="You are a warm, encouraging, top-tier academic success coach.",
                api_key=api_key
            )
        except Exception:
            pass

    # Offline intelligent response
    tips = [
        "### 🎯 Personalized Study Strategy Recommendations",
        f"- **Prioritize Urgent Topics:** Focus your highest-energy time slot on your most critical weak topic.",
        "- **Spaced Interleaving:** Alternate 45-minute blocks between challenging subjects and lighter topics.",
        "- **Active Recall:** Instead of passive re-reading, summarize key concepts from memory and solve sample problems.",
        "- **Maintain Study Streak:** Even 20-30 minutes of consistent review daily builds long-term retention far better than weekend cramming."
    ]
    if weak_topics:
        top_weak = weak_topics[0]
        tips.insert(1, f"- **Immediate Focus:** Dedicate your next study session to **{top_weak['topic_name']}** ({top_weak['subject_name']}) because: *{top_weak['reason']}*.")

    return "\n\n".join(tips)

"""
AI Study Assistant with multi-mode intelligence (Simple, Teacher, Exam),
student context awareness (weak topics, subjects, exam countdowns),
and robust Google Gemini integration with graceful offline fallbacks.
"""

import os
from typing import Dict, Any, List, Optional
from datetime import datetime
from database.models import ChatMessage, Subject, Topic
from database.db import get_db
from analytics.progress import analyze_weak_and_strong_topics, get_progress_overview


# Mode Prompts
SYSTEM_PROMPTS = {
    "Simple": (
        "You are an encouraging, friendly peer tutor for a student. "
        "Explain ideas in plain, conversational English with intuitive real-world analogies. "
        "Keep jargon to a minimum and focus on making complex concepts feel intuitive, accessible, and fun."
    ),
    "Teacher": (
        "You are an experienced, pedagogical professor. "
        "Break down concepts methodically in a structured, step-by-step curriculum format. "
        "Provide clear code/concrete examples, highlight common misunderstandings, "
        "and conclude with 1-2 quick check questions to verify the student's understanding."
    ),
    "Exam": (
        "You are an elite exam preparation coach. "
        "Provide high-yield, exam-oriented study materials:\n"
        "1. Precise Definitions & Key Terminology\n"
        "2. Core Concepts with High-Scoring Keywords\n"
        "3. Quick Revision Bullet Points\n"
        "4. Likely Exam Questions & Model Answer Hints\n"
        "Be concise, structured, and focused purely on maximizing exam performance."
    )
}


def get_student_context(user_id: int) -> str:
    """
    Builds a summary of the student's academic context to personalize AI responses.
    Includes active subjects, current weak topics needing revision, and upcoming exams.
    """
    try:
        overview = get_progress_overview(user_id)
        topic_analysis = analyze_weak_and_strong_topics(user_id)
        weak_topics = topic_analysis.get("weak_topics", [])

        lines = ["--- STUDENT ACADEMIC PROFILE & CONTEXT ---"]

        with get_db() as db:
            subjects = db.query(Subject).filter(Subject.user_id == user_id).all()
            subject_names = [s.name for s in subjects]
            if subject_names:
                lines.append(f"Enrolled Subjects: {', '.join(subject_names)}")

        if weak_topics:
            weak_strs = [f"{wt['topic_name']} ({wt['subject_name']}): {wt['reason']}" for wt in weak_topics[:4]]
            lines.append(f"Topics Needing Revision: {'; '.join(weak_strs)}")

        if overview.get("upcoming_exam"):
            exam = overview["upcoming_exam"]
            lines.append(f"Upcoming Exam: {exam['subject_name']} - {exam['topic_name']} on {exam['date']} ({exam['days_left']} days left)")

        lines.append("------------------------------------------")
        return "\n".join(lines)
    except Exception:
        return ""


def get_configured_api_key(custom_key: Optional[str] = None) -> Optional[str]:
    """Retrieves Google API key from session, custom parameter, or environment."""
    if custom_key and custom_key.strip():
        return custom_key.strip()
    key = os.getenv("GOOGLE_API_KEY", "")
    return key.strip() if key.strip() else None


def query_gemini(
    prompt: str,
    system_instruction: str,
    api_key: str,
    temperature: float = 0.7
) -> str:
    """
    Queries Google Gemini model using the official SDK.
    Supports google-genai and google-generativeai with automatic fallback.
    """
    # Try new google-genai SDK first
    try:
        from google import genai
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config={
                "system_instruction": system_instruction,
                "temperature": temperature,
            }
        )
        if response and response.text:
            return response.text
    except Exception:
        pass

    # Try google-generativeai SDK fallback
    try:
        import google.generativeai as gai
        gai.configure(api_key=api_key)
        model = gai.GenerativeModel(
            model_name="gemini-1.5-flash",
            system_instruction=system_instruction
        )
        response = model.generate_content(prompt)
        if response and response.text:
            return response.text
    except Exception as e:
        raise RuntimeError(f"Google Gemini API error: {str(e)}")

    raise RuntimeError("Unable to communicate with Google Gemini API.")


def generate_fallback_offline_response(
    query: str,
    mode: str,
    student_context: str
) -> str:
    """
    Provides a comprehensive, intelligent offline response when no Google API key is configured.
    Ensures the application never crashes and provides actionable study guidance.
    """
    header = (
        "> 💡 **SmartStudy AI Offline Mode**\n"
        "> *To unlock live Google Gemini AI answers, enter your free Google API Key in Settings or `.env`.*\n\n"
    )

    query_lower = query.lower()

    if mode == "Simple":
        body = (
            f"### Simplified Explanation for: *{query}*\n\n"
            "Here is how to think about this intuitively:\n"
            "- **Analogy:** Break the problem down into everyday concepts. Imagine a blueprint versus a built house, or a recipe versus a baked cake.\n"
            "- **The Big Picture:** Focus on *why* this concept exists before worrying about syntax or technical nuances.\n"
            "- **Quick Rule of Thumb:** Understand the input, the process, and the expected outcome.\n\n"
            "💡 *Tip:* Test your understanding by explaining this concept in your own words to someone else without using technical jargon!"
        )
    elif mode == "Teacher":
        body = (
            f"### Step-by-Step Tutorial: *{query}*\n\n"
            "**Step 1: Foundational Principles**\n"
            "Identify the prerequisite terms and definitions required to understand this topic.\n\n"
            "**Step 2: Practical Walkthrough**\n"
            "Work through a concrete example from start to finish. Observe how each component affects the next.\n\n"
            "**Step 3: Verification Question**\n"
            "- *Self-Check:* What would happen if you altered the core assumption of this concept? Can you sketch the solution from memory?\n"
        )
    else:  # Exam Mode
        body = (
            f"### Exam Revision Guide: *{query}*\n\n"
            "**1. Core Definition & Key Terminology**\n"
            "- Write down standard academic definitions. Underline high-scoring keywords.\n\n"
            "**2. Critical Exam Pitfalls**\n"
            "- Common mistake: Confusing this topic with its closest counterpart.\n"
            "- Watch out for edge cases and boundary conditions.\n\n"
            "**3. Sample Exam Question & Strategy**\n"
            "- *Question:* Define and explain the importance of this concept with a suitable diagram/example. (5 Marks)\n"
            "- *Strategy:* Start with definition (1m), diagram/code (2m), and real-world advantages (2m).\n"
        )

    return header + body


def ask_study_assistant(
    user_id: int,
    user_query: str,
    mode: str = "Simple",
    custom_api_key: Optional[str] = None,
    save_to_history: bool = True
) -> str:
    """
    Main entry point for AI study questions.
    Constructs context-aware instructions, queries Gemini (or smart fallback),
    and records the exchange in the persistent ChatMessage database table.
    """
    student_ctx = get_student_context(user_id)
    base_instruction = SYSTEM_PROMPTS.get(mode, SYSTEM_PROMPTS["Simple"])

    full_system_instruction = (
        f"{base_instruction}\n\n"
        f"You are tutoring a specific student with the following profile:\n{student_ctx}\n"
        "Reference their subjects, weak topics, or exams if directly relevant to their question to give personalized learning support."
    )

    api_key = get_configured_api_key(custom_key=custom_api_key)

    if api_key:
        try:
            ai_response = query_gemini(
                prompt=user_query,
                system_instruction=full_system_instruction,
                api_key=api_key
            )
        except Exception as e:
            # Fallback gracefully if API quota exceeded or network issue
            ai_response = (
                f"> ⚠️ *Gemini API notice: {str(e)}*\n\n"
                f"{generate_fallback_offline_response(user_query, mode, student_ctx)}"
            )
    else:
        ai_response = generate_fallback_offline_response(user_query, mode, student_ctx)

    if save_to_history:
        with get_db() as db:
            # Save user message
            db.add(ChatMessage(
                user_id=user_id,
                role="user",
                content=user_query,
                mode=mode,
                timestamp=datetime.now()
            ))
            # Save assistant message
            db.add(ChatMessage(
                user_id=user_id,
                role="assistant",
                content=ai_response,
                mode=mode,
                timestamp=datetime.now()
            ))

    return ai_response


def get_chat_history(user_id: int, limit: int = 50) -> List[Dict[str, Any]]:
    """Fetches chat message history for the specified student."""
    with get_db() as db:
        messages = (
            db.query(ChatMessage)
            .filter(ChatMessage.user_id == user_id)
            .order_by(ChatMessage.timestamp.asc())
            .limit(limit)
            .all()
        )
        return [
            {
                "id": m.id,
                "role": m.role,
                "content": m.content,
                "mode": m.mode,
                "timestamp": m.timestamp
            }
            for m in messages
        ]


def clear_chat_history(user_id: int) -> bool:
    """Deletes all chat messages for the specified student."""
    with get_db() as db:
        db.query(ChatMessage).filter(ChatMessage.user_id == user_id).delete()
        return True

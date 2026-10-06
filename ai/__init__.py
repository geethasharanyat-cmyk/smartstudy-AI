"""AI package for SmartStudy AI."""
from .chatbot import (
    ask_study_assistant,
    get_chat_history,
    clear_chat_history,
    get_student_context,
    get_configured_api_key,
    SYSTEM_PROMPTS,
)
from .document_qa import (
    ask_document_question,
    summarize_document,
    generate_exam_questions_from_doc,
)
from .planner_ai import (
    get_ai_study_recommendations,
)

__all__ = [
    "ask_study_assistant",
    "get_chat_history",
    "clear_chat_history",
    "get_student_context",
    "get_configured_api_key",
    "SYSTEM_PROMPTS",
    "ask_document_question",
    "summarize_document",
    "generate_exam_questions_from_doc",
    "get_ai_study_recommendations",
]

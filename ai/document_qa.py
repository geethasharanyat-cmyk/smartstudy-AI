"""
Document-Based Question Answering and Summarization Engine.
Uses semantic TF-IDF chunk retrieval and Google Gemini to answer questions,
summarize study materials, and generate practice exam questions.
"""

from typing import Optional, List, Dict, Any
from documents.processor import chunk_text, search_relevant_chunks
from ai.chatbot import get_configured_api_key, query_gemini
from database.models import UploadedMaterial
from database.db import get_db


def ask_document_question(
    material_id: int,
    user_query: str,
    custom_api_key: Optional[str] = None
) -> str:
    """
    Answers a question about an uploaded study material using retrieval-augmented generation.
    Retrieves the most semantically relevant text chunks before querying the model.
    """
    with get_db() as db:
        material = db.query(UploadedMaterial).filter(UploadedMaterial.id == material_id).first()
        if not material:
            return "Error: Study material not found in your account."

        text = material.extracted_text
        filename = material.filename

    if not text or not text.strip():
        return f"The uploaded file '{filename}' does not contain readable text content."

    # Chunk text
    chunks = chunk_text(text, chunk_size=800, chunk_overlap=150)
    top_matches = search_relevant_chunks(user_query, chunks, top_k=3)

    retrieved_context = "\n\n---\n\n".join([f"[Excerpt {i+1}]:\n{chunk}" for i, (chunk, _) in enumerate(top_matches)])

    prompt = (
        f"You are an AI study tutor assisting a student with their uploaded document: '{filename}'.\n\n"
        f"STUDENT QUESTION:\n{user_query}\n\n"
        f"RELEVANT DOCUMENT EXCERPTS:\n{retrieved_context}\n\n"
        "INSTRUCTIONS:\n"
        "Answer the student's question accurately using the provided document excerpts. "
        "If the document excerpts do not provide sufficient information, state what is covered and supplement with general knowledge, clearly distinguishing the two."
    )

    system_instruction = "You are an expert academic tutor answering questions about uploaded student study notes."
    api_key = get_configured_api_key(custom_key=custom_api_key)

    if api_key:
        try:
            return query_gemini(prompt=prompt, system_instruction=system_instruction, api_key=api_key)
        except Exception as e:
            return (
                f"> ⚠️ *API error: {str(e)}*\n\n"
                f"**Offline Summary based on matching document sections:**\n\n"
                f"{retrieved_context[:600]}..."
            )
    else:
        # Offline extraction response
        return (
            f"> 💡 **SmartStudy AI Document Retrieval (Offline Mode)**\n"
            f"> *Configure your Google API key to generate conversational AI synthesis.*\n\n"
            f"**Most Relevant Excerpts Found in '{filename}':**\n\n"
            f"{retrieved_context}"
        )


def summarize_document(material_id: int, custom_api_key: Optional[str] = None) -> str:
    """Generates an executive summary of the uploaded document."""
    query = "Summarize the key concepts, main topics, and essential takeaways of this document in clear study notes."
    return ask_document_question(material_id, query, custom_api_key=custom_api_key)


def generate_exam_questions_from_doc(material_id: int, custom_api_key: Optional[str] = None) -> str:
    """Generates practice exam questions (MCQs, short answer, essay) from the document."""
    query = (
        "Generate 5 high-yield practice exam questions based on this study material: "
        "2 Multiple Choice Questions (with answers explained), 2 Short Answer Questions, and 1 Conceptual Essay Question."
    )
    return ask_document_question(material_id, query, custom_api_key=custom_api_key)

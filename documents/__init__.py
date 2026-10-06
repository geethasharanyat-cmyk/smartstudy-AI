"""Document processing package for SmartStudy AI."""
from .processor import (
    process_uploaded_document,
    chunk_text,
    search_relevant_chunks,
    extract_text_from_pdf,
    extract_text_from_docx,
    extract_text_from_txt,
    extract_text_from_image,
)

__all__ = [
    "process_uploaded_document",
    "chunk_text",
    "search_relevant_chunks",
    "extract_text_from_pdf",
    "extract_text_from_docx",
    "extract_text_from_txt",
    "extract_text_from_image",
]

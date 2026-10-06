"""
Document Processing and Retrieval Engine for Study Materials.
Handles text extraction from PDF, DOCX, TXT, and Images (with OCR/vision fallback).
Provides fast TF-IDF semantic chunking and retrieval using scikit-learn.
"""

import os
import io
import re
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def extract_text_from_pdf(file_bytes: bytes) -> Tuple[bool, str]:
    """Extracts text content from PDF file bytes."""
    try:
        import pypdf
        reader = pypdf.PdfReader(io.BytesIO(file_bytes))
        text_pages = []
        for i, page in enumerate(reader.pages):
            page_text = page.extract_text()
            if page_text and page_text.strip():
                text_pages.append(f"--- Page {i+1} ---\n{page_text.strip()}")

        extracted = "\n\n".join(text_pages)
        if not extracted.strip():
            return False, "PDF appears to be scanned or contains only non-selectable images. Try uploading as an image or use OCR."
        return True, extracted
    except ImportError:
        try:
            import PyPDF2
            reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
            text_pages = [p.extract_text() for p in reader.pages if p.extract_text()]
            return True, "\n\n".join(text_pages)
        except Exception as e:
            return False, f"PDF extraction library error: {str(e)}"
    except Exception as e:
        return False, f"Failed to extract text from PDF: {str(e)}"


def extract_text_from_docx(file_bytes: bytes) -> Tuple[bool, str]:
    """Extracts text content from DOCX file bytes."""
    try:
        import docx
        doc = docx.Document(io.BytesIO(file_bytes))
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        for table in doc.tables:
            for row in table.rows:
                row_text = " | ".join(cell.text.strip() for cell in row.cells if cell.text.strip())
                if row_text:
                    paragraphs.append(row_text)

        full_text = "\n\n".join(paragraphs)
        if not full_text.strip():
            return False, "DOCX file contains no readable text."
        return True, full_text
    except ImportError:
        return False, "python-docx package is not installed."
    except Exception as e:
        return False, f"Failed to extract text from DOCX: {str(e)}"


def extract_text_from_txt(file_bytes: bytes) -> Tuple[bool, str]:
    """Extracts text from TXT or Markdown file bytes with multiple encoding fallbacks."""
    for enc in ["utf-8", "utf-8-sig", "latin-1", "cp1252"]:
        try:
            text = file_bytes.decode(enc)
            return True, text
        except (UnicodeDecodeError, LookupError):
            continue
    return False, "Could not decode text file with standard UTF-8 or Latin encodings."


def extract_text_from_image(file_bytes: bytes) -> Tuple[bool, str]:
    """
    Attempts OCR on image bytes using pytesseract or PIL fallback.
    If OCR binary is not installed, returns a helpful message.
    """
    try:
        from PIL import Image
        image = Image.open(io.BytesIO(file_bytes))

        # Check pytesseract
        try:
            import pytesseract
            text = pytesseract.image_to_string(image)
            if text and text.strip():
                return True, text.strip()
            return False, "No legible text found in image via OCR."
        except Exception:
            return True, f"[Image Uploaded: {image.format} {image.size[0]}x{image.size[1]} px. OCR tool not configured on server; visual understanding is handled during AI questions if API key is provided.]"
    except Exception as e:
        return False, f"Unable to process image file: {str(e)}"


def process_uploaded_document(
    filename: str,
    file_bytes: bytes
) -> Tuple[bool, str, str, str]:
    """
    Detects file extension and extracts readable text.
    Returns: (success, extracted_text, file_type, message)
    """
    ext = os.path.splitext(filename)[1].lower().replace(".", "")

    if ext in ["pdf"]:
        success, text = extract_text_from_pdf(file_bytes)
        return success, text if success else "", "pdf", text if not success else "PDF parsed successfully."

    elif ext in ["docx", "doc"]:
        success, text = extract_text_from_docx(file_bytes)
        return success, text if success else "", "docx", text if not success else "DOCX parsed successfully."

    elif ext in ["txt", "md", "csv", "log"]:
        success, text = extract_text_from_txt(file_bytes)
        return success, text if success else "", "txt", text if not success else "Text file parsed successfully."

    elif ext in ["png", "jpg", "jpeg", "webp", "bmp"]:
        success, text = extract_text_from_image(file_bytes)
        return success, text if success else "", "image", text if not success else "Image registered successfully."

    else:
        return False, "", "unsupported", f"Unsupported file format: '.{ext}'. Supported formats: PDF, DOCX, TXT, PNG, JPG."


def chunk_text(text: str, chunk_size: int = 700, chunk_overlap: int = 150) -> List[str]:
    """
    Splits long text into overlapping chunks suitable for semantic search and LLM context.
    Preserves sentence boundaries where possible.
    """
    if not text or len(text) <= chunk_size:
        return [text] if text else []

    paragraphs = text.split("\n\n")
    chunks = []
    current_chunk = ""

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue

        if len(current_chunk) + len(para) <= chunk_size:
            current_chunk += ("\n\n" if current_chunk else "") + para
        else:
            if current_chunk:
                chunks.append(current_chunk)

            # If the single paragraph is longer than chunk_size, split by sentences or slice
            if len(para) > chunk_size:
                sentences = re.split(r"(?<=[.!?]) +", para)
                sub_chunk = ""
                for s in sentences:
                    if len(sub_chunk) + len(s) <= chunk_size:
                        sub_chunk += (" " if sub_chunk else "") + s
                    else:
                        if sub_chunk:
                            chunks.append(sub_chunk)
                        sub_chunk = s
                if sub_chunk:
                    current_chunk = sub_chunk
                else:
                    current_chunk = ""
            else:
                current_chunk = para

    if current_chunk:
        chunks.append(current_chunk)

    return chunks


def search_relevant_chunks(
    query: str,
    chunks: List[str],
    top_k: int = 3
) -> List[Tuple[str, float]]:
    """
    Performs deterministic TF-IDF semantic retrieval over text chunks using scikit-learn.
    Returns: List of (chunk_text, similarity_score) sorted by relevance.
    """
    if not chunks:
        return []

    if len(chunks) == 1:
        return [(chunks[0], 1.0)]

    try:
        corpus = [query] + chunks
        vectorizer = TfidfVectorizer(stop_words="english", lowercase=True)
        tfidf_matrix = vectorizer.fit_transform(corpus)

        # Query vector is at index 0, chunks are 1..N
        query_vector = tfidf_matrix[0:1]
        chunk_vectors = tfidf_matrix[1:]

        similarities = cosine_similarity(query_vector, chunk_vectors).flatten()

        # Get top-k indices
        top_indices = np.argsort(similarities)[::-1][:top_k]

        results = []
        for idx in top_indices:
            score = float(similarities[idx])
            results.append((chunks[idx], round(score, 3)))

        return results
    except Exception:
        # Fallback to first few chunks if TF-IDF fails (e.g. all empty words)
        return [(c, 0.5) for c in chunks[:top_k]]

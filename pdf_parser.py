"""
pdf_parser.py

PDF text extraction utilities for the AI Resume Analyzer.
"""

from __future__ import annotations

from pathlib import Path
from typing import Union


# ============================================================
# PDF TEXT EXTRACTION
# ============================================================

def extract_text_from_pdf(
    pdf_source: Union[str, Path, bytes, bytearray],
) -> str:
    """
    Extract text from a PDF file.

    Supports:
        - file path
        - pathlib.Path
        - raw PDF bytes
        - bytearray

    Returns:
        Extracted text as a single string.
    """

    try:
        import fitz
    except ImportError as exc:
        raise ImportError(
            "PyMuPDF is required for PDF parsing. "
            "Install it with: pip install pymupdf"
        ) from exc

    document = None

    try:
        # ----------------------------------------------------
        # Open PDF
        # ----------------------------------------------------

        if isinstance(pdf_source, (bytes, bytearray)):
            document = fitz.open(
                stream=bytes(pdf_source),
                filetype="pdf",
            )

        else:
            path = Path(pdf_source)

            if not path.exists():
                raise FileNotFoundError(
                    f"PDF file not found: {path}"
                )

            document = fitz.open(str(path))

        # ----------------------------------------------------
        # Extract page text
        # ----------------------------------------------------

        pages = []

        for page_number, page in enumerate(document, start=1):
            try:
                text = page.get_text("text") or ""
            except Exception:
                text = ""

            text = text.strip()

            if text:
                pages.append(text)

        return "\n\n".join(pages).strip()    
    except FileNotFoundError:
        raise

    except Exception as exc:
        raise RuntimeError(
            f"Unable to extract text from PDF: {exc}"
        ) from exc

    finally:
        if document is not None:
            try:
                document.close()
            except Exception:
                pass


# ============================================================
# PDF VALIDATION
# ============================================================

def is_pdf_file(file_path) -> bool:
    """
    Check whether a path points to a PDF file.
    """

    try:
        return Path(file_path).suffix.lower() == ".pdf"
    except Exception:
        return False


def validate_pdf(pdf_source) -> bool:
    """
    Validate that a PDF can be opened and contains readable content.
    """

    try:
        text = extract_text_from_pdf(pdf_source)
        return bool(text.strip())

    except Exception:
        return False


# ============================================================
# PAGE-LEVEL EXTRACTION
# ============================================================

def extract_pdf_pages(pdf_source):
    """
    Return extracted text for each PDF page.

    Returns:
        List[str]
    """

    try:
        import fitz
    except ImportError as exc:
        raise ImportError(
            "PyMuPDF is required for PDF parsing. "
            "Install it with: pip install pymupdf"
        ) from exc

    document = None

    try:
        if isinstance(pdf_source, (bytes, bytearray)):
            document = fitz.open(
                stream=bytes(pdf_source),
                filetype="pdf",
            )
        else:
            path = Path(pdf_source)

            if not path.exists():
                raise FileNotFoundError(
                    f"PDF file not found: {path}"
                )

            document = fitz.open(str(path))

        pages = []

        for page in document:
            try:
                text = page.get_text("text") or ""
            except Exception:
                text = ""

            pages.append(text.strip())

        return pages

    except Exception as exc:
        raise RuntimeError(
            f"Unable to read PDF pages: {exc}"
        ) from exc

    finally:
        if document is not None:
            try:
                document.close()
            except Exception:
                pass


# ============================================================
# PDF METADATA
# ============================================================

def get_pdf_metadata(pdf_source):
    """
    Return basic PDF metadata and page count.
    """

    try:
        import fitz
    except ImportError as exc:
        raise ImportError(
            "PyMuPDF is required for PDF parsing. "
            "Install it with: pip install pymupdf"
        ) from exc

    document = None

    try:
        if isinstance(pdf_source, (bytes, bytearray)):
            document = fitz.open(
                stream=bytes(pdf_source),
                filetype="pdf",
            )
        else:
            path = Path(pdf_source)

            if not path.exists():
                raise FileNotFoundError(
                    f"PDF file not found: {path}"
                )

            document = fitz.open(str(path))

        metadata = document.metadata or {}

        return {
            "page_count": len(document),
            "title": metadata.get("title", ""),
            "author": metadata.get("author", ""),
            "subject": metadata.get("subject", ""),
            "keywords": metadata.get("keywords", ""),
            "creator": metadata.get("creator", ""),
            "producer": metadata.get("producer", ""),
        }

    except Exception as exc:
        raise RuntimeError(
            f"Unable to read PDF metadata: {exc}"
        ) from exc

    finally:
        if document is not None:
            try:
                document.close()
            except Exception:
                pass


# ============================================================
# BACKWARD-COMPATIBLE ALIASES
# ============================================================

def parse_pdf(pdf_source) -> str:
    """
    Alias for extract_text_from_pdf().
    """
    return extract_text_from_pdf(pdf_source)


def read_pdf(pdf_source) -> str:
    """
    Alias for extract_text_from_pdf().
    """
    return extract_text_from_pdf(pdf_source)


# ============================================================
# SCRIPT TEST
# ============================================================

if __name__ == "__main__":
    print("PDF parser loaded successfully.")
    print(
        "Use extract_text_from_pdf(path_or_bytes) "
        "to extract resume text."
    )

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

    Raises:
        FileNotFoundError:
            If the supplied PDF path does not exist.
        ImportError:
            If PyMuPDF is not installed.
        RuntimeError:
            If the PDF cannot be opened or processed.
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

        for page_number, page in enumerate(
            document,
            start=1,
        ):
            try:
                text = page.get_text("text") or ""
            except Exception:
                text = ""

            text = text.strip()

            if text:
                pages.append(text)

        return "\n\n".join(pages).strip()

    # --------------------------------------------------------
    # Preserve expected file-not-found error
    # --------------------------------------------------------

    except FileNotFoundError:
        raise

    # --------------------------------------------------------
    # Convert other PDF errors into RuntimeError
    # --------------------------------------------------------

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
    Return True when the supplied file has a .pdf extension.
    """

    if not file_path:
        return False

    return Path(file_path).suffix.lower() == ".pdf"


def validate_pdf(file_path) -> bool:
    """
    Validate that a PDF exists and can be opened.

    Raises:
        FileNotFoundError:
            If the file does not exist.
        ValueError:
            If the file is not a PDF or contains no pages.
        RuntimeError:
            If the PDF cannot be opened.
    """

    path = Path(file_path)

    # --------------------------------------------------------
    # Check existence
    # --------------------------------------------------------

    if not path.exists():
        raise FileNotFoundError(
            f"PDF file not found: {path}"
        )

    # --------------------------------------------------------
    # Check extension
    # --------------------------------------------------------

    if not is_pdf_file(path):
        raise ValueError(
            "The supplied file is not a PDF."
        )

    document = None

    try:
        document = fitz.open(str(path))

        if document.page_count == 0:
            raise ValueError(
                "The PDF does not contain any pages."
            )

        return True

    except FileNotFoundError:
        raise

    except ValueError:
        raise

    except Exception as exc:
        raise RuntimeError(
            f"Unable to validate PDF: {exc}"
        ) from exc

    finally:
        if document is not None:
            document.close()


# ============================================================
# TEXT EXTRACTION USING VALIDATION
# ============================================================

def extract_validated_pdf_text(file_path) -> str:
    """
    Validate a PDF and then extract its text.

    This function is useful when validation should happen
    explicitly before extraction.
    """

    path = Path(file_path)

    validate_pdf(path)

    return extract_text_from_pdf(path)


# ============================================================
# PDF PAGE EXTRACTION
# ============================================================

def extract_pdf_pages(file_path):
    """
    Extract text page by page.

    Returns:
        list[str]
    """

    path = Path(file_path)

    validate_pdf(path)

    document = fitz.open(str(path))

    try:
        pages = []

        for page in document:
            text = page.get_text("text") or ""
            pages.append(text.strip())

        return pages

    finally:
        document.close()


# ============================================================
# METADATA
# ============================================================

def get_pdf_metadata(file_path):
    """
    Return PDF metadata and page count.
    """

    path = Path(file_path)

    validate_pdf(path)

    document = fitz.open(str(path))

    try:
        metadata = document.metadata or {}

        return {
            "page_count": document.page_count,
            "title": metadata.get(
                "title",
                "",
            ),
            "author": metadata.get(
                "author",
                "",
            ),
            "subject": metadata.get(
                "subject",
                "",
            ),
            "creator": metadata.get(
                "creator",
                "",
            ),
            "producer": metadata.get(
                "producer",
                "",
            ),
        }

    finally:
        document.close()


# ============================================================
# PDF PAGE COUNT
# ============================================================

def get_page_count(file_path):
    """
    Return the number of pages in a PDF.
    """

    path = Path(file_path)

    validate_pdf(path)

    document = fitz.open(str(path))

    try:
        return document.page_count

    finally:
        document.close()


# ============================================================
# SEARCH TEXT INSIDE PDF
# ============================================================

def search_pdf(file_path, query):
    """
    Search for a phrase inside the uploaded PDF.

    Returns:
        list of dictionaries containing page numbers
        and match counts.
    """

    if not query:
        return []

    path = Path(file_path)

    validate_pdf(path)

    document = fitz.open(str(path))

    results = []

    try:
        for page_number, page in enumerate(
            document,
            start=1,
        ):
            matches = page.search_for(
                str(query)
            )

            if matches:
                results.append(
                    {
                        "page": page_number,
                        "matches": len(matches),
                    }
                )

    finally:
        document.close()

    return results


# ============================================================
# RESUME TEXT CLEANING
# ============================================================

def extract_clean_text_from_pdf(file_path):
    """
    Extract PDF text and perform light whitespace cleanup.

    This does not alter the user's actual PDF.
    """

    text = extract_text_from_pdf(
        file_path
    )

    lines = []

    for line in text.splitlines():
        line = line.strip()

        if not line:
            continue

        lines.append(line)

    return "\n".join(lines)


# ============================================================
# FILE-LIKE OBJECT / BYTES SUPPORT
# ============================================================

def extract_text_from_pdf_bytes(pdf_bytes):
    """
    Extract text directly from PDF bytes.

    Useful for Streamlit uploaded files.
    """

    if not pdf_bytes:
        return ""

    if hasattr(pdf_bytes, "read"):
        pdf_bytes = pdf_bytes.read()

    if not isinstance(
        pdf_bytes,
        (bytes, bytearray),
    ):
        raise TypeError(
            "pdf_bytes must be bytes or a file-like object."
        )

    document = fitz.open(
        stream=bytes(pdf_bytes),
        filetype="pdf",
    )

    try:
        pages = []

        for page in document:
            text = page.get_text("text") or ""

            if text:
                pages.append(
                    text.strip()
                )

        return "\n".join(
            page for page in pages
            if page
        ).strip()

    finally:
        document.close()


# ============================================================
# BACKWARD-COMPATIBLE ALIASES
# ============================================================

parse_pdf = extract_text_from_pdf

extract_pdf_text = extract_text_from_pdf

get_pdf_text = extract_text_from_pdf

read_pdf = extract_text_from_pdf
"""
Tests for pdf_parser.py
"""

from pathlib import Path

import pytest

from pdf_parser import (
    extract_text_from_pdf,
    extract_pdf_pages,
    get_pdf_metadata,
    is_pdf_file,
    validate_pdf,
)


# ============================================================
# SAMPLE PDF CREATION
# ============================================================

def create_sample_pdf(path: Path):
    """
    Create a small valid PDF for testing.
    """

    fitz = pytest.importorskip(
        "fitz"
    )

    document = fitz.open()

    page = document.new_page()

    page.insert_text(
        (72, 72),
        "AI Resume Analyzer\nPython SQL Git",
    )

    document.save(
        str(path)
    )

    document.close()


# ============================================================
# FILE TYPE
# ============================================================

def test_is_pdf_file():
    assert is_pdf_file(
        "resume.pdf"
    )

    assert is_pdf_file(
        Path("resume.pdf")
    )


def test_is_not_pdf_file():
    assert not is_pdf_file(
        "resume.docx"
    )


# ============================================================
# TEXT EXTRACTION
# ============================================================

def test_extract_text_from_pdf(
    tmp_path,
):
    pdf_path = (
        tmp_path
        / "sample.pdf"
    )

    create_sample_pdf(
        pdf_path
    )

    text = extract_text_from_pdf(
        pdf_path
    )

    assert isinstance(
        text,
        str,
    )

    assert "AI Resume Analyzer" in text
    assert "Python" in text
    assert "SQL" in text
    assert "Git" in text


def test_extract_text_from_pdf_bytes(
    tmp_path,
):
    pdf_path = (
        tmp_path
        / "sample.pdf"
    )

    create_sample_pdf(
        pdf_path
    )

    pdf_bytes = pdf_path.read_bytes()

    text = extract_text_from_pdf(
        pdf_bytes
    )

    assert isinstance(
        text,
        str,
    )

    assert "Python" in text


# ============================================================
# PAGE EXTRACTION
# ============================================================

def test_extract_pdf_pages(
    tmp_path,
):
    pdf_path = (
        tmp_path
        / "sample.pdf"
    )

    create_sample_pdf(
        pdf_path
    )

    pages = extract_pdf_pages(
        pdf_path
    )

    assert isinstance(
        pages,
        list,
    )

    assert len(pages) == 1
    assert "AI Resume Analyzer" in pages[0]


# ============================================================
# METADATA
# ============================================================

def test_get_pdf_metadata(
    tmp_path,
):
    pdf_path = (
        tmp_path
        / "sample.pdf"
    )

    create_sample_pdf(
        pdf_path
    )

    metadata = get_pdf_metadata(
        pdf_path
    )

    assert isinstance(
        metadata,
        dict,
    )

    assert metadata["page_count"] == 1


# ============================================================
# VALIDATION
# ============================================================

def test_validate_pdf_valid(
    tmp_path,
):
    pdf_path = (
        tmp_path
        / "sample.pdf"
    )

    create_sample_pdf(
        pdf_path
    )

    assert validate_pdf(
        pdf_path
    ) is True


def test_validate_pdf_missing_file(
    tmp_path,
):
    missing_path = (
        tmp_path
        / "missing.pdf"
    )

    assert validate_pdf(
        missing_path
    ) is False


# ============================================================
# INVALID INPUT
# ============================================================

def test_extract_missing_pdf_raises_error(
    tmp_path,
):
    missing_path = (
        tmp_path
        / "missing.pdf"
    )

    with pytest.raises(
        FileNotFoundError
    ):
        extract_text_from_pdf(
            missing_path
        )


def test_extract_invalid_file_raises_error(
    tmp_path,
):
    invalid_path = (
        tmp_path
        / "invalid.pdf"
    )

    invalid_path.write_text(
        "This is not a PDF.",
        encoding="utf-8",
    )

    with pytest.raises(
        RuntimeError
    ):
        extract_text_from_pdf(
            invalid_path
        )
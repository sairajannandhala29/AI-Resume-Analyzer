"""
Text Cleaning Module
--------------------

Provides safe text normalization for:

- Uploaded resumes
- Job descriptions
- ATS processing
- Skill extraction

This module does not modify the user's original resume file.
"""

import re


# ============================================================
# BASIC NORMALIZATION
# ============================================================

def normalize_whitespace(text):
    """
    Normalize repeated spaces while preserving line breaks.
    """
    if text is None:
        return ""

    text = str(text)

    text = text.replace("\r\n", "\n")
    text = text.replace("\r", "\n")

    # Normalize tabs/spaces inside individual lines.
    lines = []

    for line in text.split("\n"):
        line = re.sub(
            r"[ \t]+",
            " ",
            line,
        ).strip()

        lines.append(line)

    return "\n".join(lines)


# ============================================================
# UNICODE NORMALIZATION
# ============================================================

def normalize_unicode(text):
    """
    Normalize common Unicode punctuation and symbols.
    """
    if text is None:
        return ""

    text = str(text)

    replacements = {
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u2013": "-",
        "\u2014": "-",
        "\u2212": "-",
        "\u2022": "•",
        "\u00a0": " ",
    }

    for old, new in replacements.items():
        text = text.replace(
            old,
            new,
        )

    return text


# ============================================================
# DUPLICATE LINES
# ============================================================

def remove_duplicate_lines(text):
    """
    Remove exact duplicate non-empty lines while preserving order.
    """
    if not text:
        return ""

    seen = set()
    result = []

    for line in str(text).splitlines():
        cleaned = line.strip()

        if not cleaned:
            continue

        key = cleaned.lower()

        if key in seen:
            continue

        seen.add(key)
        result.append(cleaned)

    return "\n".join(result)


# ============================================================
# EMPTY LINES
# ============================================================

def collapse_empty_lines(
    text,
    max_consecutive=1,
):
    """
    Limit consecutive blank lines.
    """
    if not text:
        return ""

    lines = str(text).splitlines()

    result = []
    empty_count = 0

    for line in lines:
        if not line.strip():
            empty_count += 1

            if empty_count <= max_consecutive:
                result.append("")

        else:
            empty_count = 0
            result.append(
                line.rstrip()
            )

    return "\n".join(result).strip()


# ============================================================
# SYMBOL CLEANUP
# ============================================================

def normalize_bullets(text):
    """
    Normalize common bullet symbols into a standard bullet.
    """
    if not text:
        return ""

    replacements = {
        "●": "•",
        "○": "•",
        "▪": "•",
        "▫": "•",
        "◦": "•",
        "■": "•",
        "➢": "•",
        "➤": "•",
        "►": "•",
        "»": "•",
    }

    for old, new in replacements.items():
        text = str(text).replace(
            old,
            new,
        )

    return text


# ============================================================
# CONTACT / SPECIAL CHARACTER PRESERVATION
# ============================================================

def clean_special_spacing(text):
    """
    Clean spacing around common punctuation without changing
    the actual factual content.
    """
    if not text:
        return ""

    text = str(text)

    # Remove accidental spaces before punctuation.
    text = re.sub(
        r"\s+([,.;:!?])",
        r"\1",
        text,
    )

    # Normalize spaces after punctuation.
    text = re.sub(
        r"([,.;:!?])([A-Za-z])",
        r"\1 \2",
        text,
    )

    # Keep common separators readable.
    text = re.sub(
        r"\s*\|\s*",
        " | ",
        text,
    )

    return text


# ============================================================
# GENERAL CLEANING
# ============================================================

def clean_text(text):
    """
    Perform conservative text cleaning.

    The goal is to improve parser/ATS consistency without
    changing factual information.
    """
    if text is None:
        return ""

    text = str(text)

    text = normalize_unicode(
        text
    )

    text = normalize_bullets(
        text
    )

    text = normalize_whitespace(
        text
    )

    text = clean_special_spacing(
        text
    )

    text = collapse_empty_lines(
        text,
        max_consecutive=1,
    )

    return text.strip()


# ============================================================
# RESUME-SPECIFIC CLEANING
# ============================================================

def clean_resume_text(text):
    """
    Clean extracted resume text conservatively.
    """
    if not text:
        return ""

    cleaned = clean_text(
        text
    )

    return cleaned


# ============================================================
# JOB DESCRIPTION CLEANING
# ============================================================

def clean_job_description(text):
    """
    Clean a pasted job description.
    """
    if not text:
        return ""

    cleaned = clean_text(
        text
    )

    return cleaned


# ============================================================
# LINE EXTRACTION
# ============================================================

def get_clean_lines(text):
    """
    Return cleaned non-empty lines.
    """
    cleaned = clean_text(
        text
    )

    return [
        line.strip()
        for line in cleaned.splitlines()
        if line.strip()
    ]


# ============================================================
# WORD NORMALIZATION
# ============================================================

def normalize_words(text):
    """
    Convert text into normalized word tokens.

    Useful for keyword comparison.
    """
    if not text:
        return []

    cleaned = clean_text(
        text
    ).lower()

    return re.findall(
        r"[a-zA-Z0-9+#./-]+",
        cleaned,
    )


# ============================================================
# TEXT STATISTICS
# ============================================================

def get_text_statistics(text):
    """
    Return basic statistics for supplied text.
    """
    cleaned = clean_text(
        text
    )

    words = normalize_words(
        cleaned
    )

    lines = get_clean_lines(
        cleaned
    )

    return {
        "characters": len(cleaned),
        "words": len(words),
        "lines": len(lines),
    }


# ============================================================
# EMAIL EXTRACTION
# ============================================================

def extract_emails(text):
    """
    Extract email addresses.
    """
    if not text:
        return []

    pattern = (
        r"\b[A-Za-z0-9._%+-]+"
        r"@[A-Za-z0-9.-]+\."
        r"[A-Za-z]{2,}\b"
    )

    return list(
        dict.fromkeys(
            re.findall(
                pattern,
                str(text),
            )
        )
    )


# ============================================================
# PHONE EXTRACTION
# ============================================================

def extract_phone_numbers(text):
    """
    Extract common phone-number formats.

    This is deliberately conservative.
    """
    if not text:
        return []

    pattern = (
        r"(?<!\d)"
        r"(?:\+?\d{1,3}[\s.-]?)?"
        r"(?:\d{3}[\s.-]?)"
        r"\d{3}[\s.-]?"
        r"\d{4}"
        r"(?!\d)"
    )

    matches = re.findall(
        pattern,
        str(text),
    )

    return [
        match.strip()
        for match in dict.fromkeys(matches)
        if len(re.sub(r"\D", "", match)) >= 10
    ]


# ============================================================
# URL EXTRACTION
# ============================================================

def extract_urls(text):
    """
    Extract URLs.
    """
    if not text:
        return []

    pattern = (
        r"\b(?:https?://|www\.)"
        r"[^\s<>()]+"
    )

    return list(
        dict.fromkeys(
            re.findall(
                pattern,
                str(text),
                flags=re.IGNORECASE,
            )
        )
    )


# ============================================================
# DATE EXTRACTION
# ============================================================

def extract_dates(text):
    """
    Extract common resume/JD date formats.
    """
    if not text:
        return []

    patterns = [
        r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b",
        r"\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b",
        r"\b(?:Jan|January|Feb|February|Mar|March|Apr|April|May|"
        r"Jun|June|Jul|July|Aug|August|Sep|September|Oct|October|"
        r"Nov|November|Dec|December)\s+\d{4}\b",
        r"\b\d{4}\s*[-–]\s*(?:Present|\d{4})\b",
        r"\b(?:Present|Current)\b",
    ]

    results = []

    for pattern in patterns:
        results.extend(
            re.findall(
                pattern,
                str(text),
                flags=re.IGNORECASE,
            )
        )

    return list(
        dict.fromkeys(
            item.strip()
            for item in results
        )
    )


# ============================================================
# YEAR EXTRACTION
# ============================================================

def extract_years(text):
    """
    Extract four-digit years.
    """
    if not text:
        return []

    years = re.findall(
        r"\b(?:19|20)\d{2}\b",
        str(text),
    )

    return list(
        dict.fromkeys(
            years
        )
    )


# ============================================================
# SENTENCE CLEANING
# ============================================================

def clean_sentences(text):
    """
    Clean individual sentences while preserving wording.
    """
    if not text:
        return ""

    cleaned = clean_text(
        text
    )

    cleaned = re.sub(
        r"\s+",
        " ",
        cleaned,
    )

    return cleaned.strip()


# ============================================================
# ATS-FRIENDLY NORMALIZATION
# ============================================================

def prepare_for_ats(text):
    """
    Prepare text for ATS analysis.

    This is used for analysis only and never changes the
    original uploaded resume file.
    """
    if not text:
        return ""

    text = normalize_unicode(
        text
    )

    text = normalize_bullets(
        text
    )

    text = normalize_whitespace(
        text
    )

    text = collapse_empty_lines(
        text,
        max_consecutive=1,
    )

    return text.strip()


# ============================================================
# BACKWARD-COMPATIBLE ALIASES
# ============================================================

normalize_text = clean_text

clean = clean_text

sanitize_text = clean_text

clean_resume = clean_resume_text

clean_jd = clean_job_description
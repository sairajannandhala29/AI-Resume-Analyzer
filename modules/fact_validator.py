"""
fact_validator.py

Validates AI-generated resume content against the original resume.

Purpose:
- Detect unsupported skills
- Detect unsupported numbers
- Detect unsupported years/dates
- Detect unsupported factual terms
- Measure textual overlap
- Prevent the AI optimizer from silently inventing candidate facts

Important:
This validator is intentionally conservative. It flags potentially
unsupported additions so the application can ask the user to review
them rather than treating invented information as fact.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Set


# ============================================================
# CONFIGURATION
# ============================================================

MIN_TEXT_OVERLAP = 0.35


# ============================================================
# KNOWN TERMINOLOGY EQUIVALENCES
# ============================================================

TERM_EQUIVALENCES = {
    "git": {
        "git",
        "version control",
    },
    "version control": {
        "git",
        "version control",
    },
    "javascript": {
        "javascript",
        "js",
    },
    "js": {
        "javascript",
        "js",
    },
    "typescript": {
        "typescript",
        "ts",
    },
    "ts": {
        "typescript",
        "ts",
    },
    "postgresql": {
        "postgresql",
        "postgres",
    },
    "postgres": {
        "postgresql",
        "postgres",
    },
    "sql server": {
        "sql server",
        "mssql",
        "microsoft sql server",
    },
    "mssql": {
        "sql server",
        "mssql",
        "microsoft sql server",
    },
    "machine learning": {
        "machine learning",
        "ml",
    },
    "ml": {
        "machine learning",
        "ml",
    },
    "artificial intelligence": {
        "artificial intelligence",
        "ai",
    },
    "ai": {
        "artificial intelligence",
        "ai",
    },
    "natural language processing": {
        "natural language processing",
        "nlp",
    },
    "nlp": {
        "natural language processing",
        "nlp",
    },
    "object-oriented programming": {
        "object-oriented programming",
        "object oriented programming",
        "oop",
    },
    "oop": {
        "object-oriented programming",
        "object oriented programming",
        "oop",
    },
    "rest api": {
        "rest api",
        "restful api",
    },
    "restful api": {
        "rest api",
        "restful api",
    },
    "html": {
        "html",
        "html5",
    },
    "css": {
        "css",
        "css3",
    },
    "react": {
        "react",
        "reactjs",
        "react.js",
    },
    "node.js": {
        "node.js",
        "nodejs",
        "node js",
    },
    "excel": {
        "excel",
        "microsoft excel",
    },
    "power bi": {
        "power bi",
        "powerbi",
    },
    "aws": {
        "aws",
        "amazon web services",
    },
    "azure": {
        "azure",
        "microsoft azure",
    },
    "gcp": {
        "gcp",
        "google cloud",
        "google cloud platform",
    },
    "scikit-learn": {
        "scikit-learn",
        "scikit learn",
        "sklearn",
    },
}


# ============================================================
# BASIC TEXT UTILITIES
# ============================================================

def normalize_text(text: Any) -> str:
    """
    Normalize text for comparison.
    """

    if text is None:
        return ""

    text = str(text)

    text = text.replace("\u00a0", " ")
    text = text.replace("–", "-")
    text = text.replace("—", "-")
    text = text.replace("−", "-")
    text = text.replace("“", '"')
    text = text.replace("”", '"')
    text = text.replace("‘", "'")
    text = text.replace("’", "'")

    text = re.sub(
        r"\s+",
        " ",
        text,
    )

    return text.strip().lower()


def tokenize(text: str) -> Set[str]:
    """
    Create a set of meaningful lowercase tokens.
    """

    text = normalize_text(text)

    if not text:
        return set()

    tokens = re.findall(
        r"[a-zA-Z0-9]+(?:[+#./-][a-zA-Z0-9+#./-]+)*",
        text,
    )

    return {
        token.lower()
        for token in tokens
        if token.strip()
    }


def _clean_list(value) -> List[str]:
    """
    Convert supported values into a flat list of strings.
    """

    if value is None:
        return []

    if isinstance(value, str):
        return [
            line.strip()
            for line in value.splitlines()
            if line.strip()
        ]

    if isinstance(value, dict):
        result = []

        for item in value.values():
            result.extend(
                _clean_list(item)
            )

        return result

    if isinstance(value, (list, tuple, set)):
        result = []

        for item in value:
            if isinstance(item, dict):
                result.extend(
                    _clean_list(item)
                )
            else:
                text = str(item).strip()

                if text:
                    result.append(text)

        return result

    return [str(value).strip()]


# ============================================================
# TERM MATCHING
# ============================================================

def normalize_term(term: str) -> str:
    """
    Normalize a term for equivalence checking.
    """

    term = normalize_text(term)

    term = re.sub(
        r"\s+",
        " ",
        term,
    )

    return term.strip()


def terms_equivalent(
    first: str,
    second: str,
) -> bool:
    """
    Return True when two terms are the same or a known equivalent.
    """

    a = normalize_term(first)
    b = normalize_term(second)

    if not a or not b:
        return False

    if a == b:
        return True

    if b in TERM_EQUIVALENCES.get(a, set()):
        return True

    if a in TERM_EQUIVALENCES.get(b, set()):
        return True

    return False


def term_present(
    text: str,
    term: str,
) -> bool:
    """
    Determine whether a meaningful term exists in text.
    """

    text = normalize_text(text)
    term = normalize_term(term)

    if not text or not term:
        return False

    variants = TERM_EQUIVALENCES.get(
        term,
        {term},
    )

    for variant in variants:
        escaped = re.escape(
            normalize_term(variant)
        )

        escaped = escaped.replace(
            r"\ ",
            r"\s+",
        )

        pattern = (
            rf"(?<![a-z0-9])"
            rf"{escaped}"
            rf"(?![a-z0-9])"
        )

        if re.search(
            pattern,
            text,
            flags=re.IGNORECASE,
        ):
            return True

    return False


# ============================================================
# NUMBER VALIDATION
# ============================================================

def extract_numbers(text: str) -> List[str]:
    """
    Extract numbers that may represent metrics, quantities,
    percentages, versions, or other factual information.
    """

    if not text:
        return []

    return re.findall(
        r"(?<![A-Za-z])"
        r"\d+(?:[.,]\d+)?"
        r"%?"
        r"(?![A-Za-z])",
        str(text),
    )


def extract_years(text: str) -> List[str]:
    """
    Extract four-digit years.
    """

    if not text:
        return []

    return re.findall(
        r"\b(?:19|20)\d{2}\b",
        str(text),
    )


def extract_dates(text: str) -> List[str]:
    """
    Extract common date representations.
    """

    if not text:
        return []

    patterns = [
        r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b",
        r"\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b",
        r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|"
        r"Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}\b",
        r"\b(?:January|February|March|April|May|June|"
        r"July|August|September|October|November|December)"
        r"\s+\d{4}\b",
    ]

    found = []

    for pattern in patterns:
        found.extend(
            re.findall(
                pattern,
                text,
                flags=re.IGNORECASE,
            )
        )

    return list(
        dict.fromkeys(found)
    )


# ============================================================
# SKILL VALIDATION
# ============================================================

def extract_supported_skills(
    text: str,
) -> List[str]:
    """
    Extract known skills using the project's skill extractor.
    """

    try:
        from modules.skill_extractor import extract_skills

        result = extract_skills(text)

        return [
            str(skill).strip()
            for skill in result
            if str(skill).strip()
        ]

    except Exception:
        return []


def find_unsupported_skills(
    original_text: str,
    generated_text: str,
) -> List[str]:
    """
    Find known skills in generated text that do not appear in the
    original resume, while honoring supported terminology equivalences.
    """

    original_skills = extract_supported_skills(
        original_text
    )

    generated_skills = extract_supported_skills(
        generated_text
    )

    unsupported = []

    for generated_skill in generated_skills:
        found = any(
            terms_equivalent(
                generated_skill,
                original_skill,
            )
            for original_skill in original_skills
        )

        if not found:
            unsupported.append(
                generated_skill
            )

    return list(
        dict.fromkeys(unsupported)
    )


# ============================================================
# NUMBER VALIDATION
# ============================================================

def find_unsupported_numbers(
    original_text: str,
    generated_text: str,
) -> List[str]:
    """
    Find numbers present in generated text but not in the original.
    """

    original_numbers = set(
        extract_numbers(original_text)
    )

    generated_numbers = extract_numbers(
        generated_text
    )

    unsupported = [
        number
        for number in generated_numbers
        if number not in original_numbers
    ]

    return list(
        dict.fromkeys(unsupported)
    )


# ============================================================
# YEAR VALIDATION
# ============================================================

def find_unsupported_years(
    original_text: str,
    generated_text: str,
) -> List[str]:
    """
    Find years present in generated content but absent from
    the original resume.
    """

    original_years = set(
        extract_years(original_text)
    )

    generated_years = extract_years(
        generated_text
    )

    unsupported = [
        year
        for year in generated_years
        if year not in original_years
    ]

    return list(
        dict.fromkeys(unsupported)
    )


# ============================================================
# DATE VALIDATION
# ============================================================

def find_unsupported_dates(
    original_text: str,
    generated_text: str,
) -> List[str]:
    """
    Find date strings that occur in generated content but are
    not represented in the original content.
    """

    original_dates = {
        normalize_term(date)
        for date in extract_dates(
            original_text
        )
    }

    generated_dates = extract_dates(
        generated_text
    )

    unsupported = []

    for date in generated_dates:
        if normalize_term(date) not in original_dates:
            unsupported.append(date)

    return list(
        dict.fromkeys(unsupported)
    )


# ============================================================
# TEXT OVERLAP
# ============================================================

def calculate_text_overlap(
    original_text: str,
    generated_text: str,
) -> float:
    """
    Calculate basic lexical overlap.

    The denominator is the unique-token count of the original
    resume.
    """

    original_tokens = tokenize(
        original_text
    )

    generated_tokens = tokenize(
        generated_text
    )

    if not original_tokens:
        return 0.0

    overlap = (
        original_tokens
        .intersection(
            generated_tokens
        )
    )

    return round(
        len(overlap)
        / len(original_tokens)
        * 100,
        2,
    )


# ============================================================
# CRITICAL FACT CHECKS
# ============================================================

def validate_company_names(
    original_text: str,
    generated_text: str,
) -> List[str]:
    """
    Perform a conservative check for likely company-name changes.

    This function intentionally focuses on obvious labeled lines
    rather than attempting full entity recognition.
    """

    original_lower = normalize_text(
        original_text
    )

    generated_lower = normalize_text(
        generated_text
    )

    labels = [
        "company:",
        "employer:",
        "organization:",
        "organisation:",
    ]

    original_values = []

    for label in labels:
        for match in re.finditer(
            re.escape(label)
            + r"\s*([^\n|]+)",
            original_lower,
            flags=re.IGNORECASE,
        ):
            value = match.group(1).strip()

            if value:
                original_values.append(
                    value
                )

    unsupported = []

    for label in labels:
        for match in re.finditer(
            re.escape(label)
            + r"\s*([^\n|]+)",
            generated_lower,
            flags=re.IGNORECASE,
        ):
            value = match.group(1).strip()

            if value and value not in original_values:
                unsupported.append(value)

    return list(
        dict.fromkeys(unsupported)
    )


# ============================================================
# ENTITY-LIKE FACT CHECK
# ============================================================

def find_new_capitalized_terms(
    original_text: str,
    generated_text: str,
) -> List[str]:
    """
    Identify potentially new multi-word named entities.

    This is a conservative warning signal, not a definitive
    entity detector.
    """

    original_terms = set(
        re.findall(
            r"\b[A-Z][A-Za-z0-9&.-]+"
            r"(?:\s+[A-Z][A-Za-z0-9&.-]+){1,3}\b",
            original_text or "",
        )
    )

    generated_terms = set(
        re.findall(
            r"\b[A-Z][A-Za-z0-9&.-]+"
            r"(?:\s+[A-Z][A-Za-z0-9&.-]+){1,3}\b",
            generated_text or "",
        )
    )

    new_terms = [
        term
        for term in generated_terms
        if term not in original_terms
    ]

    return sorted(
        set(new_terms)
    )


# ============================================================
# MAIN VALIDATOR
# ============================================================

def validate_generated_resume(
    original_text: str,
    generated_text: str,
) -> Dict[str, Any]:
    """
    Validate generated resume content against the original resume.

    Returns a detailed validation dictionary used by the optimizer
    and Streamlit application.
    """

    original_text = str(
        original_text or ""
    ).strip()

    generated_text = str(
        generated_text or ""
    ).strip()

    if not original_text:
        raise ValueError(
            "Original resume text cannot be empty."
        )

    if not generated_text:
        raise ValueError(
            "Generated resume text cannot be empty."
        )

    unsupported_skills = (
        find_unsupported_skills(
            original_text,
            generated_text,
        )
    )

    unsupported_numbers = (
        find_unsupported_numbers(
            original_text,
            generated_text,
        )
    )

    unsupported_years = (
        find_unsupported_years(
            original_text,
            generated_text,
        )
    )

    unsupported_dates = (
        find_unsupported_dates(
            original_text,
            generated_text,
        )
    )

    unsupported_companies = (
        validate_company_names(
            original_text,
            generated_text,
        )
    )

    new_named_terms = (
        find_new_capitalized_terms(
            original_text,
            generated_text,
        )
    )

    overlap = calculate_text_overlap(
        original_text,
        generated_text,
    )

    warnings = []

    if unsupported_skills:
        warnings.append(
            "Potentially unsupported skills detected: "
            + ", ".join(
                unsupported_skills
            )
        )

    if unsupported_numbers:
        warnings.append(
            "Potentially unsupported numbers detected: "
            + ", ".join(
                unsupported_numbers
            )
        )

    if unsupported_years:
        warnings.append(
            "Potentially unsupported years detected: "
            + ", ".join(
                unsupported_years
            )
        )

    if unsupported_dates:
        warnings.append(
            "Potentially unsupported dates detected: "
            + ", ".join(
                unsupported_dates
            )
        )

    if unsupported_companies:
        warnings.append(
            "Potentially changed company/employer values detected."
        )

    # Very low overlap is a warning, but not automatically invalid.
    if overlap < MIN_TEXT_OVERLAP * 100:
        warnings.append(
            "Generated text has relatively low lexical overlap "
            "with the original resume and should be reviewed."
        )

    valid = not (
        unsupported_skills
        or unsupported_numbers
        or unsupported_years
        or unsupported_dates
        or unsupported_companies
    )

    return {
        "valid": valid,
        "text_overlap": overlap,
        "unsupported_skills": unsupported_skills,
        "unsupported_numbers": unsupported_numbers,
        "unsupported_years": unsupported_years,
        "unsupported_dates": unsupported_dates,
        "unsupported_companies": unsupported_companies,
        "new_named_terms": new_named_terms,
        "warnings": warnings,
    }


# ============================================================
# SIMPLE VALIDATION
# ============================================================

def is_valid_generated_resume(
    original_text: str,
    generated_text: str,
) -> bool:
    """
    Return True when no major unsupported facts are detected.
    """

    result = validate_generated_resume(
        original_text,
        generated_text,
    )

    return bool(
        result.get(
            "valid",
            False,
        )
    )


# ============================================================
# BACKWARD-COMPATIBLE ALIASES
# ============================================================

def validate_resume(
    original_text: str,
    generated_text: str,
):
    """
    Alias for validate_generated_resume().
    """

    return validate_generated_resume(
        original_text,
        generated_text,
    )


def check_factuality(
    original_text: str,
    generated_text: str,
):
    """
    Alias for validate_generated_resume().
    """

    return validate_generated_resume(
        original_text,
        generated_text,
    )


# ============================================================
# SCRIPT TEST
# ============================================================

if __name__ == "__main__":

    original = """
    Sai Rajan Nandhala
    Python Developer

    Skills:
    Python, SQL, Git

    Experience:
    Worked on CRM implementation and debugging.
    """

    generated = """
    Sai Rajan Nandhala
    Python Developer

    Skills:
    Python, SQL, Git, AWS

    Experience:
    Worked on CRM implementation and debugging.
    Managed AWS deployments for 5 clients.
    """

    result = validate_generated_resume(
        original,
        generated,
    )

    print("Validation result:")
    print(
        f"Valid: {result['valid']}"
    )

    print(
        f"Text overlap: {result['text_overlap']}%"
    )

    print(
        "Unsupported skills:",
        result["unsupported_skills"],
    )

    print(
        "Unsupported numbers:",
        result["unsupported_numbers"],
    )

    print(
        "Warnings:"
    )

    for warning in result["warnings"]:
        print(
            f"- {warning}"
        )
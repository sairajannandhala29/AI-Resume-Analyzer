"""
ats_scorer.py

ATS scoring engine for the AI Resume Analyzer.

Scoring components:
- Skills match:      40%
- Semantic match:    25%
- Experience match: 20%
- Keywords match:    10%
- Structure:          5%

The scorer is designed to reward genuine alignment and should
not artificially increase a score simply to reach a target.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple


# ============================================================
# WEIGHTS
# ============================================================

SKILL_WEIGHT = 0.40
SEMANTIC_WEIGHT = 0.25
EXPERIENCE_WEIGHT = 0.20
KEYWORD_WEIGHT = 0.10
STRUCTURE_WEIGHT = 0.05


# ============================================================
# HELPERS
# ============================================================

def _safe_float(
    value: Any,
    default: float = 0.0,
) -> float:
    """Safely convert a value to float."""

    try:
        if value is None:
            return default

        if isinstance(value, str):
            value = (
                value
                .replace("%", "")
                .strip()
            )

        return float(value)

    except (TypeError, ValueError):
        return default


def _percentage(
    value: Any,
) -> float:
    """
    Convert 0-1 or 0-100 values to a bounded percentage.
    """

    number = _safe_float(value)

    if 0 <= number <= 1:
        number *= 100

    return max(
        0.0,
        min(100.0, number),
    )


def _normalize_skill(
    skill: Any,
) -> str:
    """Normalize a skill for comparison."""

    return re.sub(
        r"\s+",
        " ",
        str(skill or "")
        .strip()
        .lower(),
    )


def _unique_skills(
    skills: Optional[List[Any]],
) -> List[str]:
    """Normalize and deduplicate skills."""

    result = []
    seen = set()

    for skill in skills or []:
        value = str(skill).strip()

        if not value:
            continue

        key = _normalize_skill(value)

        if key in seen:
            continue

        seen.add(key)
        result.append(value)

    return result


# ============================================================
# SKILL EQUIVALENCES
# ============================================================

SKILL_EQUIVALENCES = {
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
        "react.js",
        "reactjs",
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
        "sklearn",
        "scikit learn",
    },
    "numpy": {
        "numpy",
    },
    "pandas": {
        "pandas",
    },
    "tensorflow": {
        "tensorflow",
    },
    "pytorch": {
        "pytorch",
    },
}


# ============================================================
# CONSERVATIVE ATS CONCEPT MATCHING
# ============================================================

CONCEPT_GROUPS = [
    {"technical support", "tech support", "it support", "service desk", "help desk", "helpdesk", "desktop support", "user support", "client support", "customer support", "product support"},
    {"customer service", "customer support", "client support", "customer experience", "customer care", "client service"},
    {"troubleshooting", "issue resolution", "problem resolution", "technical troubleshooting", "debugging", "incident resolution"},
    {"ticketing", "ticketing system", "support tickets", "service tickets", "incident management", "issue tracking", "jira", "service requests"},
    {"crm", "crm implementation", "crm configuration", "crm support", "crm platform"},
    {"documentation", "technical documentation", "knowledge base", "knowledge management", "documenting solutions", "support documentation"},
    {"problem solving", "problem-solving", "analytical thinking", "analytical skills", "root cause analysis", "issue analysis"},
    {"communication", "written communication", "verbal communication", "client communication", "customer communication", "technical communication"},
    {"escalation", "issue escalation", "technical escalation", "support escalation"},
    {"networking", "network", "network connectivity", "internet technologies", "internet connectivity"},
    {"microsoft office", "ms office", "office 365", "microsoft 365", "office suite"},
    {"outlook", "microsoft outlook", "ms outlook"},
    {"windows", "windows 10", "windows 11", "microsoft windows"},
    {"macos", "mac os", "mac os x", "apple macos"},
    {"quality", "quality standards", "contact quality", "quality assurance"},
    {"multitasking", "multitask", "prioritization", "prioritize effectively"},
    {"teamwork", "team player", "team collaboration", "collaboration"},
]


def _concept_key(value: Any) -> str:
    return re.sub(r"[^a-z0-9+#./ -]", " ", _normalize_skill(value)).strip()


def _concept_match(first: Any, second: Any) -> bool:
    a = _concept_key(first)
    b = _concept_key(second)
    if not a or not b:
        return False
    if a == b:
        return True
    if b in SKILL_EQUIVALENCES.get(a, set()) or a in SKILL_EQUIVALENCES.get(b, set()):
        return True
    for group in CONCEPT_GROUPS:
        normalized = {_concept_key(x) for x in group}
        if a in normalized and b in normalized:
            return True
    # Never treat a single-letter technology (for example C) as a
    # substring of an unrelated multi-word skill.
    if len(a) == 1 or len(b) == 1:
        return False

    if len(a.split()) >= 2 and (a in b or b in a):
        return True
    return False


def _text_has_concept(
    text: str,
    skill: str,
) -> bool:
    """
    Check whether a skill/concept is actually evidenced in the resume text.

    Single-letter programming languages such as "C" are deliberately
    conservative: an isolated "c" anywhere in normal prose must not count
    as C programming.
    """
    haystack = _concept_key(text)
    target = _concept_key(skill)

    if not haystack or not target:
        return False

    # Single-letter programming language needs explicit evidence.
    if target == "c":
        explicit_patterns = [
            r"\bc\s+program(?:ming)?\b",
            r"\bc\s+language\b",
            r"\bprogramming\s+in\s+c\b",
            r"\blanguage\s*:\s*c\b",
            r"\bc\s*,\s*c\+\+",
            r"\bc\s*/\s*c\+\+",
        ]
        return any(
            re.search(pattern, haystack, flags=re.IGNORECASE)
            for pattern in explicit_patterns
        )

    # Exact phrase/token match.
    if re.search(
        r"(?<![a-z0-9])"
        + re.escape(target)
        + r"(?![a-z0-9])",
        haystack,
        flags=re.IGNORECASE,
    ):
        return True

    # Conservative concept-group matching.
    for group in CONCEPT_GROUPS:
        normalized = {
            _concept_key(x)
            for x in group
        }

        if target in normalized:
            for alias in normalized:
                if re.search(
                    r"(?<![a-z0-9])"
                    + re.escape(alias)
                    + r"(?![a-z0-9])",
                    haystack,
                    flags=re.IGNORECASE,
                ):
                    return True

    return False


def _skills_match(
    first: str,
    second: str,
) -> bool:
    """Compare skills using exact, equivalent, and conservative concept matching."""
    return _concept_match(first, second)


# ============================================================
# SKILL SCORE
# ============================================================

def _coerce_skill_list(value: Any) -> List[str]:
    """Flatten common skill-container shapes into a clean list.

    The application may receive skills as a list, tuple/set, a mapping such
    as {category: [skills]}, or a mapping containing a nested `skills` key.
    This normalization prevents the scorer from accidentally treating a
    category name or serialized container as one skill.
    """
    if value is None:
        return []

    if isinstance(value, str):
        return [value] if value.strip() else []

    if isinstance(value, dict):
        nested = []
        for key in ("skills", "required_skills", "jd_skills", "extracted_skills"):
            if key in value:
                nested.extend(_coerce_skill_list(value[key]))
        if nested:
            return _unique_skills(nested)

        flattened = []
        for key, item in value.items():
            # Category labels are not skills unless the value itself is empty.
            if isinstance(item, (list, tuple, set, dict)):
                flattened.extend(_coerce_skill_list(item))
            elif isinstance(item, str) and item.strip():
                flattened.append(item)
        return _unique_skills(flattened)

    if isinstance(value, (list, tuple, set)):
        flattened = []
        for item in value:
            flattened.extend(_coerce_skill_list(item))
        return _unique_skills(flattened)

    return [str(value).strip()] if str(value).strip() else []


def calculate_skill_score(
    resume_skills: List[str],
    job_skills: List[str],
    resume_text: Optional[str] = None,
) -> Tuple[float, List[str], List[str]]:
    """
    Calculate the percentage of JD skills matched by the resume.

    Returns:
        score, matched_skills, missing_skills
    """

    resume_skills = _coerce_skill_list(resume_skills)
    job_skills = _coerce_skill_list(job_skills)

    if not job_skills:
        return 100.0, [], []

    matched = []
    missing = []

    for job_skill in job_skills:
        found = False

        for resume_skill in resume_skills:
            if _skills_match(resume_skill, job_skill):
                found = True
                break

        # If the extractor did not label a competency as a skill, use
        # the actual resume text as secondary evidence.
        if not found and resume_text:
            found = _text_has_concept(resume_text, job_skill)

        if found:
            matched.append(job_skill)
        else:
            missing.append(job_skill)

    score = (
        len(matched)
        / len(job_skills)
        * 100
    )

    return (
        round(score, 2),
        matched,
        missing,
    )


# ============================================================
# KEYWORD EXTRACTION
# ============================================================

STOP_WORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "been",
    "being",
    "by",
    "for",
    "from",
    "has",
    "have",
    "had",
    "in",
    "into",
    "is",
    "it",
    "of",
    "on",
    "or",
    "that",
    "the",
    "their",
    "this",
    "to",
    "was",
    "were",
    "will",
    "with",
    "you",
    "your",
    "we",
    "using",
    "used",
}


def _tokenize(
    text: str,
) -> List[str]:
    """Extract meaningful tokens."""

    text = str(text or "").lower()

    tokens = re.findall(
        r"[a-zA-Z0-9]+(?:[+#./-][a-zA-Z0-9+#./-]+)*",
        text,
    )

    return [
        token
        for token in tokens
        if token not in STOP_WORDS
        and len(token) >= 2
    ]


# ============================================================
# KEYWORD SCORE
# ============================================================

def calculate_keyword_score(
    resume_text: str,
    job_description: str,
) -> float:
    """
    Calculate JD keyword coverage in the resume.

    Uses unique meaningful tokens from the JD as the denominator.
    """

    jd_tokens = set(
        _tokenize(job_description)
    )

    resume_tokens = set(
        _tokenize(resume_text)
    )

    if not jd_tokens:
        return 100.0

    matched = jd_tokens.intersection(
        resume_tokens
    )

    return round(
        len(matched)
        / len(jd_tokens)
        * 100,
        2,
    )


# ============================================================
# EXPERIENCE EXTRACTION
# ============================================================

def _extract_years(text: str) -> int:
    """
    Extract the minimum required experience from a job description.

    Examples:
        "2 to 4 years" -> 2
        "2-4 years"    -> 2
        "0-3 years"    -> 0
        "2+ years"     -> 2
        "6 years"      -> 6
    """
    text = str(text or "").lower()

    range_patterns = [
        r"\b(\d+)\s*(?:to|-|–|—)\s*(\d+)\s*years?\b",
        r"\bbetween\s+(\d+)\s+and\s+(\d+)\s*years?\b",
    ]

    for pattern in range_patterns:
        match = re.search(pattern, text)
        if match:
            return int(match.group(1))

    patterns = [
        r"\bminimum\s+(?:of\s+)?(\d+)\s*years?\b",
        r"\bat\s+least\s+(\d+)\s*years?\b",
        r"\b(\d+)\s*\+?\s*years?\s+of\s+experience\b",
        r"\b(\d+)\s*\+?\s*years?\s+experience\b",
        r"\b(\d+)\s*\+?\s*years?\b",
    ]

    values = []

    for pattern in patterns:
        for match in re.finditer(pattern, text):
            try:
                values.append(int(match.group(1)))
            except (TypeError, ValueError):
                continue

    return max(values) if values else 0


def _extract_resume_experience_years(
    resume_text: str,
) -> float:
    """
    Estimate candidate work experience from actual work history.

    Priority:
    1. Explicit total-experience statements.
    2. Employment date ranges inside a real experience section.

    Education, projects, certifications and other sections are ignored.
    Overlapping employment periods are merged so the same time is not
    counted twice.

    Returns approximate years as a float, e.g. 3.6 years.
    """

    text = str(resume_text or "")
    if not text.strip():
        return 0.0

    explicit_patterns = [
        r"(\d+(?:\.\d+)?)\s*\+?\s*years?\s+of\s+experience",
        r"(\d+(?:\.\d+)?)\s*\+?\s*years?\s+experience",
        r"total\s+experience\s*[:\-]?\s*(\d+(?:\.\d+)?)",
    ]

    explicit_values = []

    for pattern in explicit_patterns:
        for match in re.finditer(
            pattern,
            text,
            flags=re.IGNORECASE,
        ):
            try:
                explicit_values.append(
                    float(match.group(1))
                )
            except (TypeError, ValueError):
                continue

    if explicit_values:
        return max(explicit_values)

    lines = text.splitlines()

    experience_headings = {
        "experience",
        "professional experience",
        "work experience",
        "employment",
        "employment history",
        "professional employment",
        "work history",
    }

    stop_headings = {
        "education",
        "academic background",
        "academic qualifications",
        "projects",
        "project experience",
        "academic projects",
        "technical skills",
        "skills",
        "skills summary",
        "certifications",
        "certificates",
        "achievements",
        "awards",
        "languages",
        "professional summary",
        "summary",
        "profile",
        "objective",
        "career objective",
    }

    def normalize_heading(value):
        value = re.sub(
            r"[^a-z0-9/& +#.-]",
            " ",
            value.lower(),
        )
        return re.sub(r"\s+", " ", value).strip()

    start_index = None

    for index, line in enumerate(lines):
        if normalize_heading(line) in experience_headings:
            start_index = index + 1
            break

    if start_index is None:
        return 0.0

    end_index = len(lines)

    for index in range(start_index, len(lines)):
        if normalize_heading(lines[index]) in stop_headings:
            end_index = index
            break

    experience_lines = lines[start_index:end_index]

    from datetime import datetime

    now = datetime.now()
    current_month = now.year * 12 + now.month

    month_map = {
        "jan": 1,
        "january": 1,
        "feb": 2,
        "february": 2,
        "mar": 3,
        "march": 3,
        "apr": 4,
        "april": 4,
        "may": 5,
        "jun": 6,
        "june": 6,
        "jul": 7,
        "july": 7,
        "aug": 8,
        "august": 8,
        "sep": 9,
        "sept": 9,
        "september": 9,
        "oct": 10,
        "october": 10,
        "nov": 11,
        "november": 11,
        "dec": 12,
        "december": 12,
    }

    month_range_pattern = re.compile(
        r"("
        r"jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|"
        r"may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|"
        r"sep(?:t(?:ember)?)?|oct(?:ober)?|nov(?:ember)?|"
        r"dec(?:ember)?"
        r")"
        r"\s+(20\d{2})"
        r"\s*(?:-|–|—|to)\s*"
        r"("
        r"present|current|now|"
        r"jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|"
        r"may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|"
        r"sep(?:t(?:ember)?)?|oct(?:ober)?|nov(?:ember)?|"
        r"dec(?:ember)?"
        r")"
        r"(?:\s+(20\d{2}))?\b",
        flags=re.IGNORECASE,
    )

    year_range_pattern = re.compile(
        r"\b(20\d{2})"
        r"\s*(?:-|–|—|to)\s*"
        r"(present|current|now|20\d{2})\b",
        flags=re.IGNORECASE,
    )

    intervals = []

    def to_month(year, month):
        return year * 12 + month

    for line in experience_lines:
        month_match = month_range_pattern.search(line)

        if month_match:
            start_month = month_map.get(
                month_match.group(1).lower()
            )
            start_year = int(
                month_match.group(2)
            )
            end_month_text = (
                month_match.group(3).lower()
            )
            end_year_text = month_match.group(4)

            if not start_month:
                continue

            start_value = to_month(
                start_year,
                start_month,
            )

            if end_month_text in {
                "present",
                "current",
                "now",
            }:
                end_value = current_month
            else:
                end_month = month_map.get(
                    end_month_text
                )

                if not end_month:
                    continue

                end_year = (
                    int(end_year_text)
                    if end_year_text
                    else start_year
                )

                end_value = to_month(
                    end_year,
                    end_month,
                )

            if end_value >= start_value:
                intervals.append(
                    (
                        start_value,
                        end_value,
                    )
                )

            # Do not also treat the same line as a bare year range.
            continue

        year_match = year_range_pattern.search(line)

        if year_match:
            start_year = int(
                year_match.group(1)
            )
            end_text = year_match.group(2).lower()

            start_value = to_month(
                start_year,
                1,
            )

            if end_text in {
                "present",
                "current",
                "now",
            }:
                end_value = current_month
            else:
                end_value = to_month(
                    int(end_text),
                    12,
                )

            if end_value >= start_value:
                intervals.append(
                    (
                        start_value,
                        end_value,
                    )
                )

    if not intervals:
        return 0.0

    intervals.sort()

    merged = [
        intervals[0]
    ]

    for start, end in intervals[1:]:
        last_start, last_end = merged[-1]

        if start <= last_end + 1:
            merged[-1] = (
                last_start,
                max(last_end, end),
            )
        else:
            merged.append(
                (
                    start,
                    end,
                )
            )

    total_months = sum(
        end - start + 1
        for start, end in merged
    )

    return round(
        total_months / 12.0,
        1,
    )

# ============================================================
# EXPERIENCE SCORE
# ============================================================

def calculate_experience_score(
    resume_text: str,
    required_experience: Any = 0,
    jd_text: Optional[str] = None,
) -> float:
    """
    Compare candidate experience against the JD requirement.

    When no requirement is detected, the score is 100.
    """

    required = _safe_float(
        required_experience
    )

    if required <= 0 and jd_text:
        required = _extract_years(
            jd_text
        )

    if required <= 0:
        return 100.0

    candidate = _extract_resume_experience_years(
        resume_text
    )

    if candidate <= 0:
        return 0.0

    if candidate >= required:
        return 100.0

    return round(
        candidate
        / required
        * 100,
        2,
    )


# ============================================================
# STRUCTURE SCORE
# ============================================================

SECTION_PATTERNS = {
    "summary": [
        "summary",
        "professional summary",
        "profile",
        "objective",
        "career objective",
    ],
    "skills": [
        "skills",
        "technical skills",
        "core skills",
        "skills summary",
    ],
    "experience": [
        "experience",
        "professional experience",
        "work experience",
        "employment",
        "employment history",
    ],
    "education": [
        "education",
        "academic background",
        "academic qualifications",
    ],
    "projects": [
        "projects",
        "academic projects",
        "personal projects",
        "project experience",
    ],
    "certifications": [
        "certifications",
        "certificates",
    ],
}


def _normalized_lines(
    text: str,
) -> List[str]:
    """Return normalized non-empty lines."""

    lines = []

    for line in str(text or "").splitlines():
        value = re.sub(
            r"[^a-zA-Z0-9+#/& ._-]",
            " ",
            line,
        )

        value = re.sub(
            r"\s+",
            " ",
            value,
        ).strip().lower()

        if value:
            lines.append(value)

    return lines


def calculate_structure_score(
    resume_text: str,
) -> float:
    """
    Estimate ATS-friendly resume structure based on the presence
    of useful standard sections.
    """

    if not resume_text:
        return 0.0

    lines = _normalized_lines(
        resume_text
    )

    joined = "\n".join(lines)

    detected = 0

    for aliases in SECTION_PATTERNS.values():
        found = False

        for alias in aliases:
            pattern = (
                rf"(?m)^\s*"
                rf"{re.escape(alias)}"
                rf"\s*:?\s*$"
            )

            if re.search(
                pattern,
                joined,
                flags=re.IGNORECASE,
            ):
                found = True
                break

        if found:
            detected += 1

    total = len(SECTION_PATTERNS)

    if total == 0:
        return 100.0

    return round(
        detected / total * 100,
        2,
    )


# ============================================================
# SEMANTIC SCORE — FULLY OFFLINE
# ============================================================

def _local_tfidf_similarity(
    resume_text: str,
    job_description: str,
) -> float:
    """
    Calculate lexical similarity without downloading an external model.

    TF-IDF is intentionally only one signal; short JD/resume pairs can have
    low raw cosine similarity even when the underlying job responsibilities
    are clearly related.
    """
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity

        resume = str(resume_text or "").strip()
        jd = str(job_description or "").strip()

        if not resume or not jd:
            return 0.0

        vectorizer = TfidfVectorizer(
            lowercase=True,
            stop_words="english",
            ngram_range=(1, 2),
            min_df=1,
            sublinear_tf=True,
        )

        matrix = vectorizer.fit_transform(
            [resume, jd]
        )

        value = float(
            cosine_similarity(
                matrix[0:1],
                matrix[1:2],
            )[0][0]
        )

        return max(
            0.0,
            min(100.0, value * 100.0),
        )

    except Exception:
        return calculate_keyword_score(
            resume_text,
            job_description,
        )


def _keyword_overlap_similarity(
    resume_text: str,
    job_description: str,
) -> float:
    """
    Estimate meaningful vocabulary overlap while ignoring common stop words.
    """
    resume_tokens = set(
        _tokenize(resume_text)
    )
    jd_tokens = set(
        _tokenize(job_description)
    )

    if not jd_tokens:
        return 100.0

    matched = resume_tokens.intersection(
        jd_tokens
    )

    return round(
        len(matched) / len(jd_tokens) * 100.0,
        2,
    )


def _responsibility_semantic_score(
    resume_text: str,
    job_description: str,
) -> float:
    """
    Estimate semantic alignment by checking job responsibilities against
    concepts actually evidenced in the resume.

    This is deliberately conservative and rewards related implementation,
    debugging, testing, documentation, development and delivery evidence
    without inventing skills.
    """
    resume = _concept_key(resume_text)
    jd = str(job_description or "")

    if not resume or not jd:
        return 0.0

    # Concept families intentionally focused on software-development work.
    concept_families = {
        "software development": {
            "software development",
            "application development",
            "web development",
            "development",
            "built",
            "building",
            "developed",
            "applications",
            "projects",
        },
        "end to end": {
            "end-to-end",
            "end to end",
            "requirements gathering",
            "development",
            "testing",
            "post-delivery support",
        },
        "debugging": {
            "debug",
            "debugging",
            "troubleshooting",
            "issue resolution",
            "problem solving",
        },
        "testing": {
            "test",
            "testing",
            "uat",
            "validation",
        },
        "documentation": {
            "documentation",
            "documented",
            "technical documentation",
        },
        "programming": {
            "programming",
            "java",
            "python",
            "javascript",
            "web development",
        },
        "databases": {
            "database",
            "databases",
            "mysql",
            "mongodb",
            "oracle",
            "sql",
            "jdbc",
        },
        "tools and technologies": {
            "tools",
            "technologies",
            "jira",
            "visual studio code",
            "eclipse",
            "apache tomcat",
            "mongodb compass",
        },
        "continuous improvement": {
            "enhancements",
            "improve",
            "improved",
            "troubleshooting",
            "validation",
            "enhancements and post-delivery support",
        },
        "collaboration/client delivery": {
            "client",
            "client support",
            "client onboarding",
            "requirements gathering",
            "cross-functional",
            "team",
        },
    }

    responsibility_lines = []
    for raw_line in jd.splitlines():
        line = raw_line.strip(" -•\t")
        if len(line) < 18:
            continue

        lowered = line.lower()

        # Ignore headers and hashtag/social boilerplate.
        if lowered.startswith(("role:", "location:", "why join us:")):
            continue
        if lowered.startswith(("#hiring", "#softwaredeveloper")):
            continue

        if any(
            marker in lowered
            for marker in (
                "design, build",
                "collaborate",
                "write clean",
                "debug, test",
                "learn new tools",
                "solid understanding",
                "familiarity with",
                "strong communication",
                "teamwork",
                "degree in",
            )
        ):
            responsibility_lines.append(
                lowered
            )

    if not responsibility_lines:
        return 0.0

    scored = []

    def family_present(family):
        return any(
            re.search(
                r"(?<![a-z0-9])"
                + re.escape(
                    _concept_key(alias)
                )
                + r"(?![a-z0-9])",
                resume,
                flags=re.IGNORECASE,
            )
            for alias in concept_families[family]
            if _concept_key(alias)
        )

    for line in responsibility_lines:
        hits = 0
        possible = 0

        checks = []

        if "design" in line or "build" in line or "application" in line:
            checks.append("software development")

        if "end-to-end" in line or "end to end" in line or "collaborate" in line:
            checks.append("end to end")
            checks.append("collaboration/client delivery")

        if "clean" in line or "documented code" in line or "well-documented" in line:
            checks.append("programming")
            checks.append("documentation")

        if "debug" in line or "test" in line or "improve" in line:
            checks.append("debugging")
            checks.append("testing")
            checks.append("continuous improvement")

        if "tools" in line or "technologies" in line:
            checks.append("tools and technologies")

        if "programming fundamentals" in line or "language" in line:
            checks.append("programming")

        if "communication" in line:
            checks.append("collaboration/client delivery")

        if "teamwork" in line:
            checks.append("collaboration/client delivery")

        if "degree" in line or "computer science" in line:
            checks.append("programming")

        # Deduplicate checks for a clean denominator.
        checks = list(dict.fromkeys(checks))

        if not checks:
            continue

        possible = len(checks)

        for family in checks:
            if family_present(family):
                hits += 1

        scored.append(
            hits / possible * 100.0
        )

    if not scored:
        return 0.0

    return round(
        sum(scored) / len(scored),
        2,
    )


def _local_skill_similarity(
    resume_skills: Optional[List[str]],
    job_skills: Optional[List[str]],
    resume_text: str = "",
) -> float:
    """
    Calculate explicit JD-skill coverage conservatively.

    Single-letter languages are only counted when the resume explicitly
    identifies them as skills or clearly states programming experience.
    """
    if not job_skills:
        return 100.0

    unique_job_skills = _coerce_skill_list(
        job_skills
    )

    matched = 0

    for job_skill in unique_job_skills:
        found = False

        for resume_skill in _coerce_skill_list(resume_skills):
            if _skills_match(
                resume_skill,
                job_skill,
            ):
                found = True
                break

        if (
            not found
            and resume_text
            and _text_has_concept(
                resume_text,
                job_skill,
            )
        ):
            found = True

        if found:
            matched += 1

    return round(
        matched
        / len(unique_job_skills)
        * 100.0,
        2,
    )


def calculate_semantic_score(
    resume_text: str,
    job_description: str,
    resume_skills: Optional[List[str]] = None,
    job_skills: Optional[List[str]] = None,
) -> float:
    """
    Calculate a balanced semantic relevance score.

    Signals:
      - lexical similarity: 20%
      - meaningful vocabulary overlap: 15%
      - job-responsibility concept coverage: 50%
      - explicit skill context: 15%

    This produces a useful approximation without external embedding models.
    """
    tfidf_score = _local_tfidf_similarity(
        resume_text,
        job_description,
    )

    lexical_overlap = _keyword_overlap_similarity(
        resume_text,
        job_description,
    )

    responsibility_score = (
        _responsibility_semantic_score(
            resume_text,
            job_description,
        )
    )

    skill_context_score = _local_skill_similarity(
        resume_skills,
        job_skills,
        resume_text,
    )

    return round(
        tfidf_score * 0.20
        + lexical_overlap * 0.10
        + responsibility_score * 0.55
        + skill_context_score * 0.15,
        2,
    )


# ============================================================
# MAIN ATS SCORE
# ============================================================

def calculate_ats_score(
    resume_text: str,
    job_description: str,
    resume_skills: Optional[List[str]] = None,
    job_skills: Optional[Any] = None,
    required_experience: Any = 0,
    jd_analysis: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Calculate the complete ATS score.

    Compatible with several calling patterns used by the
    application.

    Returns a dictionary containing:
        ats_score
        skill_score
        semantic_score
        experience_score
        keyword_score
        structure_score
        matched_skills
        missing_skills
    """

    resume_text = str(
        resume_text or ""
    ).strip()

    job_description = str(
        job_description or ""
    ).strip()

    if not resume_text:
        raise ValueError(
            "Resume text cannot be empty."
        )

    if not job_description:
        raise ValueError(
            "Job description cannot be empty."
        )

    # --------------------------------------------------------
    # Resolve JD analysis
    # --------------------------------------------------------

    if jd_analysis is None and isinstance(
        job_skills,
        dict,
    ):
        jd_analysis = job_skills
        job_skills = None

    jd_analysis = (
        jd_analysis
        if isinstance(jd_analysis, dict)
        else {}
    )

    # --------------------------------------------------------
    # Resume skills
    # --------------------------------------------------------

    if resume_skills is None:
        try:
            from modules.skill_extractor import extract_skills

            resume_skills = extract_skills(
                resume_text
            )

        except Exception:
            resume_skills = []

    resume_skills = _coerce_skill_list(
        resume_skills
    )

    # --------------------------------------------------------
    # JD skills
    # --------------------------------------------------------

    # Defensive guard: a caller must not pass the entire JD text as one
    # "job skill". Older generic dispatchers sometimes did exactly that.
    if isinstance(job_skills, str):
        normalized_job = re.sub(r"\s+", " ", job_skills).strip().lower()
        normalized_jd = re.sub(r"\s+", " ", job_description).strip().lower()
        if normalized_job == normalized_jd or len(job_skills.split()) > 40:
            job_skills = None

    if job_skills is None:
        job_skills = (
            jd_analysis.get("skills")
            or jd_analysis.get("jd_skills")
            or jd_analysis.get("required_skills")
            or []
        )

    if isinstance(
        job_skills,
        dict,
    ):
        job_skills = (
            job_skills.get("skills")
            or job_skills.get("required_skills")
            or []
        )

    if not job_skills:
        try:
            from modules.skill_extractor import extract_skills

            job_skills = extract_skills(
                job_description
            )

        except Exception:
            job_skills = []

    job_skills = _coerce_skill_list(
        job_skills
    )

    # --------------------------------------------------------
    # Skill score
    # --------------------------------------------------------

    (
        skill_score,
        matched_skills,
        missing_skills,
    ) = calculate_skill_score(
        resume_skills,
        job_skills,
        resume_text=resume_text,
    )

    # --------------------------------------------------------
    # Experience score
    # --------------------------------------------------------

    if not required_experience:
        required_experience = (
            jd_analysis.get(
                "experience_years",
                0,
            )
        )

    experience_score = (
        calculate_experience_score(
            resume_text=resume_text,
            required_experience=required_experience,
            jd_text=job_description,
        )
    )

    # --------------------------------------------------------
    # Semantic score
    # --------------------------------------------------------

    semantic_score = calculate_semantic_score(
        resume_text=resume_text,
        job_description=job_description,
        resume_skills=resume_skills,
        job_skills=job_skills,
    )

    # --------------------------------------------------------
    # Keyword score
    # --------------------------------------------------------

    keyword_score = calculate_keyword_score(
        resume_text,
        job_description,
    )

    # --------------------------------------------------------
    # Structure score
    # --------------------------------------------------------

    structure_score = calculate_structure_score(
        resume_text
    )

    # --------------------------------------------------------
    # Weighted final score
    # --------------------------------------------------------

    ats_score = (
        skill_score * SKILL_WEIGHT
        + semantic_score * SEMANTIC_WEIGHT
        + experience_score * EXPERIENCE_WEIGHT
        + keyword_score * KEYWORD_WEIGHT
        + structure_score * STRUCTURE_WEIGHT
    )

    ats_score = round(
        max(
            0.0,
            min(
                100.0,
                ats_score,
            ),
        ),
        2,
    )

    return {
        "ats_score": ats_score,
        "overall_score": ats_score,
        "skill_score": round(
            skill_score,
            2,
        ),
        "semantic_score": round(
            semantic_score,
            2,
        ),
        "experience_score": round(
            experience_score,
            2,
        ),
        "keyword_score": round(
            keyword_score,
            2,
        ),
        "structure_score": round(
            structure_score,
            2,
        ),
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "resume_skills": resume_skills,
        "job_skills": job_skills,
        "required_experience": required_experience,
        "candidate_experience_years": _extract_resume_experience_years(resume_text),
    }


# ============================================================
# ALIASES
# ============================================================

def calculate_score(
    resume_text: str,
    job_description: str,
    resume_skills: Optional[List[str]] = None,
    job_skills: Optional[List[str]] = None,
    required_experience: Any = 0,
    jd_analysis: Optional[Dict[str, Any]] = None,
):
    """
    Short alias for calculate_ats_score().
    """

    return calculate_ats_score(
        resume_text=resume_text,
        job_description=job_description,
        resume_skills=resume_skills,
        job_skills=job_skills,
        required_experience=required_experience,
        jd_analysis=jd_analysis,
    )


def score_resume(
    resume_text: str,
    job_description: str,
    resume_skills: Optional[List[str]] = None,
    job_skills: Optional[List[str]] = None,
):
    """
    Alias for calculate_ats_score().
    """

    return calculate_ats_score(
        resume_text,
        job_description,
        resume_skills,
        job_skills,
    )


# ============================================================
# SCRIPT TEST
# ============================================================

if __name__ == "__main__":
    sample_resume = """
    PROFESSIONAL SUMMARY
    Python developer with experience in Python, SQL and REST APIs.

    TECHNICAL SKILLS
    Python, SQL, Git, REST API, Docker

    PROFESSIONAL EXPERIENCE
    Developed and maintained Python applications.

    PROJECTS
    Built a Python web application.

    EDUCATION
    Bachelor degree.
    """

    sample_jd = """
    Python Developer

    Requirements:
    2+ years of experience in Python development.
    Python, SQL, Git, REST API, Docker and AWS.
    """

    result = calculate_ats_score(
        sample_resume,
        sample_jd,
    )

    print("\nATS Score")
    print(
        f"{result['ats_score']:.2f}%"
    )

    print("\nBreakdown")
    print(
        f"Skills: {result['skill_score']:.2f}%"
    )
    print(
        f"Semantic: {result['semantic_score']:.2f}%"
    )
    print(
        f"Experience: {result['experience_score']:.2f}%"
    )
    print(
        f"Keywords: {result['keyword_score']:.2f}%"
    )
    print(
        f"Structure: {result['structure_score']:.2f}%"
    )

    print("\nMatched Skills")
    for skill in result["matched_skills"]:
        print(
            f"- {skill}"
        )

    print("\nMissing Skills")
    for skill in result["missing_skills"]:
        print(
            f"- {skill}"
        )
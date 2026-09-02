"""
Skill Extraction Module
-----------------------

Loads skills from:
    data/skills.csv

Expected CSV columns:
    skill,category

Provides:
- extract_skills()
- find_matching_skills()
- find_missing_skills()
- calculate_skill_match()
- get_skill_categories()
"""


import csv
import re
from pathlib import Path
from functools import lru_cache

from config import SKILLS_FILE


# ============================================================
# NORMALIZATION
# ============================================================

def normalize_text(text):
    """
    Normalize text for reliable skill matching.
    """
    if text is None:
        return ""

    text = str(text).lower()

    text = text.replace("–", "-")
    text = text.replace("—", "-")
    text = text.replace("’", "'")

    text = re.sub(r"\s+", " ", text)

    return text.strip()


def normalize_skill(skill):
    """
    Normalize a skill name.
    """
    return normalize_text(skill)


# ============================================================
# CSV LOADING
# ============================================================

@lru_cache(maxsize=1)
def load_skill_database():
    """
    Load the project's skills.csv.

    Expected format:

        skill,category
        Python,Programming
        Java,Programming
        SQL,Database
    """
    skill_file = Path(SKILLS_FILE)

    if not skill_file.exists():
        raise FileNotFoundError(
            f"Skills database not found: {skill_file}"
        )

    skills = []

    with skill_file.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as file:
        reader = csv.DictReader(file)

        if not reader.fieldnames:
            raise ValueError(
                "skills.csv does not contain a header row."
            )

        field_map = {
            str(field).strip().lower(): field
            for field in reader.fieldnames
        }

        if "skill" not in field_map:
            raise ValueError(
                "skills.csv must contain a 'skill' column."
            )

        skill_column = field_map["skill"]
        category_column = field_map.get("category")

        for row in reader:
            skill = str(
                row.get(skill_column, "")
            ).strip()

            if not skill:
                continue

            category = ""

            if category_column:
                category = str(
                    row.get(category_column, "")
                ).strip()

            skills.append(
                {
                    "skill": skill,
                    "category": category,
                }
            )

    return skills


# ============================================================
# DATABASE ACCESS
# ============================================================

def get_skill_database():
    """
    Return the complete loaded skill database.
    """
    return load_skill_database()


def get_all_skills():
    """
    Return all unique skills from skills.csv.
    """
    skills = []

    seen = set()

    for item in load_skill_database():
        skill = item["skill"]
        key = normalize_skill(skill)

        if key in seen:
            continue

        seen.add(key)
        skills.append(skill)

    return skills


def get_skill_categories():
    """
    Return a mapping of category -> skills.
    """
    categories = {}

    for item in load_skill_database():
        category = item["category"] or "General"
        skill = item["skill"]

        categories.setdefault(
            category,
            [],
        ).append(skill)

    return categories


# ============================================================
# MATCHING HELPERS
# ============================================================

def _contains_skill(text, skill):
    """
    Determine whether a skill appears in the supplied text.

    Uses boundaries to avoid false positives such as:
        C  -> matching inside 'CSS'
        R  -> matching inside unrelated words
    """
    normalized_text = normalize_text(text)
    normalized_skill = normalize_skill(skill)

    if not normalized_text or not normalized_skill:
        return False

    # Escape literal skill text for regex matching.
    escaped = re.escape(
        normalized_skill
    )

    # Skills containing punctuation such as C++, C#, .NET,
    # CI/CD, etc. need a flexible boundary strategy.
    if re.fullmatch(
        r"[a-z0-9]+",
        normalized_skill,
    ):
        pattern = rf"(?<![a-z0-9]){escaped}(?![a-z0-9])"

    else:
        pattern = rf"(?<!\w){escaped}(?!\w)"

    return re.search(
        pattern,
        normalized_text,
        flags=re.IGNORECASE,
    ) is not None


# ============================================================
# SKILL EXTRACTION
# ============================================================

def extract_skills(text):
    """
    Extract skills from arbitrary resume/JD text.

    Returns:
        list[str]
    """
    if not text:
        return []

    detected = []

    # Longer skills first so that:
    # "Microsoft SQL Server" is detected before "SQL".
    database = sorted(
        load_skill_database(),
        key=lambda item: len(item["skill"]),
        reverse=True,
    )

    seen = set()

    for item in database:
        skill = item["skill"]

        if _contains_skill(text, skill):
            key = normalize_skill(skill)

            if key in seen:
                continue

            seen.add(key)
            detected.append(skill)

    return detected


# ============================================================
# EXTRACT SKILLS WITH CATEGORIES
# ============================================================

def extract_skills_with_categories(text):
    """
    Extract detected skills with their categories.

    Returns:
        [
            {
                "skill": "Python",
                "category": "Programming"
            }
        ]
    """
    if not text:
        return []

    results = []

    database = sorted(
        load_skill_database(),
        key=lambda item: len(item["skill"]),
        reverse=True,
    )

    seen = set()

    for item in database:
        skill = item["skill"]

        if _contains_skill(text, skill):
            key = normalize_skill(skill)

            if key in seen:
                continue

            seen.add(key)

            results.append(
                {
                    "skill": skill,
                    "category": item["category"],
                }
            )

    return results


# ============================================================
# MATCHED SKILLS
# ============================================================

def find_matching_skills(
    resume_text,
    job_description,
):
    """
    Return JD skills that are also detected in the resume.
    """
    resume_skills = extract_skills(
        resume_text
    )

    jd_skills = extract_skills(
        job_description
    )

    resume_normalized = {
        normalize_skill(skill)
        for skill in resume_skills
    }

    matched = []

    for skill in jd_skills:
        if normalize_skill(skill) in resume_normalized:
            matched.append(skill)

    return matched


# ============================================================
# MISSING SKILLS
# ============================================================

def find_missing_skills(
    resume_text,
    job_description,
):
    """
    Return JD skills that were not detected in the resume.
    """
    resume_skills = extract_skills(
        resume_text
    )

    jd_skills = extract_skills(
        job_description
    )

    resume_normalized = {
        normalize_skill(skill)
        for skill in resume_skills
    }

    missing = []

    for skill in jd_skills:
        if normalize_skill(skill) not in resume_normalized:
            missing.append(skill)

    return missing


# ============================================================
# SKILL MATCH PERCENTAGE
# ============================================================

def calculate_skill_match(
    resume_text,
    job_description,
):
    """
    Calculate JD skill coverage percentage.

    Returns:
        float from 0 to 100
    """
    jd_skills = extract_skills(
        job_description
    )

    if not jd_skills:
        return 100.0

    matched = find_matching_skills(
        resume_text,
        job_description,
    )

    score = (
        len(matched)
        / len(jd_skills)
    ) * 100

    return round(
        min(100.0, max(0.0, score)),
        2,
    )


# ============================================================
# SKILL GAP
# ============================================================

def get_skill_gap(
    resume_text,
    job_description,
):
    """
    Return complete resume/JD skill comparison.
    """
    resume_skills = extract_skills(
        resume_text
    )

    jd_skills = extract_skills(
        job_description
    )

    matched = find_matching_skills(
        resume_text,
        job_description,
    )

    missing = find_missing_skills(
        resume_text,
        job_description,
    )

    return {
        "resume_skills": resume_skills,
        "jd_skills": jd_skills,
        "matched": matched,
        "missing": missing,
        "match_percentage": calculate_skill_match(
            resume_text,
            job_description,
        ),
    }


# ============================================================
# CATEGORY ANALYSIS
# ============================================================

def analyze_skill_categories(text):
    """
    Return detected skills grouped by category.
    """
    results = {}

    for item in extract_skills_with_categories(text):
        category = (
            item["category"]
            or "General"
        )

        results.setdefault(
            category,
            [],
        ).append(
            item["skill"]
        )

    return results


# ============================================================
# CACHE CONTROL
# ============================================================

def reload_skill_database():
    """
    Clear the cached CSV database.

    Useful when skills.csv is modified while the app is running.
    """
    load_skill_database.cache_clear()


# ============================================================
# BACKWARD-COMPATIBLE ALIASES
# ============================================================

load_skills = get_all_skills

get_skills = get_all_skills

match_skills = find_matching_skills

missing_skills = find_missing_skills
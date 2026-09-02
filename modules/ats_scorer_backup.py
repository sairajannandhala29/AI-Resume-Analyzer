from .semantic_matcher import (
    calculate_semantic_similarity,
    calculate_skill_similarity
)
from .skill_extractor import compare_skills


# ATS scoring weights
SKILL_WEIGHT = 0.40
SEMANTIC_WEIGHT = 0.25
EXPERIENCE_WEIGHT = 0.20
KEYWORD_WEIGHT = 0.10
STRUCTURE_WEIGHT = 0.05


def calculate_experience_score(
    resume_text,
    required_years
):
    """
    Estimate experience compatibility.

    This is intentionally conservative.
    It does not invent experience.
    """

    if required_years is None:
        return 100.0

    resume_text_lower = resume_text.lower()

    experience_patterns = [
        "years of experience",
        "year of experience",
        "years experience",
        "year experience"
    ]

    has_experience_reference = any(
        pattern in resume_text_lower
        for pattern in experience_patterns
    )

    if not has_experience_reference:
        return 0.0

    # Detect common numeric experience values.
    import re

    matches = re.findall(
        r"(\d+)\+?\s*(?:years?|yrs?)",
        resume_text_lower
    )

    if not matches:
        return 50.0

    max_years = max(
        int(value)
        for value in matches
    )

    if max_years >= required_years:
        return 100.0

    return round(
        (max_years / required_years) * 100,
        2
    )


def calculate_keyword_score(
    resume_text,
    job_description
):
    """
    Calculate keyword coverage between
    the resume and job description.
    """

    import re

    resume_words = set(
        re.findall(
            r"\b[a-zA-Z][a-zA-Z+#.-]{2,}\b",
            resume_text.lower()
        )
    )

    job_words = set(
        re.findall(
            r"\b[a-zA-Z][a-zA-Z+#.-]{2,}\b",
            job_description.lower()
        )
    )

    if not job_words:
        return 0.0

    common_words = (
        resume_words & job_words
    )

    score = (
        len(common_words)
        / len(job_words)
    ) * 100

    return round(
        min(score, 100),
        2
    )


def calculate_structure_score(resume_text):
    """
    Check for common ATS-friendly resume sections.
    """

    text = resume_text.lower()

    sections = {
        "summary": [
            "summary",
            "professional summary",
            "profile"
        ],

        "skills": [
            "skills",
            "technical skills",
            "core skills"
        ],

        "experience": [
            "experience",
            "work experience",
            "professional experience"
        ],

        "education": [
            "education",
            "academic background"
        ],

        "projects": [
            "projects",
            "academic projects",
            "personal projects"
        ]
    }

    found_sections = 0

    for keywords in sections.values():

        if any(
            keyword in text
            for keyword in keywords
        ):
            found_sections += 1

    score = (
        found_sections
        / len(sections)
    ) * 100

    return round(score, 2)


def calculate_ats_score(
    resume_text,
    job_description,
    resume_skills,
    job_skills,
    required_experience=None
):
    """
    Calculate the overall ATS compatibility score.

    Score components:

    Skill Match        = 40%
    Semantic Match     = 25%
    Experience Match  = 20%
    Keyword Match     = 10%
    ATS Structure      = 5%
    """

    # --------------------------------
    # 1. Skill Match
    # --------------------------------

    skill_score = calculate_skill_similarity(
        resume_skills,
        job_skills
    )

    # --------------------------------
    # 2. Semantic Match
    # --------------------------------

    semantic_score = calculate_semantic_similarity(
        resume_text,
        job_description
    )

    # --------------------------------
    # 3. Experience Match
    # --------------------------------

    experience_score = calculate_experience_score(
        resume_text,
        required_experience
    )

    # --------------------------------
    # 4. Keyword Match
    # --------------------------------

    keyword_score = calculate_keyword_score(
        resume_text,
        job_description
    )

    # --------------------------------
    # 5. ATS Structure
    # --------------------------------

    structure_score = calculate_structure_score(
        resume_text
    )

    # --------------------------------
    # Weighted final score
    # --------------------------------

    final_score = (
        skill_score * SKILL_WEIGHT
        + semantic_score * SEMANTIC_WEIGHT
        + experience_score * EXPERIENCE_WEIGHT
        + keyword_score * KEYWORD_WEIGHT
        + structure_score * STRUCTURE_WEIGHT
    )

    final_score = round(
        min(final_score, 100),
        2
    )

    # --------------------------------
    # Skill comparison
    # --------------------------------

    matched_skills, missing_skills = (
        compare_skills(
            resume_skills,
            job_skills
        )
    )

    return {
        "ats_score": final_score,

        "skill_score": skill_score,

        "semantic_score": semantic_score,

        "experience_score": experience_score,

        "keyword_score": keyword_score,

        "structure_score": structure_score,

        "matched_skills": matched_skills,

        "missing_skills": missing_skills
    }
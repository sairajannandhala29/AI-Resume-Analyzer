"""
Tests for modules.ats_scorer
"""

import pytest

from modules.ats_scorer import (
    calculate_ats_score,
    calculate_experience_score,
    calculate_keyword_score,
    calculate_skill_score,
    calculate_structure_score,
)


# ============================================================
# SKILL SCORE
# ============================================================

def test_skill_score_all_matched():
    score, matched, missing = calculate_skill_score(
        ["Python", "SQL", "Git"],
        ["Python", "SQL", "Git"],
    )

    assert score == 100.0
    assert len(matched) == 3
    assert missing == []


def test_skill_score_partial_match():
    score, matched, missing = calculate_skill_score(
        ["Python", "SQL"],
        ["Python", "SQL", "Docker", "AWS"],
    )

    assert score == 50.0

    assert "Python" in matched
    assert "SQL" in matched

    assert "Docker" in missing
    assert "AWS" in missing


def test_skill_score_no_match():
    score, matched, missing = calculate_skill_score(
        ["Python"],
        ["Java", "Docker"],
    )

    assert score == 0.0
    assert matched == []
    assert len(missing) == 2


def test_skill_score_empty_jd():
    score, matched, missing = calculate_skill_score(
        ["Python"],
        [],
    )

    assert score == 100.0
    assert matched == []
    assert missing == []


# ============================================================
# SKILL EQUIVALENCE
# ============================================================

def test_git_version_control_equivalence():
    score, matched, missing = calculate_skill_score(
        ["Git"],
        ["Version Control"],
    )

    assert score == 100.0
    assert matched == ["Version Control"]
    assert missing == []


def test_javascript_js_equivalence():
    score, matched, missing = calculate_skill_score(
        ["JavaScript"],
        ["JS"],
    )

    assert score == 100.0
    assert matched == ["JS"]
    assert missing == []


def test_postgres_postgresql_equivalence():
    score, matched, missing = calculate_skill_score(
        ["PostgreSQL"],
        ["Postgres"],
    )

    assert score == 100.0
    assert missing == []


# ============================================================
# KEYWORD SCORE
# ============================================================

def test_keyword_score_good_match():
    resume = """
    Python developer with experience in SQL,
    REST APIs and Git.
    """

    jd = """
    Python developer with experience in SQL,
    REST APIs and Git.
    """

    score = calculate_keyword_score(
        resume,
        jd,
    )

    assert score >= 80.0


def test_keyword_score_no_match():
    resume = """
    Java developer.
    """

    jd = """
    Python SQL Docker AWS.
    """

    score = calculate_keyword_score(
        resume,
        jd,
    )

    assert score < 50.0


def test_keyword_score_empty_jd():
    score = calculate_keyword_score(
        "Python developer",
        "",
    )

    assert score == 100.0


# ============================================================
# EXPERIENCE SCORE
# ============================================================

def test_experience_meets_requirement():
    resume = """
    Python developer with 4 years of experience.
    """

    score = calculate_experience_score(
        resume_text=resume,
        required_experience=2,
    )

    assert score == 100.0


def test_experience_below_requirement():
    resume = """
    Python developer with 1 year of experience.
    """

    score = calculate_experience_score(
        resume_text=resume,
        required_experience=3,
    )

    assert score == pytest.approx(
        33.33,
        abs=0.01,
    )


def test_experience_missing():
    resume = """
    Python developer.
    """

    score = calculate_experience_score(
        resume_text=resume,
        required_experience=3,
    )

    assert score == 0.0


def test_experience_requirement_not_detected():
    resume = """
    Python developer.
    """

    score = calculate_experience_score(
        resume_text=resume,
        required_experience=0,
    )

    assert score == 100.0


# ============================================================
# STRUCTURE SCORE
# ============================================================

def test_structure_score_good_resume():
    resume = """
    PROFESSIONAL SUMMARY
    Python developer.

    SKILLS
    Python, SQL, Git

    PROFESSIONAL EXPERIENCE
    Developed applications.

    PROJECTS
    Built an application.

    EDUCATION
    B.Sc. Statistics.

    CERTIFICATIONS
    Python Certificate.
    """

    score = calculate_structure_score(
        resume
    )

    assert score >= 80.0


def test_structure_score_empty_resume():
    score = calculate_structure_score(
        ""
    )

    assert score == 0.0


def test_structure_score_unstructured_text():
    resume = """
    Python developer looking for a job.
    """

    score = calculate_structure_score(
        resume
    )

    assert score < 50.0


# ============================================================
# COMPLETE ATS SCORE
# ============================================================

def test_complete_ats_score():
    resume = """
    PROFESSIONAL SUMMARY
    Python developer with 3 years of experience.

    SKILLS
    Python, SQL, Git, REST API

    PROFESSIONAL EXPERIENCE
    Developed Python applications and REST APIs.

    PROJECTS
    Built Python applications.

    EDUCATION
    B.Sc. Statistics.
    """

    jd = """
    Python Developer

    Requirements:
    2+ years of experience.
    Python, SQL, Git and REST API.
    """

    result = calculate_ats_score(
        resume_text=resume,
        job_description=jd,
    )

    assert isinstance(
        result,
        dict,
    )

    assert "ats_score" in result
    assert "skill_score" in result
    assert "semantic_score" in result
    assert "experience_score" in result
    assert "keyword_score" in result
    assert "structure_score" in result

    assert 0 <= result["ats_score"] <= 100


def test_ats_score_contains_skill_results():
    result = calculate_ats_score(
        resume_text="""
        Python developer with SQL and Git.
        """,
        job_description="""
        Looking for Python, SQL, Git and Docker.
        """,
    )

    assert "matched_skills" in result
    assert "missing_skills" in result

    assert "Python" in result["matched_skills"]
    assert "SQL" in result["matched_skills"]
    assert "Git" in result["matched_skills"]

    assert "Docker" in result["missing_skills"]


def test_ats_score_is_bounded():
    result = calculate_ats_score(
        resume_text="""
        Python SQL Git REST API
        """,
        job_description="""
        Python SQL Git REST API
        """,
    )

    assert 0 <= result["ats_score"] <= 100


# ============================================================
# INVALID INPUT
# ============================================================

def test_empty_resume_raises_error():
    with pytest.raises(ValueError):
        calculate_ats_score(
            "",
            "Python developer",
        )


def test_empty_job_description_raises_error():
    with pytest.raises(ValueError):
        calculate_ats_score(
            "Python developer",
            "",
        )
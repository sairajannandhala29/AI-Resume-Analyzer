"""
Tests for analyzer.py
"""

import pytest

from analyzer import (
    analyze_jd,
    analyze_resume,
    calculate_score,
    get_jd_skills,
    match_skills,
    normalize_score,
)


# ============================================================
# NORMALIZE SCORE
# ============================================================

def test_normalize_score_percentage():
    assert normalize_score(85) == 85.0


def test_normalize_score_decimal():
    assert normalize_score(0.85) == 85.0


def test_normalize_score_string():
    assert normalize_score("72%") == 72.0


def test_normalize_score_dict():
    assert normalize_score(
        {"ats_score": 91}
    ) == 91.0


def test_normalize_score_none():
    assert normalize_score(None) == 0.0


# ============================================================
# SKILL MATCHING
# ============================================================

def test_match_skills():
    result = match_skills(
        [
            "Python",
            "SQL",
            "Git",
        ],
        [
            "Python",
            "SQL",
            "Docker",
        ],
    )

    assert result["matched"] == [
        "Python",
        "SQL",
    ]

    assert result["missing"] == [
        "Docker",
    ]


def test_match_skills_case_insensitive():
    result = match_skills(
        [
            "python",
            "SQL",
        ],
        [
            "Python",
            "sql",
        ],
    )

    assert len(result["matched"]) == 2
    assert result["missing"] == []


def test_match_skills_empty_jd():
    result = match_skills(
        ["Python"],
        [],
    )

    assert result["matched"] == []
    assert result["missing"] == []


# ============================================================
# JD ANALYSIS
# ============================================================

def test_analyze_jd():
    jd = """
    Python Developer

    Requirements:
    2+ years of experience in Python development.
    Python, SQL and Git.
    """

    result = analyze_jd(jd)

    assert isinstance(
        result,
        dict,
    )

    assert "skills" in result


def test_get_jd_skills():
    result = get_jd_skills(
        {
            "skills": [
                "Python",
                "SQL",
            ]
        }
    )

    assert result == [
        "Python",
        "SQL",
    ]


def test_get_jd_skills_empty():
    assert get_jd_skills({}) == []


# ============================================================
# ANALYZER
# ============================================================

def test_analyze_resume_rejects_empty_resume():
    with pytest.raises(ValueError):
        analyze_resume(
            "",
            "Python developer",
        )


def test_analyze_resume_rejects_empty_jd():
    with pytest.raises(ValueError):
        analyze_resume(
            "Python developer",
            "",
        )


# ============================================================
# SCORE API
# ============================================================

def test_calculate_score_calls_scorer(monkeypatch):
    import analyzer

    def fake_scorer(*args):
        return {
            "ats_score": 80,
        }

    monkeypatch.setattr(
        analyzer,
        "calculate_ats_score",
        fake_scorer,
    )

    result = calculate_score(
        "Python developer",
        "Python developer",
        ["Python"],
        {"skills": ["Python"]},
    )

    assert result["ats_score"] == 80


# ============================================================
# COMPLETE ANALYSIS
# ============================================================

def test_complete_analysis(
    monkeypatch,
):
    import analyzer

    def fake_scorer(*args):
        return {
            "ats_score": 82,
            "skill_score": 100,
            "semantic_score": 80,
            "experience_score": 100,
            "keyword_score": 75,
            "structure_score": 80,
            "matched_skills": ["Python"],
            "missing_skills": [],
        }

    monkeypatch.setattr(
        analyzer,
        "calculate_ats_score",
        fake_scorer,
    )

    resume = """
    PROFESSIONAL SUMMARY
    Python developer.

    SKILLS
    Python, SQL
    """

    jd = """
    Python Developer

    Requirements:
    Python
    """

    result = analyze_resume(
        resume,
        jd,
    )

    assert isinstance(
        result,
        dict,
    )

    assert result["ats_score"] == 82.0

    assert "resume_skills" in result
    assert "jd_skills" in result
    assert "matched_skills" in result
    assert "missing_skills" in result
    assert "strengths" in result
    assert "recommendations" in result


# ============================================================
# ALIAS TESTS
# ============================================================

def test_analyze_jd_returns_dict():
    result = analyze_jd(
        "Python developer with SQL."
    )

    assert isinstance(
        result,
        dict,
    )
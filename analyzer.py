"""
analyzer.py

Main analysis layer for the AI Resume Analyzer.

This module provides reusable functions for:
- Resume text analysis
- Job description analysis
- ATS scoring
- Skill matching
- Resume strengths
- Recommendations

The Streamlit app can use these functions directly, while the
individual modules remain responsible for their specialized work.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional


# ============================================================
# MODULE IMPORTS
# ============================================================

from modules.skill_extractor import extract_skills
from modules.ats_scorer import calculate_ats_score

try:
    from modules.jd_analyzer import analyze_job_description
except ImportError:
    analyze_job_description = None

try:
    from modules.recommendations import (
        get_resume_strengths,
        generate_recommendations,
    )
except ImportError:
    get_resume_strengths = None
    generate_recommendations = None


# ============================================================
# TEXT HELPERS
# ============================================================

def normalize_text(text: Any) -> str:
    """
    Convert a value into clean text.

    Keeps this function lightweight so analyzer.py can be used
    independently of the Streamlit application.
    """
    if text is None:
        return ""

    return str(text).strip()


# ============================================================
# SCORE HELPERS
# ============================================================

def normalize_score(value: Any) -> float:
    """
    Convert different ATS score formats into a percentage.

    Examples:
        0.85      -> 85.0
        85        -> 85.0
        "85%"     -> 85.0
        {"score": 85} -> 85.0
    """

    if value is None:
        return 0.0

    if isinstance(value, (int, float)):
        number = float(value)

        if 0 <= number <= 1:
            number *= 100

        return max(0.0, min(100.0, number))

    if isinstance(value, str):
        cleaned = value.replace("%", "").strip()

        try:
            number = float(cleaned)

            if 0 <= number <= 1:
                number *= 100

            return max(0.0, min(100.0, number))

        except ValueError:
            return 0.0

    if isinstance(value, dict):
        for key in (
            "ats_score",
            "overall_score",
            "overall",
            "score",
            "total_score",
        ):
            if key in value:
                return normalize_score(value[key])

    return 0.0


# ============================================================
# JOB DESCRIPTION
# ============================================================

def analyze_jd(job_description: str) -> Dict[str, Any]:
    """
    Analyze a job description.

    Uses modules.jd_analyzer when available. Falls back to the
    project's skill extractor when the JD analyzer is unavailable.
    """

    job_description = normalize_text(job_description)

    if not job_description:
        return {
            "skills": [],
            "experience_years": 0,
            "education": [],
            "responsibilities": [],
        }

    if analyze_job_description is not None:
        try:
            result = analyze_job_description(job_description)

            if isinstance(result, dict):
                return result

        except Exception:
            # Fall back to basic skill extraction below.
            pass

    skills = extract_skills(job_description)

    return {
        "skills": list(skills),
        "experience_years": 0,
        "education": [],
        "responsibilities": [],
    }


# ============================================================
# JD SKILL EXTRACTION
# ============================================================

def get_jd_skills(jd_analysis: Dict[str, Any]) -> List[str]:
    """
    Extract the skill list from different possible JD-analysis
    result formats.
    """

    if not isinstance(jd_analysis, dict):
        return []

    possible_keys = (
        "skills",
        "jd_skills",
        "required_skills",
        "extracted_skills",
        "technical_skills",
    )

    for key in possible_keys:
        value = jd_analysis.get(key)

        if isinstance(value, (list, tuple, set)):
            return [
                str(item).strip()
                for item in value
                if str(item).strip()
            ]

    return []


# ============================================================
# SKILL MATCHING
# ============================================================

def match_skills(
    resume_skills: List[str],
    jd_skills: List[str],
) -> Dict[str, List[str]]:
    """
    Compare skills detected in the resume and job description.
    Matching is case-insensitive.
    """

    resume_skills = [
        str(skill).strip()
        for skill in (resume_skills or [])
        if str(skill).strip()
    ]

    jd_skills = [
        str(skill).strip()
        for skill in (jd_skills or [])
        if str(skill).strip()
    ]

    resume_map = {
        skill.lower(): skill
        for skill in resume_skills
    }

    matched = []
    missing = []

    for skill in jd_skills:
        normalized = skill.lower()

        if normalized in resume_map:
            matched.append(resume_map[normalized])
        else:
            missing.append(skill)

    return {
        "matched": matched,
        "missing": missing,
    }


# ============================================================
# ATS SCORER COMPATIBILITY
# ============================================================

def calculate_score(
    resume_text: str,
    job_description: str,
    resume_skills: Optional[List[str]] = None,
    jd_analysis: Optional[Dict[str, Any]] = None,
) -> Any:
    """
    Call the project's ATS scorer while supporting the common
    function signatures used in this project.
    """

    resume_text = normalize_text(resume_text)
    job_description = normalize_text(job_description)

    resume_skills = resume_skills or extract_skills(resume_text)
    jd_analysis = jd_analysis or analyze_jd(job_description)

    attempts = [
        (
            resume_text,
            job_description,
            resume_skills,
            jd_analysis,
        ),
        (
            resume_text,
            job_description,
            resume_skills,
        ),
        (
            resume_text,
            job_description,
        ),
    ]

    last_type_error = None

    for args in attempts:
        try:
            return calculate_ats_score(*args)

        except TypeError as exc:
            last_type_error = exc

    raise TypeError(
        "Could not call calculate_ats_score using the "
        "available scorer signature."
    ) from last_type_error


# ============================================================
# STRENGTHS
# ============================================================

def build_strengths(
    ats_result: Any,
    matched_skills: List[str],
    resume_skills: List[str],
) -> List[str]:
    """
    Generate resume strengths using the recommendations module
    when available, with a safe fallback.
    """

    if get_resume_strengths is not None:
        try:
            result = get_resume_strengths(ats_result)

            if isinstance(result, list):
                return [
                    str(item).strip()
                    for item in result
                    if str(item).strip()
                ]

        except Exception:
            pass

    score = normalize_score(ats_result)

    strengths = []

    if matched_skills:
        strengths.append(
            f"{len(matched_skills)} relevant skills match the job description."
        )

    if len(resume_skills) >= 5:
        strengths.append(
            "The resume contains a solid range of identifiable skills."
        )

    if score >= 75:
        strengths.append(
            "Strong overall alignment with the job description."
        )
    elif score >= 50:
        strengths.append(
            "Moderate alignment with the job description."
        )
    else:
        strengths.append(
            "The resume has clear opportunities for ATS optimization."
        )

    return strengths


# ============================================================
# RECOMMENDATIONS
# ============================================================

def build_recommendations(
    ats_result: Any,
    resume_skills: List[str],
    jd_skills: List[str],
    missing_skills: List[str],
) -> List[str]:
    """
    Generate ATS recommendations.

    Uses the project recommendation module when possible and
    provides fallback recommendations otherwise.
    """

    if generate_recommendations is not None:
        try:
            result = generate_recommendations(
                ats_result,
                resume_skills,
                jd_skills,
            )

            if isinstance(result, list):
                return [
                    str(item).strip()
                    for item in result
                    if str(item).strip()
                ]

        except TypeError:
            try:
                result = generate_recommendations(
                    ats_result=ats_result,
                    resume_skills=resume_skills,
                    job_skills=jd_skills,
                )

                if isinstance(result, list):
                    return [
                        str(item).strip()
                        for item in result
                        if str(item).strip()
                    ]

            except Exception:
                pass

        except Exception:
            pass

    score = normalize_score(ats_result)

    recommendations = []

    if score < 50:
        recommendations.append(
            "Improve alignment with the job description by emphasizing "
            "relevant existing skills and experience."
        )
    elif score < 70:
        recommendations.append(
            "Improve job-specific wording and keyword coverage while "
            "keeping all information factual."
        )
    else:
        recommendations.append(
            "Maintain the strong alignment while refining job-specific "
            "wording naturally."
        )

    if missing_skills:
        recommendations.append(
            "Only add missing skills when they genuinely reflect your "
            "existing knowledge or experience."
        )

    recommendations.append(
        "Use relevant job-description terminology naturally within "
        "existing resume content."
    )

    recommendations.append(
        "Make relevant responsibilities and achievements more explicit "
        "without inventing facts."
    )

    return recommendations


# ============================================================
# COMPLETE RESUME ANALYSIS
# ============================================================

def analyze_resume(
    resume_text: str,
    job_description: str,
) -> Dict[str, Any]:
    """
    Perform complete resume-vs-JD analysis.

    Returns:
        {
            "ats_score": float,
            "score_result": ...,
            "resume_skills": [...],
            "jd_analysis": {...},
            "jd_skills": [...],
            "matched_skills": [...],
            "missing_skills": [...],
            "strengths": [...],
            "recommendations": [...]
        }
    """

    resume_text = normalize_text(resume_text)
    job_description = normalize_text(job_description)

    if not resume_text:
        raise ValueError("Resume text cannot be empty.")

    if not job_description:
        raise ValueError("Job description cannot be empty.")

    # --------------------------------------------------------
    # Resume skills
    # --------------------------------------------------------

    resume_skills = extract_skills(resume_text)

    resume_skills = [
        str(skill).strip()
        for skill in resume_skills
        if str(skill).strip()
    ]

    # --------------------------------------------------------
    # JD analysis
    # --------------------------------------------------------

    jd_analysis = analyze_jd(job_description)

    jd_skills = get_jd_skills(jd_analysis)

    # --------------------------------------------------------
    # Skill matching
    # --------------------------------------------------------

    skill_match = match_skills(
        resume_skills,
        jd_skills,
    )

    matched_skills = skill_match["matched"]
    missing_skills = skill_match["missing"]

    # --------------------------------------------------------
    # ATS score
    # --------------------------------------------------------

    score_result = calculate_score(
        resume_text=resume_text,
        job_description=job_description,
        resume_skills=resume_skills,
        jd_analysis=jd_analysis,
    )

    ats_score = normalize_score(score_result)

    # --------------------------------------------------------
    # Strengths
    # --------------------------------------------------------

    strengths = build_strengths(
        ats_result=score_result,
        matched_skills=matched_skills,
        resume_skills=resume_skills,
    )

    # --------------------------------------------------------
    # Recommendations
    # --------------------------------------------------------

    recommendations = build_recommendations(
        ats_result=score_result,
        resume_skills=resume_skills,
        jd_skills=jd_skills,
        missing_skills=missing_skills,
    )

    return {
        "ats_score": round(ats_score, 2),
        "score_result": score_result,
        "resume_skills": resume_skills,
        "jd_analysis": jd_analysis,
        "jd_skills": jd_skills,
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "strengths": strengths,
        "recommendations": recommendations,
    }


# ============================================================
# BACKWARD-COMPATIBLE ALIASES
# ============================================================

def analyze(
    resume_text: str,
    job_description: str,
) -> Dict[str, Any]:
    """
    Short alias for analyze_resume().
    """
    return analyze_resume(
        resume_text,
        job_description,
    )


def run_analysis(
    resume_text: str,
    job_description: str,
) -> Dict[str, Any]:
    """
    Alias used by scripts or tests that expect a run_analysis()
    entry point.
    """
    return analyze_resume(
        resume_text,
        job_description,
    )


# ============================================================
# TEST / SCRIPT ENTRY POINT
# ============================================================

if __name__ == "__main__":
    print(
        "AI Resume Analyzer analyzer.py loaded successfully."
    )
    print(
        "Use analyze_resume(resume_text, job_description) "
        "to run an analysis."
    )
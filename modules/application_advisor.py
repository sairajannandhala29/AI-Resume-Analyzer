"""
Application Recommendation Engine
----------------------------------

Calculates an application-readiness score using:

- Final ATS score
- JD skill match
- Missing skills
- Resume strength
- Overall alignment

This module does not modify the resume.
"""


# ============================================================
# SCORE HELPERS
# ============================================================

def _safe_float(value, default=0.0):
    try:
        if value is None:
            return default

        if isinstance(value, str):
            value = value.replace("%", "").strip()

        return float(value)

    except (TypeError, ValueError):
        return default


def _clamp(value, minimum=0.0, maximum=100.0):
    return max(
        minimum,
        min(maximum, value),
    )


# ============================================================
# SKILL MATCH
# ============================================================

def calculate_skill_match(
    matched_skills,
    jd_skills,
):
    """
    Calculate percentage of JD skills already present
    in the resume.
    """
    if not jd_skills:
        return 100.0

    matched = {
        str(skill).strip().lower()
        for skill in (matched_skills or [])
        if str(skill).strip()
    }

    required = {
        str(skill).strip().lower()
        for skill in (jd_skills or [])
        if str(skill).strip()
    }

    if not required:
        return 100.0

    return round(
        _clamp(
            (len(matched) / len(required)) * 100
        ),
        2,
    )


# ============================================================
# APPLICATION SCORE
# ============================================================

def calculate_application_score(
    ats_score,
    skill_match,
    experience_score=0,
    semantic_score=0,
    structure_score=0,
):
    """
    Calculate an overall application readiness score.

    Weighting:
        ATS Score        40%
        Skill Match      25%
        Semantic Match   15%
        Experience       10%
        Structure        10%
    """
    ats_score = _clamp(
        _safe_float(ats_score)
    )

    skill_match = _clamp(
        _safe_float(skill_match)
    )

    semantic_score = _clamp(
        _safe_float(semantic_score)
    )

    experience_score = _clamp(
        _safe_float(experience_score)
    )

    structure_score = _clamp(
        _safe_float(structure_score)
    )

    score = (
        ats_score * 0.40
        + skill_match * 0.25
        + semantic_score * 0.15
        + experience_score * 0.10
        + structure_score * 0.10
    )

    return round(
        _clamp(score),
        2,
    )


# ============================================================
# DECISION LEVEL
# ============================================================

def get_application_decision(application_score):
    """
    Convert application score into a readable recommendation.
    """
    score = _safe_float(
        application_score
    )

    if score >= 80:
        return {
            "decision": "Strongly Recommended",
            "level": "strong",
            "emoji": "🟢",
            "message": (
                "Your resume shows strong alignment with "
                "the job description. You can confidently "
                "apply."
            ),
        }

    if score >= 65:
        return {
            "decision": "Recommended",
            "level": "good",
            "emoji": "🟢",
            "message": (
                "Your resume has good alignment with the "
                "job description. Applying is reasonable."
            ),
        }

    if score >= 50:
        return {
            "decision": "Apply with Improvements",
            "level": "moderate",
            "emoji": "🟡",
            "message": (
                "Your resume has moderate alignment. "
                "Improving relevant skills and wording "
                "could strengthen the application."
            ),
        }

    return {
        "decision": "Needs Improvement",
        "level": "weak",
        "emoji": "🔴",
        "message": (
            "Your resume currently has limited alignment "
            "with the job description. Consider improving "
            "the resume before applying."
        ),
    }


# ============================================================
# SELECTION CHANCE
# ============================================================

def estimate_selection_chance(
    application_score,
    ats_score,
    skill_match,
):
    """
    Estimate a broad selection-chance category.

    This is NOT a prediction of actual hiring probability.
    It is an application-readiness indicator based only
    on resume/JD alignment.
    """
    application_score = _safe_float(
        application_score
    )

    ats_score = _safe_float(
        ats_score
    )

    skill_match = _safe_float(
        skill_match
    )

    combined = (
        application_score * 0.50
        + ats_score * 0.25
        + skill_match * 0.25
    )

    combined = _clamp(
        combined
    )

    if combined >= 85:
        return {
            "chance": "High",
            "percentage_range": "70-90%",
            "score": round(combined, 2),
        }

    if combined >= 70:
        return {
            "chance": "Good",
            "percentage_range": "50-70%",
            "score": round(combined, 2),
        }

    if combined >= 55:
        return {
            "chance": "Moderate",
            "percentage_range": "30-50%",
            "score": round(combined, 2),
        }

    if combined >= 40:
        return {
            "chance": "Low",
            "percentage_range": "15-30%",
            "score": round(combined, 2),
        }

    return {
        "chance": "Very Low",
        "percentage_range": "Below 15%",
        "score": round(combined, 2),
    }


# ============================================================
# STRENGTHS
# ============================================================

def _build_strengths(
    ats_score,
    skill_match,
    semantic_score,
    experience_score,
    structure_score,
):
    """
    Generate factual strength messages from calculated scores.
    """
    strengths = []

    if ats_score >= 80:
        strengths.append(
            "Strong overall ATS alignment."
        )
    elif ats_score >= 65:
        strengths.append(
            "Good overall ATS alignment."
        )

    if skill_match >= 80:
        strengths.append(
            "Strong coverage of the skills requested in the JD."
        )
    elif skill_match >= 60:
        strengths.append(
            "A good portion of the required JD skills are already present."
        )

    if semantic_score >= 75:
        strengths.append(
            "Strong semantic similarity with the job description."
        )
    elif semantic_score >= 60:
        strengths.append(
            "Resume wording has reasonable semantic alignment with the JD."
        )

    if experience_score >= 75:
        strengths.append(
            "Experience alignment is strong for the analyzed role."
        )

    if structure_score >= 90:
        strengths.append(
            "Resume structure is highly ATS-friendly."
        )

    return strengths


# ============================================================
# GAPS
# ============================================================

def _build_gaps(
    missing_skills,
    ats_score,
    skill_match,
):
    """
    Generate the main application gaps.
    """
    gaps = []

    if missing_skills:
        gaps.append(
            "Missing or undetected JD skills: "
            + ", ".join(
                str(skill)
                for skill in missing_skills[:10]
            )
        )

    if skill_match < 60:
        gaps.append(
            "JD skill coverage is currently below the preferred level."
        )

    if ats_score < 50:
        gaps.append(
            "Overall ATS alignment is currently low."
        )
    elif ats_score < 65:
        gaps.append(
            "Overall ATS alignment can be improved."
        )

    return gaps


# ============================================================
# MAIN RECOMMENDATION
# ============================================================

def calculate_application_recommendation(
    ats_score=0,
    matched_skills=None,
    missing_skills=None,
    jd_skills=None,
    semantic_score=0,
    experience_score=0,
    structure_score=0,
    **kwargs,
):
    """
    Calculate a complete application recommendation.

    Parameters are intentionally flexible so this function can
    work with different ATS result dictionaries used by the app.

    Returns a dictionary containing:

    - ats_score
    - skill_match
    - application_score
    - selection_chance
    - decision
    - message
    - strengths
    - missing_skills
    - recommendation
    """
    # --------------------------------------------------------
    # Support alternate argument names
    # --------------------------------------------------------

    if not ats_score:
        ats_score = kwargs.get(
            "score",
            kwargs.get(
                "final_ats_score",
                0,
            ),
        )

    if not matched_skills:
        matched_skills = kwargs.get(
            "matched",
            kwargs.get(
                "matched_jd_skills",
                [],
            ),
        )

    if not missing_skills:
        missing_skills = kwargs.get(
            "missing",
            kwargs.get(
                "missing_jd_skills",
                [],
            ),
        )

    if not jd_skills:
        jd_skills = kwargs.get(
            "job_skills",
            kwargs.get(
                "required_skills",
                [],
            ),
        )

    # --------------------------------------------------------
    # Normalize list values
    # --------------------------------------------------------

    matched_skills = (
        list(matched_skills)
        if matched_skills
        else []
    )

    missing_skills = (
        list(missing_skills)
        if missing_skills
        else []
    )

    jd_skills = (
        list(jd_skills)
        if jd_skills
        else []
    )

    # --------------------------------------------------------
    # Skill match
    # --------------------------------------------------------

    if not jd_skills:
        total_skill_count = (
            len(matched_skills)
            + len(missing_skills)
        )

        if total_skill_count:
            jd_skills = (
                matched_skills
                + missing_skills
            )

    skill_match = calculate_skill_match(
        matched_skills=matched_skills,
        jd_skills=jd_skills,
    )

    # --------------------------------------------------------
    # Calculate application score
    # --------------------------------------------------------

    application_score = calculate_application_score(
        ats_score=ats_score,
        skill_match=skill_match,
        semantic_score=semantic_score,
        experience_score=experience_score,
        structure_score=structure_score,
    )

    # --------------------------------------------------------
    # Decision
    # --------------------------------------------------------

    decision_data = get_application_decision(
        application_score
    )

    # --------------------------------------------------------
    # Selection chance
    # --------------------------------------------------------

    selection_data = estimate_selection_chance(
        application_score=application_score,
        ats_score=ats_score,
        skill_match=skill_match,
    )

    # --------------------------------------------------------
    # Strengths
    # --------------------------------------------------------

    strengths = _build_strengths(
        ats_score=_safe_float(ats_score),
        skill_match=skill_match,
        semantic_score=_safe_float(
            semantic_score
        ),
        experience_score=_safe_float(
            experience_score
        ),
        structure_score=_safe_float(
            structure_score
        ),
    )

    # --------------------------------------------------------
    # Gaps
    # --------------------------------------------------------

    gaps = _build_gaps(
        missing_skills=missing_skills,
        ats_score=_safe_float(ats_score),
        skill_match=skill_match,
    )

    # --------------------------------------------------------
    # Recommendation text
    # --------------------------------------------------------

    if application_score >= 80:
        recommendation = (
            "Your resume is well aligned with this job. "
            "Apply with the optimized version while ensuring "
            "all information remains factually accurate."
        )

    elif application_score >= 65:
        recommendation = (
            "Your resume is reasonably aligned with this job. "
            "Applying is recommended, with further improvement "
            "to relevant skill coverage where genuinely supported."
        )

    elif application_score >= 50:
        recommendation = (
            "Your resume has moderate alignment. "
            "Improve relevant wording and strengthen supported "
            "JD skill coverage before applying."
        )

    else:
        recommendation = (
            "Your resume currently has limited alignment. "
            "Consider optimizing the resume and addressing "
            "genuine skill gaps before applying."
        )

    # --------------------------------------------------------
    # Return
    # --------------------------------------------------------

    return {
        "ats_score": round(
            _safe_float(ats_score),
            2,
        ),
        "skill_match": round(
            skill_match,
            2,
        ),
        "application_score": round(
            application_score,
            2,
        ),
        "selection_chance": selection_data[
            "chance"
        ],
        "selection_percentage_range": selection_data[
            "percentage_range"
        ],
        "selection_score": selection_data[
            "score"
        ],
        "decision": decision_data[
            "decision"
        ],
        "level": decision_data[
            "level"
        ],
        "emoji": decision_data[
            "emoji"
        ],
        "message": decision_data[
            "message"
        ],
        "strengths": strengths,
        "missing_skills": missing_skills,
        "matched_skills": matched_skills,
        "recommendation": recommendation,
        "semantic_score": round(
            _safe_float(semantic_score),
            2,
        ),
        "experience_score": round(
            _safe_float(experience_score),
            2,
        ),
        "structure_score": round(
            _safe_float(structure_score),
            2,
        ),
    }


# ============================================================
# BACKWARD-COMPATIBLE ALIASES
# ============================================================

calculate_application_score_with_details = (
    calculate_application_recommendation
)

get_application_recommendation = (
    calculate_application_recommendation
)

estimate_selection_probability = (
    estimate_selection_chance
)
"""
Resume Strengths and ATS Recommendations
----------------------------------------

Provides:
- Resume strengths
- ATS improvement recommendations
- Skill-gap recommendations

This module does not modify the uploaded resume.
"""


# ============================================================
# HELPERS
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


def _unique(items):
    """
    Preserve order while removing duplicates.
    """
    result = []
    seen = set()

    for item in items or []:
        text = str(item).strip()

        if not text:
            continue

        key = text.lower()

        if key not in seen:
            seen.add(key)
            result.append(text)

    return result


# ============================================================
# RESUME STRENGTHS
# ============================================================

def get_resume_strengths(
    ats_analysis=None,
    resume_text="",
    resume_skills=None,
    jd_skills=None,
    matched_skills=None,
):
    """
    Generate strengths based on the available ATS analysis.

    The function uses only information already supplied by
    the analyzer. It does not invent resume claims.
    """
    ats_analysis = ats_analysis or {}

    resume_skills = resume_skills or []
    jd_skills = jd_skills or []
    matched_skills = matched_skills or []

    strengths = []

    ats_score = _safe_float(
        ats_analysis.get(
            "ats_score",
            ats_analysis.get(
                "score",
                0,
            ),
        )
    )

    skill_score = _safe_float(
        ats_analysis.get(
            "skill_score",
            ats_analysis.get(
                "skills",
                0,
            ),
        )
    )

    semantic_score = _safe_float(
        ats_analysis.get(
            "semantic_score",
            ats_analysis.get(
                "semantic",
                0,
            ),
        )
    )

    experience_score = _safe_float(
        ats_analysis.get(
            "experience_score",
            ats_analysis.get(
                "experience",
                0,
            ),
        )
    )

    keyword_score = _safe_float(
        ats_analysis.get(
            "keyword_score",
            ats_analysis.get(
                "keywords",
                0,
            ),
        )
    )

    structure_score = _safe_float(
        ats_analysis.get(
            "structure_score",
            ats_analysis.get(
                "structure",
                0,
            ),
        )
    )

    # --------------------------------------------------------
    # Overall ATS strength
    # --------------------------------------------------------

    if ats_score >= 80:
        strengths.append(
            "Strong overall ATS alignment with the target job."
        )

    elif ats_score >= 65:
        strengths.append(
            "Good overall ATS alignment with the target job."
        )

    elif ats_score >= 50:
        strengths.append(
            "Moderate ATS alignment with opportunities for improvement."
        )

    # --------------------------------------------------------
    # Skills
    # --------------------------------------------------------

    if skill_score >= 80:
        strengths.append(
            "Strong coverage of job-relevant technical and professional skills."
        )

    elif skill_score >= 60:
        strengths.append(
            "A good portion of the required skills are already represented."
        )

    if matched_skills:
        strengths.append(
            f"{len(matched_skills)} relevant JD skill"
            f"{'' if len(matched_skills) == 1 else 's'} "
            "already detected in the resume."
        )

    # --------------------------------------------------------
    # Semantic alignment
    # --------------------------------------------------------

    if semantic_score >= 80:
        strengths.append(
            "Resume content has strong semantic alignment with the JD."
        )

    elif semantic_score >= 65:
        strengths.append(
            "Resume wording has good semantic relevance to the JD."
        )

    # --------------------------------------------------------
    # Experience
    # --------------------------------------------------------

    if experience_score >= 80:
        strengths.append(
            "Experience content aligns well with the target requirements."
        )

    elif experience_score >= 60:
        strengths.append(
            "Experience section shows reasonable relevance to the target role."
        )

    # --------------------------------------------------------
    # Keywords
    # --------------------------------------------------------

    if keyword_score >= 80:
        strengths.append(
            "Strong use of relevant job-description terminology."
        )

    elif keyword_score >= 60:
        strengths.append(
            "Relevant keywords are present and can be improved further."
        )

    # --------------------------------------------------------
    # Structure
    # --------------------------------------------------------

    if structure_score >= 90:
        strengths.append(
            "Resume structure is highly compatible with ATS processing."
        )

    elif structure_score >= 75:
        strengths.append(
            "Resume has a generally ATS-friendly structure."
        )

    # --------------------------------------------------------
    # Resume skill count
    # --------------------------------------------------------

    if len(resume_skills) >= 10:
        strengths.append(
            f"{len(resume_skills)} skills were detected in the resume."
        )

    # --------------------------------------------------------
    # JD skill count
    # --------------------------------------------------------

    if jd_skills and matched_skills:
        match_ratio = (
            len(matched_skills)
            / max(len(jd_skills), 1)
        )

        if match_ratio >= 0.70:
            strengths.append(
                "Most detected JD skills have corresponding "
                "resume skill coverage."
            )

    return _unique(strengths)


# ============================================================
# GENERAL RECOMMENDATIONS
# ============================================================

def generate_recommendations(
    ats_analysis=None,
    missing_skills=None,
    matched_skills=None,
    jd_analysis=None,
    resume_text="",
):
    """
    Generate ATS recommendations based on analysis results.
    """
    ats_analysis = ats_analysis or {}
    jd_analysis = jd_analysis or {}

    missing_skills = _unique(
        missing_skills or []
    )

    matched_skills = _unique(
        matched_skills or []
    )

    recommendations = []

    ats_score = _safe_float(
        ats_analysis.get(
            "ats_score",
            ats_analysis.get(
                "score",
                0,
            ),
        )
    )

    skill_score = _safe_float(
        ats_analysis.get(
            "skill_score",
            ats_analysis.get(
                "skills",
                0,
            ),
        )
    )

    semantic_score = _safe_float(
        ats_analysis.get(
            "semantic_score",
            ats_analysis.get(
                "semantic",
                0,
            ),
        )
    )

    experience_score = _safe_float(
        ats_analysis.get(
            "experience_score",
            ats_analysis.get(
                "experience",
                0,
            ),
        )
    )

    keyword_score = _safe_float(
        ats_analysis.get(
            "keyword_score",
            ats_analysis.get(
                "keywords",
                0,
            ),
        )
    )

    structure_score = _safe_float(
        ats_analysis.get(
            "structure_score",
            ats_analysis.get(
                "structure",
                0,
            ),
        )
    )

    # ========================================================
    # OVERALL ATS
    # ========================================================

    if ats_score < 50:
        recommendations.append(
            "The resume has low alignment with the job description. "
            "Prioritize relevant skills, experience, and keywords."
        )

    elif ats_score < 70:
        recommendations.append(
            "The resume has moderate alignment. "
            "Improve job-specific wording and relevant skill coverage."
        )

    else:
        recommendations.append(
            "Maintain the current alignment while refining job-specific wording."
        )

    # ========================================================
    # SKILLS
    # ========================================================

    if missing_skills:
        shown = ", ".join(
            missing_skills[:5]
        )

        recommendations.append(
            "Consider adding the following skills only if you "
            "genuinely have experience with them: "
            f"{shown}."
        )

    if skill_score < 50:
        recommendations.append(
            "Increase alignment between your existing skills "
            "and the skills requested in the JD."
        )

    elif skill_score < 70:
        recommendations.append(
            "Improve the visibility and placement of your "
            "existing job-relevant skills."
        )

    # ========================================================
    # SEMANTIC MATCH
    # ========================================================

    if semantic_score < 60:
        recommendations.append(
            "Improve semantic alignment by using job-relevant "
            "terminology naturally within your existing experience."
        )

    elif semantic_score < 75:
        recommendations.append(
            "Strengthen semantic alignment by using clearer "
            "job-relevant wording supported by your experience."
        )

    # ========================================================
    # EXPERIENCE
    # ========================================================

    if experience_score < 50:
        recommendations.append(
            "Review the experience section and make relevant "
            "responsibilities, tools, and outcomes more explicit."
        )

    elif experience_score < 70:
        recommendations.append(
            "Refine experience descriptions to better connect "
            "your existing responsibilities with the target role."
        )

    # ========================================================
    # KEYWORDS
    # ========================================================

    if keyword_score < 50:
        recommendations.append(
            "Improve keyword coverage by naturally incorporating "
            "relevant terminology from the JD where it accurately "
            "reflects your experience."
        )

    elif keyword_score < 70:
        recommendations.append(
            "Use existing relevant keywords more consistently "
            "throughout the resume."
        )

    # ========================================================
    # STRUCTURE
    # ========================================================

    if structure_score < 70:
        recommendations.append(
            "Improve resume structure and formatting for easier "
            "ATS parsing."
        )

    elif structure_score < 90:
        recommendations.append(
            "Keep formatting consistent and easy for ATS systems "
            "to parse."
        )

    # ========================================================
    # JOB DESCRIPTION EXPERIENCE
    # ========================================================

    required_experience = _safe_float(
        jd_analysis.get(
            "experience_years",
            0,
        )
    )

    if required_experience > 0 and experience_score < 60:
        recommendations.append(
            f"The JD indicates approximately "
            f"{required_experience:g}+ years of experience. "
            "Ensure your resume clearly presents only your "
            "actual relevant experience."
        )

    # ========================================================
    # EDUCATION
    # ========================================================

    education = jd_analysis.get(
        "education",
        [],
    )

    if education and not resume_text:
        recommendations.append(
            "Review the education section to ensure relevant "
            "qualifications are clearly visible."
        )

    return _unique(recommendations)


# ============================================================
# SKILL-SPECIFIC RECOMMENDATIONS
# ============================================================

def get_skill_recommendations(
    missing_skills=None,
    max_items=10,
):
    """
    Convert missing skills into safe recommendations.

    The output explicitly avoids claiming that the candidate
    possesses a missing skill.
    """
    missing_skills = _unique(
        missing_skills or []
    )

    if max_items is None:
        max_items = len(missing_skills)

    recommendations = []

    for skill in missing_skills[:max_items]:
        recommendations.append(
            f"Consider including {skill} only if you have "
            "genuine experience or training with it."
        )

    return recommendations


# ============================================================
# FULL REPORT
# ============================================================

def build_recommendation_report(
    ats_analysis=None,
    resume_text="",
    resume_skills=None,
    jd_skills=None,
    matched_skills=None,
    missing_skills=None,
    jd_analysis=None,
):
    """
    Produce a complete recommendations report.
    """
    strengths = get_resume_strengths(
        ats_analysis=ats_analysis,
        resume_text=resume_text,
        resume_skills=resume_skills,
        jd_skills=jd_skills,
        matched_skills=matched_skills,
    )

    recommendations = generate_recommendations(
        ats_analysis=ats_analysis,
        missing_skills=missing_skills,
        matched_skills=matched_skills,
        jd_analysis=jd_analysis,
        resume_text=resume_text,
    )

    skill_recommendations = get_skill_recommendations(
        missing_skills=missing_skills,
    )

    return {
        "strengths": strengths,
        "recommendations": recommendations,
        "skill_recommendations": skill_recommendations,
    }


# ============================================================
# BACKWARD-COMPATIBLE ALIASES
# ============================================================

get_recommendations = generate_recommendations

get_strengths = get_resume_strengths

get_ats_recommendations = generate_recommendations

build_recommendations = build_recommendation_report
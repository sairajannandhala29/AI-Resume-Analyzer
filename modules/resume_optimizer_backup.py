# modules/resume_optimizer.py

from __future__ import annotations

import re
from typing import Any, Dict, List

from modules.ai_rewriter import rewrite_resume
from modules.fact_validator import validate_generated_resume
from modules.skill_extractor import extract_skills


# ============================================================
# HELPERS
# ============================================================

def _safe_list(value) -> List[str]:
    if value is None:
        return []

    if isinstance(value, list):
        return [str(x).strip() for x in value if str(x).strip()]

    if isinstance(value, str):
        return [
            x.strip("•- \t")
            for x in re.split(r"[\n,;]+", value)
            if x.strip()
        ]

    return []


def _unique(items: List[str]) -> List[str]:
    result = []
    seen = set()

    for item in items:
        value = str(item).strip()

        if not value:
            continue

        key = value.lower()

        if key not in seen:
            seen.add(key)
            result.append(value)

    return result


def _normalise_resume(result: Dict[str, Any]) -> Dict[str, Any]:

    return {
        "summary": str(
            result.get("summary", "")
        ).strip(),

        "skills": _unique(
            _safe_list(result.get("skills", []))
        ),

        "experience": _safe_list(
            result.get("experience", [])
        ),

        "projects": _safe_list(
            result.get("projects", [])
        ),

        "education": _safe_list(
            result.get("education", [])
        ),

        "certifications": _safe_list(
            result.get("certifications", [])
        ),

        "achievements": _safe_list(
            result.get("achievements", [])
        ),
    }


# ============================================================
# CONVERT STRUCTURED RESUME BACK TO TEXT
# ============================================================

def resume_to_text(resume: Dict[str, Any]) -> str:

    parts = []

    summary = resume.get("summary", "")

    if summary:
        parts.append("PROFESSIONAL SUMMARY")
        parts.append(summary)

    skills = resume.get("skills", [])

    if skills:
        parts.append("SKILLS")
        parts.append(", ".join(skills))

    experience = resume.get("experience", [])

    if experience:
        parts.append("PROFESSIONAL EXPERIENCE")

        for item in experience:
            parts.append(str(item))

    projects = resume.get("projects", [])

    if projects:
        parts.append("PROJECTS")

        for item in projects:
            parts.append(str(item))

    education = resume.get("education", [])

    if education:
        parts.append("EDUCATION")

        for item in education:
            parts.append(str(item))

    certifications = resume.get("certifications", [])

    if certifications:
        parts.append("CERTIFICATIONS")

        for item in certifications:
            parts.append(str(item))

    achievements = resume.get("achievements", [])

    if achievements:
        parts.append("ACHIEVEMENTS")

        for item in achievements:
            parts.append(str(item))

    return "\n".join(parts)


# ============================================================
# JD SKILL GAP
# ============================================================

def get_skill_gap(
    resume_text: str,
    job_description: str,
) -> Dict[str, List[str]]:

    resume_skills = _unique(
        extract_skills(resume_text)
    )

    jd_skills = _unique(
        extract_skills(job_description)
    )

    resume_lower = {
        x.lower()
        for x in resume_skills
    }

    matched = []
    missing = []

    for skill in jd_skills:

        if skill.lower() in resume_lower:
            matched.append(skill)
        else:
            missing.append(skill)

    return {
        "resume_skills": resume_skills,
        "jd_skills": jd_skills,
        "matched": matched,
        "missing": missing,
    }


# ============================================================
# AI OPTIMIZATION PROMPT
# ============================================================

def build_optimization_context(
    original_resume: str,
    job_description: str,
    current_resume: Dict[str, Any] | None = None,
    ats_analysis: Dict[str, Any] | None = None,
) -> str:

    skill_gap = get_skill_gap(
        original_resume,
        job_description,
    )

    matched = skill_gap["matched"]
    missing = skill_gap["missing"]

    current_text = ""

    if current_resume:
        current_text = resume_to_text(
            current_resume
        )

    score = 0

    if ats_analysis:
        score = ats_analysis.get(
            "ats_score",
            0,
        )

    context = f"""
You are an expert ATS resume optimizer.

OBJECTIVE:
Increase the resume's genuine ATS relevance for the supplied job description.

CURRENT ATS SCORE:
{score}%

TARGET:
Aim for 80-90% ONLY when the candidate's existing information supports it.

IMPORTANT:
Never invent information.

You MUST NOT fabricate:
- employment
- companies
- job titles
- years of experience
- dates
- degrees
- certifications
- projects
- achievements
- metrics
- responsibilities
- technologies the candidate never demonstrated

You MAY:
- rewrite existing content
- improve wording
- improve ATS keyword placement
- use keywords already supported by the original resume
- combine existing information more effectively
- make existing responsibilities clearer
- improve semantic alignment
- move relevant existing skills into prominent sections

JOB DESCRIPTION:
{job_description}

ORIGINAL RESUME:
{original_resume}

SKILLS ALREADY SUPPORTED BY RESUME:
{", ".join(skill_gap["resume_skills"])}

MATCHED JD SKILLS:
{", ".join(matched)}

IMPORTANT JD SKILLS NOT CURRENTLY DETECTED:
{", ".join(missing)}

CURRENT OPTIMIZED VERSION:
{current_text}

OPTIMIZATION RULES:

1. Professional Summary
Create a highly targeted ATS summary using relevant skills and responsibilities
that are actually supported by the original resume.

2. Skills
Prioritize skills that are explicitly present or clearly supported by the original resume.

3. Experience
Rewrite bullets using strong action verbs and terminology from the JD,
but only when the original experience supports the statement.

4. Projects
Improve project descriptions using relevant terminology already supported
by the original resume.

5. Keywords
Place important supported JD keywords naturally in:
- summary
- skills
- experience
- projects

6. Do not keyword stuff.

7. Preserve factual accuracy.

8. Do not remove relevant original information.

9. Do not add unsupported skills simply to increase the ATS score.

10. Make the resume highly targeted to this particular JD.

Return ONLY the structured resume in the format expected by the application.
"""

    return context


# ============================================================
# SINGLE OPTIMIZATION PASS
# ============================================================

def optimize_resume_with_ai(
    original_resume: str,
    job_description: str,
    ats_analysis: Dict[str, Any],
    provider: str,
    current_resume: Dict[str, Any] | None = None,
) -> Dict[str, Any]:

    prompt = build_optimization_context(
        original_resume=original_resume,
        job_description=job_description,
        current_resume=current_resume,
        ats_analysis=ats_analysis,
    )

    result = rewrite_resume(
        original_resume,
        job_description,
        provider=provider,
        optimization_context=prompt,
    )

    if not isinstance(result, dict):
        raise ValueError(
            "AI optimizer did not return a structured resume."
        )

    return _normalise_resume(result)


# ============================================================
# MAIN OPTIMIZER
# ============================================================

def generate_verified_optimized_resume(
    resume_text: str,
    job_description: str,
    ats_analysis: Dict[str, Any],
    provider: str,
) -> Dict[str, Any]:

    # --------------------------------------------------------
    # First AI pass
    # --------------------------------------------------------

    optimized = optimize_resume_with_ai(
        original_resume=resume_text,
        job_description=job_description,
        ats_analysis=ats_analysis,
        provider=provider,
        current_resume=None,
    )

    # --------------------------------------------------------
    # Fact validation
    # --------------------------------------------------------

    generated_text = resume_to_text(
        optimized
    )

    validation = validate_generated_resume(
        original_text=resume_text,
        generated_text=generated_text,
    )

    # --------------------------------------------------------
    # Skill information
    # --------------------------------------------------------

    skill_gap = get_skill_gap(
        resume_text,
        job_description,
    )

    optimized_skills = optimized.get(
        "skills",
        [],
    )

    optimized["skills"] = _unique(
        optimized_skills
    )

    # --------------------------------------------------------
    # Metadata
    # --------------------------------------------------------

    optimized["supported_jd_skills"] = (
        skill_gap["matched"]
    )

    optimized["missing_jd_skills"] = (
        skill_gap["missing"]
    )

    optimized["validation"] = validation

    optimized["ai_provider"] = provider

    optimized["original_ats_score"] = (
        ats_analysis.get(
            "ats_score",
            0,
        )
    )

    return optimized


# ============================================================
# BACKWARD COMPATIBILITY
# ============================================================

def optimize_resume(
    resume_text: str,
    job_description: str,
    ats_analysis: Dict[str, Any] | None = None,
):

    """
    Existing rule-based entry point.

    Kept for compatibility with the existing app.
    """

    ats_analysis = ats_analysis or {}

    skill_gap = get_skill_gap(
        resume_text,
        job_description,
    )

    return {
        "summary": "",
        "skills": skill_gap["resume_skills"],
        "experience": [],
        "projects": [],
        "education": [],
        "certifications": [],
        "achievements": [],
        "supported_jd_skills": skill_gap["matched"],
        "missing_jd_skills": skill_gap["missing"],
        "original_ats_score": ats_analysis.get(
            "ats_score",
            0,
        ),
    }
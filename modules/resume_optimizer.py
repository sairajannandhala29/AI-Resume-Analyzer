"""
resume_optimizer.py

AI-powered resume optimization layer.

Responsibilities:
- Compare the resume with the job description
- Build a strict optimization prompt
- Ask the selected AI provider to rewrite supported content
- Validate the generated resume against the original
- Preserve factual information
- Return a structured result for resume_editor.py
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from modules.ai_rewriter import rewrite_resume
from modules.fact_validator import validate_generated_resume
from modules.skill_extractor import extract_skills


# ============================================================
# HELPERS
# ============================================================

def _safe_list(value: Any) -> List[str]:
    """
    Convert a simple value into a list of strings.
    """

    if value is None:
        return []

    if isinstance(value, list):
        result = []

        for item in value:
            if isinstance(item, dict):
                result.append(item)
            else:
                text = str(item).strip()

                if text:
                    result.append(text)

        return result

    if isinstance(value, tuple):
        return [
            str(item).strip()
            for item in value
            if str(item).strip()
        ]

    if isinstance(value, str):
        return [
            item.strip("•- \t")
            for item in re.split(
                r"[\n,;]+",
                value,
            )
            if item.strip()
        ]

    return []


def _unique(items: List[Any]) -> List[Any]:
    """
    Remove duplicate simple values while preserving order.

    Dictionaries are preserved as structured objects.
    """

    result = []
    seen = set()

    for item in items:
        if isinstance(item, dict):
            result.append(item)
            continue

        value = str(item).strip()

        if not value:
            continue

        key = value.lower()

        if key not in seen:
            seen.add(key)
            result.append(value)

    return result


# ============================================================
# STRUCTURED RESULT NORMALIZATION
# ============================================================

def _normalize_items(value: Any) -> List[Any]:
    """
    Normalize structured resume sections without converting
    dictionaries into raw string representations.
    """

    if value is None:
        return []

    if isinstance(value, dict):
        return [dict(value)]

    if isinstance(value, list):
        result = []

        for item in value:

            if isinstance(item, dict):
                result.append(dict(item))

            elif isinstance(item, str):
                text = item.strip()

                if text:
                    result.append(text)

        return result

    if isinstance(value, tuple):
        return _normalize_items(
            list(value)
        )

    if isinstance(value, str):
        result = []

        for line in value.splitlines():
            line = line.strip("•- \t")

            if line:
                result.append(line)

        return result

    return []


def _normalise_resume(
    result: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Normalize the AI-generated structured resume.
    """

    if not isinstance(result, dict):
        raise ValueError(
            "AI optimizer returned an invalid result."
        )

    return {
        "summary": str(
            result.get(
                "summary",
                "",
            )
            or ""
        ).strip(),

        "skills": _unique(
            _safe_list(
                result.get(
                    "skills",
                    [],
                )
            )
        ),

        "experience": _normalize_items(
            result.get(
                "experience",
                [],
            )
        ),

        "projects": _normalize_items(
            result.get(
                "projects",
                [],
            )
        ),

        "education": _normalize_items(
            result.get(
                "education",
                [],
            )
        ),

        "certifications": _normalize_items(
            result.get(
                "certifications",
                [],
            )
        ),

        "achievements": _normalize_items(
            result.get(
                "achievements",
                [],
            )
        ),
    }


# ============================================================
# STRUCTURED ITEM TO TEXT
# ============================================================

def _item_to_text(item: Any) -> str:
    """
    Convert a structured item into clean text for validation.
    """

    if item is None:
        return ""

    if isinstance(item, dict):

        preferred_keys = [
            "name",
            "title",
            "project_name",
            "description",
            "details",
            "content",
            "text",
        ]

        parts = []

        for key in preferred_keys:
            value = item.get(key)

            if value is not None:
                text = str(value).strip()

                if text:
                    parts.append(text)

        if parts:
            return " ".join(parts)

        return " ".join(
            str(value).strip()
            for value in item.values()
            if value is not None
            and str(value).strip()
        )

    return str(item).strip()


# ============================================================
# CONVERT RESUME TO TEXT
# ============================================================

def resume_to_text(
    resume: Dict[str, Any],
) -> str:
    """
    Convert a structured resume into text for validation
    and analysis.
    """

    if not isinstance(resume, dict):
        return ""

    parts = []

    summary = str(
        resume.get(
            "summary",
            "",
        )
        or ""
    ).strip()

    if summary:
        parts.append(
            "PROFESSIONAL SUMMARY"
        )
        parts.append(summary)

    skills = resume.get(
        "skills",
        [],
    )

    if skills:
        parts.append(
            "SKILLS"
        )

        if isinstance(
            skills,
            (list, tuple),
        ):
            parts.append(
                ", ".join(
                    str(skill).strip()
                    for skill in skills
                    if str(skill).strip()
                )
            )
        else:
            parts.append(
                str(skills).strip()
            )

    section_titles = [
        (
            "experience",
            "PROFESSIONAL EXPERIENCE",
        ),
        (
            "projects",
            "PROJECTS",
        ),
        (
            "education",
            "EDUCATION",
        ),
        (
            "certifications",
            "CERTIFICATIONS",
        ),
        (
            "achievements",
            "ACHIEVEMENTS",
        ),
    ]

    for section_key, section_title in section_titles:

        items = resume.get(
            section_key,
            [],
        )

        if not items:
            continue

        parts.append(
            section_title
        )

        if isinstance(
            items,
            (list, tuple),
        ):
            for item in items:
                text = _item_to_text(
                    item
                )

                if text:
                    parts.append(text)

        else:
            text = _item_to_text(
                items
            )

            if text:
                parts.append(text)

    return "\n".join(parts).strip()


# ============================================================
# SKILL GAP
# ============================================================

def get_skill_gap(
    resume_text: str,
    job_description: str,
) -> Dict[str, List[str]]:
    """
    Identify matched and missing JD skills.
    """

    resume_skills = _unique(
        extract_skills(
            resume_text
        )
    )

    jd_skills = _unique(
        extract_skills(
            job_description
        )
    )

    resume_lookup = {
        str(skill).lower(): skill
        for skill in resume_skills
    }

    matched = []
    missing = []

    for skill in jd_skills:

        key = str(skill).lower()

        if key in resume_lookup:
            matched.append(
                resume_lookup[key]
            )
        else:
            missing.append(
                skill
            )

    return {
        "resume_skills": resume_skills,
        "jd_skills": jd_skills,
        "matched": matched,
        "missing": missing,
    }


# ============================================================
# OPTIMIZATION PROMPT
# ============================================================

def build_optimization_context(
    original_resume: str,
    job_description: str,
    current_resume: Optional[Dict[str, Any]] = None,
    ats_analysis: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Build a strict prompt for AI resume optimization.

    The original resume is explicitly treated as the source
    of truth.
    """

    original_resume = str(
        original_resume or ""
    ).strip()

    job_description = str(
        job_description or ""
    ).strip()

    ats_analysis = (
        ats_analysis
        if isinstance(
            ats_analysis,
            dict,
        )
        else {}
    )

    skill_gap = get_skill_gap(
        original_resume,
        job_description,
    )

    current_text = ""

    if current_resume:
        current_text = resume_to_text(
            current_resume
        )

    ats_score = ats_analysis.get(
        "ats_score",
        ats_analysis.get(
            "overall_score",
            0,
        ),
    )

    return f"""
You are an expert ATS resume optimizer.

OBJECTIVE:
Improve the candidate's existing resume for the supplied job
description while preserving factual truth and the original
resume structure.

CURRENT ATS SCORE:
{ats_score}%

TARGET:
Aim for a genuine ATS score in the 80-90% range ONLY when the
candidate's existing background supports that level of alignment.
Never add unsupported information just to increase the score.

============================================================
ABSOLUTE FACTUALITY RULES
============================================================

1. The ORIGINAL RESUME is the only source of truth.

2. NEVER invent or assume:
   - skills
   - technologies
   - programming languages
   - tools
   - frameworks
   - companies
   - employers
   - job titles
   - roles
   - employment dates
   - education
   - degrees
   - institutions
   - certifications
   - projects
   - achievements
   - metrics
   - percentages
   - years of experience
   - responsibilities
   - clients
   - awards
   - locations

3. NEVER add a missing JD skill unless that skill is explicitly
   supported by the original resume.

4. NEVER create a fake achievement or metric.

5. NEVER convert an implied skill into a claimed professional
   experience unless the original resume supports it.

6. NEVER change the meaning of an existing factual statement.

============================================================
STRUCTURE RULES
============================================================

7. Preserve every original section.

8. Preserve every section heading exactly as it appears in the
   original resume.

9. Do NOT rename section headings.

10. Do NOT change section heading capitalization.

11. Do NOT create new sections.

12. Do NOT delete sections.

13. Do NOT merge sections.

14. Do NOT reorder sections.

15. Do NOT move content between sections unless absolutely
    necessary to preserve the same original document structure.

============================================================
IDENTITY / EMPLOYMENT RULES
============================================================

16. Preserve every company name exactly.

17. Preserve every job title exactly.

18. Preserve every employment date exactly.

19. Preserve every project name exactly.

20. Preserve education names, institutions and dates exactly.

21. Preserve certifications exactly.

22. Preserve achievements exactly.

============================================================
OPTIMIZATION RULES
============================================================

23. Rewrite wording inside existing content using stronger
    action verbs.

24. Improve clarity and professionalism.

25. Improve ATS keyword placement using keywords genuinely
    supported by the original resume.

26. Naturally align existing experience with the JD.

27. Prefer concrete wording already supported by the original
    content.

28. Keep all claims truthful and defensible.

29. Do not stuff keywords unnaturally.

30. Do not add repeated keywords solely for score manipulation.

============================================================
SKILLS
============================================================

SUPPORTED RESUME SKILLS:
{", ".join(map(str, skill_gap["resume_skills"]))}

MATCHED JD SKILLS:
{", ".join(map(str, skill_gap["matched"]))}

MISSING JD SKILLS:
{", ".join(map(str, skill_gap["missing"]))}

Only use skills from the supported resume skills list when
rewriting the resume.

============================================================
JOB DESCRIPTION
============================================================

{job_description}

============================================================
ORIGINAL RESUME
============================================================

{original_resume}

============================================================
CURRENT OPTIMIZED VERSION
============================================================

{current_text}

============================================================
OUTPUT FORMAT
============================================================

Return ONLY valid JSON.

Do not return markdown.

Do not return commentary.

Do not return a code block.

Use exactly this JSON structure:

{{
    "summary": "Optimized version of the existing summary",

    "skills": [
        "Existing supported skill 1",
        "Existing supported skill 2"
    ],

    "experience": [
        "Rewritten existing experience bullet 1",
        "Rewritten existing experience bullet 2"
    ],

    "projects": [
        "Rewritten existing project content"
    ],

    "education": [
        "Preserved education content"
    ],

    "certifications": [
        "Preserved certification content"
    ],

    "achievements": [
        "Preserved achievement content"
    ]
}}

IMPORTANT:
The output values contain CONTENT only.

Never place section headings inside these fields.

Never output headings such as:
PROFESSIONAL SUMMARY
SKILLS
PROFESSIONAL EXPERIENCE
PROJECTS
EDUCATION
CERTIFICATIONS
ACHIEVEMENTS

The document editor will preserve the original headings and
layout separately.
""".strip()


# ============================================================
# SINGLE AI OPTIMIZATION
# ============================================================

def optimize_resume_with_ai(
    original_resume: str,
    job_description: str,
    ats_analysis: Dict[str, Any],
    provider: str,
    current_resume: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Run one AI optimization pass.
    """

    prompt = build_optimization_context(
        original_resume=original_resume,
        job_description=job_description,
        current_resume=current_resume,
        ats_analysis=ats_analysis,
    )

    result = rewrite_resume(
        original_resume,
        job_description,
        ats_analysis=ats_analysis,
        provider=provider,
        optimization_context=prompt,
    )

    if not isinstance(
        result,
        dict,
    ):
        raise ValueError(
            "AI optimizer did not return a structured resume dictionary."
        )

    return _normalise_resume(
        result
    )


# ============================================================
# VERIFIED OPTIMIZATION
# ============================================================

def generate_verified_optimized_resume(
    resume_text: str,
    job_description: str,
    ats_analysis: Dict[str, Any],
    provider: str,
) -> Dict[str, Any]:
    """
    Generate and validate an optimized resume.
    """

    original_resume = str(
        resume_text or ""
    ).strip()

    job_description = str(
        job_description or ""
    ).strip()

    if not original_resume:
        raise ValueError(
            "Original resume text is empty."
        )

    if not job_description:
        raise ValueError(
            "Job description is empty."
        )

    # --------------------------------------------------------
    # AI OPTIMIZATION
    # --------------------------------------------------------

    optimized = optimize_resume_with_ai(
        original_resume=original_resume,
        job_description=job_description,
        ats_analysis=ats_analysis or {},
        provider=provider,
        current_resume=None,
    )

    # --------------------------------------------------------
    # VALIDATION
    # --------------------------------------------------------

    generated_text = resume_to_text(
        optimized
    )

    validation = validate_generated_resume(
        original_text=original_resume,
        generated_text=generated_text,
    )

    # --------------------------------------------------------
    # SKILLS
    # --------------------------------------------------------

    skill_gap = get_skill_gap(
        original_resume,
        job_description,
    )

    optimized["skills"] = _unique(
        optimized.get(
            "skills",
            [],
        )
    )

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
        if isinstance(
            ats_analysis,
            dict,
        )
        else 0
    )

    optimized["_generated_text"] = (
        generated_text
    )

    return optimized


# ============================================================
# BACKWARD COMPATIBILITY
# ============================================================

def optimize_resume(
    resume_text: str,
    job_description: str,
    ats_analysis: Optional[Dict[str, Any]] = None,
):
    """
    Lightweight backward-compatible optimizer result.

    The full AI generation is handled by
    generate_verified_optimized_resume().
    """

    ats_analysis = (
        ats_analysis
        if isinstance(
            ats_analysis,
            dict,
        )
        else {}
    )

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
        "supported_jd_skills": skill_gap[
            "matched"
        ],
        "missing_jd_skills": skill_gap[
            "missing"
        ],
        "original_ats_score": ats_analysis.get(
            "ats_score",
            0,
        ),
    }


# ============================================================
# VALIDATION HELPER
# ============================================================

def validate_optimization_result(
    original_resume: str,
    optimized_resume: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Validate an already-structured optimized resume.
    """

    generated_text = resume_to_text(
        optimized_resume
    )

    return validate_generated_resume(
        original_text=original_resume,
        generated_text=generated_text,
    )
    print("\n===== FACTUAL VALIDATION =====")
    print("VALID:", validation.get("valid"))
    print("UNSUPPORTED SKILLS:", validation.get("unsupported_skills"))
    print("UNSUPPORTED NUMBERS:", validation.get("unsupported_numbers"))
    print("UNSUPPORTED YEARS:", validation.get("unsupported_years"))
    print("UNSUPPORTED DATES:", validation.get("unsupported_dates"))
    print("UNSUPPORTED COMPANIES:", validation.get("unsupported_companies"))
    print("NEW NAMED TERMS:", validation.get("new_named_terms"))
    print("TEXT OVERLAP:", validation.get("text_overlap"))
    print("WARNINGS:", validation.get("warnings"))
    print("==============================\n")


# ============================================================
# SCRIPT TEST
# ============================================================

if __name__ == "__main__":

    sample_resume = """
    PROFESSIONAL SUMMARY
    Python developer with experience in CRM implementation.

    TECHNICAL SKILLS
    Python, SQL, Git

    PROFESSIONAL EXPERIENCE
    Worked on CRM implementation and debugging.

    PROJECTS
    Built an academic project using Python.

    EDUCATION
    B.Sc. Statistics
    """

    sample_jd = """
    Python Developer

    Requirements:
    Python, SQL, Git, REST API.
    2+ years of experience.
    """

    print(
        "Resume skill gap:"
    )

    print(
        get_skill_gap(
            sample_resume,
            sample_jd,
        )
    )

    print(
        "\nOptimizer module loaded successfully."
    )
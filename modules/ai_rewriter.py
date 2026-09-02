"""
ai_rewriter.py

AI-powered resume rewriting for the AI Resume Analyzer.

Supported providers:
    - Gemini
    - OpenAI

Important rules:
    - Never invent candidate facts.
    - Preserve factual information.
    - Optimize wording for ATS relevance.
    - Return structured JSON whenever possible.
"""

from __future__ import annotations

import json
import os
import re
from typing import Any, Dict, Optional


# ============================================================
# ENVIRONMENT
# ============================================================

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass


# ============================================================
# PROVIDER DETECTION
# ============================================================

def get_available_providers():
    """
    Return configured AI providers.

    Provider names are kept as:
        Gemini
        OpenAI
    """

    providers = []

    if os.getenv("GEMINI_API_KEY", "").strip():
        providers.append("Gemini")

    if os.getenv("OPENAI_API_KEY", "").strip():
        providers.append("OpenAI")

    return providers


def is_provider_available(provider: str) -> bool:
    """
    Check whether the requested provider has an API key.
    """

    provider = str(provider or "").strip().lower()

    if provider == "gemini":
        return bool(
            os.getenv(
                "GEMINI_API_KEY",
                "",
            ).strip()
        )

    if provider == "openai":
        return bool(
            os.getenv(
                "OPENAI_API_KEY",
                "",
            ).strip()
        )

    return False


# ============================================================
# TEXT HELPERS
# ============================================================

def _clean(value: Any) -> str:
    """
    Convert a value into clean text.
    """

    if value is None:
        return ""

    return str(value).strip()


def _strip_markdown_json(text: str) -> str:
    """
    Remove markdown code fences around JSON.
    """

    text = _clean(text)

    if not text:
        return ""

    # ```json ... ```
    match = re.match(
        r"^\s*```(?:json)?\s*(.*?)\s*```\s*$",
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )

    if match:
        return match.group(1).strip()

    return text


def _extract_json_object(text: str):
    """
    Extract the first JSON object from a model response.
    """

    text = _strip_markdown_json(text)

    if not text:
        return None

    # First try the entire response.
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Then look for a JSON object.
    start = text.find("{")
    end = text.rfind("}")

    if start == -1 or end == -1 or end <= start:
        return None

    candidate = text[start:end + 1]

    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        return None


# ============================================================
# RESUME STRUCTURE NORMALIZATION
# ============================================================

def _normalize_list(value):
    """
    Normalize a value into a list without destroying structured
    dictionaries returned by the model.
    """

    if value is None:
        return []

    if isinstance(value, list):
        result = []

        for item in value:
            if isinstance(item, dict):
                result.append(item)
            elif isinstance(item, str):
                text = item.strip()

                if text:
                    result.append(text)

        return result

    if isinstance(value, dict):
        return [value]

    if isinstance(value, str):
        lines = []

        for line in value.splitlines():
            line = re.sub(
                r"^\s*(?:[•●▪◦‣►▸]|[-*]|\d+[.)])\s*",
                "",
                line,
            ).strip()

            if line:
                lines.append(line)

        return lines

    return []


def _normalize_skills(value):
    """
    Normalize the skills field.
    """

    values = _normalize_list(value)

    result = []
    seen = set()

    for item in values:
        if isinstance(item, dict):
            text = (
                item.get("name")
                or item.get("skill")
                or item.get("title")
                or ""
            )
        else:
            text = item

        text = _clean(text)

        if not text:
            continue

        key = text.lower()

        if key not in seen:
            seen.add(key)
            result.append(text)

    return result


def normalize_resume_result(
    result: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Normalize the AI response into the structure expected by
    resume_optimizer.py and resume_editor.py.
    """

    if not isinstance(result, dict):
        raise ValueError(
            "AI response is not a valid resume dictionary."
        )

    return {
        "summary": _clean(
            result.get("summary", "")
        ),
        "skills": _normalize_skills(
            result.get("skills", [])
        ),
        "experience": _normalize_list(
            result.get("experience", [])
        ),
        "projects": _normalize_list(
            result.get("projects", [])
        ),
        "education": _normalize_list(
            result.get("education", [])
        ),
        "certifications": _normalize_list(
            result.get("certifications", [])
        ),
        "achievements": _normalize_list(
            result.get("achievements", [])
        ),
    }


# ============================================================
# PROMPT
# ============================================================

def build_prompt(
    resume_text: str,
    job_description: str,
    ats_analysis: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Build the default resume optimization prompt.
    """

    resume_text = _clean(resume_text)
    job_description = _clean(job_description)
    ats_analysis = ats_analysis or {}

    ats_score = ats_analysis.get(
        "ats_score",
        ats_analysis.get(
            "overall_score",
            0,
        ),
    )

    matched_skills = ats_analysis.get(
        "matched_skills",
        [],
    )

    missing_skills = ats_analysis.get(
        "missing_skills",
        [],
    )

    return f"""
You are an expert ATS resume optimizer.

Your task is to optimize the candidate's EXISTING resume for
the supplied job description.

CURRENT ATS SCORE:
{ats_score}%

MATCHED SKILLS:
{", ".join(str(x) for x in matched_skills)}

MISSING JD SKILLS:
{", ".join(str(x) for x in missing_skills)}

STRICT FACTUAL RULES:

1. The original resume is the only source of truth.
2. NEVER invent skills, technologies, employment, companies,
   job titles, projects, certifications, education, dates,
   achievements, metrics, responsibilities, or experience.
3. NEVER change a company name.
4. NEVER change a job title.
5. NEVER change employment dates.
6. NEVER change education institutions, degrees, or dates.
7. NEVER change project names.
8. NEVER fabricate numbers or percentages.
9. Missing JD skills must NOT be added unless they are already
   supported by the original resume.
10. Improve wording, clarity, action verbs, keyword placement,
    and ATS relevance using only facts already present.
11. Preserve every existing section conceptually.
12. Do not add unrelated sections.
13. Do not remove factual content merely to increase the score.
14. Keep the resume professional and concise.
15. Target a genuine high ATS score only when the original
    background supports it.

SECTION RULES:

SUMMARY:
Rewrite the existing summary with stronger wording and
job-relevant terminology supported by the original resume.

SKILLS:
Prioritize relevant existing skills. Do not introduce
unsupported skills.

EXPERIENCE:
Rewrite the existing responsibilities and achievements using
stronger ATS-friendly language. Preserve company, role and dates.

PROJECTS:
Improve descriptions only using information already present.
Preserve project names and factual details.

EDUCATION:
Preserve all education facts.

CERTIFICATIONS:
Preserve certifications exactly and do not create any.

ACHIEVEMENTS:
Preserve existing achievements and do not create any.

JOB DESCRIPTION:
{job_description}

ORIGINAL RESUME:
{resume_text}

OUTPUT REQUIREMENTS:

Return ONLY valid JSON.

Use exactly this structure:

{{
    "summary": "optimized summary",
    "skills": [
        "existing supported skill"
    ],
    "experience": [
        "optimized existing experience bullet"
    ],
    "projects": [
        "optimized existing project content"
    ],
    "education": [
        "preserved education content"
    ],
    "certifications": [
        "preserved certification content"
    ],
    "achievements": [
        "preserved achievement content"
    ]
}}
""".strip()


# ============================================================
# GEMINI
# ============================================================

def rewrite_with_gemini(
    prompt: str,
) -> Dict[str, Any]:
    """
    Rewrite the resume using Google Gemini.
    """

    api_key = os.getenv(
        "GEMINI_API_KEY",
        "",
    ).strip()

    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is not configured."
        )

    try:
        from google import genai
    except ImportError as exc:
        raise ImportError(
            "google-genai is required for Gemini support. "
            "Install it with: pip install google-genai"
        ) from exc

    model_name = os.getenv(
        "GEMINI_MODEL",
        "gemini-2.5-flash",
    ).strip()

    try:
        client = genai.Client(
            api_key=api_key,
            http_options={
                "timeout": 120000,
            },
        )

        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
        )

    except Exception as exc:
        raise RuntimeError(
            f"Gemini API request failed: {exc}"
        ) from exc

    response_text = getattr(
        response,
        "text",
        None,
    )

    if not response_text:
        raise RuntimeError(
            "Gemini returned an empty response."
        )

    result = _extract_json_object(
        response_text
    )

    if not isinstance(result, dict):
        raise ValueError(
            "Gemini did not return valid JSON."
        )

    return normalize_resume_result(
        result
    )


# ============================================================
# OPENAI
# ============================================================

def rewrite_with_openai(
    prompt: str,
) -> Dict[str, Any]:
    """
    Rewrite the resume using OpenAI.
    """

    api_key = os.getenv(
        "OPENAI_API_KEY",
        "",
    ).strip()

    if not api_key:
        raise RuntimeError(
            "OPENAI_API_KEY is not configured."
        )

    try:
        from openai import OpenAI
    except ImportError as exc:
        raise ImportError(
            "openai is required for OpenAI support. "
            "Install it with: pip install openai"
        ) from exc

    model_name = os.getenv(
        "OPENAI_MODEL",
        "gpt-4o-mini",
    ).strip()

    try:
        client = OpenAI(
            api_key=api_key,
        )

        response = client.chat.completions.create(
            model=model_name,
            temperature=0.2,
            response_format={
                "type": "json_object",
            },
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an expert ATS resume optimizer. "
                        "Return only valid JSON."
                    ),
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
        )

    except Exception as exc:
        raise RuntimeError(
            f"OpenAI API request failed: {exc}"
        ) from exc

    try:
        response_text = (
            response.choices[0]
            .message
            .content
        )
    except (
        AttributeError,
        IndexError,
        TypeError,
    ) as exc:
        raise RuntimeError(
            "OpenAI returned an invalid response."
        ) from exc

    if not response_text:
        raise RuntimeError(
            "OpenAI returned an empty response."
        )

    result = _extract_json_object(
        response_text
    )

    if not isinstance(result, dict):
        raise ValueError(
            "OpenAI did not return valid JSON."
        )

    return normalize_resume_result(
        result
    )


# ============================================================
# MAIN REWRITER
# ============================================================

def rewrite_resume(
    resume_text,
    job_description,
    ats_analysis=None,
    provider="Gemini",
    optimization_context=None,
):
    """
    Rewrite an existing resume with the selected AI provider.

    Parameters:
        resume_text:
            Original resume text.

        job_description:
            Target job description.

        ats_analysis:
            Optional ATS analysis.

        provider:
            Gemini or OpenAI.

        optimization_context:
            Optional fully constructed prompt. When supplied,
            it takes precedence over the default prompt.
    """

    resume_text = _clean(
        resume_text
    )

    job_description = _clean(
        job_description
    )

    if not resume_text:
        raise ValueError(
            "Resume text cannot be empty."
        )

    if not job_description:
        raise ValueError(
            "Job description cannot be empty."
        )

    provider_name = _clean(
        provider
    ).lower()

    if provider_name not in {
        "gemini",
        "openai",
    }:
        raise ValueError(
            "Unsupported AI provider. "
            "Choose Gemini or OpenAI."
        )

    if not is_provider_available(
        provider_name
    ):
        raise RuntimeError(
            f"{provider} is not configured. "
            f"Please add the required API key to your .env file."
        )

    if optimization_context:
        prompt = optimization_context
    else:
        prompt = build_prompt(
            resume_text,
            job_description,
            ats_analysis,
        )

    if provider_name == "gemini":
        return rewrite_with_gemini(
            prompt
        )

    return rewrite_with_openai(
        prompt
    )


# ============================================================
# PROVIDER-SPECIFIC WRAPPERS
# ============================================================

def rewrite_with_ai(
    resume_text,
    job_description,
    provider="Gemini",
    ats_analysis=None,
):
    """
    Generic AI rewrite wrapper.
    """

    return rewrite_resume(
        resume_text=resume_text,
        job_description=job_description,
        ats_analysis=ats_analysis,
        provider=provider,
    )


def rewrite_with_gemini_provider(
    resume_text,
    job_description,
    ats_analysis=None,
):
    """
    Gemini-specific resume rewriting wrapper.
    """

    prompt = build_prompt(
        resume_text,
        job_description,
        ats_analysis,
    )

    return rewrite_with_gemini(
        prompt
    )


def rewrite_with_openai_provider(
    resume_text,
    job_description,
    ats_analysis=None,
):
    """
    OpenAI-specific resume rewriting wrapper.
    """

    prompt = build_prompt(
        resume_text,
        job_description,
        ats_analysis,
    )

    return rewrite_with_openai(
        prompt
    )


# ============================================================
# CONFIGURATION HELPERS
# ============================================================

def get_provider_status():
    """
    Return configuration status for both providers.
    """

    return {
        "Gemini": bool(
            os.getenv(
                "GEMINI_API_KEY",
                "",
            ).strip()
        ),
        "OpenAI": bool(
            os.getenv(
                "OPENAI_API_KEY",
                "",
            ).strip()
        ),
    }


def get_provider_model(
    provider: str,
) -> Optional[str]:
    """
    Return configured model name for a provider.
    """

    provider = _clean(
        provider
    ).lower()

    if provider == "gemini":
        return os.getenv(
            "GEMINI_MODEL",
            "gemini-2.5-flash",
        ).strip()

    if provider == "openai":
        return os.getenv(
            "OPENAI_MODEL",
            "gpt-4o-mini",
        ).strip()

    return None


# ============================================================
# BACKWARD-COMPATIBLE ALIASES
# ============================================================

def available_providers():
    """
    Alias for get_available_providers().
    """

    return get_available_providers()


def get_ai_providers():
    """
    Alias for get_available_providers().
    """

    return get_available_providers()


def ai_rewrite(
    resume_text,
    job_description,
    provider="Gemini",
):
    """
    Alias for rewrite_resume().
    """

    return rewrite_resume(
        resume_text,
        job_description,
        provider=provider,
    )


# ============================================================
# SCRIPT TEST
# ============================================================

if __name__ == "__main__":
    print(
        "Configured AI providers:"
    )

    providers = get_available_providers()

    if providers:
        for provider in providers:
            print(
                f"- {provider}"
            )
    else:
        print(
            "No AI providers configured."
        )
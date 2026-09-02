import json
import os

from dotenv import load_dotenv
from openai import OpenAI
from google import genai


load_dotenv()


OPENAI_MODEL = "gpt-5.6-luna"
GEMINI_MODEL = "gemini-2.5-flash"


def get_available_providers():
    """
    Return AI providers for which an API key exists.
    """

    providers = []

    if os.getenv("OPENAI_API_KEY"):
        providers.append("OpenAI")

    if os.getenv("GEMINI_API_KEY"):
        providers.append("Gemini")

    return providers


def get_openai_client():
    """Create OpenAI client."""

    api_key = os.getenv(
        "OPENAI_API_KEY"
    )

    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY is not configured."
        )

    return OpenAI(
        api_key=api_key
    )


def get_gemini_client():
    """Create Gemini client with explicit HTTP settings."""

    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise ValueError(
            "GEMINI_API_KEY is not configured."
        )

    http_options = {
        "timeout": 120000,
    }

    return genai.Client(
        api_key=api_key,
        http_options=http_options,
    )


def build_prompt(
    resume_text,
    job_description,
    ats_analysis
):
    """
    Build the controlled AI resume optimization prompt.
    """

    matched_skills = ats_analysis.get(
        "matched_skills",
        []
    )

    missing_skills = ats_analysis.get(
        "missing_skills",
        []
    )

    return f"""
You are an expert ATS resume optimization assistant.

Optimize the candidate's EXISTING resume for the
provided job description.

STRICT FACTUALITY RULES:

1. Never invent experience.
2. Never invent companies.
3. Never invent job titles.
4. Never invent education.
5. Never invent certifications.
6. Never invent projects.
7. Never invent technologies.
8. Never invent metrics.
9. Never invent achievements.
10. Never add skills that are not supported by
    the original resume.
11. Preserve the candidate's factual meaning.
12. Improve grammar and professional wording.
13. Improve ATS keyword alignment naturally.
14. Use JD terminology only when supported by
    the candidate's original information.
15. Do not change dates.
16. Do not change numerical values.
17. Do not remove important factual information.
18. Keep the candidate's real experience intact.

MATCHED SKILLS:
{json.dumps(matched_skills)}

MISSING SKILLS:
{json.dumps(missing_skills)}

ORIGINAL RESUME:
{resume_text}

JOB DESCRIPTION:
{job_description}

Return ONLY valid JSON.

Required format:

{{
    "summary": "Improved professional summary",
    "experience": [
        "Improved bullet 1",
        "Improved bullet 2"
    ],
    "projects": [
        "Improved project bullet 1",
        "Improved project bullet 2"
    ]
}}
"""


def parse_ai_response(output):
    """
    Convert AI JSON output into a Python dictionary.
    """

    if not output:
        raise ValueError(
            "AI returned an empty response."
        )

    output = output.strip()

    # Remove accidental markdown JSON fences.
    if output.startswith("```"):

        output = output.replace(
            "```json",
            ""
        )

        output = output.replace(
            "```",
            ""
        )

        output = output.strip()

    try:

        return json.loads(
            output
        )

    except json.JSONDecodeError as error:

        raise ValueError(
            f"AI returned invalid JSON: {error}"
        )


def rewrite_with_openai(
    prompt
):
    """
    Rewrite resume using OpenAI.
    """

    client = get_openai_client()

    response = client.responses.create(
        model=OPENAI_MODEL,
        input=prompt
    )

    return parse_ai_response(
        response.output_text
    )


def rewrite_with_gemini(
    prompt
):
    """
    Rewrite resume using Gemini.
    """

    client = get_gemini_client()

    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
        config={
            "temperature": 0.2,
            "response_mime_type": "application/json",
        },
    )

    return parse_ai_response(
        response.text
    )


def rewrite_resume(
    resume_text,
    job_description,
    ats_analysis,
    provider="Gemini"
):
    """
    Rewrite resume using the selected AI provider.
    """

    prompt = build_prompt(
        resume_text,
        job_description,
        ats_analysis
    )

    provider = provider.strip().lower()

    if provider == "openai":

        return rewrite_with_openai(
            prompt
        )

    if provider == "gemini":

        return rewrite_with_gemini(
            prompt
        )

    raise ValueError(
        "Unsupported AI provider. "
        "Choose OpenAI or Gemini."
    )
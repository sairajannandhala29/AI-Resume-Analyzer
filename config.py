"""
config.py

Central configuration for the AI Resume Analyzer.
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv


# ============================================================
# LOAD ENVIRONMENT VARIABLES
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

load_dotenv(
    BASE_DIR / ".env"
)


# ============================================================
# PROJECT DIRECTORIES
# ============================================================

DATA_DIR = BASE_DIR / "data"
MODELS_DIR = BASE_DIR / "models"
MODULES_DIR = BASE_DIR / "modules"
TEMPLATES_DIR = BASE_DIR / "templates"
TESTS_DIR = BASE_DIR / "tests"


# Create directories when they do not exist.
DATA_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

MODELS_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

TEMPLATES_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

TESTS_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


# ============================================================
# DATA FILES
# ============================================================

SKILLS_FILE = DATA_DIR / "skills.csv"


# ============================================================
# AI API KEYS
# ============================================================

GEMINI_API_KEY = os.getenv(
    "GEMINI_API_KEY",
    "",
).strip()

OPENAI_API_KEY = os.getenv(
    "OPENAI_API_KEY",
    "",
).strip()


# ============================================================
# AI PROVIDER SETTINGS
# ============================================================

DEFAULT_AI_PROVIDER = os.getenv(
    "DEFAULT_AI_PROVIDER",
    "Gemini",
).strip()


GEMINI_MODEL = os.getenv(
    "GEMINI_MODEL",
    "gemini-2.5-flash",
).strip()


OPENAI_MODEL = os.getenv(
    "OPENAI_MODEL",
    "gpt-4o-mini",
).strip()


# ============================================================
# SEMANTIC MODEL
# ============================================================

SEMANTIC_MODEL_NAME = os.getenv(
    "SEMANTIC_MODEL_NAME",
    "all-MiniLM-L6-v2",
).strip()


# ============================================================
# ATS SCORING WEIGHTS
# ============================================================

ATS_SKILL_WEIGHT = 0.40

ATS_SEMANTIC_WEIGHT = 0.25

ATS_EXPERIENCE_WEIGHT = 0.20

ATS_KEYWORD_WEIGHT = 0.10

ATS_STRUCTURE_WEIGHT = 0.05


# ============================================================
# APPLICATION RECOMMENDATION
# ============================================================

APPLICATION_STRONG_THRESHOLD = 80

APPLICATION_GOOD_THRESHOLD = 65

APPLICATION_MODERATE_THRESHOLD = 50


# ============================================================
# OPTIMIZATION TARGET
# ============================================================

TARGET_ATS_MIN = 80

TARGET_ATS_MAX = 90


# ============================================================
# FILE SETTINGS
# ============================================================

SUPPORTED_RESUME_EXTENSIONS = (
    ".pdf",
    ".docx",
)

MAX_UPLOAD_SIZE_MB = 10


# ============================================================
# RESUME INTEGRITY SETTINGS
# ============================================================

PRESERVE_STRUCTURE = True

PRESERVE_SECTION_HEADINGS = True

PRESERVE_COMPANY_NAMES = True

PRESERVE_JOB_TITLES = True

PRESERVE_DATES = True

PRESERVE_PROJECT_NAMES = True

PRESERVE_EDUCATION = True

ALLOW_FACTUAL_INVENTION = False


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def is_gemini_configured() -> bool:
    """
    Return True when a Gemini API key is configured.
    """

    return bool(
        GEMINI_API_KEY
    )


def is_openai_configured() -> bool:
    """
    Return True when an OpenAI API key is configured.
    """

    return bool(
        OPENAI_API_KEY
    )


def get_available_ai_providers() -> list[str]:
    """
    Return all configured AI providers.
    """

    providers = []

    if is_gemini_configured():
        providers.append(
            "Gemini"
        )

    if is_openai_configured():
        providers.append(
            "OpenAI"
        )

    return providers


def get_default_provider() -> str | None:
    """
    Return the configured default provider.

    If the configured provider is unavailable, use the first
    available provider.
    """

    providers = get_available_ai_providers()

    if not providers:
        return None

    for provider in providers:
        if provider.lower() == DEFAULT_AI_PROVIDER.lower():
            return provider

    return providers[0]


def get_ai_model(
    provider: str,
) -> str | None:
    """
    Return the configured model for an AI provider.
    """

    provider = str(
        provider or ""
    ).strip().lower()

    if provider == "gemini":
        return GEMINI_MODEL

    if provider == "openai":
        return OPENAI_MODEL

    return None


def get_api_key(
    provider: str,
) -> str:
    """
    Return the API key for an AI provider.
    """

    provider = str(
        provider or ""
    ).strip().lower()

    if provider == "gemini":
        return GEMINI_API_KEY

    if provider == "openai":
        return OPENAI_API_KEY

    return ""


def is_provider_configured(
    provider: str,
) -> bool:
    """
    Check whether a specific AI provider is configured.
    """

    return bool(
        get_api_key(provider)
    )


def get_project_info() -> dict:
    """
    Return useful project configuration information.
    """

    return {
        "base_dir": str(BASE_DIR),
        "data_dir": str(DATA_DIR),
        "models_dir": str(MODELS_DIR),
        "modules_dir": str(MODULES_DIR),
        "templates_dir": str(TEMPLATES_DIR),
        "tests_dir": str(TESTS_DIR),
        "skills_file": str(SKILLS_FILE),
        "semantic_model": SEMANTIC_MODEL_NAME,
        "default_provider": get_default_provider(),
        "available_providers": get_available_ai_providers(),
        "preserve_structure": PRESERVE_STRUCTURE,
        "preserve_section_headings": PRESERVE_SECTION_HEADINGS,
        "allow_factual_invention": ALLOW_FACTUAL_INVENTION,
    }


# ============================================================
# SCRIPT TEST
# ============================================================

if __name__ == "__main__":

    print(
        "AI Resume Analyzer configuration loaded."
    )

    print(
        "\nBase directory:"
    )
    print(
        BASE_DIR
    )

    print(
        "\nSkills file:"
    )
    print(
        SKILLS_FILE
    )

    print(
        "\nAvailable AI providers:"
    )

    providers = get_available_ai_providers()

    if providers:
        for provider in providers:
            print(
                f"- {provider}"
            )
    else:
        print(
            "- None configured"
        )

    print(
        "\nDefault provider:"
    )
    print(
        get_default_provider()
    )
"""
skill_extractor.py

Extracts technical and professional skills from resumes and
job descriptions for the AI Resume Analyzer.
"""

from __future__ import annotations

import re
from typing import Iterable, List


# ============================================================
# SKILL DATABASE
# ============================================================

SKILL_ALIASES = {
    # Programming languages
    "python": ["python"],
    "java": ["java"],
    "javascript": ["javascript", "js"],
    "typescript": ["typescript", "ts"],
    "c": ["c programming", "c language"],
    "c++": ["c++"],
    "c#": ["c#", "c sharp"],
    "php": ["php"],
    "r": ["r programming", "r language"],
    "go": ["golang", "go language"],
    "ruby": ["ruby"],
    "kotlin": ["kotlin"],
    "swift": ["swift"],

    # Web
    "html": ["html", "html5"],
    "css": ["css", "css3"],
    "react": ["react", "react.js", "reactjs"],
    "angular": ["angular", "angularjs"],
    "vue": ["vue", "vue.js", "vuejs"],
    "node.js": ["node.js", "nodejs", "node js"],
    "express": ["express", "express.js", "expressjs"],
    "next.js": ["next.js", "nextjs"],
    "bootstrap": ["bootstrap"],
    "tailwind css": ["tailwind", "tailwind css"],
    "jquery": ["jquery"],

    # Databases
    "sql": ["sql"],
    "mysql": ["mysql"],
    "postgresql": ["postgresql", "postgres"],
    "mongodb": ["mongodb", "mongo db", "mongo"],
    "sqlite": ["sqlite"],
    "oracle": ["oracle database", "oracle"],
    "sql server": ["sql server", "mssql", "microsoft sql server"],
    "redis": ["redis"],

    # Data / Analytics
    "pandas": ["pandas"],
    "numpy": ["numpy"],
    "scikit-learn": ["scikit-learn", "sklearn", "scikit learn"],
    "matplotlib": ["matplotlib"],
    "seaborn": ["seaborn"],
    "power bi": ["power bi", "powerbi"],
    "tableau": ["tableau"],
    "excel": ["excel", "microsoft excel"],
    "statistics": ["statistics", "statistical analysis"],
    "data analysis": ["data analysis", "data analytics"],
    "data visualization": ["data visualization"],

    # Machine Learning / AI
    "machine learning": ["machine learning", "machine-learning"],
    "deep learning": ["deep learning", "deep-learning"],
    "artificial intelligence": [
        "artificial intelligence",
        "artificial intelligence",
        "ai",
    ],
    "natural language processing": [
        "natural language processing",
        "nlp",
    ],
    "computer vision": ["computer vision"],
    "tensorflow": ["tensorflow"],
    "pytorch": ["pytorch"],
    "keras": ["keras"],
    "llm": ["llm", "large language model", "large language models"],
    "generative ai": [
        "generative ai",
        "generative artificial intelligence",
        "genai",
    ],
    "prompt engineering": ["prompt engineering"],
    "hugging face": ["hugging face", "huggingface"],

    # Cloud
    "aws": ["aws", "amazon web services"],
    "azure": ["azure", "microsoft azure"],
    "gcp": ["gcp", "google cloud", "google cloud platform"],

    # DevOps / Tools
    "git": ["git"],
    "github": ["github"],
    "gitlab": ["gitlab"],
    "docker": ["docker"],
    "kubernetes": ["kubernetes", "k8s"],
    "jenkins": ["jenkins"],
    "ci/cd": ["ci/cd", "cicd", "continuous integration", "continuous deployment"],
    "linux": ["linux"],
    "windows": ["windows"],
    "bash": ["bash", "shell scripting"],
    "postman": ["postman"],
    "jira": ["jira"],
    "vs code": ["vs code", "visual studio code"],

    # APIs / Architecture
    "rest api": [
        "rest api",
        "restful api",
        "rest apis",
        "restful apis",
    ],
    "graphql": ["graphql"],
    "microservices": ["microservices", "microservice architecture"],
    "api development": ["api development", "api integration"],

    # Software engineering
    "object-oriented programming": [
        "object-oriented programming",
        "object oriented programming",
        "oop",
    ],
    "data structures": ["data structures", "data structure"],
    "algorithms": ["algorithms", "algorithm"],
    "software development": ["software development"],
    "software testing": ["software testing", "testing"],
    "debugging": ["debugging", "debugging skills"],
    "troubleshooting": ["troubleshooting"],
    "version control": ["version control"],

    # CRM / Enterprise
    "crm": ["crm", "customer relationship management"],
    "salesforce": ["salesforce"],
    "hubspot": ["hubspot"],
    "sap": ["sap"],
    "erp": ["erp", "enterprise resource planning"],

    # Documentation / Communication
    "technical documentation": ["technical documentation"],
    "documentation": ["documentation"],
    "communication": ["communication skills", "communication"],
    "problem solving": ["problem solving", "problem-solving"],
    "teamwork": ["teamwork", "team work"],
    "leadership": ["leadership"],
}


# ============================================================
# NORMALIZATION
# ============================================================

def normalize_skill_text(text: str) -> str:
    """
    Normalize text for reliable skill matching.
    """

    text = str(text or "").lower()

    replacements = {
        "–": "-",
        "—": "-",
        "’": "'",
        "\u00a0": " ",
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    text = re.sub(r"\s+", " ", text)

    return text.strip()


# ============================================================
# WORD BOUNDARY MATCHING
# ============================================================

def contains_skill(text: str, skill_variant: str) -> bool:
    """
    Check whether a skill variant appears as a meaningful term.

    Handles punctuation and multi-word skills while reducing
    accidental partial matches.
    """

    text = normalize_skill_text(text)
    variant = normalize_skill_text(skill_variant)

    if not text or not variant:
        return False

    # Exact short aliases such as "r" and "c" need special handling.
    if len(variant) <= 2 and variant.isalpha():
        pattern = rf"(?<![a-z0-9+#]){re.escape(variant)}(?![a-z0-9+#])"
    else:
        escaped = re.escape(variant)
        escaped = escaped.replace(r"\ ", r"\s+")
        pattern = rf"(?<![a-z0-9]){escaped}(?![a-z0-9])"

    return re.search(pattern, text, flags=re.IGNORECASE) is not None


# ============================================================
# CANONICAL SKILL
# ============================================================

def canonicalize_skill(skill: str) -> str:
    """
    Convert a skill/alias into its canonical skill name when known.
    """

    normalized = normalize_skill_text(skill)

    for canonical, aliases in SKILL_ALIASES.items():
        if normalized == normalize_skill_text(canonical):
            return canonical

        for alias in aliases:
            if normalized == normalize_skill_text(alias):
                return canonical

    return str(skill).strip()


# ============================================================
# UNIQUE SKILLS
# ============================================================

def unique_skills(skills: Iterable[str]) -> List[str]:
    """
    Remove duplicate skills while preserving order.
    """

    result = []
    seen = set()

    for skill in skills:
        value = canonicalize_skill(str(skill).strip())

        if not value:
            continue

        key = value.lower()

        if key not in seen:
            seen.add(key)
            result.append(value)

    return result


# ============================================================
# MAIN EXTRACTION
# ============================================================

def extract_skills(text: str) -> List[str]:
    """
    Extract known skills from the supplied text.

    The extractor intentionally uses a controlled vocabulary
    rather than allowing arbitrary words to become skills.
    """

    text = normalize_skill_text(text)

    if not text:
        return []

    found = []

    for canonical, aliases in SKILL_ALIASES.items():

        variants = [canonical, *aliases]

        matched = False

        for variant in variants:
            if contains_skill(text, variant):
                matched = True
                break

        if matched:
            found.append(canonical)

    return unique_skills(found)


# ============================================================
# SKILL SET COMPARISON
# ============================================================

def find_matching_skills(
    resume_text: str,
    job_description: str,
):
    """
    Return skills that occur in both the resume and JD.
    """

    resume_skills = extract_skills(resume_text)
    jd_skills = extract_skills(job_description)

    resume_map = {
        skill.lower(): skill
        for skill in resume_skills
    }

    matched = []

    for skill in jd_skills:
        if skill.lower() in resume_map:
            matched.append(resume_map[skill.lower()])

    return unique_skills(matched)


def find_missing_skills(
    resume_text: str,
    job_description: str,
):
    """
    Return JD skills that were not detected in the resume.
    """

    resume_skills = extract_skills(resume_text)
    jd_skills = extract_skills(job_description)

    resume_set = {
        skill.lower()
        for skill in resume_skills
    }

    missing = [
        skill
        for skill in jd_skills
        if skill.lower() not in resume_set
    ]

    return unique_skills(missing)


# ============================================================
# SKILL MATCH PERCENTAGE
# ============================================================

def calculate_skill_match(
    resume_text: str,
    job_description: str,
) -> float:
    """
    Calculate the percentage of detected JD skills that are also
    detected in the resume.
    """

    jd_skills = extract_skills(job_description)

    if not jd_skills:
        return 0.0

    matched = find_matching_skills(
        resume_text,
        job_description,
    )

    return round(
        len(matched) / len(jd_skills) * 100,
        2,
    )


# ============================================================
# SKILL GAP REPORT
# ============================================================

def get_skill_gap(
    resume_text: str,
    job_description: str,
):
    """
    Return a complete skill-gap report.
    """

    resume_skills = extract_skills(resume_text)
    jd_skills = extract_skills(job_description)

    matched = find_matching_skills(
        resume_text,
        job_description,
    )

    missing = find_missing_skills(
        resume_text,
        job_description,
    )

    return {
        "resume_skills": resume_skills,
        "jd_skills": jd_skills,
        "matched": matched,
        "missing": missing,
        "match_percentage": calculate_skill_match(
            resume_text,
            job_description,
        ),
    }


# ============================================================
# SKILL EXISTENCE CHECK
# ============================================================

def has_skill(
    text: str,
    skill: str,
) -> bool:
    """
    Check whether a specific skill is present in the text.
    """

    canonical = canonicalize_skill(skill)

    aliases = SKILL_ALIASES.get(
        canonical,
        [canonical],
    )

    return any(
        contains_skill(text, variant)
        for variant in aliases
    )


# ============================================================
# CUSTOM SKILL EXTRACTION
# ============================================================

def extract_custom_skills(
    text: str,
    skills: Iterable[str],
) -> List[str]:
    """
    Extract only skills from a caller-provided skill list.

    Useful when the JD analyzer supplies a custom list.
    """

    result = []

    for skill in skills or []:
        skill = str(skill).strip()

        if not skill:
            continue

        if has_skill(text, skill):
            result.append(
                canonicalize_skill(skill)
            )

    return unique_skills(result)


# ============================================================
# BACKWARD-COMPATIBLE ALIASES
# ============================================================

def get_skills(text: str) -> List[str]:
    """
    Alias for extract_skills().
    """
    return extract_skills(text)


def extract_resume_skills(text: str) -> List[str]:
    """
    Alias for extract_skills().
    """
    return extract_skills(text)


def extract_job_skills(text: str) -> List[str]:
    """
    Alias for extract_skills().
    """
    return extract_skills(text)


# ============================================================
# SCRIPT TEST
# ============================================================

if __name__ == "__main__":
    sample = """
    Python, SQL, JavaScript, React, Git, Docker and AWS.
    Experience with REST APIs and machine learning.
    """

    print("Detected skills:")
    for skill in extract_skills(sample):
        print(f"- {skill}")
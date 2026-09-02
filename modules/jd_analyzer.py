"""
jd_analyzer.py

Job Description Analyzer for the AI Resume Analyzer.

Extracts:
- Required skills
- Experience requirements
- Education requirements
- Responsibilities
- Job title
- Basic JD keywords
"""

from __future__ import annotations

import re
from typing import Any, Dict, List

from modules.skill_extractor import extract_skills


# ============================================================
# HELPERS
# ============================================================

def _clean_text(text: Any) -> str:
    """Return normalized text."""
    if text is None:
        return ""

    text = str(text)
    text = text.replace("\r\n", "\n")
    text = text.replace("\r", "\n")
    text = text.replace("\u00a0", " ")
    text = re.sub(r"[ \t]+", " ", text)

    return text.strip()


def _unique(items: List[str]) -> List[str]:
    """Remove duplicates while preserving order."""
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


# ============================================================
# EXPERIENCE EXTRACTION
# ============================================================

def extract_experience_years(text: str) -> int:
    """
    Detect the minimum required years of experience.

    Examples:
        "2 years of experience" -> 2
        "3+ years experience"   -> 3
        "2 to 4 years"          -> 2
        "2-4 years"             -> 2
        "minimum 5 years"       -> 5

    For experience ranges, the lower value is treated as
    the minimum eligibility requirement.
    """

    text = _clean_text(text).lower()

    if not text:
        return 0

    # Experience ranges: use the LOWER value as the
    # minimum eligibility requirement.
    range_patterns = [
        r"\b(\d+)\s*(?:to|-|–|—)\s*(\d+)\s*years?\b",
        r"\bbetween\s+(\d+)\s+and\s+(\d+)\s*years?\b",
    ]

    for pattern in range_patterns:
        match = re.search(pattern, text)
        if match:
            return int(match.group(1))

    patterns = [
        r"(\d+)\s*\+?\s*years?\s+of\s+experience",
        r"(\d+)\s*\+?\s*years?\s+experience",
        r"(\d+)\s*\+?\s*years?\s+of\s+professional\s+experience",
        r"minimum\s+(?:of\s+)?(\d+)\s*\+?\s*years?",
        r"at\s+least\s+(\d+)\s*\+?\s*years?",
        r"(\d+)\s*\+?\s*yrs?\s+of\s+experience",
    ]

    values = []

    for pattern in patterns:
        for match in re.finditer(pattern, text):
            try:
                values.append(int(match.group(1)))
            except (TypeError, ValueError):
                pass

    return max(values) if values else 0
    """
    Detect the minimum explicitly stated years of experience.

    Examples:
        "2 years of experience" -> 2
        "3+ years experience"   -> 3
        "minimum 5 years"       -> 5

    When multiple requirements exist, the largest explicit
    requirement is returned.
    """

    text = _clean_text(text).lower()

    if not text:
        return 0

    patterns = [
        r"(\d+)\s*\+?\s*years?\s+of\s+experience",
        r"(\d+)\s*\+?\s*years?\s+experience",
        r"(\d+)\s*\+?\s*years?\s+of\s+professional\s+experience",
        r"minimum\s+(?:of\s+)?(\d+)\s*\+?\s*years?",
        r"at\s+least\s+(\d+)\s*\+?\s*years?",
        r"(\d+)\s*\+?\s*yrs?\s+of\s+experience",
    ]

    values = []

    for pattern in patterns:
        for match in re.finditer(pattern, text):
            try:
                values.append(int(match.group(1)))
            except (TypeError, ValueError):
                pass

    return max(values) if values else 0


# ============================================================
# EDUCATION EXTRACTION
# ============================================================

EDUCATION_TERMS = [
    "bachelor",
    "bachelors",
    "bachelor's",
    "master",
    "masters",
    "master's",
    "b.tech",
    "btech",
    "m.tech",
    "mtech",
    "b.e",
    "be degree",
    "m.e",
    "me degree",
    "b.sc",
    "bsc",
    "m.sc",
    "msc",
    "b.com",
    "bcom",
    "m.com",
    "mcom",
    "mba",
    "mca",
    "phd",
    "doctorate",
    "degree",
    "diploma",
    "computer science",
    "information technology",
    "engineering",
    "statistics",
    "mathematics",
    "data science",
]


def extract_education(text: str) -> List[str]:
    """
    Detect common education requirements.
    """

    text = _clean_text(text)

    if not text:
        return []

    lower_text = text.lower()
    found = []

    for term in EDUCATION_TERMS:
        if term.lower() in lower_text:
            found.append(term)

    return _unique(found)


# ============================================================
# RESPONSIBILITY EXTRACTION
# ============================================================

RESPONSIBILITY_HEADERS = [
    "responsibilities",
    "responsibility",
    "what you'll do",
    "what you will do",
    "what you'll be doing",
    "key responsibilities",
    "duties",
    "role and responsibilities",
    "job responsibilities",
]


REQUIREMENT_HEADERS = [
    "requirements",
    "qualifications",
    "required qualifications",
    "what we're looking for",
    "what we are looking for",
    "skills required",
    "technical requirements",
    "preferred qualifications",
]


def _is_header(line: str, headers: List[str]) -> bool:
    """Check whether a line is a known JD section header."""
    normalized = line.strip().lower()

    if normalized.endswith(":"):
        normalized = normalized[:-1].strip()

    return normalized in {
        header.lower()
        for header in headers
    }


def _remove_bullet_prefix(line: str) -> str:
    """Remove common bullet/list markers."""
    return re.sub(
        r"^\s*(?:[•●▪◦‣►▸]|[-*]|\d+[.)]|[a-zA-Z][.)])\s*",
        "",
        line,
    ).strip()


def extract_responsibilities(text: str) -> List[str]:
    """
    Extract responsibility statements from a JD.

    Looks for a responsibilities section first. If no explicit
    section is found, falls back to lines beginning with common
    action verbs.
    """

    text = _clean_text(text)

    if not text:
        return []

    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]

    responsibilities = []
    in_responsibilities = False

    section_headers = (
        RESPONSIBILITY_HEADERS
        + REQUIREMENT_HEADERS
        + [
            "education",
            "benefits",
            "about the company",
            "about us",
            "preferred",
            "preferred skills",
            "salary",
        ]
    )

    for line in lines:
        if _is_header(line, RESPONSIBILITY_HEADERS):
            in_responsibilities = True
            continue

        if _is_header(line, section_headers) and not _is_header(
            line,
            RESPONSIBILITY_HEADERS,
        ):
            if in_responsibilities:
                break

        if in_responsibilities:
            cleaned = _remove_bullet_prefix(line)

            if len(cleaned) >= 15:
                responsibilities.append(cleaned)

    if responsibilities:
        return _unique(responsibilities)

    # --------------------------------------------------------
    # Fallback action-verb detection
    # --------------------------------------------------------

    action_pattern = re.compile(
        r"^(?:"
        r"develop|design|build|create|implement|"
        r"maintain|manage|analyze|test|debug|"
        r"support|collaborate|lead|coordinate|"
        r"monitor|optimize|integrate|deploy|"
        r"document|research|configure|"
        r"work|assist|drive|deliver"
        r")\b",
        re.IGNORECASE,
    )

    for line in lines:
        cleaned = _remove_bullet_prefix(line)

        if action_pattern.match(cleaned):
            responsibilities.append(cleaned)

    return _unique(responsibilities)


# ============================================================
# JOB TITLE
# ============================================================

JOB_TITLE_PATTERNS = [
    r"(?:job\s+title|position|role)\s*:\s*(.+)",
    r"(?:title)\s*:\s*(.+)",
]


def extract_job_title(text: str) -> str:
    """
    Extract an explicitly labelled job title when present.
    """

    text = _clean_text(text)

    if not text:
        return ""

    for line in text.splitlines():
        line = line.strip()

        for pattern in JOB_TITLE_PATTERNS:
            match = re.search(
                pattern,
                line,
                flags=re.IGNORECASE,
            )

            if match:
                return match.group(1).strip()

    return ""


# ============================================================
# SKILL CATEGORIES
# ============================================================

def categorize_skills(skills: List[str]) -> Dict[str, List[str]]:
    """
    Group detected skills into broad categories.
    """

    categories = {
        "programming": [],
        "web": [],
        "database": [],
        "data": [],
        "ai_ml": [],
        "cloud": [],
        "devops": [],
        "software": [],
        "business": [],
        "other": [],
    }

    programming = {
        "python",
        "java",
        "javascript",
        "typescript",
        "c",
        "c++",
        "c#",
        "php",
        "r",
        "go",
        "ruby",
        "kotlin",
        "swift",
    }

    web = {
        "html",
        "css",
        "react",
        "angular",
        "vue",
        "node.js",
        "express",
        "next.js",
        "bootstrap",
        "tailwind css",
        "jquery",
    }

    database = {
        "sql",
        "mysql",
        "postgresql",
        "mongodb",
        "sqlite",
        "oracle",
        "sql server",
        "redis",
    }

    data = {
        "pandas",
        "numpy",
        "scikit-learn",
        "matplotlib",
        "seaborn",
        "power bi",
        "tableau",
        "excel",
        "statistics",
        "data analysis",
        "data analytics",
        "data visualization",
    }

    ai_ml = {
        "machine learning",
        "deep learning",
        "artificial intelligence",
        "natural language processing",
        "computer vision",
        "tensorflow",
        "pytorch",
        "keras",
        "llm",
        "generative ai",
        "prompt engineering",
        "hugging face",
    }

    cloud = {
        "aws",
        "azure",
        "gcp",
    }

    devops = {
        "git",
        "github",
        "gitlab",
        "docker",
        "kubernetes",
        "jenkins",
        "ci/cd",
        "linux",
        "bash",
    }

    software = {
        "rest api",
        "graphql",
        "microservices",
        "api development",
        "object-oriented programming",
        "data structures",
        "algorithms",
        "software development",
        "software testing",
        "debugging",
        "troubleshooting",
        "version control",
        "postman",
        "jira",
    }

    business = {
        "crm",
        "salesforce",
        "hubspot",
        "sap",
        "erp",
        "communication",
        "leadership",
        "teamwork",
        "problem solving",
        "documentation",
        "technical documentation",
    }

    for skill in skills:
        normalized = str(skill).strip()
        key = normalized.lower()

        if key in programming:
            categories["programming"].append(normalized)
        elif key in web:
            categories["web"].append(normalized)
        elif key in database:
            categories["database"].append(normalized)
        elif key in data:
            categories["data"].append(normalized)
        elif key in ai_ml:
            categories["ai_ml"].append(normalized)
        elif key in cloud:
            categories["cloud"].append(normalized)
        elif key in devops:
            categories["devops"].append(normalized)
        elif key in software:
            categories["software"].append(normalized)
        elif key in business:
            categories["business"].append(normalized)
        else:
            categories["other"].append(normalized)

    return categories


# ============================================================
# COMPLETE JD ANALYSIS
# ============================================================

def analyze_job_description(
    job_description: str,
) -> Dict[str, Any]:
    """
    Perform complete job description analysis.
    """

    job_description = _clean_text(job_description)

    if not job_description:
        return {
            "job_title": "",
            "skills": [],
            "required_skills": [],
            "experience_years": 0,
            "education": [],
            "responsibilities": [],
            "skill_categories": categorize_skills([]),
        }

    skills = _unique(
        extract_skills(job_description)
    )

    experience_years = extract_experience_years(
        job_description
    )

    education = extract_education(
        job_description
    )

    responsibilities = extract_responsibilities(
        job_description
    )

    job_title = extract_job_title(
        job_description
    )

    return {
        "job_title": job_title,
        "skills": skills,
        "required_skills": skills,
        "experience_years": experience_years,
        "education": education,
        "responsibilities": responsibilities,
        "skill_categories": categorize_skills(skills),
    }


# ============================================================
# BACKWARD-COMPATIBLE ALIASES
# ============================================================

def analyze_jd(
    job_description: str,
) -> Dict[str, Any]:
    """
    Alias for analyze_job_description().
    """
    return analyze_job_description(
        job_description
    )


def extract_jd_skills(
    job_description: str,
) -> List[str]:
    """
    Extract skills from a job description.
    """
    return _unique(
        extract_skills(job_description)
    )


def get_required_experience(
    job_description: str,
) -> int:
    """
    Return required experience in years.
    """
    return extract_experience_years(
        job_description
    )


# ============================================================
# SCRIPT TEST
# ============================================================

if __name__ == "__main__":
    sample_jd = """
    Job Title: Python Developer

    Requirements:
    - 2+ years of experience in Python development.
    - Strong knowledge of Python, SQL, Git and REST API.
    - Experience with AWS and Docker.
    - Bachelor's degree in Computer Science or related field.

    Responsibilities:
    - Develop and maintain Python applications.
    - Build REST APIs and integrate backend services.
    - Debug and test applications.
    - Collaborate with cross-functional teams.
    """

    result = analyze_job_description(sample_jd)

    print("Job Title:")
    print(result["job_title"])

    print("\nSkills:")
    print(result["skills"])

    print("\nExperience:")
    print(result["experience_years"])

    print("\nEducation:")
    print(result["education"])

    print("\nResponsibilities:")
    for item in result["responsibilities"]:
        print(f"- {item}")
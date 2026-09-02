"""
semantic_matcher.py

Semantic similarity utilities for the AI Resume Analyzer.

Uses Sentence Transformers lazily so that the Streamlit application
does not load the model during startup.

Primary model:
    all-MiniLM-L6-v2
"""

from __future__ import annotations

from functools import lru_cache
from typing import Iterable, List

import numpy as np


MODEL_NAME = "all-MiniLM-L6-v2"


# ============================================================
# MODEL
# ============================================================

@lru_cache(maxsize=1)
def get_model():
    """
    Load the Sentence Transformer model lazily.

    The model is cached after the first load.
    """

    try:
        from sentence_transformers import SentenceTransformer
    except ImportError as exc:
        raise ImportError(
            "sentence-transformers is required for semantic matching. "
            "Install it with: pip install sentence-transformers"
        ) from exc

    return SentenceTransformer(MODEL_NAME)


# ============================================================
# TEXT HELPERS
# ============================================================

def _clean_text(text) -> str:
    """
    Normalize text into a clean string.
    """

    if text is None:
        return ""

    return str(text).strip()


def _clean_list(values: Iterable) -> List[str]:
    """
    Convert an iterable into a clean list of strings.
    """

    if values is None:
        return []

    result = []

    for value in values:
        text = _clean_text(value)

        if text:
            result.append(text)

    return result


# ============================================================
# COSINE SIMILARITY
# ============================================================

def _cosine_similarity(
    first_vector,
    second_vector,
) -> float:
    """
    Calculate cosine similarity between two vectors.
    """

    first = np.asarray(
        first_vector,
        dtype=float,
    ).reshape(-1)

    second = np.asarray(
        second_vector,
        dtype=float,
    ).reshape(-1)

    if first.size == 0 or second.size == 0:
        return 0.0

    first_norm = np.linalg.norm(first)
    second_norm = np.linalg.norm(second)

    if first_norm == 0 or second_norm == 0:
        return 0.0

    similarity = float(
        np.dot(first, second)
        / (first_norm * second_norm)
    )

    return max(
        -1.0,
        min(
            1.0,
            similarity,
        ),
    )


def similarity_to_percentage(
    similarity: float,
) -> float:
    """
    Convert cosine similarity into a percentage.

    Cosine similarity normally ranges from -1 to 1.
    For resume/JD matching, the value is normalized into 0-100.
    """

    value = float(similarity)

    percentage = (
        (value + 1.0)
        / 2.0
        * 100.0
    )

    return round(
        max(
            0.0,
            min(
                100.0,
                percentage,
            ),
        ),
        2,
    )


# ============================================================
# SENTENCE EMBEDDING
# ============================================================

def encode_text(
    texts,
    normalize_embeddings: bool = True,
):
    """
    Generate embeddings for one or more texts.
    """

    model = get_model()

    if isinstance(texts, str):
        texts = [texts]

    texts = _clean_list(texts)

    if not texts:
        return np.empty(
            (0, 0),
            dtype=float,
        )

    embeddings = model.encode(
        texts,
        convert_to_numpy=True,
        normalize_embeddings=normalize_embeddings,
        show_progress_bar=False,
    )

    return np.asarray(
        embeddings,
        dtype=float,
    )


# ============================================================
# TEXT SEMANTIC SIMILARITY
# ============================================================

def calculate_semantic_similarity(
    resume_text: str,
    job_description: str,
) -> float:
    """
    Calculate semantic similarity between a resume and a JD.

    Returns:
        Percentage between 0 and 100.
    """

    resume_text = _clean_text(
        resume_text
    )

    job_description = _clean_text(
        job_description
    )

    if not resume_text or not job_description:
        return 0.0

    try:
        embeddings = encode_text(
            [
                resume_text,
                job_description,
            ]
        )

        similarity = _cosine_similarity(
            embeddings[0],
            embeddings[1],
        )

        return similarity_to_percentage(
            similarity
        )

    except Exception:
        # Semantic scoring should not crash the whole ATS analyzer.
        return 0.0


# ============================================================
# SKILL SEMANTIC SIMILARITY
# ============================================================

def calculate_skill_similarity(
    resume_skills,
    job_skills,
) -> float:
    """
    Calculate semantic similarity between resume skills and JD skills.

    Each skill from the JD is compared against the best matching
    resume skill.

    Returns:
        Percentage between 0 and 100.
    """

    resume_skills = _clean_list(
        resume_skills
    )

    job_skills = _clean_list(
        job_skills
    )

    if not resume_skills or not job_skills:
        return 0.0

    try:
        resume_embeddings = encode_text(
            resume_skills
        )

        jd_embeddings = encode_text(
            job_skills
        )

        scores = []

        for jd_vector in jd_embeddings:
            best_score = -1.0

            for resume_vector in resume_embeddings:
                score = _cosine_similarity(
                    resume_vector,
                    jd_vector,
                )

                if score > best_score:
                    best_score = score

            if best_score >= -1.0:
                scores.append(
                    best_score
                )

        if not scores:
            return 0.0

        average_similarity = float(
            np.mean(scores)
        )

        return similarity_to_percentage(
            average_similarity
        )

    except Exception:
        return 0.0


# ============================================================
# BATCH TEXT SIMILARITY
# ============================================================

def calculate_pair_similarity(
    first_text: str,
    second_text: str,
) -> float:
    """
    Calculate semantic similarity between two arbitrary text values.

    Returns:
        Percentage between 0 and 100.
    """

    return calculate_semantic_similarity(
        first_text,
        second_text,
    )


def calculate_similarity(
    first_text: str,
    second_text: str,
) -> float:
    """
    Alias for calculate_semantic_similarity().
    """

    return calculate_semantic_similarity(
        first_text,
        second_text,
    )


# ============================================================
# MULTI-SECTION SIMILARITY
# ============================================================

def calculate_section_similarity(
    resume_sections,
    jd_sections,
) -> float:
    """
    Calculate average semantic similarity between corresponding
    resume/JD sections.

    Inputs may be dictionaries or lists.
    """

    if not resume_sections or not jd_sections:
        return 0.0

    if isinstance(
        resume_sections,
        dict,
    ) and isinstance(
        jd_sections,
        dict,
    ):
        common_sections = [
            key
            for key in resume_sections
            if key in jd_sections
        ]

        if not common_sections:
            return 0.0

        scores = []

        for key in common_sections:
            resume_value = resume_sections.get(
                key,
                "",
            )
            jd_value = jd_sections.get(
                key,
                "",
            )

            score = calculate_semantic_similarity(
                resume_value,
                jd_value,
            )

            scores.append(score)

        return round(
            float(np.mean(scores)),
            2,
        )

    if isinstance(
        resume_sections,
        (list, tuple),
    ) and isinstance(
        jd_sections,
        (list, tuple),
    ):
        if not resume_sections or not jd_sections:
            return 0.0

        scores = []

        pair_count = min(
            len(resume_sections),
            len(jd_sections),
        )

        for index in range(pair_count):
            scores.append(
                calculate_semantic_similarity(
                    resume_sections[index],
                    jd_sections[index],
                )
            )

        if not scores:
            return 0.0

        return round(
            float(np.mean(scores)),
            2,
        )

    return 0.0


# ============================================================
# TOP MATCHING TEXT
# ============================================================

def find_best_matching_text(
    query_text: str,
    candidate_texts,
):
    """
    Find the candidate text with the highest semantic similarity
    to a query.

    Returns:
        {
            "text": ...,
            "score": ...
        }
    """

    query_text = _clean_text(
        query_text
    )

    candidate_texts = _clean_list(
        candidate_texts
    )

    if not query_text or not candidate_texts:
        return {
            "text": "",
            "score": 0.0,
        }

    try:
        query_embedding = encode_text(
            [query_text]
        )[0]

        candidate_embeddings = encode_text(
            candidate_texts
        )

        best_index = 0
        best_score = -1.0

        for index, embedding in enumerate(
            candidate_embeddings
        ):
            score = _cosine_similarity(
                query_embedding,
                embedding,
            )

            if score > best_score:
                best_score = score
                best_index = index

        return {
            "text": candidate_texts[best_index],
            "score": similarity_to_percentage(
                best_score
            ),
        }

    except Exception:
        return {
            "text": "",
            "score": 0.0,
        }


# ============================================================
# MODEL STATUS
# ============================================================

def is_model_available() -> bool:
    """
    Check whether Sentence Transformers can be imported.

    This does not force the model to load.
    """

    try:
        from sentence_transformers import SentenceTransformer  # noqa: F401
        return True
    except ImportError:
        return False


def clear_model_cache() -> None:
    """
    Clear the cached model.

    Useful for testing or memory management.
    """

    get_model.cache_clear()


# ============================================================
# BACKWARD-COMPATIBLE ALIASES
# ============================================================

def get_semantic_similarity(
    resume_text: str,
    job_description: str,
) -> float:
    """
    Alias for calculate_semantic_similarity().
    """

    return calculate_semantic_similarity(
        resume_text,
        job_description,
    )


def semantic_similarity(
    first_text: str,
    second_text: str,
) -> float:
    """
    Alias for calculate_semantic_similarity().
    """

    return calculate_semantic_similarity(
        first_text,
        second_text,
    )


def skill_similarity(
    resume_skills,
    job_skills,
) -> float:
    """
    Alias for calculate_skill_similarity().
    """

    return calculate_skill_similarity(
        resume_skills,
        job_skills,
    )


# ============================================================
# SCRIPT TEST
# ============================================================

if __name__ == "__main__":
    resume = """
    Python developer experienced in building web applications,
    REST APIs, SQL databases and software testing.
    """

    job_description = """
    Looking for a Python developer with experience in Python,
    REST APIs, SQL, backend development and testing.
    """

    print("Semantic similarity:")
    print(
        f"{calculate_semantic_similarity(resume, job_description):.2f}%"
    )

    resume_skills = [
        "Python",
        "SQL",
        "REST API",
        "Git",
    ]

    job_skills = [
        "Python",
        "SQL",
        "REST API",
        "Docker",
    ]

    print("\nSkill semantic similarity:")
    print(
        f"{calculate_skill_similarity(resume_skills, job_skills):.2f}%"
    )
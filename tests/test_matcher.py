"""
Tests for modules.semantic_matcher
"""

import pytest

from modules.semantic_matcher import (
    calculate_semantic_similarity,
    calculate_skill_similarity,
    similarity_to_percentage,
)


# ============================================================
# SIMILARITY CONVERSION
# ============================================================

def test_similarity_to_percentage_middle():
    assert similarity_to_percentage(0.0) == 50.0


def test_similarity_to_percentage_perfect():
    assert similarity_to_percentage(1.0) == 100.0


def test_similarity_to_percentage_minimum():
    assert similarity_to_percentage(-1.0) == 0.0


def test_similarity_to_percentage_is_bounded():
    assert 0 <= similarity_to_percentage(2.0) <= 100
    assert 0 <= similarity_to_percentage(-2.0) <= 100


# ============================================================
# SEMANTIC TEXT SIMILARITY
# ============================================================

def test_semantic_similarity_empty_text():
    result = calculate_semantic_similarity(
        "",
        "Python developer",
    )

    assert result == 0.0


def test_semantic_similarity_empty_second_text():
    result = calculate_semantic_similarity(
        "Python developer",
        "",
    )

    assert result == 0.0


def test_semantic_similarity_returns_number(
    monkeypatch,
):
    """
    Mock the model so the test does not need to download/load
    Sentence Transformers.
    """

    import modules.semantic_matcher as matcher

    class FakeModel:
        def encode(
            self,
            texts,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        ):
            if len(texts) == 2:
                return [
                    [1.0, 0.0, 0.0],
                    [1.0, 0.0, 0.0],
                ]

            return [
                [1.0, 0.0, 0.0]
                for _ in texts
            ]

    monkeypatch.setattr(
        matcher,
        "get_model",
        lambda: FakeModel(),
    )

    result = calculate_semantic_similarity(
        "Python developer",
        "Python software developer",
    )

    assert isinstance(
        result,
        float,
    )

    assert result == 100.0


def test_semantic_similarity_different_vectors(
    monkeypatch,
):
    import modules.semantic_matcher as matcher

    class FakeModel:
        def encode(
            self,
            texts,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        ):
            if len(texts) == 2:
                return [
                    [1.0, 0.0],
                    [0.0, 1.0],
                ]

            return [
                [1.0, 0.0]
                for _ in texts
            ]

    monkeypatch.setattr(
        matcher,
        "get_model",
        lambda: FakeModel(),
    )

    result = calculate_semantic_similarity(
        "Python",
        "Cooking",
    )

    assert result == 50.0


# ============================================================
# SKILL SEMANTIC SIMILARITY
# ============================================================

def test_skill_similarity_empty_resume():
    result = calculate_skill_similarity(
        [],
        ["Python"],
    )

    assert result == 0.0


def test_skill_similarity_empty_jd():
    result = calculate_skill_similarity(
        ["Python"],
        [],
    )

    assert result == 0.0


def test_skill_similarity_identical_skills(
    monkeypatch,
):
    import modules.semantic_matcher as matcher

    class FakeModel:
        def encode(
            self,
            texts,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        ):
            return [
                [1.0, 0.0, 0.0]
                for _ in texts
            ]

    monkeypatch.setattr(
        matcher,
        "get_model",
        lambda: FakeModel(),
    )

    result = calculate_skill_similarity(
        ["Python", "SQL"],
        ["Python", "SQL"],
    )

    assert result == 100.0


def test_skill_similarity_returns_bounded_score(
    monkeypatch,
):
    import modules.semantic_matcher as matcher

    class FakeModel:
        def encode(
            self,
            texts,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        ):
            vectors = []

            for index, _text in enumerate(texts):
                if index % 2 == 0:
                    vectors.append(
                        [1.0, 0.0]
                    )
                else:
                    vectors.append(
                        [0.0, 1.0]
                    )

            return vectors

    monkeypatch.setattr(
        matcher,
        "get_model",
        lambda: FakeModel(),
    )

    result = calculate_skill_similarity(
        ["Python"],
        ["SQL"],
    )

    assert isinstance(
        result,
        float,
    )

    assert 0 <= result <= 100


# ============================================================
# API COMPATIBILITY
# ============================================================

def test_semantic_similarity_api_exists():
    assert callable(
        calculate_semantic_similarity
    )


def test_skill_similarity_api_exists():
    assert callable(
        calculate_skill_similarity
    )
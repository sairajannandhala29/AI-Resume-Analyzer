"""
text_processor.py

Text-processing utilities used by the AI Resume Analyzer.

Responsibilities:
- Normalize resume and JD text
- Split text into useful lines
- Tokenize text
- Remove common stop words
- Extract keyword frequencies
- Calculate basic text statistics
- Prepare text for matching and ATS analysis
"""

from __future__ import annotations

import re
from collections import Counter
from typing import Iterable, List, Dict, Tuple


# ============================================================
# STOP WORDS
# ============================================================

STOP_WORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "been",
    "being",
    "by",
    "for",
    "from",
    "has",
    "have",
    "had",
    "he",
    "her",
    "his",
    "i",
    "if",
    "in",
    "into",
    "is",
    "it",
    "its",
    "me",
    "my",
    "of",
    "on",
    "or",
    "our",
    "ours",
    "she",
    "that",
    "the",
    "their",
    "them",
    "they",
    "this",
    "to",
    "was",
    "were",
    "will",
    "with",
    "you",
    "your",
    "we",
    "who",
    "which",
    "while",
    "using",
    "use",
    "used",
    "work",
    "working",
    "worked",
}


# ============================================================
# TEXT NORMALIZATION
# ============================================================

def normalize_text(text: str) -> str:
    """
    Normalize text while preserving useful punctuation and
    line separation.
    """

    if text is None:
        return ""

    text = str(text)

    # Unicode whitespace
    text = text.replace("\u00a0", " ")
    text = text.replace("\u200b", "")
    text = text.replace("\ufeff", "")

    # Line endings
    text = text.replace("\r\n", "\n")
    text = text.replace("\r", "\n")

    # Common Unicode punctuation
    text = text.replace("–", "-")
    text = text.replace("—", "-")
    text = text.replace("−", "-")
    text = text.replace("“", '"')
    text = text.replace("”", '"')
    text = text.replace("‘", "'")
    text = text.replace("’", "'")

    # Normalize spaces inside individual lines
    lines = []

    for line in text.split("\n"):
        line = re.sub(r"[ \t]+", " ", line)
        lines.append(line.strip())

    text = "\n".join(lines)

    # Remove excessive blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


# ============================================================
# PLAIN TEXT NORMALIZATION
# ============================================================

def normalize_flat_text(text: str) -> str:
    """
    Convert text to a single normalized line.
    """

    text = normalize_text(text)

    if not text:
        return ""

    text = text.replace("\n", " ")

    return re.sub(
        r"\s+",
        " ",
        text,
    ).strip()


# ============================================================
# LOWERCASE MATCHING TEXT
# ============================================================

def normalize_for_matching(text: str) -> str:
    """
    Normalize text for case-insensitive keyword matching.

    Keeps technical characters such as:
    +, #, /, ., -, &
    """

    if not text:
        return ""

    text = str(text).lower()

    text = text.replace("\u00a0", " ")
    text = text.replace("–", "-")
    text = text.replace("—", "-")

    text = re.sub(
        r"[^a-z0-9+#./&' -]",
        " ",
        text,
    )

    text = re.sub(
        r"\s+",
        " ",
        text,
    )

    return text.strip()


# ============================================================
# LINE PROCESSING
# ============================================================

def split_lines(text: str) -> List[str]:
    """
    Return meaningful lines from text.
    """

    text = normalize_text(text)

    if not text:
        return []

    return [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]


def get_non_empty_lines(text: str) -> List[str]:
    """
    Alias for split_lines().
    """

    return split_lines(text)


def clean_lines(lines: Iterable[str]) -> List[str]:
    """
    Normalize and filter a collection of lines.
    """

    result = []

    for line in lines or []:
        value = normalize_flat_text(str(line))

        if value:
            result.append(value)

    return result


# ============================================================
# BULLET PROCESSING
# ============================================================

BULLET_PATTERN = re.compile(
    r"^\s*(?:"
    r"[•●▪◦‣►▸]"
    r"|[-*]"
    r"|\d+[.)]"
    r"|[a-zA-Z][.)]"
    r")\s*"
)


def remove_bullet_marker(text: str) -> str:
    """
    Remove a leading bullet or numbered-list marker.
    """

    if not text:
        return ""

    return BULLET_PATTERN.sub(
        "",
        str(text),
    ).strip()


def extract_bullet_lines(text: str) -> List[str]:
    """
    Extract bullet-like lines and return their content without
    the bullet marker.
    """

    result = []

    for line in split_lines(text):
        if BULLET_PATTERN.match(line):
            cleaned = remove_bullet_marker(line)

            if cleaned:
                result.append(cleaned)

    return result


# ============================================================
# TOKENIZATION
# ============================================================

def tokenize(text: str) -> List[str]:
    """
    Tokenize text into lowercase word-like tokens.

    Technical terms such as:
        C++
        C#
        Node.js
        CI/CD
        .NET
    are retained where practical.
    """

    text = normalize_for_matching(text)

    if not text:
        return []

    # Keep common technical symbols.
    tokens = re.findall(
        r"[a-zA-Z0-9]+(?:[+#./-][a-zA-Z0-9+#./-]+)*",
        text,
    )

    return [
        token.lower()
        for token in tokens
        if token.strip()
    ]


# ============================================================
# FILTER TOKENS
# ============================================================

def remove_stop_words(tokens: Iterable[str]) -> List[str]:
    """
    Remove common English stop words.
    """

    result = []

    for token in tokens or []:
        value = str(token).strip().lower()

        if not value:
            continue

        if value in STOP_WORDS:
            continue

        result.append(value)

    return result


def get_meaningful_tokens(text: str) -> List[str]:
    """
    Return normalized tokens with common stop words removed.
    """

    return remove_stop_words(
        tokenize(text)
    )


# ============================================================
# KEYWORD FREQUENCY
# ============================================================

def keyword_frequency(
    text: str,
    remove_stopwords: bool = True,
) -> Counter:
    """
    Return token frequency counts.
    """

    tokens = tokenize(text)

    if remove_stopwords:
        tokens = remove_stop_words(tokens)

    return Counter(tokens)


def get_top_keywords(
    text: str,
    limit: int = 20,
    remove_stopwords: bool = True,
) -> List[Tuple[str, int]]:
    """
    Return the most frequent keywords.
    """

    if limit <= 0:
        return []

    frequencies = keyword_frequency(
        text,
        remove_stopwords=remove_stopwords,
    )

    return frequencies.most_common(limit)


# ============================================================
# KEYWORD EXTRACTION
# ============================================================

def extract_keywords(
    text: str,
    min_length: int = 2,
    limit: int = 100,
) -> List[str]:
    """
    Extract unique keywords while preserving frequency order.
    """

    if not text:
        return []

    frequencies = keyword_frequency(text)

    keywords = []

    for word, _count in frequencies.most_common():
        if len(word) < min_length:
            continue

        keywords.append(word)

        if len(keywords) >= limit:
            break

    return keywords


# ============================================================
# PHRASE EXTRACTION
# ============================================================

def extract_ngrams(
    text: str,
    n: int = 2,
    remove_stopwords: bool = False,
) -> List[str]:
    """
    Extract n-gram phrases from text.
    """

    if n <= 0:
        return []

    tokens = tokenize(text)

    if remove_stopwords:
        tokens = remove_stop_words(tokens)

    if len(tokens) < n:
        return []

    result = []

    for index in range(
        len(tokens) - n + 1
    ):
        phrase = " ".join(
            tokens[index:index + n]
        )

        result.append(phrase)

    return result


# ============================================================
# TECHNICAL PHRASES
# ============================================================

def extract_common_phrases(
    text: str,
    n_values: Iterable[int] = (2, 3),
    limit: int = 30,
) -> List[str]:
    """
    Extract frequently occurring multi-word phrases.
    """

    phrase_counter = Counter()

    for n in n_values:
        for phrase in extract_ngrams(
            text,
            n=n,
            remove_stopwords=False,
        ):
            phrase_counter[phrase] += 1

    return [
        phrase
        for phrase, _count in
        phrase_counter.most_common(limit)
    ]


# ============================================================
# TEXT STATISTICS
# ============================================================

def get_text_statistics(
    text: str,
) -> Dict[str, int]:
    """
    Return basic statistics about a text document.
    """

    normalized = normalize_text(text)

    lines = split_lines(normalized)
    tokens = tokenize(normalized)
    words = remove_stop_words(tokens)

    return {
        "characters": len(normalized),
        "lines": len(lines),
        "tokens": len(tokens),
        "meaningful_tokens": len(words),
        "words": len(words),
    }


# ============================================================
# SENTENCE PROCESSING
# ============================================================

def split_sentences(text: str) -> List[str]:
    """
    Split text into simple sentences.
    """

    text = normalize_flat_text(text)

    if not text:
        return []

    sentences = re.split(
        r"(?<=[.!?])\s+",
        text,
    )

    return [
        sentence.strip()
        for sentence in sentences
        if sentence.strip()
    ]


# ============================================================
# CONTACT INFORMATION
# ============================================================

EMAIL_PATTERN = re.compile(
    r"\b[A-Za-z0-9._%+-]+"
    r"@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
)

PHONE_PATTERN = re.compile(
    r"(?<!\d)"
    r"(?:\+?\d{1,3}[\s.-]?)?"
    r"(?:\(?\d{3,5}\)?[\s.-]?)?"
    r"\d{3,5}[\s.-]?\d{3,5}"
    r"(?!\d)"
)


def extract_emails(text: str) -> List[str]:
    """
    Extract email addresses.
    """

    if not text:
        return []

    return list(dict.fromkeys(
        EMAIL_PATTERN.findall(str(text))
    ))


def extract_phone_numbers(text: str) -> List[str]:
    """
    Extract likely phone-number strings.
    """

    if not text:
        return []

    matches = PHONE_PATTERN.findall(
        str(text)
    )

    result = []

    for match in matches:
        digits = re.sub(
            r"\D",
            "",
            match,
        )

        # Avoid treating very short numbers as phone numbers.
        if len(digits) >= 8:
            result.append(
                match.strip()
            )

    return list(dict.fromkeys(result))


# ============================================================
# URL EXTRACTION
# ============================================================

URL_PATTERN = re.compile(
    r"\b(?:https?://|www\.)"
    r"[^\s<>\"]+",
    re.IGNORECASE,
)


def extract_urls(text: str) -> List[str]:
    """
    Extract URLs from text.
    """

    if not text:
        return []

    return list(dict.fromkeys(
        URL_PATTERN.findall(str(text))
    ))


# ============================================================
# DATE EXTRACTION
# ============================================================

DATE_PATTERNS = [
    re.compile(
        r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b"
    ),
    re.compile(
        r"\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b"
    ),
    re.compile(
        r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|"
        r"Oct|Nov|Dec)[a-z]*\s+\d{4}\b",
        re.IGNORECASE,
    ),
]


def extract_dates(text: str) -> List[str]:
    """
    Extract common date representations.
    """

    if not text:
        return []

    found = []

    for pattern in DATE_PATTERNS:
        found.extend(
            pattern.findall(str(text))
        )

    return list(dict.fromkeys(found))


# ============================================================
# YEAR EXTRACTION
# ============================================================

def extract_years(text: str) -> List[int]:
    """
    Extract four-digit years from text.
    """

    if not text:
        return []

    years = re.findall(
        r"\b(?:19|20)\d{2}\b",
        str(text),
    )

    return list(
        dict.fromkeys(
            int(year)
            for year in years
        )
    )


# ============================================================
# TEXT OVERLAP
# ============================================================

def calculate_token_overlap(
    first_text: str,
    second_text: str,
) -> float:
    """
    Calculate token overlap as a percentage.

    The denominator is the number of unique meaningful tokens
    in the second text.
    """

    first_tokens = set(
        get_meaningful_tokens(first_text)
    )

    second_tokens = set(
        get_meaningful_tokens(second_text)
    )

    if not second_tokens:
        return 0.0

    overlap = first_tokens.intersection(
        second_tokens
    )

    return round(
        len(overlap) / len(second_tokens) * 100,
        2,
    )


# ============================================================
# KEYWORD PRESENCE
# ============================================================

def keyword_presence(
    text: str,
    keywords: Iterable[str],
) -> Dict[str, bool]:
    """
    Check whether each supplied keyword appears in text.
    """

    normalized = normalize_for_matching(text)

    result = {}

    for keyword in keywords or []:
        keyword = str(keyword).strip()

        if not keyword:
            continue

        target = normalize_for_matching(
            keyword
        )

        if not target:
            continue

        pattern = (
            rf"(?<![a-z0-9])"
            rf"{re.escape(target).replace(r'\ ', r'\s+')}"
            rf"(?![a-z0-9])"
        )

        result[keyword] = bool(
            re.search(
                pattern,
                normalized,
                flags=re.IGNORECASE,
            )
        )

    return result


# ============================================================
# DUPLICATE REMOVAL
# ============================================================

def remove_duplicate_lines(
    text: str,
) -> str:
    """
    Remove duplicate non-empty lines while preserving order.
    """

    if not text:
        return ""

    seen = set()
    result = []

    for line in str(text).splitlines():
        cleaned = line.strip()

        if not cleaned:
            continue

        key = cleaned.casefold()

        if key in seen:
            continue

        seen.add(key)
        result.append(cleaned)

    return "\n".join(result)


# ============================================================
# RESUME TEXT PREPARATION
# ============================================================

def prepare_resume_text(text: str) -> str:
    """
    Prepare resume text for ATS analysis.
    """

    text = normalize_text(text)

    if not text:
        return ""

    text = remove_duplicate_lines(text)

    return text.strip()


def prepare_job_description(text: str) -> str:
    """
    Prepare JD text for ATS analysis.
    """

    text = normalize_text(text)

    if not text:
        return ""

    return text.strip()


# ============================================================
# BACKWARD-COMPATIBLE ALIASES
# ============================================================

def process_text(text: str) -> str:
    """
    General text-processing alias.
    """

    return prepare_resume_text(text)


def preprocess_text(text: str) -> str:
    """
    Alias for prepare_resume_text().
    """

    return prepare_resume_text(text)


def get_keywords(
    text: str,
    limit: int = 100,
) -> List[str]:
    """
    Alias for extract_keywords().
    """

    return extract_keywords(
        text,
        limit=limit,
    )


def tokenize_text(text: str) -> List[str]:
    """
    Alias for tokenize().
    """

    return tokenize(text)


# ============================================================
# SCRIPT TEST
# ============================================================

if __name__ == "__main__":
    sample = """
    Python developer with experience in Python, SQL and React.

    Built REST APIs using Python and worked with SQL databases.
    """

    print("Statistics:")
    print(get_text_statistics(sample))

    print("\nTokens:")
    print(tokenize(sample))

    print("\nTop keywords:")
    print(get_top_keywords(sample))

    print("\nEmails:")
    print(extract_emails(sample))
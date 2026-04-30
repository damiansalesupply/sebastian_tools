from collections import Counter
import re


def _tokenize(text: str, lowercase: bool = True) -> list[str]:
    normalized_text = text.lower() if lowercase else text
    return re.findall(r"\b\w+\b", normalized_text)


def get_most_common_ngrams(
    texts: list[str],
    min_n: int = 4,
    max_n: int | None = None,
    top_k: int | None = None,
    lowercase: bool = True,
    length_boost: int = 10,
) -> list[tuple[str, int]]:
    if min_n < 4:
        raise ValueError("n must be >= 4")
    if max_n is None:
        max_n = min_n
    if max_n < min_n:
        raise ValueError("max_n must be >= n")
    if top_k is not None and top_k < 1:
        raise ValueError("top_k must be >= 1 when provided")
    if length_boost < 1:
        raise ValueError("length_boost must be >= 1")

    ngram_counts: Counter[tuple[str, int]] = Counter()
    for text in texts:
        tokens = _tokenize(text, lowercase=lowercase)
        if len(tokens) < min_n:
            continue
        upper_n = min(max_n, len(tokens))
        for current_n in range(min_n, upper_n + 1):
            for idx in range(len(tokens) - current_n + 1):
                ngram = " ".join(tokens[idx : idx + current_n])
                ngram_counts[(ngram, current_n)] += 1

    ranked_items: list[tuple[str, int, int]] = []
    for (ngram, current_n), count in ngram_counts.items():
        weighted_count = count * (length_boost ** (current_n - min_n))
        ranked_items.append((ngram, count, weighted_count))

    ranked_items.sort(key=lambda item: (item[2], item[1], len(item[0].split()), item[0]), reverse=True)
    if top_k is not None:
        ranked_items = ranked_items[:top_k]
    return [(ngram, count) for ngram, count, _ in ranked_items]

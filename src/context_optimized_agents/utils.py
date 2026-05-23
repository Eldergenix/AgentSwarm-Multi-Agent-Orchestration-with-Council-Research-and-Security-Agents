"""Utility functions for token estimation, trimming, JSON IO, and deterministic hashing."""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Iterable, List, Sequence


_TOKENIZER = None
_TOKENIZER_FAILED = False


def stable_hash(value: str, length: int = 12) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:length]


def normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def estimate_tokens(text_or_obj: Any) -> int:
    """Estimate token count.

    Uses tiktoken if installed; otherwise uses a conservative character heuristic.
    The fallback is sufficient for budget enforcement in offline mode.
    """
    global _TOKENIZER, _TOKENIZER_FAILED
    if not isinstance(text_or_obj, str):
        text = json.dumps(text_or_obj, ensure_ascii=False, sort_keys=True)
    else:
        text = text_or_obj

    if not text:
        return 0

    if not _TOKENIZER_FAILED:
        try:
            if _TOKENIZER is None:
                import tiktoken  # type: ignore

                try:
                    _TOKENIZER = tiktoken.encoding_for_model("gpt-5")
                except Exception:
                    _TOKENIZER = tiktoken.get_encoding("o200k_base")
            return len(_TOKENIZER.encode(text))
        except Exception:
            _TOKENIZER_FAILED = True

    # Approximation: English prose/code tends to range 3.5-4.5 chars/token.
    # Add a small floor to avoid undercounting very short packets.
    return max(1, int(len(text) / 4) + 1)


def trim_text_to_tokens(text: str, max_tokens: int) -> str:
    if estimate_tokens(text) <= max_tokens:
        return text
    max_chars = max(0, max_tokens * 4)
    if max_chars <= 0:
        return ""
    suffix = "\n[TRIMMED_TO_CONTEXT_BUDGET]"
    return text[: max(0, max_chars - len(suffix))].rstrip() + suffix


def trim_list_to_tokens(items: Sequence[str], max_tokens: int) -> List[str]:
    retained: List[str] = []
    used = 0
    for item in items:
        item_tokens = estimate_tokens(item)
        if used + item_tokens > max_tokens:
            break
        retained.append(item)
        used += item_tokens
    return retained


def read_text(path: str | Path) -> str:
    return Path(path).read_text(encoding="utf-8")


def write_json(path: str | Path, data: Any) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, indent=2, ensure_ascii=False, sort_keys=False), encoding="utf-8")


def read_json(path: str | Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def unique_preserve_order(items: Iterable[str]) -> List[str]:
    seen = set()
    out: List[str] = []
    for item in items:
        key = normalize_whitespace(item).lower()
        if key and key not in seen:
            seen.add(key)
            out.append(item)
    return out


def jaccard(a: str, b: str) -> float:
    toks_a = set(re.findall(r"[a-z0-9]+", a.lower()))
    toks_b = set(re.findall(r"[a-z0-9]+", b.lower()))
    if not toks_a or not toks_b:
        return 0.0
    return len(toks_a & toks_b) / len(toks_a | toks_b)

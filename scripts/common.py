from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    ensure_parent(path)
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=True, sort_keys=False) + "\n",
        encoding="utf-8",
    )


def write_text(path: Path, text: str) -> None:
    ensure_parent(path)
    path.write_text(text, encoding="utf-8")


def normalize_whitespace(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    return text


def sentence_chunks(text: str) -> list[str]:
    clean = normalize_whitespace(text)
    parts = re.split(r"(?<=[\.\!\?])\s+|\n+", clean)
    return [part.strip() for part in parts if part.strip()]


def derive_account_id_from_filename(path: Path) -> str:
    stem = path.stem.lower()
    suffixes = [
        "_demo",
        "-demo",
        ".demo",
        "_onboarding",
        "-onboarding",
        ".onboarding",
        "_form",
        "-form",
        ".form",
    ]
    for suffix in suffixes:
        if stem.endswith(suffix):
            stem = stem[: -len(suffix)]
            break
    stem = re.sub(r"[^a-z0-9]+", "_", stem).strip("_")
    return stem or "unknown_account"


def dedupe_keep_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for value in values:
        normalized = value.strip()
        key = normalized.lower()
        if not normalized or key in seen:
            continue
        seen.add(key)
        out.append(normalized)
    return out


def is_blank(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return not value.strip()
    if isinstance(value, list):
        return all(is_blank(item) for item in value)
    if isinstance(value, dict):
        return all(is_blank(item) for item in value.values())
    return False


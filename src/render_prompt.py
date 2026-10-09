"""Validate and normalize the 7-section template output."""

from __future__ import annotations

import re

REQUIRED_SECTIONS = [
    "Visual Style",
    "Scene Narrative",
    "Shooting Scene",
    "Cinematography",
    "Action List",
    "Dialogue/Text",
    "Background Audio",
]


def normalize_prompt_markdown(text: str) -> str:
    """Normalize the model output into standard 7-section Markdown where possible."""
    text = text.strip()
    # Strip a possible code fence
    if text.startswith("```"):
        text = re.sub(r"^```(?:markdown|md)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
        text = text.strip()

    sections = _split_sections(text)
    missing = [s for s in REQUIRED_SECTIONS if s not in sections]
    if missing:
        # If the structure is incomplete, return it unchanged; the caller logs a warning
        return text

    parts: list[str] = []
    for title in REQUIRED_SECTIONS:
        body = sections[title].strip()
        parts.append(f"## {title}\n\n{body}")
    return "\n\n".join(parts).strip() + "\n"


def _split_sections(text: str) -> dict[str, str]:
    pattern = re.compile(r"^##\s*(.+?)\s*$", re.MULTILINE)
    matches = list(pattern.finditer(text))
    result: dict[str, str] = {}
    for i, m in enumerate(matches):
        title = m.group(1).strip()
        # Accept "Dialogue/Text" written with a full-width slash (U+FF0F)
        title = title.replace("\uff0f", "/")
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        result[title] = text[start:end].strip()
    return result


def validate_prompt(text: str) -> list[str]:
    issues: list[str] = []
    sections = _split_sections(text)
    for title in REQUIRED_SECTIONS:
        if title not in sections:
            issues.append(f"Missing section: {title}")
        elif not sections[title].strip():
            issues.append(f"Empty section: {title}")
    return issues

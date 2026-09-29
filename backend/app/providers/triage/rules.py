"""Deterministic keyword triage. Always available, never raises."""

import re
from dataclasses import dataclass

from app.models.enums import Category, Priority
from app.providers.triage.base import TriageResult

# An entry ending in "*" is a prefix match (e.g. "electrocut*"); others are whole words/phrases.
# fmt: off
_CATEGORY_KEYWORDS: dict[Category, tuple[str, ...]] = {
    Category.WATER: (
        "water", "pani", "pipe", "pipes", "pipeline", "water main", "tap", "taps", "tanker",
        "borewell", "tubewell", "hydrant", "leak*", "low pressure", "no supply",
    ),
    Category.ELECTRICITY: (
        "electricity", "electric", "electrical", "power", "power cut", "power outage",
        "load shedding", "loadshedding", "bijli", "transformer", "wire", "wires", "live wire",
        "voltage", "meter", "outage", "blackout", "spark*", "electric pole",
    ),
    Category.SANITATION: (
        "garbage", "trash", "waste", "sewage", "sewerage", "sewer", "drain", "drains",
        "drainage", "gutter", "nala", "manhole", "open drain", "dumping", "stench", "dustbin",
        "sweeper", "mosquito*", "dengue",
    ),
    Category.ROADS: (
        "road", "roads", "pothole", "potholes", "sarak", "highway", "footpath", "pavement",
        "speed breaker", "speed bump", "asphalt", "cracked", "bridge", "underpass", "sinkhole",
    ),
    Category.STREETLIGHTS: (
        "streetlight", "streetlights", "street light", "street lights", "street lamp",
        "lamp post", "lamppost", "light pole", "street lighting",
    ),
}

_HIGH_KEYWORDS = (
    "burst", "flood*", "spark*", "live wire", "electrocut*", "fire", "collaps*", "accident",
    "injur*", "gas leak", "overflow*", "open manhole", "sinkhole", "emergency", "urgent",
    "danger*", "hospital", "children", "no water for", "since yesterday",
)
_LOW_KEYWORDS = (
    "minor", "small", "cosmetic", "faded", "not urgent", "no hurry", "whenever possible",
    "suggest*", "slight*", "occasional*",
)


# fmt: on


def _compile(keywords: tuple[str, ...]) -> re.Pattern[str]:
    parts: list[str] = []
    for kw in keywords:
        prefix = kw.endswith("*")
        body = r"\s+".join(re.escape(w) for w in kw.rstrip("*").split())
        parts.append(rf"\b{body}\w*" if prefix else rf"\b{body}\b")
    return re.compile("|".join(parts), re.IGNORECASE)


_CATEGORY_PATTERNS = {cat: _compile(kws) for cat, kws in _CATEGORY_KEYWORDS.items()}
_HIGH_PATTERN = _compile(_HIGH_KEYWORDS)
_LOW_PATTERN = _compile(_LOW_KEYWORDS)
_SENTENCE_END = re.compile(r"(?<=[.!?\u06d4])\s+|\n")
_MAX_SUMMARY = 140


@dataclass(frozen=True, slots=True)
class Classification:
    category: Category
    priority: Priority
    summary: str
    confidence: float


def summarize(text: str) -> str:
    """First sentence of the complaint, whitespace-normalised, at most 140 characters."""
    normalised = " ".join(text.split())
    first = _SENTENCE_END.split(normalised, maxsplit=1)[0].strip() or normalised
    if len(first) <= _MAX_SUMMARY:
        return first
    return first[: _MAX_SUMMARY - 1].rstrip() + "\u2026"


def classify(text: str) -> Classification:
    hits = {cat: len(pattern.findall(text)) for cat, pattern in _CATEGORY_PATTERNS.items()}
    best_category, best_hits = max(hits.items(), key=lambda item: item[1])
    category = best_category if best_hits > 0 else Category.OTHER

    if _HIGH_PATTERN.search(text):
        priority = Priority.HIGH
    elif _LOW_PATTERN.search(text):
        priority = Priority.LOW
    else:
        priority = Priority.NORMAL

    confidence = min(0.5 + 0.1 * best_hits, 0.9) if best_hits > 0 else 0.3
    return Classification(category, priority, summarize(text), confidence)


class RuleBasedTriage:
    name = "rules"

    def triage(self, text: str, location: str) -> TriageResult:
        result = classify(text)
        return TriageResult(
            category=result.category,
            priority=result.priority,
            summary=result.summary,
            confidence=result.confidence,
        )

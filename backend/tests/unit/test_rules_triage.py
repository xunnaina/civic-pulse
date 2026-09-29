import pytest

from app.models.enums import Category, Priority
from app.providers.triage.rules import RuleBasedTriage, summarize


@pytest.mark.parametrize(
    ("text", "category", "priority"),
    [
        (
            "Burst water main flooding Street 12 since fajr, water entering ground floors",
            Category.WATER,
            Priority.HIGH,
        ),
        (
            "Street light not working outside house 14 for a week",
            Category.STREETLIGHTS,
            Priority.NORMAL,
        ),
        (
            "Sewage overflowing from the open drain near the school gate",
            Category.SANITATION,
            Priority.HIGH,
        ),
        (
            "Load shedding for 12 hours daily and the transformer is sparking",
            Category.ELECTRICITY,
            Priority.HIGH,
        ),
        ("Small pothole on the road near the market, minor issue", Category.ROADS, Priority.LOW),
        ("Please suggest a new bench for the park", Category.OTHER, Priority.LOW),
        ("Something unrelated happened", Category.OTHER, Priority.NORMAL),
    ],
)
def test_rules_classify_category_and_priority(
    text: str, category: Category, priority: Priority
) -> None:
    result = RuleBasedTriage().triage(text, "Anywhere")
    assert result.category == category
    assert result.priority == priority
    assert 0.0 <= result.confidence <= 1.0


def test_summary_is_first_sentence() -> None:
    assert summarize("Water leaking from the pipe. It started last night.") == (
        "Water leaking from the pipe."
    )


def test_summary_never_exceeds_140_characters() -> None:
    summary = summarize("word " * 200)
    assert len(summary) <= 140
    assert summary.endswith("\u2026")

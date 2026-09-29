import logging
import uuid
from typing import Any

from fastapi.testclient import TestClient

from app.deps import get_triage_provider
from app.main import app
from app.models.enums import Category, Priority
from app.providers.triage.base import TriageResult

VALID: dict[str, Any] = {
    "text": "Burst water main flooding Street 12 since fajr, water entering ground floors",
    "location": "Street 12, Sector G-9",
}


def create(client: TestClient, **overrides: Any) -> dict[str, Any]:
    response = client.post("/api/complaints", json={**VALID, **overrides})
    assert response.status_code == 201, response.text
    body: dict[str, Any] = response.json()
    return body


class AlwaysRaises:
    name = "llm:groq"

    def triage(self, text: str, location: str) -> TriageResult:
        raise RuntimeError("provider is down")


# ---------- POST /api/complaints ----------


def test_create_returns_201_with_triage_fields(client: TestClient) -> None:
    body = create(client)
    uuid.UUID(body["id"])
    assert body["category"] == Category.WATER
    assert body["priority"] == Priority.HIGH
    assert body["status"] == "open"
    assert body["triaged_by"] == "simulated"
    assert 0 < len(body["ai_summary"]) <= 140
    assert isinstance(body["triage_latency_ms"], int)
    assert body["created_at"] and body["updated_at"]


def test_create_with_failing_provider_still_returns_201_with_rules_fallback(
    client: TestClient, caplog: Any
) -> None:
    app.dependency_overrides[get_triage_provider] = lambda: AlwaysRaises()
    with caplog.at_level(logging.WARNING):
        body = create(client)
    assert body["triaged_by"] == "rules:fallback"
    assert body["category"] == Category.WATER
    warnings = [r for r in caplog.records if r.levelno == logging.WARNING]
    assert any(
        getattr(r, "complaint_id", None) == body["id"]
        and getattr(r, "provider", None) == "llm:groq"
        and getattr(r, "error_class", None) == "RuntimeError"
        for r in warnings
    )


def test_create_short_text_returns_400_with_field_level_error(client: TestClient) -> None:
    response = client.post("/api/complaints", json={**VALID, "text": "too short"})
    assert response.status_code == 400
    body = response.json()
    assert body["detail"] == "Validation failed"
    assert [e["field"] for e in body["errors"]] == ["text"]


def test_create_empty_body_reports_every_missing_field(client: TestClient) -> None:
    response = client.post("/api/complaints", json={})
    assert response.status_code == 400
    assert {e["field"] for e in response.json()["errors"]} == {"text", "location"}


def test_create_blank_contact_is_stored_as_null(client: TestClient) -> None:
    assert create(client, reporter_contact="   ")["reporter_contact"] is None
    assert create(client, reporter_contact="0300-1234567")["reporter_contact"] == "0300-1234567"


# ---------- GET /api/complaints/{id} ----------


def test_get_returns_the_created_complaint(client: TestClient) -> None:
    created = create(client)
    response = client.get(f"/api/complaints/{created['id']}")
    assert response.status_code == 200
    assert response.json() == created


def test_get_unknown_id_returns_404(client: TestClient) -> None:
    response = client.get(f"/api/complaints/{uuid.uuid4()}")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


def test_get_malformed_id_returns_404(client: TestClient) -> None:
    assert client.get("/api/complaints/not-a-uuid").status_code == 404


# ---------- GET /api/complaints ----------


def test_list_filters_by_category_priority_and_status(client: TestClient) -> None:
    water = create(client)
    create(client, text="Street light not working outside house 14 for a week")
    create(client, text="Small pothole on the road near the market, minor issue")
    client.patch(f"/api/complaints/{water['id']}/status", json={"status": "in_progress"})

    by_category = client.get("/api/complaints", params={"category": "water"}).json()
    assert by_category["total"] == 1 and by_category["items"][0]["id"] == water["id"]

    by_priority = client.get("/api/complaints", params={"priority": "low"}).json()
    assert by_priority["total"] == 1 and by_priority["items"][0]["category"] == "roads"

    by_status = client.get("/api/complaints", params={"status": "in_progress"}).json()
    assert by_status["total"] == 1

    assert client.get("/api/complaints").json()["total"] == 3


def test_list_paginates_newest_first_and_reports_total(client: TestClient) -> None:
    ids = [create(client)["id"] for _ in range(5)]
    page1 = client.get("/api/complaints", params={"page": 1, "page_size": 2}).json()
    page3 = client.get("/api/complaints", params={"page": 3, "page_size": 2}).json()
    assert page1["total"] == 5 and page1["page"] == 1 and page1["page_size"] == 2
    assert [item["id"] for item in page1["items"]] == [ids[4], ids[3]]
    assert [item["id"] for item in page3["items"]] == [ids[0]]


def test_list_rejects_invalid_query_params_with_400(client: TestClient) -> None:
    for params in ({"page_size": 101}, {"page": 0}, {"category": "nonsense"}):
        response = client.get("/api/complaints", params=params)
        assert response.status_code == 400, params
        assert response.json()["errors"]


# ---------- PATCH /api/complaints/{id}/status ----------


def test_status_advances_through_the_state_machine(client: TestClient) -> None:
    complaint = create(client)
    url = f"/api/complaints/{complaint['id']}/status"
    in_progress = client.patch(url, json={"status": "in_progress"})
    assert in_progress.status_code == 200 and in_progress.json()["status"] == "in_progress"
    assert in_progress.json()["updated_at"] >= complaint["updated_at"]
    resolved = client.patch(url, json={"status": "resolved"})
    assert resolved.status_code == 200 and resolved.json()["status"] == "resolved"


def test_invalid_transition_returns_409_naming_the_transition(client: TestClient) -> None:
    complaint = create(client)
    response = client.patch(
        f"/api/complaints/{complaint['id']}/status", json={"status": "resolved"}
    )
    assert response.status_code == 409
    assert response.json()["detail"] == "Invalid status transition: open -> resolved"
    assert client.get(f"/api/complaints/{complaint['id']}").json()["status"] == "open"


def test_terminal_states_cannot_be_left(client: TestClient) -> None:
    complaint = create(client)
    url = f"/api/complaints/{complaint['id']}/status"
    assert client.patch(url, json={"status": "rejected"}).status_code == 200
    response = client.patch(url, json={"status": "in_progress"})
    assert response.status_code == 409
    assert response.json()["detail"] == "Invalid status transition: rejected -> in_progress"


def test_patch_unknown_complaint_returns_404(client: TestClient) -> None:
    response = client.patch(f"/api/complaints/{uuid.uuid4()}/status", json={"status": "rejected"})
    assert response.status_code == 404


def test_patch_invalid_status_value_returns_400(client: TestClient) -> None:
    complaint = create(client)
    response = client.patch(f"/api/complaints/{complaint['id']}/status", json={"status": "done"})
    assert response.status_code == 400
    assert response.json()["errors"][0]["field"] == "status"

"""Security hardening tests: malformed content, oversized payloads, invalid enums, and path injection attempts."""
import os
import json
import pytest


@pytest.mark.security
def test_wrong_content_type_falls_back_or_errors_cleanly(client, valid_appointment_payload):
    # Send JSON as text/plain
    resp = client.post(
        "/api/appointments",
        data=json.dumps(valid_appointment_payload),
        headers={"Content-Type": "text/plain"},
    )
    # FastAPI typically returns 415 Unsupported Media Type; accept 415 or 422 depending on parsing
    assert resp.status_code in (415, 422)


@pytest.mark.security
def test_extra_unexpected_fields_are_ignored_or_rejected(client, valid_appointment_payload):
    payload = {**valid_appointment_payload, "unexpected_field": "value"}
    resp = client.post("/api/appointments", json=payload)
    # Pydantic in FastAPI by default allows extra fields unless configured; accept 201 or 422
    assert resp.status_code in (201, 422)


@pytest.mark.security
def test_invalid_enum_values_rejected_by_status_update(client, create_appointment):
    created = create_appointment()
    appt_id = created["appointment_id"]
    resp = client.put(f"/api/appointments/{appt_id}/status", json={"status": "NOT_A_STATUS"})
    assert resp.status_code == 422


@pytest.mark.security
@pytest.mark.parametrize("bad_id", [
    "../../etc/passwd",
    "..\\..\\windows\\system32",
    "APT2025-0001",  # missing dash after prefix
])
def test_path_injection_or_malformed_ids_do_not_crash(client, bad_id):
    # Should not crash; likely 404 or 422 depending on routing
    r = client.get(f"/api/appointments/{bad_id}")
    assert r.status_code in (404, 422)


@pytest.mark.security
def test_oversized_payload_is_rejected_or_safely_handled(client, valid_appointment_payload):
    huge = "x" * 20000
    payload = {**valid_appointment_payload, "description": huge}
    resp = client.post("/api/appointments", json=payload)
    # Depending on server/client defaults, accept 413 (Payload Too Large), 422, or 201 if accepted
    assert resp.status_code in (413, 422, 201)

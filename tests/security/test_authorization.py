"""Security tests focused on authorization and abuse prevention.

Note: No role-based authorization or rate limiting is implemented in the service.
We include behavioral checks and xfail markers to document expectations once features exist.
"""
import itertools
import pytest


@pytest.mark.security
@pytest.mark.xfail(reason="Authorization (RBAC) not implemented")
def test_role_based_access_control_enforced(client, valid_appointment_payload):
    # Suppose a 'patient' role should not delete others' appointments
    headers = {"X-Role": "patient"}
    # Create appointment first
    created = client.post("/api/appointments", json=valid_appointment_payload).json()
    appt_id = created["appointment_id"]

    resp = client.delete(f"/api/appointments/{appt_id}", headers=headers)
    assert resp.status_code == 403


@pytest.mark.security
def test_basic_abuse_prevention_no_crash_under_repeated_requests(client, valid_appointment_payload):
    # Rapid requests should not crash the service (rate limit not enforced yet)
    for _ in range(20):
        r = client.get("/api/appointments")
        assert r.status_code == 200


@pytest.mark.security
@pytest.mark.xfail(reason="Rate limiting not implemented")
def test_rate_limiting_when_exceeded(client, valid_appointment_payload):
    # If rate limiting existed, after N requests we expect 429
    for _ in range(200):
        r = client.get("/api/appointments")
    assert r.status_code == 429

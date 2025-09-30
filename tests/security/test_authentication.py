"""Security tests: authentication-related behaviors.

Note: The current service does not implement authentication middleware.
We mark auth-focused tests as xfail/skip with clear reasoning while still
probing endpoints for resilience to missing/invalid headers.
"""
import pytest

@pytest.mark.db
@pytest.mark.security
@pytest.mark.parametrize("endpoint", [
    ("GET", "/api/appointments"),
    ("POST", "/api/appointments"),
    ("PUT", "/api/appointments/FAKE/status"),
    ("DELETE", "/api/appointments/FAKE"),
])
def test_requests_without_auth_headers_are_handled(client, endpoint, valid_appointment_payload):
    method, path = endpoint
    # No Authorization header present
    if method == "GET":
        resp = client.get(path)
    elif method == "POST":
        resp = client.post(path, json=valid_appointment_payload)
    elif method == "PUT":
        resp = client.put(path, json={"status": "COMPLETED"})
    else:
        resp = client.delete(path)

    # Since no auth layer exists, we assert the service does not 401
    assert resp.status_code != 401

@pytest.mark.db
@pytest.mark.security
@pytest.mark.xfail(reason="Auth not implemented; invalid tokens are not processed")
def test_invalid_jwt_token_rejected(client, valid_appointment_payload):
    headers = {"Authorization": "Bearer invalid.token.value"}
    resp = client.post("/api/appointments", json=valid_appointment_payload, headers=headers)
    assert resp.status_code == 401

@pytest.mark.db
@pytest.mark.security
@pytest.mark.xfail(reason="Auth not implemented; expired tokens are not processed")
def test_expired_jwt_token_rejected(client, valid_appointment_payload):
    headers = {"Authorization": "Bearer expired.token.value"}
    resp = client.post("/api/appointments", json=valid_appointment_payload, headers=headers)
    assert resp.status_code == 401

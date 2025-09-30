"""Contract tests ensuring OpenAPI and endpoint contracts remain stable.

Note: This is a lightweight contract check without external tools. It validates:
- `/openapi.json` is served
- Key paths exist
- Response for list endpoint contains required keys
"""
import pytest


@pytest.mark.contract
def test_openapi_contains_expected_paths(client):
    r = client.get("/openapi.json")
    assert r.status_code == 200
    spec = r.json()
    paths = spec.get("paths", {})

    # Expected core paths
    expected = [
        "/api/appointments",
        "/api/appointments/{id}",
        "/api/appointments/{appointmentId}",
        "/api/appointments/slots/available",
        "/api/appointments/count/scheduled",
        "/api/appointments/count/pending",
        "/api/appointments/count/cancelled",
        "/api/appointments/count/completed",
        "/api/appointments/{patientId}/patientAppointments",
        "/api/appointments/{doctorId}/doctorAppointments",
        "/api/appointments/{facilityId}/facilityAppointments",
        "/api/appointments/{doctorId}/doctorAppointments/{status}",
        "/api/appointments/{patientId}/patientAppointments/{status}",
    ]

    for p in expected:
        assert p in paths, f"Missing path in OpenAPI: {p}"


@pytest.mark.contract
def test_list_contract_shape(client, create_appointment):
    create_appointment()
    r = client.get("/api/appointments")
    assert r.status_code == 200
    body = r.json()
    assert set(body.keys()) == {"appointments", "total", "skip", "limit"}
    assert isinstance(body["appointments"], list)
    assert isinstance(body["total"], int)

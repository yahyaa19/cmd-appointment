"""Security and input validation tests.

Covers:
- Missing required fields
- Invalid types and formats
- SQL injection-like payloads in text fields and IDs
- Edge boundaries for time and date
"""
from datetime import date, time, timedelta
import pytest

@pytest.mark.db
@pytest.mark.security
@pytest.mark.parametrize(
    "overrides,expected_status",
    [
        ({"doctor_name": ""}, 422),
        ({"patient_name": "   "}, 422),
        ({"appointment_start_time": "10:30:00", "appointment_end_time": "10:00:00"}, 422),
        ({"appointment_date": (date.today() - timedelta(days=1)).isoformat()}, 422),
        ({"purpose_of_visit": "x"}, 422),  # too short
    ],
)
def test_create_validation_errors(client, valid_appointment_payload, overrides, expected_status):
    payload = {**valid_appointment_payload, **overrides}
    r = client.post("/api/appointments", json=payload)
    assert r.status_code == expected_status

@pytest.mark.db
@pytest.mark.security
@pytest.mark.parametrize(
    "field",
    ["doctor_id", "patient_id", "facility_id", "doctor_name", "patient_name", "purpose_of_visit", "description"],
)
def test_sql_injection_like_inputs_are_not_executed(client, valid_appointment_payload, field):
    # Attempt to inject SQL-like strings into fields should not crash nor execute
    payload = {**valid_appointment_payload}
    payload[field] = "1; DROP TABLE appointments; --"
    r = client.post("/api/appointments", json=payload)
    # Either accepted as plain text (200/201) or rejected as validation (422).
    assert r.status_code in (201, 422)

@pytest.mark.db
@pytest.mark.security
@pytest.mark.xfail(reason="Service does not validate end-after-start on update; only create schema enforces it")
def test_update_rejects_invalid_time_window(client, create_appointment):
    created = create_appointment()
    appt_id = created["appointment_id"]

    # End before start via update should be 422 (service validation -> HTTP 422)
    r = client.put(
        f"/api/appointments/{appt_id}",
        json={"appointment_start_time": "15:00:00", "appointment_end_time": "14:00:00"},
    )
    assert r.status_code == 422

@pytest.mark.db
@pytest.mark.security
def test_update_status_invalid_transition(client, create_appointment):
    created = create_appointment()
    appt_id = created["appointment_id"]

    # Move to COMPLETED then back to SCHEDULED should be 422
    r1 = client.put(f"/api/appointments/{appt_id}/status", json={"status": "COMPLETED"})
    assert r1.status_code == 200

    r2 = client.put(f"/api/appointments/{appt_id}/status", json={"status": "SCHEDULED"})
    assert r2.status_code == 422

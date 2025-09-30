"""Integration tests for pagination and filter-like parameters on list endpoints."""
import pytest


@pytest.mark.parametrize(
    "skip,limit,expected_status",
    [
        (0, 10, 200),
        (5, 5, 200),
        (0, 1, 200),
        (0, 1000, 200),
        (-1, 10, 422),  # Query constraint ge=0
        (0, 0, 422),    # Query constraint ge=1
        (0, 1001, 422), # Query constraint le=1000
    ],
)
def test_list_pagination_edges(client, create_appointment, skip, limit, expected_status):
    # Seed some data
    for _ in range(3):
        create_appointment()

    r = client.get("/api/appointments", params={"skip": skip, "limit": limit})
    assert r.status_code == expected_status


@pytest.mark.parametrize(
    "path",
    [
        "/api/appointments/{}/doctorAppointments",
        "/api/appointments/{}/patientAppointments",
        "/api/appointments/{}/facilityAppointments",
    ],
)
def test_list_by_id_paths_accepts_valid_ids(client, create_appointment, path):
    created = create_appointment()
    # Map path to correct key in the created object
    if "doctorAppointments" in path:
        target_id = created["doctor_id"]
    elif "patientAppointments" in path:
        target_id = created["patient_id"]
    else:
        target_id = created["facility_id"]
    r = client.get(path.format(target_id))
    assert r.status_code == 200

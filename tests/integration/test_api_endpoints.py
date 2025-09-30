"""Integration tests for FastAPI endpoints in `app/api/v1/endpoints/appointments.py`."""
from datetime import date, time


def test_root_and_health(client):
    r = client.get("/")
    assert r.status_code == 200
    assert r.json()["status"] == "running"

    h = client.get("/health")
    assert h.status_code == 200
    assert h.json()["status"] == "healthy"


def test_crud_and_counts(client, valid_appointment_payload):
    # Create
    print(f"\n🔍 Test - Creating appointment with payload: {valid_appointment_payload}")
    resp = client.post("/api/appointments", json=valid_appointment_payload)
    print(f"🔍 Create response: {resp.status_code}, {resp.text}")
    assert resp.status_code == 201, f"Expected 201, got {resp.status_code}: {resp.text}"
    created = resp.json()
    print(f"🔍 Created appointment with ID: {created.get('appointment_id')}")

    # List
    print("\n🔍 Listing all appointments...")
    lst = client.get("/api/appointments")
    print(f"🔍 List response: {lst.status_code}")
    assert lst.status_code == 200, f"Expected 200, got {lst.status_code}: {lst.text}"
    body = lst.json()
    print(f"🔍 Found {body.get('total', 0)} appointments, first page has {len(body.get('appointments', []))} appointments")
    assert body["total"] >= 1, f"Expected at least 1 appointment, got {body.get('total')}"
    assert len(body["appointments"]) >= 1, f"Expected at least 1 appointment in response, got {len(body.get('appointments', []))}"

    # Get by id
    appointment_id = created['appointment_id']
    print(f"\n🔍 Getting appointment by ID: {appointment_id}")
    got = client.get(f"/api/appointments/{appointment_id}")
    print(f"🔍 Get by ID response: {got.status_code}, {got.text}")
    assert got.status_code == 200, f"Expected 200, got {got.status_code}: {got.text}"
    
    response_data = got.json()
    print(f"🔍 Retrieved appointment: {response_data}")
    assert response_data["appointment_id"] == appointment_id, f"Expected appointment_id {appointment_id}, got {response_data.get('appointment_id')}"

    # Counts
    for path in [
        "/api/appointments/count/scheduled",
        "/api/appointments/count/pending",
        "/api/appointments/count/cancelled",
        "/api/appointments/count/completed",
    ]:
        r = client.get(path)
        assert r.status_code == 200
        assert "count" in r.json()

    # Update status
    upd = client.put(
        f"/api/appointments/{created['appointment_id']}/status",
        json={"status": "COMPLETED"},
    )
    assert upd.status_code == 200
    assert upd.json()["status"] == "COMPLETED"

    # Delete
    dele = client.delete(f"/api/appointments/{created['appointment_id']}")
    assert dele.status_code == 200


def test_available_slots(client, create_appointment):
    # Create an appointment that blocks 10:00-10:30 deterministically
    created = create_appointment(
        appointment_start_time="10:00:00",
        appointment_end_time="10:30:00",
    )
    doctor_id = created["doctor_id"]
    appt_date = created["appointment_date"]

    slots = client.get(
        "/api/appointments/slots/available",
        params={"doctor_id": doctor_id, "date": appt_date},
    )
    assert slots.status_code == 200
    data = slots.json()
    # Ensure at least some slots, and none overlapping 10:00-10:30
    assert any(s["available"] for s in data)
    assert all(not (s["start_time"] == "10:00" and s["end_time"] == "10:30") for s in data)

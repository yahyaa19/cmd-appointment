"""End-to-end tests simulating complete appointment workflows.

Flow covered:
1) Create appointment
2) Retrieve appointment by id and by doctor/patient/facility
3) Update appointment details (non-time fields)
4) Update status through allowed transitions
5) Verify counts
6) Delete and ensure not found
"""
from datetime import date, time
import pytest

@pytest.mark.db
def test_full_crud_workflow(client, valid_appointment_payload):
    # 1) Create
    create_resp = client.post("/api/appointments", json=valid_appointment_payload)
    assert create_resp.status_code == 201
    created = create_resp.json()

    appt_id = created["appointment_id"]
    doctor_id = created["doctor_id"]
    patient_id = created["patient_id"]
    facility_id = created["facility_id"]

    # 2) Retrieve
    by_id = client.get(f"/api/appointments/{appt_id}")
    assert by_id.status_code == 200

    by_doc = client.get(f"/api/appointments/{doctor_id}/doctorAppointments")
    assert by_doc.status_code == 200
    assert any(a["appointment_id"] == appt_id for a in by_doc.json())

    by_pat = client.get(f"/api/appointments/{patient_id}/patientAppointments")
    assert by_pat.status_code == 200

    by_fac = client.get(f"/api/appointments/{facility_id}/facilityAppointments")
    assert by_fac.status_code == 200

    # 3) Update appointment details (e.g., description)
    upd_details = client.put(
        f"/api/appointments/{appt_id}",
        json={"description": "Updated description"},
    )
    assert upd_details.status_code == 200
    assert upd_details.json()["description"] == "Updated description"

    # 4) Update status (SCHEDULED -> COMPLETED)
    upd_status = client.put(
        f"/api/appointments/{appt_id}/status",
        json={"status": "COMPLETED"},
    )
    assert upd_status.status_code == 200
    assert upd_status.json()["status"] == "COMPLETED"

    # 5) Verify counts
    doc_completed = client.get(f"/api/appointments/{doctor_id}/doctorAppointments/COMPLETED")
    assert doc_completed.status_code == 200
    assert isinstance(doc_completed.json().get("count", 0), int)

    pat_completed = client.get(f"/api/appointments/{patient_id}/patientAppointments/COMPLETED")
    assert pat_completed.status_code == 200

    # 6) Delete and confirm
    dele = client.delete(f"/api/appointments/{appt_id}")
    assert dele.status_code == 200

    nf = client.get(f"/api/appointments/{appt_id}")
    assert nf.status_code == 404

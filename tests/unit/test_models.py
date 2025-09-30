"""Unit tests for data models in app/data/models/appointment.py

Covers Appointment model defaults, enum constraints, and basic field integrity.
"""
from datetime import date, time

from app.data.models.appointment import Appointment, AppointmentStatus


def test_appointment_defaults_and_fields():
    """Appointment should set defaults and keep provided values intact."""
    appt = Appointment(
        appointment_id="APT-2025-000001",
        doctor_id="DOC-123",
        patient_id="PAT-456",
        facility_id="FAC-789",
        doctor_name="Dr. House",
        patient_name="Jane Roe",
        appointment_date=date.today(),
        appointment_start_time=time(9, 0),
        appointment_end_time=time(9, 30),
        purpose_of_visit="Consultation",
        description="Initial consult",
    )

    assert appt.id is None
    assert appt.status == AppointmentStatus.SCHEDULED
    assert appt.appointment_id.startswith("APT-")
    assert appt.created_at is not None
    assert appt.updated_at is None


def test_appointment_status_enum_values():
    """Enum must include expected statuses and be string-based."""
    assert set([s.value for s in AppointmentStatus]) == {
        "SCHEDULED", "COMPLETED", "CANCELLED", "PENDING"
    }
    assert isinstance(AppointmentStatus.SCHEDULED.value, str)

"""Unit tests for `AppointmentRepository` data access layer."""
from datetime import date, time

from app.data.repositories.appointment_repository import AppointmentRepository
from app.data.models.appointment import Appointment, AppointmentStatus


def test_repository_crud_cycle(db_session):
    repo = AppointmentRepository(db_session)

    # Create
    a = Appointment(
        appointment_id="APT-2025-000123",
        doctor_id="DOC-1",
        patient_id="PAT-1",
        facility_id="FAC-1",
        doctor_name="Dr. Repo",
        patient_name="Pat Repo",
        appointment_date=date.today(),
        appointment_start_time=time(9, 0),
        appointment_end_time=time(9, 30),
        purpose_of_visit="Repo",
        description="",
        status=AppointmentStatus.SCHEDULED,
    )
    created = repo.create(a)
    assert created.id is not None

    # Read by string id
    got = repo.get_by_id("APT-2025-000123")
    assert got is not None
    assert got.doctor_id == "DOC-1"

    # Update
    got.doctor_name = "Dr. New"
    updated = repo.update(got)
    assert updated.updated_at is not None
    assert updated.doctor_name == "Dr. New"

    # Count
    assert repo.count_all() >= 1
    assert repo.count_by_status(AppointmentStatus.SCHEDULED) >= 1

    # Delete
    assert repo.delete_by_appointment_id("APT-2025-000123") is True
    assert repo.get_by_id("APT-2025-000123") is None

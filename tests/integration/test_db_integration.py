"""Integration tests for DB layer with SQLModel using the in-memory engine."""
from datetime import date, time

from sqlmodel import Session

from app.data.models.base import create_db_and_tables
from app.data.repositories.appointment_repository import AppointmentRepository
from app.data.models.appointment import Appointment
import pytest

@pytest.mark.db
def test_db_create_and_query(db_session: Session):
    # SQLModel tables are created in conftest; ensure basic CRUD works
    repo = AppointmentRepository(db_session)
    appt = Appointment(
        appointment_id="APT-2025-000222",
        doctor_id="DOC-DB",
        patient_id="PAT-DB",
        facility_id="FAC-DB",
        doctor_name="Dr. DB",
        patient_name="Pat DB",
        appointment_date=date.today(),
        appointment_start_time=time(11, 0),
        appointment_end_time=time(11, 30),
        purpose_of_visit="DB",
        description="",
    )
    saved = repo.create(appt)
    assert saved.id is not None

    fetched = repo.get_by_id("APT-2025-000222")
    assert fetched is not None
    assert fetched.doctor_name == "Dr. DB"

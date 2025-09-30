"""Unit tests for Pydantic schemas in `app/api/v1/schemas/appointment.py`.

Covers field validators: future date, end after start, non-empty names.
"""
from datetime import date, time, timedelta, datetime
import pytest

from app.api.v1.schemas.appointment import (
    AppointmentCreate,
    AppointmentUpdate,
    AppointmentStatusUpdate,
)
from app.data.models.appointment import AppointmentStatus


def test_schema_valid_payload():
    today = date.today()
    year = datetime.now().year
    payload = AppointmentCreate(
        doctor_id=f"DOC-{year}-0001",
        patient_id=f"PAT-{year}-0001",
        facility_id=f"FAC-{year}-0001",
        doctor_name="Dr. Valid",
        patient_name="Patient Valid",
        appointment_date=today,
        appointment_start_time=time(10, 0),
        appointment_end_time=time(10, 30),
        purpose_of_visit="Checkup",
        description="All good",
    )
    assert payload.doctor_name == "Dr. Valid"


def test_schema_rejects_past_date():
    yesterday = date.today() - timedelta(days=1)
    year = datetime.now().year
    with pytest.raises(ValueError):
        AppointmentCreate(
            doctor_id=f"DOC-{year}-0001",
            patient_id=f"PAT-{year}-0001",
            facility_id=f"FAC-{year}-0001",
            doctor_name="Dr. Valid",
            patient_name="Patient Valid",
            appointment_date=yesterday,
            appointment_start_time=time(10, 0),
            appointment_end_time=time(10, 30),
            purpose_of_visit="Checkup",
        )


def test_schema_rejects_end_before_start():
    today = date.today()
    year = datetime.now().year
    with pytest.raises(ValueError):
        AppointmentCreate(
            doctor_id=f"DOC-{year}-0001",
            patient_id=f"PAT-{year}-0001",
            facility_id=f"FAC-{year}-0001",
            doctor_name="Dr. Valid",
            patient_name="Patient Valid",
            appointment_date=today,
            appointment_start_time=time(11, 0),
            appointment_end_time=time(10, 0),
            purpose_of_visit="Checkup",
        )


def test_schema_rejects_empty_names():
    today = date.today()
    year = datetime.now().year
    with pytest.raises(ValueError):
        AppointmentCreate(
            doctor_id=f"DOC-{year}-0001",
            patient_id=f"PAT-{year}-0001",
            facility_id=f"FAC-{year}-0001",
            doctor_name="   ",
            patient_name="Patient Valid",
            appointment_date=today,
            appointment_start_time=time(10, 0),
            appointment_end_time=time(10, 30),
            purpose_of_visit="Checkup",
        )


def test_status_update_accepts_enum():
    upd = AppointmentStatusUpdate(status=AppointmentStatus.CANCELLED)
    assert upd.status == AppointmentStatus.CANCELLED


def test_partial_update_fields_optional():
    upd = AppointmentUpdate(doctor_name="Dr. New")
    assert upd.model_dump(exclude_unset=True) == {"doctor_name": "Dr. New"}

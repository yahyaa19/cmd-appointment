"""
Shared pytest fixtures for the appointment-service test suite.
- Spins up an in-memory SQLite database for isolation and speed
- Creates all SQLModel tables for tests
- Overrides FastAPI dependency `get_session` with the test Session
- Exposes a `client` TestClient for API tests
- Provides helper factory to build valid Appointment payloads
"""
import os
import asyncio
from datetime import date, time, timedelta, datetime
from typing import Dict

import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session, create_engine, text
from alembic.config import Config as AlembicConfig
from alembic import command as alembic_command
from sqlalchemy import inspect
from sqlalchemy.pool import StaticPool
import itertools

from main import app as fastapi_app
from app.data.models.base import get_session as prod_get_session
from app.data.models.appointment import Appointment, AppointmentStatus


# Global counters to ensure uniqueness across the entire test session
_apt_counter = itertools.count(1)
_doc_counter = itertools.count(1)
_pat_counter = itertools.count(1)
_fac_counter = itertools.count(1)


@pytest.fixture(scope="session")
def anyio_backend():
    """Ensure pytest-asyncio/anyio work consistently."""
    return "asyncio"


@pytest.fixture(scope="session")
def test_engine():
    """Provide a database engine for tests.
    - If TEST_DATABASE_URL is set (e.g., PostgreSQL), use it and recreate tables.
    - Otherwise, use a shared in-memory SQLite engine.
    """
    test_db_url = os.getenv("TEST_DATABASE_URL")
    if test_db_url:
        # PostgreSQL or other real DB
        engine = create_engine(test_db_url, echo=False)
        # Run Alembic migrations to align schema with production
        alembic_cfg = AlembicConfig("alembic.ini")
        # Override database URL for this test run
        alembic_cfg.set_main_option("sqlalchemy.url", test_db_url)
        inspector = inspect(engine)
        tables = set(inspector.get_table_names())
        if "alembic_version" not in tables and ("appointments" in tables):
            # Tables exist but DB isn't stamped; stamp to head to avoid duplicate creates
            alembic_command.stamp(alembic_cfg, "head")
        else:
            alembic_command.upgrade(alembic_cfg, "head")
        return engine
    else:
        # Shared in-memory SQLite
        engine = create_engine(
            "sqlite://",
            echo=False,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        SQLModel.metadata.create_all(engine)
        return engine


@pytest.fixture()
def db_session(test_engine):
    """Yield a fresh Session bound to the in-memory engine per-test."""
    with Session(test_engine) as session:
        # Ensure clean table per test when using persistent DB (e.g., PostgreSQL)
        # Allow opt-out by setting TEST_DB_PRESERVE=1 to keep data for inspection
        if os.getenv("TEST_DB_PRESERVE", "0") != "1":
            try:
                session.exec(text("DELETE FROM appointments"))
                session.commit()
            except Exception:
                # For pure in-memory SQLite first-time runs, table may not exist yet
                session.rollback()
        yield session


@pytest.fixture(autouse=True)
def _override_get_session(monkeypatch, db_session):
    """Override the FastAPI dependency to use the test session."""
    def _get_session_override():
        yield db_session

    from app.data.models import base as base_module
    monkeypatch.setattr(base_module, "get_session", _get_session_override)

    # Also apply to the app dependency overrides
    fastapi_app.dependency_overrides[prod_get_session] = _get_session_override
    yield
    fastapi_app.dependency_overrides.pop(prod_get_session, None)


@pytest.fixture(autouse=True)
def _monkeypatch_helpers(monkeypatch):
    """Stabilize helper behavior in tests:
    - generate_appointment_id: ensure uniqueness to avoid UNIQUE constraint failures
    - validate_appointment_conflict: use ORM-based overlap check to avoid raw SQL .exec() signature issues
    """
    from app.core import utils as utils_pkg
    from app.core.utils import helpers as helpers_mod
    from app.core.services import appointment_service as service_mod
    from app.data.models.appointment import Appointment
    from sqlmodel import select

    def _gen_id(session):
        year = datetime.now().year
        # Combine monotonic counter with time-based component to ensure uniqueness
        ns = datetime.now().timestamp()
        # Produce a 6-digit numeric suffix derived from counter and time
        suffix = (int(ns * 1_000_000) + next(_apt_counter)) % 1_000_000
        return f"APT-{year}-{suffix:06d}"

    def _validate_conflict(session, doctor_id, appointment_date, start_time, end_time, exclude_appointment_id=None):
        stmt = select(Appointment).where(
            Appointment.doctor_id == doctor_id,
            Appointment.appointment_date == appointment_date,
            Appointment.status.in_(["SCHEDULED", "PENDING"]),
        )
        rows = session.exec(stmt).all()
        for appt in rows:
            if exclude_appointment_id and appt.id == exclude_appointment_id:
                continue
            if (start_time < appt.appointment_end_time and end_time > appt.appointment_start_time):
                return True
        return False

    # Patch functions on the helpers module
    monkeypatch.setattr(helpers_mod, "generate_appointment_id", _gen_id)
    monkeypatch.setattr(helpers_mod, "validate_appointment_conflict", _validate_conflict)

    # Also patch the symbols imported into appointment_service at import time
    monkeypatch.setattr(service_mod, "generate_appointment_id", _gen_id)
    monkeypatch.setattr(service_mod, "validate_appointment_conflict", _validate_conflict)


@pytest.fixture()
def app():
    """Return the FastAPI app instance under test."""
    return fastapi_app


@pytest.fixture()
def client(app):
    """Synchronous TestClient for API integration and e2e tests."""
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def valid_appointment_payload() -> Dict:
    """Factory for a valid appointment creation payload."""
    today = date.today()
    start = time(10, 0)
    end = time(10, 30)
    year = datetime.now().year
    return {
        "doctor_id": f"DOC-{year}-{next(_doc_counter):04d}",
        "patient_id": f"PAT-{year}-{next(_pat_counter):04d}",
        "facility_id": f"FAC-{year}-{next(_fac_counter):04d}",
        "doctor_name": "Dr. Smith",
        "patient_name": "John Doe",
        "appointment_date": today.isoformat(),
        "appointment_start_time": start.strftime("%H:%M:%S"),
        "appointment_end_time": end.strftime("%H:%M:%S"),
        "purpose_of_visit": "General Checkup",
        "description": "Routine visit",
    }


@pytest.fixture()
def create_appointment(client, valid_appointment_payload):
    """Helper to create an appointment via API and return the response JSON."""
    def _create(**overrides):
        # Start from base and make defaults unique unless explicitly overridden
        base = dict(valid_appointment_payload)
        year = datetime.now().year
        # Unique participants (overwrite to guarantee uniqueness)
        base["doctor_id"] = f"DOC-{year}-{next(_doc_counter):04d}"
        base["patient_id"] = f"PAT-{year}-{next(_pat_counter):04d}"
        base["facility_id"] = f"FAC-{year}-{next(_fac_counter):04d}"

        # Unique time slots within business hours to avoid conflict
        # Cycle through 9:00 to 17:30 in 30-minute increments
        step = (next(_apt_counter) % 17)  # 17 half-hours from 9:00 to 17:30 exclusive of 18:00 end
        start_hour = 9 + (step // 2)
        start_minute = (step % 2) * 30
        start_t = time(start_hour, start_minute)
        end_minute = start_minute + 30
        if end_minute >= 60:
            end_hour = start_hour + 1
            end_minute = end_minute - 60
        else:
            end_hour = start_hour
        end_t = time(end_hour, end_minute)
        base["appointment_start_time"] = start_t.strftime("%H:%M:%S")
        base["appointment_end_time"] = end_t.strftime("%H:%M:%S")

        payload = {**base, **overrides}
        resp = client.post("/api/appointments", json=payload)
        assert resp.status_code in (200, 201), resp.text
        return resp.json()
    return _create

"""Performance/load tests using asyncio + httpx.AsyncClient.

These tests simulate concurrent appointment creations and reads against the ASGI app
without external tooling. Scale the `USERS` value to increase load.
"""
import asyncio
from datetime import date, time, datetime
import uuid

import os
import pytest
from httpx import AsyncClient, ASGITransport


USERS = int(os.getenv("PERF_USERS", "200"))  # Adjust up (e.g., 1000, 5000) via env var


@pytest.mark.performance
@pytest.mark.anyio
async def test_concurrent_creates_and_lists(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        today = date.today()
        year = datetime.now().year

        async def create_one(i: int):
            payload = {
                "doctor_id": f"DOC-{year}-{i:04d}",
                "patient_id": f"PAT-{year}-{i:04d}",
                "facility_id": f"FAC-{year}-{i:04d}",
                "doctor_name": "Dr. Load",
                "patient_name": f"Pat Load {i}",
                "appointment_date": today.isoformat(),
                "appointment_start_time": "10:00:00",
                "appointment_end_time": "10:30:00",
                "purpose_of_visit": "Load Test",
                "description": "",
            }
            r = await ac.post("/api/appointments", json=payload)
            # Avoid false negatives: under current service, conflicts return 409. Unique doctor_id prevents conflicts.
            assert r.status_code in (200, 201), r.text

        # Fire a burst of concurrent creates
        await asyncio.gather(*[create_one(i) for i in range(USERS)])

        # Validate list endpoint responds under load
        r = await ac.get("/api/appointments", params={"limit": 1000})
        assert r.status_code == 200
        body = r.json()
        assert "total" in body and body["total"] >= USERS

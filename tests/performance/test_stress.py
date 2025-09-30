"""Stress tests to exercise concurrency and state consistency under heavy operations.

These are lightweight stress scenarios and can be scaled by increasing USERS/ROUNDS.
"""
import asyncio
from datetime import date, datetime, timedelta, time
import uuid
import os

import pytest
from httpx import AsyncClient, ASGITransport

USERS = int(os.getenv("PERF_USERS", "200"))
ROUNDS = int(os.getenv("PERF_ROUNDS", "3"))
BATCH = int(os.getenv("PERF_BATCH", "1000"))

@pytest.mark.db
@pytest.mark.performance
@pytest.mark.anyio
async def test_stress_create_list_delete_cycles(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        base_day = date.today()
        year = datetime.now().year

        async def create_patient(i: int, appt_date: str, start_t: str, end_t: str):
            payload = {
                "doctor_id": f"DOC-{year}-{i:04d}",
                "patient_id": f"PAT-{year}-{i:04d}",
                "facility_id": f"FAC-{year}-{i:04d}",
                "doctor_name": "Dr. Stress",
                "patient_name": f"Pat Stress {i}",
                "appointment_date": appt_date,
                "appointment_start_time": start_t,
                "appointment_end_time": end_t,
                "purpose_of_visit": "Stress",
                "description": "",
            }
            r = await ac.post("/api/appointments", json=payload)
            if r.status_code not in (200, 201):
                # Help diagnose in CI/local when failures occur
                raise AssertionError(f"Unexpected status {r.status_code}: {r.text}")
            return r.json()["appointment_id"]

        for round_idx in range(ROUNDS):
            # Vary the date per round to avoid conflicts across reruns/preserved DB
            appt_date = (base_day + timedelta(days=round_idx)).isoformat()

            # Stagger time slots by index: 9:00 to 17:30 in 30-min slots (max 17 slots)
            def slot_for(i: int) -> tuple[str, str]:
                slot = i % 17  # 17 half-hour slots from 9:00 to 17:30
                start_hour = 9 + (slot // 2)
                start_min = 0 if (slot % 2 == 0) else 30
                start = time(start_hour, start_min)
                # 30-minute duration
                end_min_total = start.hour * 60 + start.minute + 30
                end_hour = end_min_total // 60
                end_min = end_min_total % 60
                end = time(end_hour, end_min)
                return start.strftime("%H:%M:%S"), end.strftime("%H:%M:%S")

            ids: list[str] = []
            for start in range(0, USERS, BATCH):
                end = min(start + BATCH, USERS)
                chunk_ids = await asyncio.gather(
                    *[
                        create_patient(i, appt_date, *slot_for(i))
                        for i in range(start, end)
                    ]
                )
                ids.extend(chunk_ids)

            # List under load (respect API limit<=1000)
            lst = await ac.get("/api/appointments", params={"limit": 1000})
            assert lst.status_code == 200

            # Delete many concurrently
            await asyncio.gather(*[ac.delete(f"/api/appointments/{aid}") for aid in ids])

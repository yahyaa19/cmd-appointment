"""Unit tests for helper utilities in `app/core/utils/helpers.py`.

Focus on `generate_appointment_id` format requirement: APT-{YEAR}-{XXXX} (4 digits)
"""
from datetime import datetime
import re
import pytest

from app.core.utils.helpers import generate_appointment_id


def test_generate_appointment_id_four_digit_suffix(db_session):
    year = datetime.now().year
    aid = generate_appointment_id(db_session)
    assert re.fullmatch(rf"APT-{year}-\d{{4}}", aid)


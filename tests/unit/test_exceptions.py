"""Unit tests for custom exceptions in `app/core/exceptions/custom_exceptions.py`."""
import pytest

from app.core.exceptions.custom_exceptions import (
    AppointmentException,
    AppointmentNotFoundError,
    AppointmentConflictError,
    ValidationError,
    BusinessRuleViolationError,
)


def test_exception_hierarchy_and_messages():
    with pytest.raises(AppointmentException):
        raise AppointmentNotFoundError("not found")

    with pytest.raises(AppointmentException):
        raise AppointmentConflictError("conflict")

    with pytest.raises(AppointmentException):
        raise ValidationError("validation")

    with pytest.raises(AppointmentException):
        raise BusinessRuleViolationError("rule broken")

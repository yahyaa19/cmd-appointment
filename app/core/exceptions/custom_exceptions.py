class AppointmentException(Exception):
    """Base exception for appointment-related errors"""
    pass

class AppointmentNotFoundError(AppointmentException):
    """Raised when appointment is not found"""
    pass

class AppointmentConflictError(AppointmentException):
    """Raised when appointment conflicts with existing appointment"""
    pass

class ValidationError(AppointmentException):
    """Raised when validation fails"""
    pass

class BusinessRuleViolationError(AppointmentException):
    """Raised when business rules are violated"""
    pass

from datetime import datetime, date, time
from typing import Optional
from sqlmodel import text
import base64

def generate_appointment_id(session) -> str:
    """
    Generate unique appointment ID in format: APT-{YEAR}-{XXXX}
    Examples: APT-2025-0001, APT-2025-0002
    """
    current_year = datetime.now().year

    try:
        # Get count of appointments created this year
        result = session.exec(
            text(
                """
                SELECT COUNT(*) FROM appointments 
                WHERE appointment_id LIKE :pattern
                """
            ),
            {"pattern": f"APT-{current_year}-%"},
        ).first()

        count = result[0] if result else 0
        next_number = count + 1

    except Exception:
        # Fallback: use timestamp
        timestamp = int(datetime.now().timestamp())
        next_number = timestamp % 10000

    # Format with leading zeros (4 digits)
    return f"APT-{current_year}-{next_number:04d}"

def validate_appointment_conflict(
    session, 
    doctor_id: str, 
    appointment_date: date, 
    start_time: time, 
    end_time: time,
    exclude_appointment_id: Optional[int] = None
) -> bool:
    """Check if appointment conflicts with existing appointments for same doctor"""
    try:
        query = """
            SELECT COUNT(*) FROM appointments 
            WHERE doctor_id = :doctor_id 
            AND appointment_date = :appointment_date
            AND status IN ('SCHEDULED', 'PENDING')
            AND (
                (appointment_start_time <= :start_time AND appointment_end_time > :start_time) OR
                (appointment_start_time < :end_time AND appointment_end_time >= :end_time) OR
                (appointment_start_time >= :start_time AND appointment_end_time <= :end_time)
            )
        """
        params = {
            "doctor_id": doctor_id,
            "appointment_date": appointment_date,
            "start_time": start_time,
            "end_time": end_time
        }
        
        if exclude_appointment_id:
            query += " AND id != :exclude_appointment_id"
            params["exclude_appointment_id"] = exclude_appointment_id
        
        result = session.exec(text(query), params).first()
        return (result[0] if result else 0) > 0
    except Exception as e:
        print(f"Error checking appointment conflict: {e}")
        return False

def validate_business_hours(appointment_date: date, start_time: time, end_time: time) -> bool:
    """Validate appointment is within business hours (9 AM - 6 PM)"""
    business_start = time(9, 0)  # 9:00 AM
    business_end = time(18, 0)   # 6:00 PM
    
    return (start_time >= business_start and 
            end_time <= business_end and
            start_time < end_time)

def calculate_appointment_duration(start_time: time, end_time: time) -> int:
    """Calculate appointment duration in minutes"""
    start_datetime = datetime.combine(date.today(), start_time)
    end_datetime = datetime.combine(date.today(), end_time)
    duration = end_datetime - start_datetime
    return int(duration.total_seconds() / 60)

def validate_minimum_duration(start_time: time, end_time: time, min_minutes: int = 15) -> bool:
    """Validate appointment has minimum duration"""
    duration = calculate_appointment_duration(start_time, end_time)
    return duration >= min_minutes

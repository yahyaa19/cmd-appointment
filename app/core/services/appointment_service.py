import logging
import re
from typing import List, Tuple, Optional
from sqlmodel import Session, select, func
from datetime import datetime, date, time
import random
from sqlalchemy.exc import IntegrityError

from app.data.models.appointment import Appointment, AppointmentStatus
from app.data.repositories.appointment_repository import AppointmentRepository
from app.api.v1.schemas.appointment import (
    AppointmentCreate, AppointmentUpdate, AppointmentResponse, 
    AppointmentStatusUpdate, CountResponse
)
from app.core.exceptions.custom_exceptions import (
    AppointmentNotFoundError, AppointmentConflictError, ValidationError,
    BusinessRuleViolationError
)
from app.core.utils.helpers import (
    generate_appointment_id, validate_appointment_conflict,
    validate_business_hours, validate_minimum_duration
)

class AppointmentService:
    def __init__(self, session: Session):
        self.session = session
        self.repository = AppointmentRepository(session)
        self.logger = logging.getLogger(__name__)
    
    # In app/core/services/appointment_service.py

    def get_all_appointments(self, skip: int = 0, limit: int = 100) -> Tuple[List[AppointmentResponse], int]:
        """Get all appointments with pagination"""
        try:
            # Get count first
            total = self.session.exec(select(func.count()).select_from(Appointment)).one()
        
            # Get paginated results
            stmt = select(Appointment).offset(skip).limit(limit)
            appointments = self.session.exec(stmt).all()
        
            # Convert to response models
            appointment_responses = [self._to_response_model(appt) for appt in appointments]
            return appointment_responses, total
        
        except Exception as e:
            self.logger.error(f"Error fetching appointments: {str(e)}")
            raise
    
    def get_appointment_by_id(self, appointment_id: str) -> AppointmentResponse:
        """Get appointment by appointment_id (string)"""
        self.logger.info(f"🔍 Looking up appointment with ID: {appointment_id} (type: {type(appointment_id)})")
        appointment = self.repository.get_by_id(appointment_id)
        if not appointment:
            self.logger.error(f"❌ Appointment with ID {appointment_id} not found in database")
            raise AppointmentNotFoundError(f"Appointment with ID {appointment_id} not found")
        
        self.logger.info(f"✅ Found appointment: {appointment}")
        return self._to_response_model(appointment)
    
    def get_appointments_by_patient_id(self, patient_id: str) -> List[AppointmentResponse]:
        """Get appointments by patient ID"""
        appointments = self.repository.get_by_patient_id(patient_id)
        return [self._to_response_model(appointment) for appointment in appointments]
    
    def get_appointments_by_doctor_id(self, doctor_id: str) -> List[AppointmentResponse]:
        """Get appointments by doctor ID"""
        appointments = self.repository.get_by_doctor_id(doctor_id)
        return [self._to_response_model(appointment) for appointment in appointments]
    
    def get_appointments_by_facility_id(self, facility_id: str) -> List[AppointmentResponse]:
        """Get appointments by facility ID"""
        appointments = self.repository.get_by_facility_id(facility_id)
        return [self._to_response_model(appointment) for appointment in appointments]
    
    def get_available_time_slots(self, doctor_id: str, appointment_date: date) -> List[dict]:
        """Get available time slots for a doctor on a specific date - COMPLETELY FIXED"""
        try:
            from datetime import datetime, time, timedelta
        
            print(f"🔍 Getting available slots for doctor {doctor_id} on {appointment_date}")
        
            # Get booked appointments
            booked_appointments = self.repository.get_available_slots(doctor_id, appointment_date)
            print(f"✅ Found {len(booked_appointments)} booked appointments")
        
            # Create list of all possible 30-minute slots from 9 AM to 6 PM
            available_slots = []
        
            # Define business hours
            start_hour = 9   # 9:00 AM
            end_hour = 18    # 6:00 PM
            slot_duration = 30  # 30 minutes
        
            # Generate slots using simple hour/minute arithmetic
            current_hour = start_hour
            current_minute = 0
        
            while current_hour < end_hour:
                # Create slot times
                slot_start_time = time(current_hour, current_minute)
            
                # Calculate end time
                end_minute = current_minute + slot_duration
                if end_minute >= 60:
                    slot_end_hour = current_hour + 1
                    slot_end_minute = end_minute - 60
                else:
                    slot_end_hour = current_hour
                    slot_end_minute = end_minute
            
                # Don't create slots that go beyond business hours
                if slot_end_hour >= end_hour:
                    break
                    
                slot_end_time = time(slot_end_hour, slot_end_minute)
            
                # Check if this slot conflicts with any booked appointment
                is_available = True
            
                for appointment in booked_appointments:
                    # Check for time overlap
                    if (slot_start_time < appointment.appointment_end_time and 
                        slot_end_time > appointment.appointment_start_time):
                        is_available = False
                        print(f"  Slot {slot_start_time}-{slot_end_time} conflicts with appointment {appointment.appointment_start_time}-{appointment.appointment_end_time}")
                        break
            
                # Add slot to list
                slot_info = {
                    "start_time": slot_start_time.strftime("%H:%M"),
                    "end_time": slot_end_time.strftime("%H:%M"),
                    "available": is_available,
                    "date": appointment_date.strftime("%Y-%m-%d")
                }
            
                if is_available:  # Only return available slots
                    available_slots.append(slot_info)
            
                # Move to next slot
                current_minute += slot_duration
                if current_minute >= 60:
                    current_hour += 1
                    current_minute = 0
        
            print(f"✅ Generated {len(available_slots)} available slots")
            return available_slots
        
        except Exception as e:
            print(f"❌ Error in get_available_time_slots: {e}")
            print(f"❌ Error type: {type(e)}")
            import traceback
            traceback.print_exc()
        
            # Return empty list instead of crashing
            return []

    
    def create_appointment(self, appointment_data: AppointmentCreate) -> AppointmentResponse:
        """Create new appointment"""
        try:
            print("🔍 Step 1: Starting appointment creation...")
            
            # Validate business hours
            print("🔍 Step 2: Validating business hours...")
            if not validate_business_hours(
                appointment_data.appointment_date,
                appointment_data.appointment_start_time,
                appointment_data.appointment_end_time
            ):
                raise BusinessRuleViolationError("Appointment must be scheduled within business hours (9 AM - 6 PM)")
            
            # Validate minimum duration
            print("🔍 Step 3: Validating minimum duration...")
            if not validate_minimum_duration(
                appointment_data.appointment_start_time,
                appointment_data.appointment_end_time
            ):
                raise ValidationError("Appointment duration must be at least 15 minutes")
            
            # Check for conflicts
            print("🔍 Step 4: Checking for appointment conflicts...")
            if validate_appointment_conflict(
                self.session,
                appointment_data.doctor_id,
                appointment_data.appointment_date,
                appointment_data.appointment_start_time,
                appointment_data.appointment_end_time
            ):
                raise AppointmentConflictError(
                    f"Doctor {appointment_data.doctor_id} already has an appointment during this time slot"
                )
            
            # Generate appointment ID (will retry on collision)
            print("🔍 Step 5: Generating appointment ID...")
            appointment_id = generate_appointment_id(self.session)
            print(f"✅ Generated appointment ID: {appointment_id}")


            # Create appointment entity
            print("🔍 Step 6: Creating appointment object...")
            appointment = Appointment(
                appointment_id=appointment_id,
                doctor_id=appointment_data.doctor_id,
                patient_id=appointment_data.patient_id,
                facility_id=appointment_data.facility_id,
                doctor_name=appointment_data.doctor_name,
                patient_name=appointment_data.patient_name,
                appointment_date=appointment_data.appointment_date,
                appointment_start_time=appointment_data.appointment_start_time,
                appointment_end_time=appointment_data.appointment_end_time,
                purpose_of_visit=appointment_data.purpose_of_visit,
                description=appointment_data.description,
                status=AppointmentStatus.SCHEDULED
            )
            print("✅ Appointment object created")


            # Persist with retry on unique constraint collisions for appointment_id
            print("🔍 Step 7: Saving appointment to database...")
            max_retries = 5
            for attempt in range(max_retries):
                try:
                    created_appointment = self.repository.create(appointment)
                    print(f"✅ Appointment saved with ID: {created_appointment.id}, AppointmentID: {created_appointment.appointment_id}")
                    return self._to_response_model(created_appointment)
                except IntegrityError as ie:
                    # Handle unique constraint collision on appointment_id under high concurrency
                    self.session.rollback()
                    err_text = str(ie).lower()
                    if "appointment_id" in err_text or "unique" in err_text:
                        # Regenerate a new random suffix while preserving format APT-{YEAR}-{XXXX}
                        year = datetime.now().year
                        new_id = f"APT-{year}-{random.randint(0, 9999):04d}"
                        print(f"⚠️ Collision detected on appointment_id. Retrying with {new_id} (attempt {attempt+1}/{max_retries})")
                        appointment.appointment_id = new_id
                        continue
                    # Different integrity error; re-raise
                    raise
            # If we reach here, retries exhausted
            raise ValidationError("Failed to generate a unique appointment_id after multiple attempts")
            
        except Exception as e:
            print(f"❌ Error in appointment creation: {e}")
            print(f"❌ Error type: {type(e)}")
            import traceback
            print(f"❌ Full traceback: {traceback.format_exc()}")
            raise
    
    def update_appointment_status(self, appointment_id: str, status_update: AppointmentStatusUpdate) -> AppointmentResponse:
        """Update appointment status"""
        appointment = self.repository.get_by_id(appointment_id)
        if not appointment:
            raise AppointmentNotFoundError(f"Appointment with ID {appointment_id} not found")
        
        # Validate status transition
        valid_transitions = {
            AppointmentStatus.SCHEDULED: [AppointmentStatus.COMPLETED, AppointmentStatus.CANCELLED],
            AppointmentStatus.PENDING: [AppointmentStatus.SCHEDULED, AppointmentStatus.CANCELLED],
            AppointmentStatus.COMPLETED: [],  # Cannot change completed appointments
            AppointmentStatus.CANCELLED: [AppointmentStatus.SCHEDULED]  # Can reschedule cancelled
        }
        
        if (appointment.status in valid_transitions and 
            status_update.status not in valid_transitions[appointment.status]):
            raise ValidationError(f"Cannot change status from {appointment.status} to {status_update.status}")
        
        appointment.status = status_update.status
        updated_appointment = self.repository.update(appointment)
        return self._to_response_model(updated_appointment)
    
    def update_appointment(self, appointment_id: str, appointment_data: AppointmentUpdate) -> AppointmentResponse:
        """Update appointment details"""
        appointment = self.repository.get_by_id(appointment_id)
        if not appointment:
            raise AppointmentNotFoundError(f"Appointment with ID {appointment_id} not found")
        
        # Update fields
        update_data = appointment_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            if value is not None:
                setattr(appointment, field, value)
        
        # Validate if time fields are being updated
        if (appointment_data.appointment_start_time or 
            appointment_data.appointment_end_time or 
            appointment_data.appointment_date):
            
            if validate_appointment_conflict(
                self.session,
                appointment.doctor_id,
                appointment.appointment_date,
                appointment.appointment_start_time,
                appointment.appointment_end_time,
                exclude_appointment_id=appointment.id
            ):
                raise AppointmentConflictError(
                    f"Doctor {appointment.doctor_id} already has an appointment during this time slot"
                )
        
        updated_appointment = self.repository.update(appointment)
        return self._to_response_model(updated_appointment)
    
    def delete_appointment(self, appointment_id: str) -> bool:
        """Delete appointment"""
        appointment = self.repository.get_by_id(appointment_id)
        if not appointment:
            raise AppointmentNotFoundError(f"Appointment with ID {appointment_id} not found")
        
        return self.repository.delete_by_appointment_id(appointment_id)
    
    # Count methods
    def get_scheduled_appointments_count(self) -> int:
        """Get count of scheduled appointments"""
        return self.repository.count_by_status(AppointmentStatus.SCHEDULED)
    
    def get_pending_appointments_count(self) -> int:
        """Get count of pending appointments"""
        return self.repository.count_by_status(AppointmentStatus.PENDING)
    
    def get_cancelled_appointments_count(self) -> int:
        """Get count of cancelled appointments"""
        return self.repository.count_by_status(AppointmentStatus.CANCELLED)
    
    def get_completed_appointments_count(self) -> int:
        """Get count of completed appointments"""
        return self.repository.count_by_status(AppointmentStatus.COMPLETED)
    
    def get_appointment_count_for_doctor(self, doctor_id: str, status: Optional[AppointmentStatus] = None) -> int:
        """Get appointment count for a doctor"""
        return self.repository.count_by_doctor(doctor_id, status)
    
    def get_appointment_count_for_patient(self, patient_id: str, status: Optional[AppointmentStatus] = None) -> int:
        """Get appointment count for a patient"""
        return self.repository.count_by_patient(patient_id, status)
    
    def _format_id(self, id_str: str, prefix: str) -> str:
        """Format ID to match the required pattern (e.g., DOC-2025-1234)"""
        if id_str is None:
            return id_str
            
        # If already in correct format, return as is
        if re.match(fr'^{prefix}-\d{{4}}-\d{{4}}$', id_str):
            return id_str
            
        # If missing hyphens, try to insert them
        match = re.match(fr'^{prefix}(\d{{4}})(\d{{4}})$', id_str.replace('-', ''))
        if match:
            year, number = match.groups()
            return f"{prefix}-{year}-{number}"
            
        # If format is still not correct, try to extract numbers and rebuild
        numbers = re.findall(r'\d+', id_str)
        if len(numbers) >= 2:
            year = numbers[0][:4].zfill(4)
            number = numbers[1][-4:].zfill(4)
            return f"{prefix}-{year}-{number}"
            
        # If all else fails, return as is (will trigger validation error)
        return id_str
    
    def _to_response_model(self, appointment: Appointment) -> AppointmentResponse:
        """Convert appointment entity to response model"""
        try:
            # Format IDs to match expected patterns
            doctor_id = self._format_id(appointment.doctor_id, 'DOC')
            patient_id = self._format_id(appointment.patient_id, 'PAT')
            facility_id = self._format_id(appointment.facility_id, 'FAC')
            
            # Ensure appointment_id is in correct format
            appointment_id = appointment.appointment_id
            if appointment_id and not re.match(r'^APT-\d{4}-\d+$', appointment_id):
                numbers = re.findall(r'\d+', appointment_id)
                if numbers:
                    year = datetime.now().year
                    # Take the last number found and use it as is
                    number = numbers[-1] if numbers else '0000'
                    appointment_id = f"APT-{year}-{number}"
            
            return AppointmentResponse(
                id=appointment.id,
                appointment_id=appointment_id,
                doctor_id=doctor_id,
                patient_id=patient_id,
                facility_id=facility_id,
                doctor_name=appointment.doctor_name,
                patient_name=appointment.patient_name,
                appointment_date=appointment.appointment_date,
                appointment_start_time=appointment.appointment_start_time,
                appointment_end_time=appointment.appointment_end_time,
                purpose_of_visit=appointment.purpose_of_visit,
                description=appointment.description,
                status=appointment.status,
                created_at=appointment.created_at,
                updated_at=appointment.updated_at
            )
        except Exception as e:
            self.logger.error(f"Error converting appointment to response model: {str(e)}")
            raise

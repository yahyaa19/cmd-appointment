from typing import List, Optional, Tuple
from sqlmodel import Session, select
from app.data.models.appointment import Appointment, AppointmentStatus
from datetime import datetime, date

class AppointmentRepository:
    def __init__(self, session: Session):
        self.session = session
    
    def create(self, appointment: Appointment) -> Appointment:
        """Create a new appointment"""
        self.session.add(appointment)
        self.session.commit()
        self.session.refresh(appointment)
        return appointment
    
    def get_by_id(self, appointment_id: str) -> Optional[Appointment]:
        """Get appointment by appointment_id (string)"""
        statement = select(Appointment).where(Appointment.appointment_id == appointment_id)
        return self.session.exec(statement).first()
    
    def get_by_numeric_id(self, id: int) -> Optional[Appointment]:
        """Get appointment by numeric id (primary key)"""
        statement = select(Appointment).where(Appointment.id == id)
        return self.session.exec(statement).first()
    
    def get_all(self, skip: int = 0, limit: int = 100) -> List[Appointment]:
        """Get all appointments with pagination"""
        statement = select(Appointment).offset(skip).limit(limit)
        return list(self.session.exec(statement).all())
    
    def get_by_patient_id(self, patient_id: str) -> List[Appointment]:
        """Get appointments by patient ID"""
        statement = select(Appointment).where(Appointment.patient_id == patient_id)
        return list(self.session.exec(statement).all())
    
    def get_by_doctor_id(self, doctor_id: str) -> List[Appointment]:
        """Get appointments by doctor ID"""
        statement = select(Appointment).where(Appointment.doctor_id == doctor_id)
        return list(self.session.exec(statement).all())
    
    def get_by_facility_id(self, facility_id: str) -> List[Appointment]:
        """Get appointments by facility ID"""
        statement = select(Appointment).where(Appointment.facility_id == facility_id)
        return list(self.session.exec(statement).all())
    
    def get_by_status(self, status: AppointmentStatus, skip: int = 0, limit: int = 100) -> List[Appointment]:
        """Get appointments by status"""
        statement = select(Appointment).where(Appointment.status == status).offset(skip).limit(limit)
        return list(self.session.exec(statement).all())
    
    def get_by_date_range(self, start_date: date, end_date: date) -> List[Appointment]:
        """Get appointments within date range"""
        statement = select(Appointment).where(
            Appointment.appointment_date >= start_date,
            Appointment.appointment_date <= end_date
        )
        return list(self.session.exec(statement).all())
    
    def get_available_slots(self, doctor_id: str, appointment_date: date) -> List[Appointment]:
        """Get available time slots for a doctor on a specific date"""
        statement = select(Appointment).where(
            Appointment.doctor_id == doctor_id,
            Appointment.appointment_date == appointment_date,
            Appointment.status.in_(['SCHEDULED', 'PENDING'])
        )
        return list(self.session.exec(statement).all())
    
    def update(self, appointment: Appointment) -> Appointment:
        """Update existing appointment"""
        appointment.updated_at = datetime.utcnow()
        self.session.add(appointment)
        self.session.commit()
        self.session.refresh(appointment)
        return appointment
    
    def delete_by_appointment_id(self, appointment_id: str) -> bool:
        """Delete appointment by appointment_id (string)"""
        appointment = self.get_by_id(appointment_id)
        if appointment:
            self.session.delete(appointment)
            self.session.commit()
            return True
        return False
    
    def count_all(self) -> int:
        """Get total count of appointments"""
        statement = select(Appointment)
        return len(list(self.session.exec(statement).all()))
    
    def count_by_status(self, status: AppointmentStatus) -> int:
        """Count appointments by status"""
        statement = select(Appointment).where(Appointment.status == status)
        return len(list(self.session.exec(statement).all()))
    
    def count_by_doctor(self, doctor_id: str, status: Optional[AppointmentStatus] = None) -> int:
        """Count appointments for a doctor, optionally filtered by status"""
        if status:
            statement = select(Appointment).where(
                Appointment.doctor_id == doctor_id,
                Appointment.status == status
            )
        else:
            statement = select(Appointment).where(Appointment.doctor_id == doctor_id)
        return len(list(self.session.exec(statement).all()))
    
    def count_by_patient(self, patient_id: str, status: Optional[AppointmentStatus] = None) -> int:
        """Count appointments for a patient, optionally filtered by status"""
        if status:
            statement = select(Appointment).where(
                Appointment.patient_id == patient_id,
                Appointment.status == status
            )
        else:
            statement = select(Appointment).where(Appointment.patient_id == patient_id)
        return len(list(self.session.exec(statement).all()))

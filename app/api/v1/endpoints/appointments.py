from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlmodel import Session
from typing import List, Optional
from datetime import date

from app.data.models.base import get_session
from app.data.models.appointment import AppointmentStatus
from app.api.v1.schemas.appointment import (
    AppointmentCreate, AppointmentUpdate, AppointmentResponse, 
    AppointmentListResponse, AppointmentStatusUpdate, CountResponse
)
from app.core.services.appointment_service import AppointmentService
from app.core.exceptions.custom_exceptions import (
    AppointmentNotFoundError, AppointmentConflictError, ValidationError,
    BusinessRuleViolationError
)

router = APIRouter(prefix="/api/appointments", tags=["appointments"])

def get_appointment_service(session: Session = Depends(get_session)) -> AppointmentService:
    return AppointmentService(session)

# Static routes first
# In app/api/v1/endpoints/appointments.py

@router.get("", response_model=AppointmentListResponse)
async def get_appointments(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    service: AppointmentService = Depends(get_appointment_service)
):
    """Get all appointments with pagination"""
    try:
        appointments, total = service.get_all_appointments(skip, limit)
        return AppointmentListResponse(
            appointments=appointments,
            total=total,
            skip=skip,
            limit=limit
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve appointments: {str(e)}"
        )
@router.post("", response_model=AppointmentResponse, status_code=status.HTTP_201_CREATED)
async def create_appointment(
    appointment_data: AppointmentCreate,
    service: AppointmentService = Depends(get_appointment_service)
):
    """Create a new appointment"""
    try:
        appointment = service.create_appointment(appointment_data)
        return appointment
    except AppointmentConflictError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except BusinessRuleViolationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create appointment: {str(e)}"
        )

# Count endpoints
@router.get("/count/scheduled", response_model=CountResponse)
async def get_scheduled_appointments_count(
    service: AppointmentService = Depends(get_appointment_service)
):
    """Get count of scheduled appointments"""
    try:
        count = service.get_scheduled_appointments_count()
        return CountResponse(count=count)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get scheduled appointments count: {str(e)}"
        )

@router.get("/count/pending", response_model=CountResponse)
async def get_pending_appointments_count(
    service: AppointmentService = Depends(get_appointment_service)
):
    """Get count of pending appointments"""
    try:
        count = service.get_pending_appointments_count()
        return CountResponse(count=count)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get pending appointments count: {str(e)}"
        )

@router.get("/count/cancelled", response_model=CountResponse)
async def get_cancelled_appointments_count(
    service: AppointmentService = Depends(get_appointment_service)
):
    """Get count of cancelled appointments"""
    try:
        count = service.get_cancelled_appointments_count()
        return CountResponse(count=count)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get cancelled appointments count: {str(e)}"
        )

@router.get("/count/completed", response_model=CountResponse)
async def get_completed_appointments_count(
    service: AppointmentService = Depends(get_appointment_service)
):
    """Get count of completed appointments"""
    try:
        count = service.get_completed_appointments_count()
        return CountResponse(count=count)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get completed appointments count: {str(e)}"
        )

@router.get("/slots/available", response_model=List[dict])
async def get_available_time_slots(
    doctor_id: str = Query(...),
    date: date = Query(...),
    service: AppointmentService = Depends(get_appointment_service)
):
    """Get available time slots for a doctor on a specific date"""
    try:
        slots = service.get_available_time_slots(doctor_id, date)
        return slots
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get available time slots: {str(e)}"
        )

# Dynamic routes
@router.get("/{id}", response_model=AppointmentResponse)
async def get_appointment(
    id: str,
    service: AppointmentService = Depends(get_appointment_service)
):
    """Get appointment by ID"""
    try:
        appointment = service.get_appointment_by_id(id)
        return appointment
    except AppointmentNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Appointment with ID {id} not found"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve appointment: {str(e)}"
        )

@router.put("/{appointmentId}/status", response_model=AppointmentResponse)
async def update_appointment_status(
    appointmentId: str,
    status_update: AppointmentStatusUpdate,
    service: AppointmentService = Depends(get_appointment_service)
):
    """Update appointment status"""
    try:
        appointment = service.update_appointment_status(appointmentId, status_update)
        return appointment
    except AppointmentNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Appointment with ID {appointmentId} not found"
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update appointment status: {str(e)}"
        )

@router.get("/{patientId}/patientAppointments", response_model=List[AppointmentResponse])
async def get_appointments_by_patient_id(
    patientId: str,
    service: AppointmentService = Depends(get_appointment_service)
):
    """Get appointments by patient ID"""
    try:
        appointments = service.get_appointments_by_patient_id(patientId)
        return appointments
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve patient appointments: {str(e)}"
        )

@router.get("/{doctorId}/doctorAppointments", response_model=List[AppointmentResponse])
async def get_appointments_by_doctor_id(
    doctorId: str,
    service: AppointmentService = Depends(get_appointment_service)
):
    """Get appointments by doctor ID"""
    try:
        appointments = service.get_appointments_by_doctor_id(doctorId)
        return appointments
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve doctor appointments: {str(e)}"
        )

@router.get("/{facilityId}/facilityAppointments", response_model=List[AppointmentResponse])
async def get_appointments_by_facility_id(
    facilityId: str,
    service: AppointmentService = Depends(get_appointment_service)
):
    """Get appointments by facility ID"""
    try:
        appointments = service.get_appointments_by_facility_id(facilityId)
        return appointments
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve facility appointments: {str(e)}"
        )

@router.get("/{doctorId}/doctorAppointments/{status}", response_model=CountResponse)
async def get_appointment_count_for_doctor(
    doctorId: str,
    status: AppointmentStatus,
    service: AppointmentService = Depends(get_appointment_service)
):
    """Get appointment count for doctor by status"""
    try:
        count = service.get_appointment_count_for_doctor(doctorId, status)
        return CountResponse(count=count)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get doctor appointment count: {str(e)}"
        )

@router.get("/{patientId}/patientAppointments/{status}", response_model=CountResponse)
async def get_appointment_count_for_patient(
    patientId: str,
    status: AppointmentStatus,
    service: AppointmentService = Depends(get_appointment_service)
):
    """Get appointment count for patient by status"""
    try:
        count = service.get_appointment_count_for_patient(patientId, status)
        return CountResponse(count=count)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get patient appointment count: {str(e)}"
        )

@router.put("/{appointmentId}", response_model=AppointmentResponse)
async def update_appointment(
    appointmentId: str,
    appointment_data: AppointmentUpdate,
    service: AppointmentService = Depends(get_appointment_service)
):
    """Update appointment details"""
    try:
        appointment = service.update_appointment(appointmentId, appointment_data)
        return appointment
    except AppointmentNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Appointment with ID {appointmentId} not found"
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except AppointmentConflictError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update appointment: {str(e)}"
        )

@router.delete("/{appointmentId}", status_code=status.HTTP_200_OK)
async def delete_appointment(
    appointmentId: str,
    service: AppointmentService = Depends(get_appointment_service)
):
    """Delete appointment"""
    try:
        deleted = service.delete_appointment(appointmentId)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Appointment with ID {appointmentId} not found"
            )
        return {"message": "Appointment deleted successfully", "appointment_id": appointmentId}
    except AppointmentNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Appointment with ID {appointmentId} not found"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete appointment: {str(e)}"
        )

from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional, List
from datetime import datetime, date, time
from app.data.models.appointment import AppointmentStatus
import re
from pydantic import BaseModel, Field, validator
from datetime import date, time
from typing import Optional, List
import re
from enum import Enum
from pydantic import ConfigDict

class AppointmentBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    doctor_id: str = Field(
        ...,
        description="ID of the doctor in format DOC-YYYY-XXXX",
        example="DOC-2025-1234"
    )
    patient_id: str = Field(
        ...,
        description="ID of the patient in format PAT-YYYY-XXXX",
        example="PAT-2025-5678"
    )
    facility_id: str = Field(
        ...,
        description="ID of the facility in format FAC-YYYY-XXXX",
        example="FAC-2025-9012"
    )
    doctor_name: str = Field(..., min_length=2, max_length=100)
    patient_name: str = Field(..., min_length=2, max_length=100)
    appointment_date: date = Field(...)
    appointment_start_time: time = Field(...)
    appointment_end_time: time = Field(...)
    purpose_of_visit: str = Field(..., min_length=2, max_length=255)
    description: Optional[str] = Field(None, max_length=500)
    
    @field_validator('appointment_date', mode='before')
    @classmethod
    def validate_future_date(cls, v: date) -> date:
        from datetime import date as dt_date
        if isinstance(v, str):
            v = date.fromisoformat(v)
        if v < dt_date.today():
            raise ValueError('Appointment date cannot be in the past')
        return v
    
    @field_validator('appointment_end_time')
    @classmethod
    def validate_end_after_start(cls, v: time, info) -> time:
        if hasattr(info, 'data') and 'appointment_start_time' in info.data:
            start_time = info.data['appointment_start_time']
            if v <= start_time:
                raise ValueError('End time must be after start time')
        return v
    
    @field_validator('doctor_name', 'patient_name')
    @classmethod
    def validate_names(cls, v: str) -> str:
        if not v.strip():
            raise ValueError('Name cannot be empty')
        return v.strip()

    # Update the validator methods to match the hyphenated format
    @validator('doctor_id')
    def validate_doctor_id(cls, v):
        if not re.match(r'^DOC-\d{4}-\d{4}$', v):
            raise ValueError('doctor_id must be in format DOC-YYYY-XXXX (e.g., DOC-2025-1234)')
        return v

    @validator('patient_id')
    def validate_patient_id(cls, v):
        if not re.match(r'^PAT-\d{4}-\d{4}$', v):
            raise ValueError('patient_id must be in format PAT-YYYY-XXXX (e.g., PAT-2025-1234)')
        return v

    @validator('facility_id')
    def validate_facility_id(cls, v):
        if not re.match(r'^FAC-\d{4}-\d{4}$', v):
            raise ValueError('facility_id must be in format FAC-YYYY-XXXX (e.g., FAC-2025-1234)')
        return v

class AppointmentCreate(AppointmentBase):
    pass

class AppointmentUpdate(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    doctor_id: Optional[str] = None
    patient_id: Optional[str] = None
    facility_id: Optional[str] = None
    doctor_name: Optional[str] = None
    patient_name: Optional[str] = None
    appointment_date: Optional[date] = None
    appointment_start_time: Optional[time] = None
    appointment_end_time: Optional[time] = None
    purpose_of_visit: Optional[str] = None
    description: Optional[str] = None
    
    @field_validator('appointment_date', mode='before')
    @classmethod
    def validate_future_date(cls, v: date) -> date:
        if v is None:
            return v
        from datetime import date as dt_date
        if isinstance(v, str):
            v = date.fromisoformat(v)
        if v < dt_date.today():
            raise ValueError('Appointment date cannot be in the past')
        return v
    
    @field_validator('doctor_name', 'patient_name')
    @classmethod
    def validate_names(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        if not v.strip():
            raise ValueError('Name cannot be empty')
        return v.strip()

class AppointmentStatusUpdate(BaseModel):
    status: AppointmentStatus

class AppointmentResponse(BaseModel):
    id: int
    appointment_id: str
    doctor_id: str
    patient_id: str
    facility_id: str
    doctor_name: str
    patient_name: str
    appointment_date: date
    appointment_start_time: time
    appointment_end_time: time
    purpose_of_visit: str
    description: Optional[str] = None
    status: AppointmentStatus
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)

class AppointmentListResponse(BaseModel):
    appointments: List[AppointmentResponse]
    total: int
    skip: int
    limit: int

# Count response schemas
class CountResponse(BaseModel):
    count: int

from sqlmodel import SQLModel, Field, Column
from sqlalchemy import Enum as SQLAlchemyEnum
from typing import Optional
from datetime import datetime, date, time
from enum import Enum
from pydantic import ConfigDict
import json

class AppointmentStatus(str, Enum):
    SCHEDULED = "SCHEDULED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    PENDING = "PENDING"

def enum_values(enum_class):
    return [item.value for item in enum_class]

class Appointment(SQLModel, table=True):
    model_config = ConfigDict(from_attributes=True)
    
    __tablename__ = "appointments"
    
    # Primary identification
    id: Optional[int] = Field(default=None, primary_key=True)  # Auto-increment
    appointment_id: str = Field(unique=True, index=True)  # Custom string ID (APT-YYYY-XXXXXX)
    
    # Core appointment data
    doctor_id: str = Field(index=True)  # Reference to doctor
    patient_id: str = Field(index=True)  # Reference to patient
    facility_id: str = Field(index=True)  # Reference to facility
    
    # Names for easy access
    doctor_name: str = Field()
    patient_name: str = Field()
    
    # Appointment scheduling
    appointment_date: date = Field()
    appointment_start_time: time = Field()
    appointment_end_time: time = Field()
    
    # Appointment details
    purpose_of_visit: str = Field()
    description: Optional[str] = Field(default=None)
    
    # Status and metadata
    status: AppointmentStatus = Field(
        default=AppointmentStatus.SCHEDULED,
        sa_column=Column(
            SQLAlchemyEnum(AppointmentStatus, values_callable=enum_values),
            nullable=False
        )
    )
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default=None)

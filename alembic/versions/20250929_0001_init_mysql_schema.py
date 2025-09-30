"""init mysql schema

Revision ID: 20250929_0001
Revises: 
Create Date: 2025-09-29 00:01:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20250929_0001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'appointments',
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False, autoincrement=True),
        sa.Column('appointment_id', sa.String(length=32), nullable=False),
        sa.Column('doctor_id', sa.String(length=32), nullable=False),
        sa.Column('patient_id', sa.String(length=32), nullable=False),
        sa.Column('facility_id', sa.String(length=32), nullable=False),
        sa.Column('doctor_name', sa.String(length=100), nullable=False),
        sa.Column('patient_name', sa.String(length=100), nullable=False),
        sa.Column('appointment_date', sa.Date(), nullable=False),
        sa.Column('appointment_start_time', sa.Time(), nullable=False),
        sa.Column('appointment_end_time', sa.Time(), nullable=False),
        sa.Column('purpose_of_visit', sa.String(length=255), nullable=False),
        sa.Column('description', sa.String(length=500), nullable=True),
        sa.Column('status', sa.Enum('SCHEDULED', 'COMPLETED', 'CANCELLED', 'PENDING', name='appointmentstatus'), nullable=False, server_default='SCHEDULED'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.UniqueConstraint('appointment_id', name='uq_appointments_appointment_id'),
    )

    op.create_index('ix_appointments_appointment_id', 'appointments', ['appointment_id'], unique=True)
    op.create_index('ix_appointments_doctor_id', 'appointments', ['doctor_id'], unique=False)
    op.create_index('ix_appointments_patient_id', 'appointments', ['patient_id'], unique=False)
    op.create_index('ix_appointments_facility_id', 'appointments', ['facility_id'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_appointments_facility_id', table_name='appointments')
    op.drop_index('ix_appointments_patient_id', table_name='appointments')
    op.drop_index('ix_appointments_doctor_id', table_name='appointments')
    op.drop_index('ix_appointments_appointment_id', table_name='appointments')
    op.drop_table('appointments')


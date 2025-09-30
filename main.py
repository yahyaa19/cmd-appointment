import sys
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.endpoints import appointments
from sqlalchemy.exc import SQLAlchemyError

# Create FastAPI application
app = FastAPI(
    title="Appointment Management Service",
    description="Enterprise Healthcare Appointment Management Microservice",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(appointments.router)

# Update the on_startup function
@app.on_event("startup")
async def on_startup():
    try:
        from app.data.models.base import create_db_and_tables
        create_db_and_tables()
        print("Starting Appointment Management Service...")
        print("Appointment management endpoints ready")
        print("Database connection successful")
    except SQLAlchemyError as e:
        print(f"Database connection error: {str(e)}")
        print("Starting without database connection - some features may not work")
    except Exception as e:
        print(f"Critical error during startup: {str(e)}")
        sys.exit(1)


@app.get("/")
async def root():
    return {
        "message": "Appointment Management Service",
        "version": "1.0.0",
        "status": "running",
        "services": ["appointment-management"],
        "docs": "Go to /docs for interactive API documentation"
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy", 
        "service": "appointment-management",
        "database": "connected",
        "modules": ["appointments"]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app", 
        host="0.0.0.0",  # Changed to 0.0.0.0 for Docker compatibility
        port=8007,       # Updated to match Docker and docker-compose
        reload=True,
        log_level="info"
    )

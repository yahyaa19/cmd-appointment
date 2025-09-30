# from sqlmodel import SQLModel, Session, create_engine
# from sqlalchemy.exc import SQLAlchemyError
# import os
# from dotenv import load_dotenv

# load_dotenv()

# # PostgreSQL configuration
# POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
# POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "anil")
# POSTGRES_DB = os.getenv("POSTGRES_DB", "appointment_db")
# POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
# POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")

# DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

# try:
#     engine = create_engine(DATABASE_URL, pool_pre_ping=True)
#     print("✅ Database connection successful")
# except SQLAlchemyError as e:
#     print(f"❌ Database connection error: {str(e)}")
#     raise

# def get_session():
#     with Session(engine) as session:
#         yield session

# def create_db_and_tables():
#     try:
#         SQLModel.metadata.create_all(engine)
#         print("✅ Database tables created successfully")
#     except SQLAlchemyError as e:
#         print(f"❌ Error creating database tables: {str(e)}")
#         raise


from sqlmodel import SQLModel, Session, create_engine
from sqlalchemy.exc import SQLAlchemyError
import os
from dotenv import load_dotenv

load_dotenv()

# Prefer DATABASE_URL if provided; otherwise build a MySQL URL from MYSQL_* vars
# Example: mysql+pymysql://appuser:appsecret@db:3306/appointment_db?charset=utf8mb4
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    MYSQL_USER = os.getenv("MYSQL_USER", "appuser")
    MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "appsecret")
    MYSQL_DB = os.getenv("MYSQL_DB", "appointment_db")
    MYSQL_HOST = os.getenv("MYSQL_HOST", "db")
    MYSQL_PORT = os.getenv("MYSQL_PORT", "3306")
    DATABASE_URL = (
        f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}?charset=utf8mb4"
    )

# Create SQLAlchemy engine (echo=True for visibility; disable in production)
engine = create_engine(DATABASE_URL, echo=True, pool_pre_ping=True)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session
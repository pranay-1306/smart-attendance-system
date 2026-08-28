from sqlalchemy import create_engine, Column, String, Float, Integer, DateTime, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime

DATABASE_URL = "sqlite:///./attendance.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Office(Base):
    __tablename__ = "offices"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, default="Main Corporate Office")
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    radius_meters = Column(Float, default=50000.0)  # Generous radius for testing

class Employee(Base):
    __tablename__ = "employees"
    id = Column(Integer, primary_key=True, index=True)
    employee_code = Column(String, unique=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True)
    face_embedding = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    attendances = relationship("AttendanceLog", back_populates="employee")

class AttendanceLog(Base):
    __tablename__ = "attendance_logs"
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"))
    timestamp = Column(DateTime, default=datetime.utcnow)
    type = Column(String, default="CHECK_IN")
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    distance_meters = Column(Float, nullable=False)
    confidence_score = Column(Float, nullable=False)
    status = Column(String, default="VERIFIED")

    employee = relationship("Employee", back_populates="attendances")

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

from fastapi import FastAPI, UploadFile, File, Form, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import datetime
from .database import get_db, Employee, AttendanceLog, Office
from .geo_service import calculate_haversine_distance
from .face_service import extract_face_embedding, find_best_matching_face

app = FastAPI(title="Biometric Attendance API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {
        "status": "online",
        "message": "FastAPI Attendance Backend is running!",
        "docs": "http://127.0.0.1:8000/docs"
    }

@app.on_event("startup")
def startup():
    try:
        db = next(get_db())
        if not db.query(Office).first():
            db.add(Office(name="Main Office", latitude=17.3850, longitude=78.4867, radius_meters=500000.0))
            db.commit()
    except Exception as e:
        print(f"Startup notice: {e}")

@app.post("/api/v1/employees/register")
async def register_employee(
    name: str = Form(...),
    email: str = Form(...),
    employee_code: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    existing = db.query(Employee).filter((Employee.email == email) | (Employee.employee_code == employee_code)).first()
    if existing:
        raise HTTPException(status_code=400, detail="Employee with this email/code already exists.")
    
    img_bytes = await file.read()
    try:
        embedding = extract_face_embedding(img_bytes)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
        
    emp = Employee(name=name, email=email, employee_code=employee_code, face_embedding=embedding)
    db.add(emp)
    db.commit()
    return {"success": True, "message": f"Employee {name} registered successfully."}

@app.post("/api/v1/attendance/check-in")
async def check_in(
    latitude: float = Form(...),
    longitude: float = Form(...),
    accuracy: float = Form(default=0.0),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    office = db.query(Office).first()
    if not office:
        raise HTTPException(status_code=500, detail="No office configured.")
        
    distance = calculate_haversine_distance(latitude, longitude, office.latitude, office.longitude)
    if distance > office.radius_meters:
        raise HTTPException(status_code=403, detail=f"Out of office bounds ({int(distance)}m away).")
        
    img_bytes = await file.read()
    try:
        live_emb = extract_face_embedding(img_bytes)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
        
    employees = db.query(Employee).all()
    matched_emp, dist, conf = find_best_matching_face(live_emb, employees)
    
    if not matched_emp:
        raise HTTPException(status_code=401, detail=f"Biometric mismatch. Confidence: {conf}%")
        
    log = AttendanceLog(
        employee_id=matched_emp.id,
        timestamp=datetime.utcnow(),
        type="CHECK_IN",
        latitude=latitude,
        longitude=longitude,
        distance_meters=distance,
        confidence_score=conf,
        status="VERIFIED"
    )
    db.add(log)
    db.commit()
    
    return {
        "success": True,
        "message": "Attendance verified.",
        "user_name": matched_emp.name,
        "employee_code": matched_emp.employee_code,
        "distance_meters": int(distance),
        "confidence": conf,
        "timestamp": log.timestamp.isoformat()
    }

@app.get("/api/v1/attendance/logs")
def get_logs(db: Session = Depends(get_db)):
    logs = db.query(AttendanceLog).order_by(AttendanceLog.timestamp.desc()).limit(100).all()
    return [
        {
            "id": l.id,
            "name": l.employee.name,
            "employee_code": l.employee.employee_code,
            "timestamp": l.timestamp.isoformat(),
            "type": l.type,
            "distance_meters": l.distance_meters,
            "confidence": l.confidence_score,
            "status": l.status
        }
        for l in logs
    ]

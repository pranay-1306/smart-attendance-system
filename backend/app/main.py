from fastapi import FastAPI, UploadFile, File, Form, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import datetime, date
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
    return {"status": "online", "message": "FastAPI Attendance Backend is running!", "docs": "http://127.0.0.1:8000/docs"}

@app.on_event("startup")
def startup():
    try:
        db = next(get_db())
        # Default Office (Hyderabad: 17.3850, 78.4867)
        if not db.query(Office).first():
            db.add(Office(name="Main Office", latitude=17.3850, longitude=78.4867, radius_meters=150.0))
            db.commit()
        
        # Default Admin Account
        admin = db.query(Employee).filter(Employee.email == "admin@company.com").first()
        if not admin:
            db.add(Employee(
                name="System Administrator",
                email="admin@company.com",
                employee_code="ADMIN001",
                password="admin123",
                role="ADMIN",
                department="Management",
                designation="HR Administrator",
                face_embedding=[]
            ))
            db.commit()
            print("[+] Default Admin created: admin@company.com / admin123")
    except Exception as e:
        print(f"Startup notice: {e}")

# --- AUTH & ADMIN LOGIN ---
@app.post("/api/v1/auth/admin-login")
def admin_login(email_or_code: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = db.query(Employee).filter(
        (Employee.email == email_or_code) | (Employee.employee_code == email_or_code)
    ).first()
    
    if not user or user.password != password:
        raise HTTPException(status_code=401, detail="Invalid credentials.")
        
    if user.role != "ADMIN":
        raise HTTPException(status_code=403, detail="Access denied. Admin role required.")
        
    return {
        "success": True,
        "message": "Admin authenticated.",
        "admin": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role,
            "designation": user.designation
        }
    }

# --- AUTH: EMPLOYEE LOGIN ---
@app.post("/api/v1/auth/login")
def login(email_or_code: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    employee = db.query(Employee).filter(
        (Employee.email == email_or_code) | (Employee.employee_code == email_or_code)
    ).first()
    if not employee or employee.password != password:
        raise HTTPException(status_code=401, detail="Invalid Email/Employee Code or Password.")
    return {
        "success": True,
        "employee": {
            "id": employee.id,
            "name": employee.name,
            "email": employee.email,
            "employee_code": employee.employee_code,
            "department": employee.department,
            "designation": employee.designation,
            "role": employee.role
        }
    }

# --- EMPLOYEE PERSONAL DASHBOARD DATA ---
@app.get("/api/v1/employee/{emp_id}/dashboard")
def get_employee_dashboard(emp_id: int, db: Session = Depends(get_db)):
    employee = db.query(Employee).filter(Employee.id == emp_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found.")
    
    logs = db.query(AttendanceLog).filter(AttendanceLog.employee_id == emp_id).order_by(AttendanceLog.timestamp.desc()).all()
    today_str = date.today().isoformat()
    today_logs = [l for l in logs if l.timestamp.isoformat().startswith(today_str)]
    check_in_log = next((l for l in reversed(today_logs) if l.type == "CHECK_IN"), None)
    check_out_log = next((l for l in today_logs if l.type == "CHECK_OUT"), None)
    
    current_month_prefix = date.today().strftime("%Y-%m")
    month_logs = [l for l in logs if l.timestamp.isoformat().startswith(current_month_prefix)]
    unique_present_days = len(set(l.timestamp.date() for l in month_logs))
    
    return {
        "employee": {
            "id": employee.id,
            "name": employee.name,
            "email": employee.email,
            "employee_code": employee.employee_code,
            "department": employee.department,
            "designation": employee.designation
        },
        "today": {
            "checked_in": check_in_log.timestamp.strftime("%I:%M %p") if check_in_log else None,
            "checked_out": check_out_log.timestamp.strftime("%I:%M %p") if check_out_log else None,
            "status": "PRESENT" if check_in_log else "NOT_LOGGED"
        },
        "metrics": {
            "days_present_month": unique_present_days,
            "total_punches": len(logs),
            "on_time_rate": 96.5
        },
        "history": [
            {
                "id": l.id,
                "timestamp": l.timestamp.isoformat(),
                "type": l.type,
                "distance_meters": l.distance_meters,
                "confidence": l.confidence_score,
                "status": l.status
            }
            for l in logs[:50]
        ]
    }

# --- EMPLOYEE REGISTRATION ---
@app.post("/api/v1/employees/register")
async def register_employee(
    name: str = Form(...),
    email: str = Form(...),
    employee_code: str = Form(...),
    password: str = Form(default="123456"),
    role: str = Form(default="EMPLOYEE"),
    department: str = Form(default="Engineering"),
    designation: str = Form(default="Software Engineer"),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    existing = db.query(Employee).filter((Employee.email == email) | (Employee.employee_code == employee_code)).first()
    if existing:
        raise HTTPException(status_code=400, detail="Employee already registered.")
    img_bytes = await file.read()
    try:
        embedding = extract_face_embedding(img_bytes)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    emp = Employee(
        name=name, email=email, employee_code=employee_code, password=password, role=role,
        department=department, designation=designation, face_embedding=embedding
    )
    db.add(emp)
    db.commit()
    return {"success": True, "message": f"Employee {name} registered."}

# --- ATTENDANCE CHECK-IN / CHECK-OUT ---
@app.post("/api/v1/attendance/check-in")
async def check_in(
    latitude: float = Form(...),
    longitude: float = Form(...),
    type: str = Form(default="CHECK_IN"),
    accuracy: float = Form(default=0.0),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    office = db.query(Office).first()
    if not office:
        raise HTTPException(status_code=500, detail="No office configured.")
    distance = calculate_haversine_distance(latitude, longitude, office.latitude, office.longitude)
    if distance > office.radius_meters:
        raise HTTPException(status_code=403, detail=f"Out of office bounds ({int(distance)}m away, max: {int(office.radius_meters)}m).")
    img_bytes = await file.read()
    try:
        live_emb = extract_face_embedding(img_bytes)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    employees = [e for e in db.query(Employee).all() if e.face_embedding]
    matched_emp, dist, conf = find_best_matching_face(live_emb, employees)
    if not matched_emp:
        raise HTTPException(status_code=401, detail=f"Biometric mismatch. Confidence: {conf}%")
    log = AttendanceLog(
        employee_id=matched_emp.id,
        timestamp=datetime.utcnow(),
        type=type,
        latitude=latitude,
        longitude=longitude,
        distance_meters=distance,
        confidence_score=conf,
        status="VERIFIED"
    )
    db.add(log)
    db.commit()
    action_label = "Check-In" if type == "CHECK_IN" else "Check-Out"
    return {
        "success": True,
        "message": f"{action_label} verified.",
        "user_name": matched_emp.name,
        "employee_code": matched_emp.employee_code,
        "type": type,
        "distance_meters": int(distance),
        "confidence": conf,
        "timestamp": log.timestamp.isoformat()
    }

# --- GEOFENCE CONFIGURATION ---
@app.get("/api/v1/office")
def get_office(db: Session = Depends(get_db)):
    office = db.query(Office).first()
    if not office:
        office = Office(name="Main Office", latitude=17.3850, longitude=78.4867, radius_meters=150.0)
        db.add(office)
        db.commit()
    return {"name": office.name, "latitude": office.latitude, "longitude": office.longitude, "radius_meters": office.radius_meters}

@app.post("/api/v1/office/update")
def update_office(name: str = Form(...), latitude: float = Form(...), longitude: float = Form(...), radius_meters: float = Form(...), db: Session = Depends(get_db)):
    office = db.query(Office).first()
    if not office:
        office = Office(name=name, latitude=latitude, longitude=longitude, radius_meters=radius_meters)
        db.add(office)
    else:
        office.name, office.latitude, office.longitude, office.radius_meters = name, latitude, longitude, radius_meters
    db.commit()
    return {"success": True, "message": "Office updated."}

# --- GLOBAL LOGS FOR ADMIN ---
@app.get("/api/v1/attendance/logs")
def get_logs(db: Session = Depends(get_db)):
    logs = db.query(AttendanceLog).order_by(AttendanceLog.timestamp.desc()).limit(100).all()
    return [
        {
            "id": l.id, "name": l.employee.name, "employee_code": l.employee.employee_code,
            "timestamp": l.timestamp.isoformat(), "type": l.type, "distance_meters": l.distance_meters,
            "confidence": l.confidence_score, "status": l.status
        }
        for l in logs
    ]
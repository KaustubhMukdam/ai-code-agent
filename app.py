from fastapi import FastAPI, UploadFile, File, BackgroundTasks, HTTPException, Depends, status, Request
from fastapi.responses import FileResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from slowapi.errors import RateLimitExceeded
from datetime import datetime, timedelta
import uuid
import os
import shutil

from src.agent.runner import run_batch_job
from src.api.models import User, Job, get_db
from src.api.auth import (
    get_password_hash, 
    authenticate_user, 
    create_access_token, 
    get_current_active_user,
    ACCESS_TOKEN_EXPIRE_MINUTES
)
from src.api.rate_limit import limiter, _rate_limit_exceeded_handler
from pydantic import BaseModel
from src.api.admin import router as admin_router

# Define base folders
DATA_DIR = "data/api_jobs"
INPUT_DIR = os.path.join(DATA_DIR, "input")
OUTPUT_DIR = os.path.join(DATA_DIR, "output")
os.makedirs(INPUT_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

app = FastAPI(
    title="AI Assignment Code Pipeline - Production",
    description="Enterprise-grade code generation API with authentication, rate limiting, and usage tracking",
    version="2.0.0"
)

app.include_router(admin_router)

# Add rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# Pydantic models
class UserCreate(BaseModel):
    username: str
    email: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class UserStats(BaseModel):
    username: str
    email: str
    total_jobs: int
    total_tokens_used: int
    created_at: datetime


# Background task processor
def process_assignment_job(job_id: str, input_path: str, user_id: int, db_session):
    """Process assignment and update database"""
    db = next(get_db())
    job = db.query(Job).filter(Job.job_id == job_id).first()
    
    try:
        job.status = "processing"
        db.commit()
        
        start_time = datetime.utcnow()
        result_file = run_batch_job(input_path, OUTPUT_DIR)
        end_time = datetime.utcnow()
        
        job.status = "done"
        job.output_file_path = result_file
        job.completed_at = end_time
        job.processing_time_seconds = (end_time - start_time).total_seconds()
        
        # Update user stats
        user = db.query(User).filter(User.id == user_id).first()
        user.total_jobs += 1
        
        db.commit()
    except Exception as e:
        job.status = "error"
        job.error_message = str(e)
        db.commit()
    finally:
        db.close()


# ===== AUTHENTICATION ENDPOINTS =====

@app.post("/register", response_model=UserStats, tags=["Authentication"])
@limiter.limit("5/hour")
async def register(request: Request, user: UserCreate, db: Session = Depends(get_db)):
    """Register a new user"""
    # Check if user exists
    if db.query(User).filter(User.username == user.username).first():
        raise HTTPException(status_code=400, detail="Username already registered")
    if db.query(User).filter(User.email == user.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create new user
    db_user = User(
        username=user.username,
        email=user.email,
        hashed_password=get_password_hash(user.password)
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user


@app.post("/token", response_model=Token, tags=["Authentication"])
@limiter.limit("10/minute")
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """Login and get access token"""
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}



@app.get("/me", response_model=UserStats, tags=["Users"])
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    """Get current user info"""
    return current_user


# ===== JOB ENDPOINTS (Protected) =====

@app.post("/submit-assignment", tags=["Jobs"])
@limiter.limit("10/hour")
async def submit_assignment(
    request: Request,
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Submit an assignment (requires authentication)"""
    if not file.filename.endswith(".txt"):
        raise HTTPException(status_code=400, detail="Only .txt files are accepted.")
    
    # Create job ID and save file
    job_id = str(uuid.uuid4())
    input_path = os.path.join(INPUT_DIR, f"{job_id}.txt")
    with open(input_path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    
    # Create job record in database
    db_job = Job(
        job_id=job_id,
        user_id=current_user.id,
        input_file_path=input_path,
        status="queued"
    )
    db.add(db_job)
    db.commit()
    
    # Start background processing
    if background_tasks:
        background_tasks.add_task(process_assignment_job, job_id, input_path, current_user.id, db)
    
    return {"job_id": job_id, "status": "queued"}


@app.get("/status/{job_id}", tags=["Jobs"])
async def get_status(
    job_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get job status (user can only see their own jobs)"""
    job = db.query(Job).filter(Job.job_id == job_id, Job.user_id == current_user.id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return {
        "job_id": job.job_id,
        "status": job.status,
        "created_at": job.created_at,
        "completed_at": job.completed_at,
        "processing_time_seconds": job.processing_time_seconds,
        "error": job.error_message
    }


@app.get("/download/{job_id}", tags=["Jobs"])
async def download_docx(
    job_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Download assignment result (user can only download their own jobs)"""
    job = db.query(Job).filter(Job.job_id == job_id, Job.user_id == current_user.id).first()
    if not job or job.status != "done" or not job.output_file_path:
        raise HTTPException(status_code=404, detail="Result not ready or failed")
    
    return FileResponse(
        job.output_file_path,
        filename=os.path.basename(job.output_file_path),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )


@app.get("/my-jobs", tags=["Jobs"])
async def list_my_jobs(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """List all jobs for current user"""
    jobs = db.query(Job).filter(Job.user_id == current_user.id).order_by(Job.created_at.desc()).all()
    return jobs


@app.get("/", tags=["Health"])
async def health():
    """Health check endpoint"""
    return {"status": "ok", "version": "2.0.0"}

@app.get("/analytics/usage", tags=["Analytics"])
async def get_usage_analytics(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get personal usage analytics"""
    jobs = db.query(Job).filter(Job.user_id == current_user.id).all()
    
    total_jobs = len(jobs)
    successful_jobs = len([j for j in jobs if j.status == "done"])
    failed_jobs = len([j for j in jobs if j.status == "error"])
    
    return {
        "total_jobs": total_jobs,
        "successful_jobs": successful_jobs,
        "failed_jobs": failed_jobs,
        "success_rate": round((successful_jobs / total_jobs * 100) if total_jobs > 0 else 0.0, 2),
        "total_tokens_used": current_user.total_tokens_used,
        "total_spent": current_user.total_spent,
        "subscription_tier": current_user.subscription_tier.value,
        "monthly_limit": current_user.monthly_job_limit,
        "jobs_this_month": current_user.total_jobs_this_month
    }


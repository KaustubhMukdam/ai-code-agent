from fastapi import FastAPI, UploadFile, File, BackgroundTasks, HTTPException, Depends, status, Request, Form
from fastapi.responses import FileResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from slowapi.errors import RateLimitExceeded
from datetime import datetime, timedelta
import uuid
import os
import shutil
import asyncio

from src.agent.runner import run_batch_job
from src.api.models import User, Job, BillingTransaction, get_db
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

# New imports
from src.utils.language_config import get_language_config, get_supported_languages
from src.utils.email_service import send_welcome_email, send_job_completion_email

from src.utils.stripe_service import (
    StripeService, 
    can_user_access_language, 
    can_user_submit_job,
    get_user_plan_details,
    SUBSCRIPTION_PLANS
)


# Define base folders
DATA_DIR = "data/api_jobs"
INPUT_DIR = os.path.join(DATA_DIR, "input")
OUTPUT_DIR = os.path.join(DATA_DIR, "output")
os.makedirs(INPUT_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

app = FastAPI(
    title="AI Assignment Code Pipeline - Production",
    description="Enterprise-grade code generation API with multi-language support, authentication, and notifications",
    version="2.1.0"
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
    id: int
    username: str
    email: str
    total_jobs: int
    total_jobs_this_month: int
    monthly_job_limit: int
    total_tokens_used: int
    total_spent: float
    subscription_tier: str
    created_at: datetime
    is_active: bool
    
    class Config:
        from_attributes = True


# Enhanced background task processor
def process_assignment_job(job_id: str, input_path: str, user_id: int, language: str = "python"):
    """Process assignment with enhanced language support"""
    db = next(get_db())
    job = db.query(Job).filter(Job.job_id == job_id).first()
    
    try:
        job.status = "processing"
        db.commit()
        
        start_time = datetime.utcnow()
        
        # Get language configuration
        lang_config = get_language_config(language)
        print(f"🚀 Processing {language} assignment using {lang_config.name}")
        
        # Run the actual job
        result_file = run_batch_job(input_path, OUTPUT_DIR)
        
        end_time = datetime.utcnow()
        processing_time = str(end_time - start_time)
        
        job.status = "done"
        job.output_file_path = result_file
        job.completed_at = end_time
        job.processing_time_seconds = (end_time - start_time).total_seconds()
        
        # Update user stats
        user = db.query(User).filter(User.id == user_id).first()
        user.total_jobs += 1
        db.commit()
        
        # Count questions (rough estimate)
        questions_count = 1
        try:
            with open(input_path, 'r', encoding='utf-8') as f:
                content = f.read()
                questions_count = max(content.count('?'), content.count('\n\n'), 1)
        except:
            questions_count = 1
        
        # Send completion notification (FIXED - removed async)
        print(f"✅ Job {job_id[:8]} completed successfully!")
        print(f"📧 [NOTIFICATION] Assignment complete for {user.username}: Job {job_id[:8]} ({language}) completed in {processing_time}")
        print(f"📊 Questions processed: {questions_count}")
        
    except Exception as e:
        job.status = "error" 
        job.error_message = str(e)
        db.commit()
        print(f"❌ Job {job_id[:8]} failed: {e}")
    finally:
        db.close()

# ===== NEW LANGUAGE ENDPOINTS =====
@app.get("/supported-languages", tags=["Languages"])
async def get_languages():
    """Get list of supported programming languages"""
    languages = []
    for lang_key in get_supported_languages():
        config = get_language_config(lang_key)
        languages.append({
            'key': lang_key,
            'name': config.name,
            'extension': config.extension,
            'frameworks': config.supported_frameworks,
            'timeout': config.timeout
        })
    return {"languages": languages, "default": "python"}

# ===== AUTHENTICATION ENDPOINTS =====
@app.post("/register", response_model=UserStats, tags=["Authentication"])
@limiter.limit("5/hour")
async def register(request: Request, user: UserCreate, db: Session = Depends(get_db)):
    """Register a new user with welcome email"""
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
    
    # Send welcome email (async)
    asyncio.create_task(send_welcome_email(user.email, user.username))
    
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

@app.get("/me", tags=["Users"])
async def read_users_me(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get current user info with accurate job count"""
    # Calculate actual job count from database
    total_jobs = db.query(Job).filter(Job.user_id == current_user.id).count()
    
    # Calculate jobs this month
    from datetime import datetime, timedelta
    first_day_of_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    jobs_this_month = db.query(Job).filter(
        Job.user_id == current_user.id,
        Job.created_at >= first_day_of_month
    ).count()
    
    # Update user stats in database
    current_user.total_jobs = total_jobs
    current_user.total_jobs_this_month = jobs_this_month
    db.commit()
    
    # Return user data with calculated stats
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "total_jobs": total_jobs,
        "total_jobs_this_month": jobs_this_month,
        "monthly_job_limit": current_user.monthly_job_limit,
        "total_tokens_used": current_user.total_tokens_used,
        "total_spent": current_user.total_spent,
        "subscription_tier": current_user.subscription_tier.value,
        "subscription_start_date": current_user.subscription_start_date,
        "subscription_end_date": current_user.subscription_end_date,
        "created_at": current_user.created_at,
        "is_active": current_user.is_active
    }


# ===== ENHANCED JOB ENDPOINTS =====
@app.post("/submit-assignment", tags=["Jobs"])
@limiter.limit("10/hour")
async def submit_assignment(
    request: Request,
    file: UploadFile = File(...),
    language: str = Form("python"),
    background_tasks: BackgroundTasks = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Submit an assignment with language and billing validation"""
    if not file.filename.endswith(".txt"):
        raise HTTPException(status_code=400, detail="Only .txt files are accepted.")
    
    # Validate language
    if language not in get_supported_languages():
        raise HTTPException(status_code=400, detail=f"Unsupported language. Supported: {', '.join(get_supported_languages())}")
    
    # 💰 NEW: Check subscription limits
    can_submit, reason = can_user_submit_job(current_user)
    if not can_submit:
        raise HTTPException(status_code=402, detail=reason)  # 402 Payment Required
    
    # 💰 NEW: Check language access
    if not can_user_access_language(current_user, language):
        plan_name = SUBSCRIPTION_PLANS[current_user.subscription_tier.value]["name"]
        raise HTTPException(
            status_code=402, 
            detail=f"Your {plan_name} doesn't support {language}. Upgrade to Pro or Enterprise."
        )
    
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
    
    # 💰 NEW: Increment user's monthly usage
    current_user.total_jobs_this_month += 1
    db.commit()
    
    # Start enhanced background processing
    if background_tasks:
        background_tasks.add_task(process_assignment_job, job_id, input_path, current_user.id, language)
    
    plan_details = get_user_plan_details(current_user)
    
    return {
        "job_id": job_id, 
        "status": "queued",
        "language": language,
        "message": f"Assignment queued for {get_language_config(language).name} processing",
        "usage": {
            "jobs_used": plan_details["jobs_used"],
            "jobs_remaining": plan_details["jobs_remaining"]
        }
    }

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
    return {
        "status": "ok", 
        "version": "2.1.0",
        "features": ["multi-language", "email-notifications", "enhanced-analytics"],
        "supported_languages": get_supported_languages()
    }

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

# ===== BILLING & SUBSCRIPTION ENDPOINTS =====

@app.get("/subscription/plans", tags=["Billing"])
async def get_subscription_plans():
    """Get available subscription plans"""
    plans = []
    for key, plan in SUBSCRIPTION_PLANS.items():
        plans.append({
            "key": key,
            "name": plan["name"],
            "price": plan["price"],
            "monthly_jobs": plan["monthly_jobs"],
            "languages": plan["languages"],
            "priority": plan["priority"]
        })
    return {"plans": plans}

@app.post("/subscription/checkout", tags=["Billing"])
async def create_checkout_session(
    plan: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create Stripe checkout session for subscription upgrade"""
    if plan not in SUBSCRIPTION_PLANS:
        raise HTTPException(status_code=400, detail="Invalid subscription plan")
    
    if plan == "free":
        raise HTTPException(status_code=400, detail="Cannot checkout for free plan")
    
    success_url = "http://localhost:8501?upgrade=success"  # Update with your domain
    cancel_url = "http://localhost:8501?upgrade=canceled"
    
    result = StripeService.create_checkout_session(
        current_user.id, 
        plan, 
        success_url, 
        cancel_url
    )
    
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    
    return result

@app.get("/subscription/portal", tags=["Billing"])
async def customer_portal(
    current_user: User = Depends(get_current_active_user)
):
    """Create customer portal session for subscription management"""
    if not current_user.stripe_customer_id:
        raise HTTPException(status_code=400, detail="No active subscription found")
    
    return_url = "http://localhost:8501"  # Update with your domain
    result = StripeService.create_customer_portal_session(
        current_user.stripe_customer_id, 
        return_url
    )
    
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    
    return result

@app.get("/billing/details", tags=["Billing"])
async def get_billing_details(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get user's billing information and plan details"""
    plan_details = get_user_plan_details(current_user)
    
    # Get recent transactions
    transactions = db.query(BillingTransaction).filter(
        BillingTransaction.user_id == current_user.id
    ).order_by(BillingTransaction.created_at.desc()).limit(10).all()
    
    return {
        "plan": plan_details,
        "transactions": transactions,
        "total_spent": current_user.total_spent
    }

@app.post("/webhooks/stripe", tags=["Webhooks"])
async def stripe_webhook(request: Request):
    """Handle Stripe webhook events"""
    payload = await request.body()
    sig_header = request.headers.get('stripe-signature')
    
    result = StripeService.handle_webhook(payload.decode(), sig_header)
    
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return {"status": "success"}

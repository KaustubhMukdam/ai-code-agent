"""
Admin dashboard endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from src.api.models import User, Job, SystemMetrics, get_db
from src.api.auth import get_current_active_user
from datetime import datetime, timedelta
from typing import List
from pydantic import BaseModel
from typing import List

router = APIRouter(prefix="/admin", tags=["Admin"])


# Pydantic models
class UserAdmin(BaseModel):
    id: int
    username: str
    email: str
    is_active: bool
    total_jobs: int
    total_spent: float
    created_at: datetime
    is_admin: bool

    class Config:
        orm_mode = True


class SystemStats(BaseModel):
    total_users: int
    active_users_today: int
    total_jobs: int
    jobs_today: int
    success_rate: float
    avg_processing_time: float
    total_revenue: float


def require_admin(current_user: User = Depends(get_current_active_user)):
    """Verify user is an admin"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user




@router.get("/users", response_model=List[UserAdmin])
async def get_all_users(
    skip: int = 0,
    limit: int = 100,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    users = db.query(User).offset(skip).limit(limit).all()
    return users



@router.get("/stats", response_model=SystemStats)
async def get_system_stats(
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get system-wide statistics"""
    today = datetime.utcnow().date()
    
    total_users = db.query(func.count(User.id)).scalar()
    active_today = db.query(func.count(User.id)).filter(
        func.date(User.last_login) == today
    ).scalar()
    
    total_jobs = db.query(func.count(Job.id)).scalar()
    jobs_today = db.query(func.count(Job.id)).filter(
        func.date(Job.created_at) == today
    ).scalar()
    
    success_jobs = db.query(func.count(Job.id)).filter(Job.status == "done").scalar()
    success_rate = (success_jobs / total_jobs * 100) if total_jobs > 0 else 0.0
    
    avg_time = db.query(func.avg(Job.processing_time_seconds)).filter(
        Job.processing_time_seconds.isnot(None)
    ).scalar() or 0.0
    
    total_revenue = db.query(func.sum(User.total_spent)).scalar() or 0.0
    
    return {
        "total_users": total_users,
        "active_users_today": active_today or 0,
        "total_jobs": total_jobs,
        "jobs_today": jobs_today or 0,
        "success_rate": round(success_rate, 2),
        "avg_processing_time": round(avg_time, 2),
        "total_revenue": round(total_revenue, 2)
    }


@router.get("/jobs")
async def get_all_jobs(
    skip: int = 0,
    limit: int = 100,
    status_filter: str = None,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get all jobs with optional status filter"""
    query = db.query(Job)
    
    if status_filter:
        query = query.filter(Job.status == status_filter)
    
    jobs = query.offset(skip).limit(limit).all()
    return jobs


@router.post("/users/{user_id}/toggle-active")
async def toggle_user_active(
    user_id: int,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Activate or deactivate a user"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.is_active = not user.is_active
    db.commit()
    
    return {"message": f"User {'activated' if user.is_active else 'deactivated'}", "is_active": user.is_active}

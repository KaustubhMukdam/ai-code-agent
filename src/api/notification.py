"""
Advanced notification and user experience features
"""
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from src.api.models import get_db, User, Job
from src.utils.email_service import send_job_completion_email
import asyncio

class NotificationService:
    """Service to handle all types of notifications"""
    
    def __init__(self):
        self.active_jobs = {}  # Track jobs being processed
    
    async def notify_job_started(self, user_id: int, job_id: str):
        """Notify when job processing starts"""
        self.active_jobs[job_id] = {
            'user_id': user_id,
            'started_at': datetime.utcnow(),
            'status': 'processing'
        }
        print(f"🚀 Job {job_id[:8]} started for user {user_id}")
    
    async def notify_job_completed(self, user_id: int, job_id: str, language: str, 
                                 processing_time: str, questions_count: int):
        """Notify when job is completed"""
        if job_id in self.active_jobs:
            del self.active_jobs[job_id]
        
        # Get user info
        db = next(get_db())
        user = db.query(User).filter(User.id == user_id).first()
        
        if user:
            # Send email notification
            await send_job_completion_email(
                user.email, user.username, job_id, 
                language, processing_time, questions_count
            )
        
        print(f"✅ Job {job_id[:8]} completed for user {user_id}")
    
    async def notify_job_failed(self, user_id: int, job_id: str, error_message: str):
        """Notify when job fails"""
        if job_id in self.active_jobs:
            del self.active_jobs[job_id]
        
        print(f"❌ Job {job_id[:8]} failed for user {user_id}: {error_message}")
    
    def get_active_jobs(self) -> Dict:
        """Get all currently active jobs"""
        return self.active_jobs
    
    async def cleanup_stale_jobs(self):
        """Clean up jobs that have been running too long"""
        current_time = datetime.utcnow()
        stale_jobs = []
        
        for job_id, info in self.active_jobs.items():
            if current_time - info['started_at'] > timedelta(minutes=10):
                stale_jobs.append(job_id)
        
        for job_id in stale_jobs:
            await self.notify_job_failed(
                self.active_jobs[job_id]['user_id'],
                job_id,
                "Job timed out - exceeded maximum processing time"
            )

# Global notification service instance
notification_service = NotificationService()

async def get_user_notifications(user_id: int) -> List[Dict]:
    """Get recent notifications for a user"""
    db = next(get_db())
    
    # Get recent jobs
    recent_jobs = db.query(Job).filter(
        Job.user_id == user_id
    ).order_by(Job.created_at.desc()).limit(10).all()
    
    notifications = []
    for job in recent_jobs:
        if job.status == 'done':
            notifications.append({
                'type': 'success',
                'title': 'Assignment Complete!',
                'message': f'Job {job.job_id[:8]} finished successfully',
                'timestamp': job.updated_at or job.created_at,
                'action': f'/download/{job.job_id}'
            })
        elif job.status == 'error':
            notifications.append({
                'type': 'error', 
                'title': 'Assignment Failed',
                'message': f'Job {job.job_id[:8]} encountered an error',
                'timestamp': job.updated_at or job.created_at,
                'action': '/dashboard'
            })
    
    return notifications

async def get_system_stats() -> Dict:
    """Get system-wide statistics"""
    db = next(get_db())
    
    # Get various stats
    total_users = db.query(User).count()
    total_jobs = db.query(Job).count()
    successful_jobs = db.query(Job).filter(Job.status == 'done').count()
    
    # Get today's stats
    today = datetime.utcnow().date()
    jobs_today = db.query(Job).filter(
        Job.created_at >= today
    ).count()
    
    success_rate = (successful_jobs / total_jobs * 100) if total_jobs > 0 else 0
    
    return {
        'total_users': total_users,
        'total_jobs': total_jobs,
        'successful_jobs': successful_jobs,
        'jobs_today': jobs_today,
        'success_rate': round(success_rate, 1),
        'active_jobs': len(notification_service.get_active_jobs())
    }

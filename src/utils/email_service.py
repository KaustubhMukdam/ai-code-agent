"""
Email notification service (simplified)
"""
import os
from datetime import datetime

# For now, just log emails (can enable actual email later)
EMAIL_ENABLED = False

async def send_welcome_email(user_email: str, username: str):
    """Send welcome email to new users"""
    if EMAIL_ENABLED:
        print(f"📧 Welcome email sent to {user_email}")
    else:
        print(f"📧 [DEMO] Would send welcome email to {username} ({user_email})")

async def send_job_completion_email(user_email: str, username: str, job_id: str, 
                                  language: str, processing_time: str, questions_count: int):
    """Send job completion email"""
    if EMAIL_ENABLED:
        print(f"📧 Completion email sent to {user_email}")
    else:
        print(f"📧 [DEMO] Would send completion email to {username}: Job {job_id[:8]} ({language}) completed in {processing_time}")

"""
Enhanced database models with billing, subscriptions, and analytics
"""
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, Float, ForeignKey, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os
import enum

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/app.db")
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class SubscriptionTier(enum.Enum):
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class User(Base):
    """Enhanced user model with subscription and billing"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    
    # Subscription & Billing
    subscription_tier = Column(SQLEnum(SubscriptionTier), default=SubscriptionTier.FREE)
    subscription_start = Column(DateTime, nullable=True)
    subscription_end = Column(DateTime, nullable=True)
    
    # Usage tracking
    total_jobs = Column(Integer, default=0)
    total_jobs_this_month = Column(Integer, default=0)
    total_tokens_used = Column(Integer, default=0)
    total_spent = Column(Float, default=0.0)
    
    # Quota limits
    monthly_job_limit = Column(Integer, default=5)  # Free tier: 5/month
    
    # Relationships
    jobs = relationship("Job", back_populates="user")
    billing_records = relationship("BillingRecord", back_populates="user")


class Job(Base):
    """Enhanced job tracking with detailed metrics"""
    __tablename__ = "jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String, unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    status = Column(String, default="queued")  # queued, processing, done, error
    input_file_path = Column(String)
    output_file_path = Column(String, nullable=True)
    error_message = Column(String, nullable=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    processing_time_seconds = Column(Float, nullable=True)
    
    # AI Metrics
    tokens_used = Column(Integer, default=0)
    iterations = Column(Integer, default=0)  # Number of review iterations
    questions_processed = Column(Integer, default=0)
    
    # Billing
    cost = Column(Float, default=0.0)  # Cost for this job
    
    # Relationships
    user = relationship("User", back_populates="jobs")


class BillingRecord(Base):
    """Track all billing transactions"""
    __tablename__ = "billing_records"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    amount = Column(Float, nullable=False)
    description = Column(String)
    transaction_type = Column(String)  # "charge", "refund", "subscription"
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Stripe integration fields
    stripe_payment_id = Column(String, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="billing_records")


class SystemMetrics(Base):
    """Track system-wide metrics over time"""
    __tablename__ = "system_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Metrics
    total_users = Column(Integer, default=0)
    active_users_today = Column(Integer, default=0)
    total_jobs_today = Column(Integer, default=0)
    total_jobs_all_time = Column(Integer, default=0)
    success_rate = Column(Float, default=0.0)
    avg_processing_time = Column(Float, default=0.0)
    total_revenue = Column(Float, default=0.0)


# Create all tables
Base.metadata.create_all(bind=engine)


def get_db():
    """Dependency for database sessions"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

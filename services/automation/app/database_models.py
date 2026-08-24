#!/usr/bin/env python
"""
Database Models for User Profile, Preferences, and Jobs
Complete user data collection and storage system
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, JSON, Float, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
from typing import Optional, List, Dict, Any
import json

Base = declarative_base()


class User(Base):
    """User account information"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    email_verified = Column(Boolean, default=False)
    
    # Relationships
    profile = relationship("UserProfile", back_populates="user", uselist=False)
    preferences = relationship("UserPreferences", back_populates="user", uselist=False)
    jobs = relationship("UserJob", back_populates="user")
    applications = relationship("JobApplication", back_populates="user")
    platform_accounts = relationship("PlatformAccount", back_populates="user")


class UserProfile(Base):
    """Complete user profile information"""
    __tablename__ = "user_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    
    # Basic Information
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    phone = Column(String(50))
    date_of_birth = Column(DateTime)
    gender = Column(String(20))
    nationality = Column(String(100))
    
    # Location Information
    current_location = Column(String(200))
    preferred_locations = Column(JSON)  # List of preferred work locations
    willing_to_relocate = Column(Boolean, default=False)
    
    # Professional Information
    current_title = Column(String(200))
    professional_headline = Column(String(500))
    bio = Column(Text)
    summary = Column(Text)
    
    # Experience & Education
    total_experience_years = Column(Integer)
    current_company = Column(String(200))
    current_role = Column(String(200))
    education_level = Column(String(100))
    field_of_study = Column(String(200))
    university = Column(String(200))
    graduation_year = Column(Integer)
    
    # Skills & Expertise
    skills = Column(JSON)  # List of skills
    languages = Column(JSON)  # List of languages with proficiency
    certifications = Column(JSON)  # List of certifications
    achievements = Column(JSON)  # List of achievements/awards
    
    # Social & Professional Links
    linkedin_url = Column(String(500))
    github_url = Column(String(500))
    portfolio_url = Column(String(500))
    personal_website = Column(String(500))
    
    # Documents
    resume_path = Column(String(500))
    cover_letter_template = Column(Text)
    portfolio_files = Column(JSON)  # List of portfolio file paths
    
    # Availability
    availability = Column(String(100))  # "Immediate", "2 weeks", "1 month", etc.
    notice_period = Column(String(100))
    start_date = Column(DateTime)
    
    # Profile Completion
    profile_completion_percentage = Column(Integer, default=0)
    last_updated_section = Column(String(100))
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    user = relationship("User", back_populates="profile")


class UserPreferences(Base):
    """User job search and career preferences"""
    __tablename__ = "user_preferences"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    
    # Job Search Preferences
    job_title_keywords = Column(JSON)  # List of preferred job titles
    job_categories = Column(JSON)  # List of preferred job categories/industries
    job_levels = Column(JSON)  # Junior, Mid-level, Senior, Executive
    employment_types = Column(JSON)  # Full-time, Part-time, Contract, Freelance
    
    # Work Arrangement Preferences
    remote_work_preference = Column(String(50))  # "Remote", "Hybrid", "On-site", "Any"
    hybrid_days_per_week = Column(Integer)  # For hybrid preference
    travel_willingness = Column(String(50))  # "None", "Occasional", "Frequent", "Extensive"
    
    # Salary & Benefits
    salary_currency = Column(String(10), default="EUR")
    salary_min = Column(Integer)
    salary_max = Column(Integer)
    salary_type = Column(String(20), default="annual")  # annual, monthly, hourly
    salary_negotiable = Column(Boolean, default=True)
    benefits_important = Column(JSON)  # List of important benefits
    
    # Company Preferences
    company_size_preference = Column(JSON)  # Startup, Small, Medium, Large, Enterprise
    company_stage_preference = Column(JSON)  # Seed, Series A/B/C, IPO, Established
    company_culture_values = Column(JSON)  # List of important cultural values
    industry_preferences = Column(JSON)  # List of preferred industries
    industry_blacklist = Column(JSON)  # List of industries to avoid
    
    # Location Preferences
    preferred_work_locations = Column(JSON)  # List of cities/regions
    commute_max_time = Column(Integer)  # Maximum commute time in minutes
    willing_to_relocate = Column(Boolean, default=False)
    relocation_preferences = Column(JSON)  # List of acceptable relocation destinations
    
    # Job Application Preferences
    auto_apply_enabled = Column(Boolean, default=False)
    auto_apply_criteria = Column(JSON)  # Criteria for auto-application
    application_frequency = Column(String(50))  # "Daily", "Weekly", "Manual"
    max_applications_per_day = Column(Integer, default=5)
    
    # Career Goals & Interests
    career_goals = Column(Text)
    learning_interests = Column(JSON)  # Skills/areas they want to learn
    career_change_interest = Column(Boolean, default=False)
    target_career_field = Column(String(200))
    
    # Communication Preferences
    email_notifications = Column(Boolean, default=True)
    sms_notifications = Column(Boolean, default=False)
    job_alert_frequency = Column(String(50), default="Daily")  # Daily, Weekly, Immediate
    recruiter_contact_preference = Column(String(50), default="Email")
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    user = relationship("User", back_populates="preferences")


class UserJob(Base):
    """Jobs matched/found for the user"""
    __tablename__ = "user_jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Job Information
    job_title = Column(String(200), nullable=False)
    company_name = Column(String(200), nullable=False)
    job_url = Column(String(1000), nullable=False)
    platform = Column(String(100))  # WTTJ, LinkedIn, Indeed, etc.
    
    # Job Details
    job_description = Column(Text)
    job_requirements = Column(Text)
    job_benefits = Column(Text)
    location = Column(String(200))
    remote_option = Column(String(50))  # "Remote", "Hybrid", "On-site"
    employment_type = Column(String(50))  # Full-time, Part-time, Contract
    experience_level = Column(String(50))  # Junior, Mid-level, Senior
    
    # Salary Information
    salary_min = Column(Integer)
    salary_max = Column(Integer)
    salary_currency = Column(String(10))
    salary_disclosed = Column(Boolean, default=False)
    
    # Company Information
    company_size = Column(String(50))
    company_industry = Column(String(100))
    company_description = Column(Text)
    company_website = Column(String(500))
    company_logo_url = Column(String(500))
    
    # Matching Information
    match_score = Column(Float)  # 0.0 to 1.0 compatibility score
    match_reasons = Column(JSON)  # List of reasons why it's a good match
    skill_matches = Column(JSON)  # Skills that match
    missing_skills = Column(JSON)  # Skills user doesn't have but job requires
    
    # Job Status
    job_status = Column(String(50), default="active")  # active, expired, filled
    is_featured = Column(Boolean, default=False)
    is_bookmarked = Column(Boolean, default=False)
    is_hidden = Column(Boolean, default=False)
    
    # Dates
    job_posted_date = Column(DateTime)
    job_deadline = Column(DateTime)
    discovered_date = Column(DateTime, default=datetime.utcnow)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Metadata
    job_source_data = Column(JSON)  # Original job posting data
    tags = Column(JSON)  # User-defined tags for organization
    notes = Column(Text)  # User notes about the job
    
    # Relationship
    user = relationship("User", back_populates="jobs")
    applications = relationship("JobApplication", back_populates="job")


class JobApplication(Base):
    """Job applications submitted by user"""
    __tablename__ = "job_applications"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    job_id = Column(Integer, ForeignKey("user_jobs.id"), nullable=False)
    
    # Application Details
    application_method = Column(String(100))  # "Automated", "Manual", "Email", "Platform"
    platform_used = Column(String(100))  # WTTJ, LinkedIn, Direct, etc.
    application_url = Column(String(1000))
    
    # Application Content
    resume_used = Column(String(500))  # Path to resume file used
    cover_letter_used = Column(Text)  # Cover letter content
    custom_message = Column(Text)  # Additional message sent
    
    # Application Status
    status = Column(String(50), default="submitted")  # submitted, viewed, screening, interview, rejected, offer, accepted
    status_last_updated = Column(DateTime, default=datetime.utcnow)
    status_history = Column(JSON)  # History of status changes
    
    # Response Tracking
    employer_response_received = Column(Boolean, default=False)
    response_date = Column(DateTime)
    response_type = Column(String(100))  # email, phone, platform_message
    response_content = Column(Text)
    
    # Interview Information
    interview_scheduled = Column(Boolean, default=False)
    interview_date = Column(DateTime)
    interview_type = Column(String(100))  # phone, video, in-person, panel
    interview_notes = Column(Text)
    interview_feedback = Column(Text)
    
    # Outcome
    outcome = Column(String(50))  # pending, rejected, offer, accepted, withdrawn
    rejection_reason = Column(String(200))
    offer_details = Column(JSON)  # Salary, benefits, start date, etc.
    feedback_received = Column(Text)
    
    # Dates
    applied_date = Column(DateTime, default=datetime.utcnow)
    follow_up_date = Column(DateTime)
    final_decision_date = Column(DateTime)
    
    # Metadata
    application_data = Column(JSON)  # Additional application metadata
    auto_applied = Column(Boolean, default=False)  # Was this auto-applied?
    
    # Relationships
    user = relationship("User", back_populates="applications")
    job = relationship("UserJob", back_populates="applications")


class PlatformAccount(Base):
    """User accounts on different job platforms"""
    __tablename__ = "platform_accounts"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Platform Information
    platform_name = Column(String(100), nullable=False)  # WTTJ, LinkedIn, Indeed
    platform_email = Column(String(255), nullable=False)
    platform_password_encrypted = Column(String(500))  # Encrypted password
    platform_user_id = Column(String(200))  # Platform's internal user ID
    platform_profile_url = Column(String(500))
    
    # Account Status
    account_status = Column(String(50), default="active")  # active, inactive, suspended
    email_verified = Column(Boolean, default=False)
    profile_setup_completed = Column(Boolean, default=False)
    automation_enabled = Column(Boolean, default=True)
    
    # Sync Information
    last_sync_date = Column(DateTime)
    sync_status = Column(String(50), default="pending")  # synced, pending, failed
    sync_errors = Column(JSON)  # List of sync errors
    
    # Platform-specific Data
    platform_profile_data = Column(JSON)  # Profile data from the platform
    platform_settings = Column(JSON)  # Platform-specific settings
    
    # Statistics
    applications_sent = Column(Integer, default=0)
    profile_views = Column(Integer, default=0)
    messages_received = Column(Integer, default=0)
    connection_requests = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    user = relationship("User", back_populates="platform_accounts")


class UserActivity(Base):
    """Track user activity and engagement"""
    __tablename__ = "user_activities"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Activity Information
    activity_type = Column(String(100), nullable=False)  # login, job_view, application_submit, profile_update
    activity_description = Column(String(500))
    activity_data = Column(JSON)  # Additional activity data
    
    # Context
    platform = Column(String(100))  # Which platform/service
    device_type = Column(String(50))  # web, mobile, api
    ip_address = Column(String(50))
    user_agent = Column(String(500))
    
    # Timing
    activity_date = Column(DateTime, default=datetime.utcnow)
    session_id = Column(String(100))
    
    # Metadata
    metadata = Column(JSON)


class SystemSettings(Base):
    """System-wide settings and configuration"""
    __tablename__ = "system_settings"
    
    id = Column(Integer, primary_key=True, index=True)
    setting_key = Column(String(200), unique=True, nullable=False)
    setting_value = Column(JSON, nullable=False)
    setting_description = Column(Text)
    setting_type = Column(String(50))  # string, integer, boolean, json
    is_public = Column(Boolean, default=False)  # Can be accessed by frontend
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# Utility functions for JSON serialization
def to_dict(obj):
    """Convert SQLAlchemy model to dictionary"""
    result = {}
    for column in obj.__table__.columns:
        value = getattr(obj, column.name)
        if isinstance(value, datetime):
            result[column.name] = value.isoformat()
        elif value is None:
            result[column.name] = None
        else:
            result[column.name] = value
    return result


def create_user_profile_dict(user_profile: UserProfile) -> Dict[str, Any]:
    """Create a comprehensive user profile dictionary"""
    return {
        "basic_info": {
            "first_name": user_profile.first_name,
            "last_name": user_profile.last_name,
            "phone": user_profile.phone,
            "current_location": user_profile.current_location,
            "email": user_profile.user.email if user_profile.user else None
        },
        "professional": {
            "current_title": user_profile.current_title,
            "professional_headline": user_profile.professional_headline,
            "bio": user_profile.bio,
            "total_experience_years": user_profile.total_experience_years,
            "current_company": user_profile.current_company,
            "skills": user_profile.skills or []
        },
        "education": {
            "education_level": user_profile.education_level,
            "field_of_study": user_profile.field_of_study,
            "university": user_profile.university,
            "graduation_year": user_profile.graduation_year
        },
        "social": {
            "linkedin_url": user_profile.linkedin_url,
            "github_url": user_profile.github_url,
            "portfolio_url": user_profile.portfolio_url,
            "personal_website": user_profile.personal_website
        },
        "availability": {
            "availability": user_profile.availability,
            "notice_period": user_profile.notice_period,
            "start_date": user_profile.start_date.isoformat() if user_profile.start_date else None
        }
    }


# Database indexes for performance
def create_indexes(engine):
    """Create database indexes for better performance"""
    from sqlalchemy import Index
    
    # User indexes
    Index('idx_users_email', User.email)
    Index('idx_users_created_at', User.created_at)
    
    # Profile indexes
    Index('idx_profiles_user_id', UserProfile.user_id)
    Index('idx_profiles_skills', UserProfile.skills)
    Index('idx_profiles_location', UserProfile.current_location)
    
    # Job indexes
    Index('idx_jobs_user_id', UserJob.user_id)
    Index('idx_jobs_platform', UserJob.platform)
    Index('idx_jobs_match_score', UserJob.match_score)
    Index('idx_jobs_posted_date', UserJob.job_posted_date)
    Index('idx_jobs_status', UserJob.job_status)
    
    # Application indexes
    Index('idx_applications_user_id', JobApplication.user_id)
    Index('idx_applications_job_id', JobApplication.job_id)
    Index('idx_applications_status', JobApplication.status)
    Index('idx_applications_applied_date', JobApplication.applied_date)
    
    # Platform account indexes
    Index('idx_platform_accounts_user_id', PlatformAccount.user_id)
    Index('idx_platform_accounts_platform', PlatformAccount.platform_name)


if __name__ == "__main__":
    print("Database models defined successfully!")
    print("\nTables to be created:")
    for table_name in Base.metadata.tables.keys():
        print(f"  - {table_name}")
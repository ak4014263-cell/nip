from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, Text, JSON, Float
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from typing import Optional, List, Dict, Any

# Import database Base - handle both direct and module imports
try:
    from shared.database import Base
except ImportError:
    try:
        from .database import Base
    except ImportError:
        from database import Base

def generate_uuid():
    return str(uuid.uuid4())

class User(Base):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)  # matches actual database column
    name = Column(String)
    role = Column(String, default="candidate")
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    profile = relationship("UserProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    preferences = relationship("UserPreferences", back_populates="user", uselist=False, cascade="all, delete-orphan")
    jobs = relationship("UserJob", back_populates="user", cascade="all, delete-orphan")
    applications = relationship("JobApplication", back_populates="user", cascade="all, delete-orphan")
    platform_accounts = relationship("PlatformAccount", back_populates="user", cascade="all, delete-orphan")


class UserProfile(Base):
    """Complete user profile information"""
    __tablename__ = "user_profiles"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    
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
    
    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    
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
    
    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
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
    applications = relationship("JobApplication", back_populates="job", cascade="all, delete-orphan")


class JobApplication(Base):
    """Job applications submitted by user"""
    __tablename__ = "job_applications"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    job_id = Column(String, ForeignKey("user_jobs.id", ondelete="CASCADE"), nullable=False)
    
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
    
    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
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


class UserEmailAccount(Base):
    """Generated email accounts for users"""
    __tablename__ = "user_email_accounts"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Email account info
    email_address = Column(String(255), unique=True, nullable=False, index=True)
    email_username = Column(String(100), nullable=False)  # e.g., "user123"
    email_domain = Column(String(100), nullable=False)    # e.g., "swiply.jobs"
    
    # Purpose & status
    purpose = Column(String(100))  # "wttj", "linkedin", "indeed"
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    verification_clicked = Column(Boolean, default=False)
    
    # Forwarding settings
    forward_to = Column(String(255))  # Optional: forward to user's real email
    
    # Statistics
    emails_received = Column(Integer, default=0)
    last_email_date = Column(DateTime)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    user = relationship("User")
    emails = relationship("EmailMessage", back_populates="email_account", cascade="all, delete-orphan")


class EmailMessage(Base):
    """Emails received for user accounts"""
    __tablename__ = "email_messages"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    email_account_id = Column(String, ForeignKey("user_email_accounts.id", ondelete="CASCADE"), index=True)
    
    # Email details
    from_address = Column(String(255), nullable=False)
    from_name = Column(String(200))
    to_address = Column(String(255), nullable=False)
    subject = Column(String(500))
    body_text = Column(Text)
    body_html = Column(Text)
    
    # Categorization
    category = Column(String(50), index=True)  # "verification", "job_alert", "application_response", "recruiter_message"
    platform = Column(String(50))  # "wttj", "linkedin", "indeed"
    is_verification_email = Column(Boolean, default=False, index=True)
    verification_link = Column(String(1000))
    
    # Status
    is_read = Column(Boolean, default=False, index=True)
    is_starred = Column(Boolean, default=False)
    is_archived = Column(Boolean, default=False)
    
    # Attachments
    attachments = Column(JSON)  # List of attachment URLs
    
    # Metadata
    message_id = Column(String(200), unique=True)  # Original email message ID
    in_reply_to = Column(String(200))  # For threading
    raw_email = Column(Text)  # Store full email for debugging
    
    received_at = Column(DateTime, default=datetime.utcnow, index=True)
    read_at = Column(DateTime)
    
    # Relationships
    user = relationship("User")
    email_account = relationship("UserEmailAccount", back_populates="emails")

class Job(Base):
    __tablename__ = "jobs"
    id = Column(String, primary_key=True, default=generate_uuid)
    title = Column(String)
    company = Column(String)
    location = Column(String)
    salaryMin = Column(Integer, nullable=True)
    salaryMax = Column(Integer, nullable=True)
    employmentType = Column(String)
    description = Column(Text)
    requirements = Column(JSON) # List of strings
    remote = Column(Boolean)
    logo = Column(String)
    sourceCareerSite = Column(String)
    externalUrl = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)  # Job expiration date
    can_apply = Column(Boolean, default=True)  # Whether job can be applied to

class Swipe(Base):
    __tablename__ = "swipes"
    id = Column(String, primary_key=True, default=generate_uuid)
    candidate_id = Column(String, index=True)
    job_id = Column(String, ForeignKey("jobs.id"))
    liked = Column(Boolean)
    timestamp = Column(DateTime, default=datetime.utcnow)

class Application(Base):
    __tablename__ = "applications"
    id = Column(String, primary_key=True, default=generate_uuid)
    candidate_id = Column(String, index=True)
    job_id = Column(String, ForeignKey("jobs.id"))
    status = Column(String) # Applied, In Review, Interview
    applied_at = Column(DateTime, default=datetime.utcnow)
    
    job = relationship("Job")

class Credential(Base):
    __tablename__ = "credentials"
    id = Column(String, primary_key=True, default=generate_uuid)
    candidate_id = Column(String, index=True)
    careerSite = Column(String)
    email = Column(String)
    password = Column(String)
    isVerified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

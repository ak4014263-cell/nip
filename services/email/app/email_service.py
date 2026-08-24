"""
Enhanced Email Service with Inbox Automation
Generate temporary emails and manage inbox for job platform accounts
"""
from fastapi import FastAPI, Request, Depends, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
import sys
import os
import random
import string
import re
import httpx
from datetime import datetime
from bs4 import BeautifulSoup

# Add parent directories to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from shared.database import get_db, engine, Base
from shared.models import EmailMessage, UserEmailAccount, User

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Swiply Email & Inbox Service",
    description="Email generation and inbox automation for job platforms",
    version="2.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
EMAIL_DOMAIN = os.getenv("EMAIL_DOMAIN", "swiply.jobs")

# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class EmailGenerationRequest(BaseModel):
    user_id: str
    purpose: str = "wttj"  # wttj, linkedin, indeed

class VerifyEmailRequest(BaseModel):
    email_id: str

# ============================================================================
# EMAIL GENERATOR
# ============================================================================

class EmailGenerator:
    """Generate unique email addresses for users"""
    
    def __init__(self, domain=EMAIL_DOMAIN):
        self.domain = domain
    
    def generate_email(self, user_id: str, purpose: str = "wttj") -> str:
        """Generate unique email address"""
        # Create unique username
        timestamp = datetime.now().strftime("%y%m%d")
        random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
        
        username = f"u{user_id[:8]}-{purpose}-{random_suffix}"
        email = f"{username}@{self.domain}"
        
        return email, username

email_generator = EmailGenerator()

# ============================================================================
# EMAIL PARSING UTILITIES
# ============================================================================

def extract_verification_link(html_body: str, text_body: str) -> Optional[str]:
    """Extract verification link from email"""
    # Try HTML first
    if html_body:
        try:
            soup = BeautifulSoup(html_body, 'html.parser')
            links = soup.find_all('a', href=True)
            
            for link in links:
                href = link['href']
                text = link.get_text().lower()
                
                # Look for verification keywords
                if any(keyword in text for keyword in ['verify', 'confirm', 'activate', 'vérifier', 'activer']):
                    return href
                
                # Look for verification patterns in URL
                if any(pattern in href.lower() for pattern in ['verify', 'confirm', 'activation', 'token', 'validate']):
                    return href
        except Exception as e:
            print(f"Error parsing HTML: {e}")
    
    # Try text body
    if text_body:
        # Find URLs in text
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        urls = re.findall(url_pattern, text_body)
        
        for url in urls:
            if any(keyword in url.lower() for keyword in ['verify', 'confirm', 'activation', 'token', 'validate']):
                return url
    
    return None

def categorize_email(from_address: str, subject: str, body: str) -> str:
    """Categorize email type"""
    subject_lower = subject.lower() if subject else ""
    body_lower = body.lower() if body else ""
    
    # Verification email
    if any(keyword in subject_lower or keyword in body_lower[:500] for keyword in [
        'verify', 'confirmation', 'activate', 'vérifier', 'confirmer', 'validation'
    ]):
        return "verification"
    
    # Job alert
    if any(keyword in subject_lower for keyword in [
        'job alert', 'new jobs', 'nouvelles offres', 'job match', 'recommended jobs'
    ]):
        return "job_alert"
    
    # Application response
    if any(keyword in subject_lower or keyword in body_lower[:500] for keyword in [
        'application received', 'candidature reçue', 'thank you for applying',
        'application submitted', 'we received your application'
    ]):
        return "application_response"
    
    # Interview invitation
    if any(keyword in subject_lower or keyword in body_lower[:500] for keyword in [
        'interview', 'entretien', 'schedule', 'rendez-vous', 'invitation'
    ]):
        return "interview"
    
    # Recruiter message
    if 'recruiter' in from_address.lower() or 'talent' in from_address.lower() or 'hiring' in from_address.lower():
        return "recruiter_message"
    
    # Rejection
    if any(keyword in subject_lower or keyword in body_lower[:500] for keyword in [
        'unfortunately', 'malheureusement', 'not selected', 'pas retenu'
    ]):
        return "rejection"
    
    return "other"

def detect_platform(from_address: str, subject: str) -> str:
    """Detect which platform the email is from"""
    from_lower = from_address.lower()
    subject_lower = subject.lower() if subject else ""
    
    if "welcometothejungle" in from_lower or "wttj" in from_lower:
        return "wttj"
    elif "linkedin" in from_lower:
        return "linkedin"
    elif "indeed" in from_lower:
        return "indeed"
    elif "glassdoor" in from_lower:
        return "glassdoor"
    
    return "other"

# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.get("/")
async def root():
    return {
        "service": "email-inbox-automation",
        "version": "2.0.0",
        "status": "running",
        "features": [
            "Email Address Generation",
            "Inbox Management",
            "Email Verification Automation",
            "Email Categorization"
        ]
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# ============================================================================
# EMAIL GENERATION ENDPOINTS
# ============================================================================

@app.post("/generate-email")
async def generate_email_for_user(
    request: EmailGenerationRequest,
    db: Session = Depends(get_db)
):
    """
    Generate temporary email address for user
    
    Example:
    {
        "user_id": "user_123",
        "purpose": "wttj"
    }
    
    Returns:
    {
        "success": true,
        "email_address": "u12345678-wttj-abc123@swiply.jobs",
        "purpose": "wttj"
    }
    """
    try:
        # Check if user exists
        user = db.query(User).filter(User.id == request.user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Check if email already exists for this purpose
        existing = db.query(UserEmailAccount).filter(
            UserEmailAccount.user_id == request.user_id,
            UserEmailAccount.purpose == request.purpose,
            UserEmailAccount.is_active == True
        ).first()
        
        if existing:
            return {
                "success": True,
                "email_address": existing.email_address,
                "email_account_id": existing.id,
                "purpose": existing.purpose,
                "message": "Email already exists for this purpose",
                "is_existing": True
            }
        
        # Generate new email
        email_address, username = email_generator.generate_email(request.user_id, request.purpose)
        
        # Create email account record
        email_account = UserEmailAccount(
            user_id=request.user_id,
            email_address=email_address,
            email_username=username,
            email_domain=EMAIL_DOMAIN,
            purpose=request.purpose,
            is_active=True,
            is_verified=False
        )
        
        db.add(email_account)
        db.commit()
        db.refresh(email_account)
        
        return {
            "success": True,
            "email_address": email_address,
            "email_account_id": email_account.id,
            "purpose": request.purpose,
            "message": f"Email generated successfully",
            "is_existing": False
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to generate email: {str(e)}")

@app.get("/email-accounts/{user_id}")
async def get_user_email_accounts(user_id: str, db: Session = Depends(get_db)):
    """Get all email accounts for a user"""
    try:
        accounts = db.query(UserEmailAccount).filter(
            UserEmailAccount.user_id == user_id,
            UserEmailAccount.is_active == True
        ).all()
        
        return {
            "success": True,
            "total": len(accounts),
            "accounts": [
                {
                    "id": account.id,
                    "email_address": account.email_address,
                    "purpose": account.purpose,
                    "is_verified": account.is_verified,
                    "emails_received": account.emails_received,
                    "last_email_date": account.last_email_date.isoformat() if account.last_email_date else None,
                    "created_at": account.created_at.isoformat()
                }
                for account in accounts
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# EMAIL WEBHOOK HANDLER (FOR MAILGUN/SENDGRID)
# ============================================================================

@app.post("/webhook/email")
async def receive_email_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Webhook to receive emails from email service (Mailgun, SendGrid, etc.)
    
    This endpoint receives incoming emails and stores them in the database
    """
    try:
        # Parse form data (Mailgun format)
        form_data = await request.form()
        
        # Extract email details
        to_address = form_data.get("recipient", "")
        from_address = form_data.get("sender", "")
        from_name = form_data.get("from", from_address)
        subject = form_data.get("subject", "")
        body_text = form_data.get("body-plain", "")
        body_html = form_data.get("body-html", "")
        message_id = form_data.get("Message-Id", "")
        
        # Find email account
        email_account = db.query(UserEmailAccount).filter(
            UserEmailAccount.email_address == to_address,
            UserEmailAccount.is_active == True
        ).first()
        
        if not email_account:
            return {
                "status": "ignored",
                "reason": "email account not found or inactive"
            }
        
        # Extract verification link
        verification_link = extract_verification_link(body_html, body_text)
        is_verification = verification_link is not None
        
        # Categorize email
        category = categorize_email(from_address, subject, body_text)
        
        # Detect platform
        platform = detect_platform(from_address, subject)
        
        # Create email record
        email = EmailMessage(
            user_id=email_account.user_id,
            email_account_id=email_account.id,
            from_address=from_address,
            from_name=from_name,
            to_address=to_address,
            subject=subject,
            body_text=body_text,
            body_html=body_html,
            category=category,
            platform=platform,
            is_verification_email=is_verification,
            verification_link=verification_link,
            message_id=message_id,
            is_read=False
        )
        
        db.add(email)
        
        # Update email account statistics
        email_account.emails_received += 1
        email_account.last_email_date = datetime.utcnow()
        
        db.commit()
        db.refresh(email)
        
        return {
            "status": "success",
            "email_id": email.id,
            "category": category,
            "platform": platform,
            "is_verification": is_verification,
            "user_id": email_account.user_id
        }
        
    except Exception as e:
        db.rollback()
        print(f"Error processing email webhook: {e}")
        return {"status": "error", "error": str(e)}

# ============================================================================
# INBOX ENDPOINTS
# ============================================================================

@app.get("/inbox/{user_id}")
async def get_user_inbox(
    user_id: str,
    category: Optional[str] = None,
    platform: Optional[str] = None,
    unread_only: bool = False,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """
    Get user's inbox emails
    
    Query params:
    - category: filter by category (verification, job_alert, etc.)
    - platform: filter by platform (wttj, linkedin, etc.)
    - unread_only: show only unread emails
    - limit: number of emails to return
    - offset: pagination offset
    """
    try:
        query = db.query(EmailMessage).filter(EmailMessage.user_id == user_id)
        
        if category:
            query = query.filter(EmailMessage.category == category)
        
        if platform:
            query = query.filter(EmailMessage.platform == platform)
        
        if unread_only:
            query = query.filter(EmailMessage.is_read == False)
        
        total = query.count()
        emails = query.order_by(EmailMessage.received_at.desc()).limit(limit).offset(offset).all()
        
        return {
            "success": True,
            "total": total,
            "limit": limit,
            "offset": offset,
            "emails": [
                {
                    "id": email.id,
                    "from": email.from_address,
                    "from_name": email.from_name,
                    "subject": email.subject,
                    "preview": email.body_text[:200] if email.body_text else "",
                    "category": email.category,
                    "platform": email.platform,
                    "is_read": email.is_read,
                    "is_starred": email.is_starred,
                    "is_verification": email.is_verification_email,
                    "has_verification_link": email.verification_link is not None,
                    "received_at": email.received_at.isoformat()
                }
                for email in emails
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/inbox/stats/{user_id}")
async def get_inbox_stats(user_id: str, db: Session = Depends(get_db)):
    """Get inbox statistics for user"""
    try:
        total = db.query(EmailMessage).filter(EmailMessage.user_id == user_id).count()
        unread = db.query(EmailMessage).filter(
            EmailMessage.user_id == user_id,
            EmailMessage.is_read == False
        ).count()
        
        verification_pending = db.query(EmailMessage).filter(
            EmailMessage.user_id == user_id,
            EmailMessage.is_verification_email == True,
            EmailMessage.is_read == False
        ).count()
        
        return {
            "success": True,
            "total_emails": total,
            "unread_emails": unread,
            "verification_pending": verification_pending
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/email/{email_id}")
async def get_email_details(email_id: str, db: Session = Depends(get_db)):
    """Get full email details"""
    try:
        email = db.query(EmailMessage).filter(EmailMessage.id == email_id).first()
        
        if not email:
            raise HTTPException(status_code=404, detail="Email not found")
        
        # Mark as read
        if not email.is_read:
            email.is_read = True
            email.read_at = datetime.utcnow()
            db.commit()
        
        return {
            "success": True,
            "email": {
                "id": email.id,
                "from": email.from_address,
                "from_name": email.from_name,
                "to": email.to_address,
                "subject": email.subject,
                "body_text": email.body_text,
                "body_html": email.body_html,
                "category": email.category,
                "platform": email.platform,
                "is_verification": email.is_verification_email,
                "verification_link": email.verification_link,
                "is_read": email.is_read,
                "is_starred": email.is_starred,
                "received_at": email.received_at.isoformat(),
                "read_at": email.read_at.isoformat() if email.read_at else None
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# EMAIL VERIFICATION AUTOMATION
# ============================================================================

@app.post("/verify-email/{email_id}")
async def auto_verify_email(email_id: str, db: Session = Depends(get_db)):
    """
    Automatically click verification link in email
    
    This endpoint:
    1. Gets the verification link from email
    2. Clicks the link (HTTP GET request)
    3. Updates email account as verified
    4. Marks email as read
    """
    try:
        email = db.query(EmailMessage).filter(EmailMessage.id == email_id).first()
        
        if not email:
            raise HTTPException(status_code=404, detail="Email not found")
        
        if not email.is_verification_email or not email.verification_link:
            raise HTTPException(status_code=400, detail="Not a verification email or no verification link found")
        
        # Click the verification link
        try:
            async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
                response = await client.get(email.verification_link)
                
                success = response.status_code in [200, 201, 302]
                
                if success:
                    # Update email account as verified
                    email_account = db.query(UserEmailAccount).filter(
                        UserEmailAccount.id == email.email_account_id
                    ).first()
                    
                    if email_account:
                        email_account.is_verified = True
                        email_account.verification_clicked = True
                    
                    # Mark email as read
                    email.is_read = True
                    email.read_at = datetime.utcnow()
                    
                    db.commit()
                
                return {
                    "success": success,
                    "status_code": response.status_code,
                    "message": "Email verified successfully!" if success else "Verification request sent but response unclear",
                    "verification_link": email.verification_link,
                    "email_account_verified": success
                }
        except httpx.TimeoutException:
            return {
                "success": False,
                "error": "Request timeout",
                "message": "Verification link took too long to respond. It may still work - check manually.",
                "verification_link": email.verification_link
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to click verification link. You may need to click it manually.",
                "verification_link": email.verification_link
            }
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# EMAIL ACTIONS
# ============================================================================

@app.patch("/email/{email_id}/mark-read")
async def mark_email_read(email_id: str, db: Session = Depends(get_db)):
    """Mark email as read"""
    email = db.query(EmailMessage).filter(EmailMessage.id == email_id).first()
    if email:
        email.is_read = True
        email.read_at = datetime.utcnow()
        db.commit()
    return {"success": True}

@app.patch("/email/{email_id}/mark-unread")
async def mark_email_unread(email_id: str, db: Session = Depends(get_db)):
    """Mark email as unread"""
    email = db.query(EmailMessage).filter(EmailMessage.id == email_id).first()
    if email:
        email.is_read = False
        email.read_at = None
        db.commit()
    return {"success": True}

@app.patch("/email/{email_id}/star")
async def star_email(email_id: str, db: Session = Depends(get_db)):
    """Star/bookmark email"""
    email = db.query(EmailMessage).filter(EmailMessage.id == email_id).first()
    if email:
        email.is_starred = True
        db.commit()
    return {"success": True}

@app.patch("/email/{email_id}/unstar")
async def unstar_email(email_id: str, db: Session = Depends(get_db)):
    """Remove star from email"""
    email = db.query(EmailMessage).filter(EmailMessage.id == email_id).first()
    if email:
        email.is_starred = False
        db.commit()
    return {"success": True}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("EMAIL_PORT", 8007))
    uvicorn.run(app, host="0.0.0.0", port=port)

from fastapi import FastAPI, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
import os
import sys
import asyncio
import random
from datetime import datetime, timedelta

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))
from shared.database import get_db
from shared.models import EmailMessage as DBEmailMessage
from sqlalchemy.orm import Session
from sqlalchemy import func

app = FastAPI(title="Swiply Email Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"service": "email", "status": "running"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

# Simulate realistic email responses
EMAIL_TEMPLATES = [
    {
        "category": "Auto-Reply",
        "subject": "Application Received - {job_title}",
        "preview": "Thank you for your application to {company}",
        "body": "Dear Candidate,\n\nThank you for your application for the {job_title} position at {company}. We have received your application and will review it carefully.\n\nOur hiring team will be in touch if your profile matches our requirements.\n\nBest regards,\n{company} HR Team"
    },
    {
        "category": "Interview",
        "subject": "Interview Invitation - {job_title}",
        "preview": "We'd like to schedule an interview",
        "body": "Dear Candidate,\n\nWe were impressed by your application for the {job_title} position and would like to invite you for an interview.\n\nPlease reply with your availability for next week.\n\nLooking forward to speaking with you!\n\nBest regards,\n{company} Hiring Team"
    },
    {
        "category": "Action Required",
        "subject": "Additional Information Required - {job_title}",
        "preview": "Please provide additional documents",
        "body": "Dear Candidate,\n\nThank you for your interest in the {job_title} position at {company}.\n\nTo proceed with your application, please provide:\n- Updated CV\n- Portfolio samples\n- References\n\nBest regards,\n{company} HR"
    }
]

async def simulate_email_response(candidate_id: str, job_title: str, company: str, db: Session):
    """Simulate receiving an email response after job application"""
    # Wait a random time between 30 seconds and 2 minutes to simulate processing
    wait_time = random.randint(30, 120)
    await asyncio.sleep(wait_time)
    
    # Select random email template
    template = random.choice(EMAIL_TEMPLATES)
    
    # Create email
    email = DBEmailMessage(
        user_id=candidate_id,
        from_address=f"noreply@{company.lower().replace(' ', '')}.com",
        from_name=f"{company} Careers",
        to_address=f"{candidate_id}@swiply.com",
        subject=template["subject"].format(job_title=job_title, company=company),
        body_text=template["body"].format(job_title=job_title, company=company),
        category=template["category"],
        is_read=False
    )
    
    db.add(email)
    db.commit()
    print(f"Simulated email response for {job_title} at {company}")

@app.post("/simulate-application-response")
async def simulate_application_response(
    background_tasks: BackgroundTasks,
    request_data: dict,
    db: Session = Depends(get_db)
):
    """Simulate email response after job application"""
    candidate_id = request_data.get("candidate_id", "demo-candidate")
    job_title = request_data.get("job_title", "Developer")
    company = request_data.get("company", "TechCorp")
    
    background_tasks.add_task(simulate_email_response, candidate_id, job_title, company, db)
    
    return {"message": "Email response simulation started"}

@app.post("/send-custom")
async def send_custom_email(request_data: dict, db: Session = Depends(get_db)):
    """Add a custom simulated email to the inbox"""
    candidate_id = request_data.get("candidate_id", "demo-candidate")
    sender = request_data.get("sender", "noreply@example.com")
    subject = request_data.get("subject", "Notification")
    body = request_data.get("body", "")
    category = request_data.get("category", "General")
    
    email = DBEmailMessage(
        user_id=candidate_id,
        from_address=sender,
        to_address=f"{candidate_id}@swiply.com",
        subject=subject,
        body_text=body,
        category=category,
        is_read=False
    )
    db.add(email)
    db.commit()
    db.refresh(email)
    return {"status": "success", "id": email.id}

@app.get("/emails")
async def get_emails(candidate_id: str = "demo-candidate", db: Session = Depends(get_db)):
    emails = db.query(DBEmailMessage).filter(DBEmailMessage.user_id == candidate_id).order_by(DBEmailMessage.received_at.desc()).all()
    return {
        "emails": [
            {
                "id": e.id,
                "sender": e.from_address,
                "from_name": e.from_name,
                "subject": e.subject,
                "preview": (e.body_text or "")[:100],
                "body": e.body_text,
                "category": e.category,
                "unread": not e.is_read,
                "timestamp": e.received_at.isoformat() if e.received_at else datetime.utcnow().isoformat()
            } for e in emails
        ],
        "total": len(emails)
    }

@app.get("/emails/stats")
async def get_email_stats(candidate_id: str = "demo-candidate", db: Session = Depends(get_db)):
    total = db.query(DBEmailMessage).filter(DBEmailMessage.user_id == candidate_id).count()
    unread = db.query(DBEmailMessage).filter(DBEmailMessage.user_id == candidate_id, DBEmailMessage.is_read == False).count()
    
    return {
        "total": total,
        "unread": unread
    }

@app.patch("/emails/{email_id}/read")
async def mark_read(email_id: str, db: Session = Depends(get_db)):
    email = db.query(DBEmailMessage).filter(DBEmailMessage.id == email_id).first()
    if email:
        email.unread = False
        db.commit()
    return {"status": "success"}

@app.patch("/emails/{email_id}/unread")
async def mark_unread(email_id: str, db: Session = Depends(get_db)):
    email = db.query(DBEmailMessage).filter(DBEmailMessage.id == email_id).first()
    if email:
        email.unread = True
        db.commit()
    return {"status": "success"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8007))
    uvicorn.run(app, host="0.0.0.0", port=port)

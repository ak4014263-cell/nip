"""
Credential Service
Manages auto-generated login credentials for career sites
"""
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
import secrets
import string
from cryptography.fernet import Fernet
from datetime import datetime
import os
import sys

# Add root directory to path for shared modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))
from shared.database import get_db
from shared.models import Credential as DBCredential
from sqlalchemy.orm import Session
from sqlalchemy import func

app = FastAPI(
    title="Swiply Credential Service",
    description="Manages auto-generated login credentials",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Encryption setup
cipher_suite = Fernet(Fernet.generate_key())


def generate_password(length: int = 16) -> str:
    """Generate a strong random password"""
    characters = string.ascii_letters + string.digits + "!@#$%^&*"
    password = ''.join(secrets.choice(characters) for _ in range(length))
    return password


@app.get("/")
async def root():
    return {"service": "credential", "status": "running"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.get("/credentials")
async def get_credentials(candidate_id: str = "demo-candidate", db: Session = Depends(get_db)):
    """Get all credentials for a candidate"""
    creds = db.query(DBCredential).filter(DBCredential.candidate_id == candidate_id).all()
    
    return [
        {
            "id": c.id,
            "candidateId": c.candidate_id,
            "careerSite": c.careerSite,
            "email": c.email,
            "password": c.password,
            "isVerified": c.isVerified,
            "createdAt": c.created_at.isoformat()
        } for c in creds
    ]
@app.get("/credentials/stats")
async def get_stats(candidate_id: str = "demo-candidate", db: Session = Depends(get_db)):
    """Get credential statistics"""
    total = db.query(DBCredential).filter(DBCredential.candidate_id == candidate_id).count()
    verified = db.query(DBCredential).filter(DBCredential.candidate_id == candidate_id, DBCredential.isVerified == True).count()
    unverified = total - verified
    
    by_site = db.query(DBCredential.careerSite, func.count(DBCredential.id)).filter(DBCredential.candidate_id == candidate_id).group_by(DBCredential.careerSite).all()
    
    return {
        "total": total,
        "verified": verified,
        "unverified": unverified,
        "bySite": [
            {"careerSite": site, "_count": count} for site, count in by_site
        ]
    }
@app.get("/credentials/{site}")
async def get_credential_for_site(site: str, candidate_id: str = "demo-candidate", db: Session = Depends(get_db)):
    """Get credentials for a specific career site"""
    cred = db.query(DBCredential).filter(DBCredential.candidate_id == candidate_id, DBCredential.careerSite == site).first()
    if not cred:
        return {"error": "Credential not found"}
    return {
        "id": cred.id,
        "candidateId": cred.candidate_id,
        "careerSite": cred.careerSite,
        "email": cred.email,
        "password": cred.password,
        "isVerified": cred.isVerified,
        "createdAt": cred.created_at.isoformat()
    }

@app.post("/credentials/{site}")
async def create_credentials(site: str, candidate_id: str = "demo-candidate", db: Session = Depends(get_db)):
    """Create or get credentials for a career site"""
    # Check if exists
    cred = db.query(DBCredential).filter(DBCredential.candidate_id == candidate_id, DBCredential.careerSite == site).first()
    if cred:
        return {
            "id": cred.id,
            "candidateId": cred.candidate_id,
            "careerSite": cred.careerSite,
            "email": cred.email,
            "password": cred.password,
            "isVerified": cred.isVerified,
            "createdAt": cred.created_at.isoformat()
        }
        
    email = f"candidate+{site.lower()}@swiply-jobs.com"
    password = generate_password()
    
    new_cred = DBCredential(
        candidate_id=candidate_id,
        careerSite=site,
        email=email,
        password=password,
        isVerified=False
    )
    db.add(new_cred)
    db.commit()
    db.refresh(new_cred)
    
    return {
        "id": new_cred.id,
        "candidateId": new_cred.candidate_id,
        "careerSite": new_cred.careerSite,
        "email": new_cred.email,
        "password": new_cred.password,
        "isVerified": new_cred.isVerified,
        "createdAt": new_cred.created_at.isoformat()
    }

@app.post("/credentials")
async def create_custom_credentials(request_data: dict, db: Session = Depends(get_db)):
    """Create credentials with custom data"""
    candidate_id = request_data.get("candidate_id")
    career_site = request_data.get("careerSite")
    email = request_data.get("email")
    password = request_data.get("password")
    is_verified = request_data.get("isVerified", False)
    
    # Check if exists
    cred = db.query(DBCredential).filter(
        DBCredential.candidate_id == candidate_id,
        DBCredential.careerSite == career_site
    ).first()
    
    if cred:
        # Update existing
        cred.email = email
        cred.password = password
        cred.isVerified = is_verified
        db.commit()
        db.refresh(cred)
    else:
        # Create new
        cred = DBCredential(
            candidate_id=candidate_id,
            careerSite=career_site,
            email=email,
            password=password,
            isVerified=is_verified
        )
        db.add(cred)
        db.commit()
        db.refresh(cred)
    
    return {
        "id": cred.id,
        "candidateId": cred.candidate_id,
        "careerSite": cred.careerSite,
        "email": cred.email,
        "password": cred.password,
        "isVerified": cred.isVerified,
        "createdAt": cred.created_at.isoformat()
    }


@app.patch("/credentials/{credential_id}/verify")
async def verify_credentials(credential_id: str, db: Session = Depends(get_db)):
    """Mark credentials as verified"""
    cred = db.query(DBCredential).filter(DBCredential.id == credential_id).first()
    if not cred:
        return {"error": "Credential not found"}
    
    cred.isVerified = True
    db.commit()
    
    return {
        "id": cred.id,
        "candidateId": cred.candidate_id,
        "careerSite": cred.careerSite,
        "email": cred.email,
        "password": cred.password,
        "isVerified": cred.isVerified,
        "createdAt": cred.created_at.isoformat()
    }


@app.delete("/credentials/{credential_id}")
async def delete_credentials(credential_id: str, db: Session = Depends(get_db)):
    """Delete credentials"""
    cred = db.query(DBCredential).filter(DBCredential.id == credential_id).first()
    if cred:
        db.delete(cred)
        db.commit()
    return {"message": "Credentials deleted successfully"}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8009))
    uvicorn.run(app, host="0.0.0.0", port=port)

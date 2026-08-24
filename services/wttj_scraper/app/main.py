#!/usr/bin/env python3
"""
WTTJ Scraper Microservice
Port 8013 - Welcome to the Jungle Job Scraping, Parsing & Database Synchronization Service
"""
import os
import sys
import logging
import asyncio
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, BackgroundTasks, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# Setup root path for shared modules
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from shared.database import get_db, SessionLocal
from shared.models import Job
from sqlalchemy.orm import Session
from services.wttj_scraper.app.scraper_engine import WTTJScraperEngine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("wttj_scraper_service")

app = FastAPI(
    title="Swiply WTTJ Job Scraper Microservice",
    description="Microservice for scraping, parsing, indexing, and synchronizing Welcome to the Jungle job postings into Swiply.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

engine = WTTJScraperEngine()

# ---------------------------------------------------------------------------
# Pydantic Request Models
# ---------------------------------------------------------------------------
class JobSearchRequest(BaseModel):
    query: Optional[str] = "Software Engineer"
    location: Optional[str] = None
    remote: Optional[bool] = None
    contract: Optional[str] = None
    page: Optional[int] = 0
    limit: Optional[int] = 20
    sync_to_db: Optional[bool] = False

class LiveBrowserScrapeRequest(BaseModel):
    search_term: Optional[str] = "Developer"
    limit: Optional[int] = 10
    sync_to_db: Optional[bool] = True

class JobDetailRequest(BaseModel):
    job_url: str = Field(..., description="Full Welcome to the Jungle job posting URL")

class SyncRequest(BaseModel):
    query: Optional[str] = "Software Engineer"
    limit: Optional[int] = 30
    sources: Optional[List[str]] = ["api", "live_browser"]

# ---------------------------------------------------------------------------
# Microservice Endpoints
# ---------------------------------------------------------------------------

@app.get("/")
@app.get("/health")
async def health_check():
    """Health check and service status"""
    db = SessionLocal()
    try:
        wttj_count = db.query(Job).filter(Job.sourceCareerSite == "WTTJ").count()
        total_count = db.query(Job).count()
    except Exception:
        wttj_count = 0
        total_count = 0
    finally:
        db.close()
        
    return {
        "status": "healthy",
        "service": "wttj_job_scraper",
        "port": 8013,
        "database_stats": {
            "wttj_jobs_stored": wttj_count,
            "total_jobs_stored": total_count
        },
        "supported_features": [
            "Algolia search index queries",
            "Playwright live browser DOM extraction",
            "Deep job description parsing",
            "Automatic SQLite upsert & deduplication"
        ],
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@app.post("/scrape/search")
async def search_wttj_jobs(req: JobSearchRequest):
    """
    Search and scrape Welcome to the Jungle jobs via high-speed API
    """
    try:
        jobs = await engine.search_api_jobs(
            query=req.query or "",
            location=req.location,
            remote=req.remote,
            contract=req.contract,
            page=req.page or 0,
            limit=req.limit or 20
        )
        
        sync_result = None
        if req.sync_to_db and jobs:
            sync_result = engine.sync_jobs_to_db(jobs)
            
        return {
            "success": True,
            "query": req.query,
            "total_scraped": len(jobs),
            "jobs": jobs,
            "sync": sync_result
        }
    except Exception as e:
        logger.error(f"Search jobs error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/scrape/live-browser")
async def live_browser_scrape(req: LiveBrowserScrapeRequest):
    """
    Scrape jobs directly from live Welcome to the Jungle web pages using Playwright
    """
    try:
        jobs = await engine.live_browser_scrape(
            search_term=req.search_term or "Developer",
            limit=req.limit or 10,
            headless=True
        )
        
        sync_result = None
        if req.sync_to_db and jobs:
            sync_result = engine.sync_jobs_to_db(jobs)
            
        return {
            "success": True,
            "mode": "live_browser",
            "search_term": req.search_term,
            "total_scraped": len(jobs),
            "jobs": jobs,
            "sync": sync_result
        }
    except Exception as e:
        logger.error(f"Live browser scrape error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/scrape/job-details")
async def get_job_details(req: JobDetailRequest):
    """
    Scrape detailed requirements and full markdown description for a specific WTTJ job URL
    """
    try:
        result = await engine.scrape_job_details(req.job_url)
        return result
    except Exception as e:
        logger.error(f"Job details error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/scrape/sync")
async def sync_wttj_jobs_endpoint(req: SyncRequest, background_tasks: BackgroundTasks):
    """
    Comprehensive sync: runs API and browser scraping, then synchronizes into swiply.db
    """
    try:
        all_jobs = []
        
        # 1. API Search
        if "api" in (req.sources or []):
            api_jobs = await engine.search_api_jobs(query=req.query or "", limit=req.limit or 20)
            all_jobs.extend(api_jobs)
            
        # 2. Live Browser Scrape (if needed or requested)
        if "live_browser" in (req.sources or []) and len(all_jobs) < (req.limit or 20):
            browser_jobs = await engine.live_browser_scrape(
                search_term=req.query or "Software Engineer",
                limit=10,
                headless=True
            )
            all_jobs.extend(browser_jobs)
            
        # 3. Sync to Database
        sync_result = engine.sync_jobs_to_db(all_jobs)
        
        return {
            "success": True,
            "query": req.query,
            "scraped_count": len(all_jobs),
            "sync_details": sync_result
        }
    except Exception as e:
        logger.error(f"Sync error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/jobs")
async def get_scraped_jobs(
    query: Optional[str] = None,
    company: Optional[str] = None,
    remote: Optional[bool] = None,
    limit: int = Query(50, le=200),
    db: Session = Depends(get_db)
):
    """
    Get stored WTTJ jobs from Swiply database
    """
    q = db.query(Job).filter(Job.sourceCareerSite == "WTTJ")
    if query:
        q = q.filter(Job.title.ilike(f"%{query}%"))
    if company:
        q = q.filter(Job.company.ilike(f"%{company}%"))
    if remote is not None:
        q = q.filter(Job.remote == remote)
        
    jobs = q.limit(limit).all()
    return {
        "success": True,
        "count": len(jobs),
        "jobs": [
            {
                "id": j.id,
                "title": j.title,
                "company": j.company,
                "location": j.location,
                "logo": j.logo,
                "salary": f"€{j.salaryMin:,} - €{j.salaryMax:,}" if (j.salaryMin and j.salaryMax) else "Competitive",
                "remote": j.remote,
                "contract": j.employmentType,
                "external_url": j.externalUrl,
                "created_at": j.created_at.isoformat() if j.created_at else None
            }
            for j in jobs
        ]
    }

@app.post("/fix-existing-jobs")
async def fix_existing_jobs(db: Session = Depends(get_db)):
    """
    Fix existing WTTJ jobs to set can_apply=True so they appear in JobSwipe
    """
    try:
        # Update all WTTJ jobs that don't have can_apply set
        wttj_jobs = db.query(Job).filter(Job.sourceCareerSite == "WTTJ").all()
        updated_count = 0
        
        for job in wttj_jobs:
            if job.can_apply is None or job.can_apply == False:
                job.can_apply = True
                updated_count += 1
                
        db.commit()
        
        return {
            "success": True,
            "message": f"Fixed {updated_count} existing WTTJ jobs",
            "total_wttj_jobs": len(wttj_jobs),
            "updated_count": updated_count
        }
    except Exception as e:
        db.rollback()
        logger.error(f"Error fixing jobs: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8013)

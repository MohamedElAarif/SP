from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel, HttpUrl
from typing import Dict, List, Optional
from datetime import datetime
import asyncio

from app.database import get_db, ScrapeJob, ScrapeCache, User
from app.auth import get_current_user
from app.scrapers.base_scraper import BaseScraper
from app.config import settings
from app.utils.export import export_to_csv, export_to_json, export_to_pdf, export_to_excel

router = APIRouter()

class ScrapeRequest(BaseModel):
    url: HttpUrl
    selectors: Dict[str, str]
    use_selenium: bool = False

class ScrapeResponse(BaseModel):
    id: int
    url: str
    status: str
    created_at: datetime
    message: str

class ScrapeResult(BaseModel):
    id: int
    url: str
    status: str
    result_data: Optional[Dict]
    error_message: Optional[str]
    created_at: datetime
    completed_at: Optional[datetime]

def check_cache(db: Session, url: str) -> Optional[Dict]:
    """Check if URL is cached and not expired"""
    cache_entry = db.query(ScrapeCache).filter(
        ScrapeCache.url == str(url),
        ScrapeCache.expires_at > datetime.utcnow()
    ).first()
    
    if cache_entry:
        return cache_entry.data
    return None

def save_to_cache(db: Session, url: str, data: Dict):
    """Save scraped data to cache"""
    # Remove old cache entries for this URL
    db.query(ScrapeCache).filter(ScrapeCache.url == str(url)).delete()
    
    # Create new cache entry (expires in 1 hour)
    expires_at = datetime.utcnow().replace(hour=datetime.utcnow().hour + 1)
    cache_entry = ScrapeCache(
        url=str(url),
        data=data,
        expires_at=expires_at
    )
    db.add(cache_entry)
    db.commit()

def perform_scraping(db: Session, job_id: int):
    """Background task to perform scraping"""
    job = db.query(ScrapeJob).filter(ScrapeJob.id == job_id).first()
    if not job:
        return
    
    try:
        # Update status to running
        job.status = "running"
        db.commit()
        
        # Check cache first
        cached_data = check_cache(db, job.url)
        if cached_data:
            job.result_data = cached_data
            job.status = "completed"
            job.completed_at = datetime.utcnow()
            db.commit()
            return
        
        # Perform scraping
        scraper = BaseScraper(use_selenium=job.selectors.get("use_selenium", False))
        result = scraper.scrape_url(str(job.url), job.selectors)
        
        if "error" in result:
            job.status = "failed"
            job.error_message = result["error"]
        else:
            job.status = "completed"
            job.result_data = result
            # Save to cache
            save_to_cache(db, job.url, result)
        
        job.completed_at = datetime.utcnow()
        db.commit()
        
    except Exception as e:
        job.status = "failed"
        job.error_message = str(e)
        job.completed_at = datetime.utcnow()
        db.commit()

@router.post("/", response_model=ScrapeResponse)
async def create_scrape_job(
    request: ScrapeRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Check if user has too many pending jobs
    pending_jobs = db.query(ScrapeJob).filter(
        ScrapeJob.user_id == current_user.id,
        ScrapeJob.status.in_(["pending", "running"])
    ).count()
    
    if pending_jobs >= settings.MAX_CONCURRENT_SCRAPES:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many concurrent scraping jobs"
        )
    
    # Check cache first
    cached_data = check_cache(db, request.url)
    if cached_data:
        # Create a completed job with cached data
        job = ScrapeJob(
            user_id=current_user.id,
            url=str(request.url),
            selectors=request.selectors,
            status="completed",
            result_data=cached_data,
            completed_at=datetime.utcnow()
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        
        return ScrapeResponse(
            id=job.id,
            url=str(request.url),
            status=job.status,
            created_at=job.created_at,
            message="Data retrieved from cache"
        )
    
    # Create new scraping job
    job = ScrapeJob(
        user_id=current_user.id,
        url=str(request.url),
        selectors=request.selectors
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    
    # Start background scraping task
    background_tasks.add_task(perform_scraping, db, job.id)
    
    return ScrapeResponse(
        id=job.id,
        url=str(request.url),
        status=job.status,
        created_at=job.created_at,
        message="Scraping job created and started"
    )

@router.get("/{job_id}", response_model=ScrapeResult)
async def get_scrape_result(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    job = db.query(ScrapeJob).filter(
        ScrapeJob.id == job_id,
        ScrapeJob.user_id == current_user.id
    ).first()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scraping job not found"
        )
    
    return ScrapeResult(
        id=job.id,
        url=job.url,
        status=job.status,
        result_data=job.result_data,
        error_message=job.error_message,
        created_at=job.created_at,
        completed_at=job.completed_at
    )

@router.delete("/{job_id}")
async def delete_scrape_job(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    job = db.query(ScrapeJob).filter(
        ScrapeJob.id == job_id,
        ScrapeJob.user_id == current_user.id
    ).first()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scraping job not found"
        )
    
    db.delete(job)
    db.commit()
    
    return {"message": "Scraping job deleted successfully"}

@router.get("/{job_id}/export/csv")
async def export_scrape_result_csv(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    job = db.query(ScrapeJob).filter(
        ScrapeJob.id == job_id,
        ScrapeJob.user_id == current_user.id
    ).first()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scraping job not found"
        )
    
    if job.status != "completed" or not job.result_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No data available for export"
        )
    
    return export_to_csv(job.result_data)

@router.get("/{job_id}/export/json")
async def export_scrape_result_json(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    job = db.query(ScrapeJob).filter(
        ScrapeJob.id == job_id,
        ScrapeJob.user_id == current_user.id
    ).first()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scraping job not found"
        )
    
    if job.status != "completed" or not job.result_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No data available for export"
        )
    
    return export_to_json(job.result_data)

@router.get("/{job_id}/export/pdf")
async def export_scrape_result_pdf(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    job = db.query(ScrapeJob).filter(
        ScrapeJob.id == job_id,
        ScrapeJob.user_id == current_user.id
    ).first()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scraping job not found"
        )
    
    if job.status != "completed" or not job.result_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No data available for export"
        )
    
    return export_to_pdf(job.result_data)

@router.get("/{job_id}/export/excel")
async def export_scrape_result_excel(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    job = db.query(ScrapeJob).filter(
        ScrapeJob.id == job_id,
        ScrapeJob.user_id == current_user.id
    ).first()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scraping job not found"
        )
    
    if job.status != "completed" or not job.result_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No data available for export"
        )
    
    return export_to_excel(job.result_data)

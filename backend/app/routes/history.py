from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel

from app.database import get_db, ScrapeJob, User
from app.auth import get_current_user

router = APIRouter()

class HistoryItem(BaseModel):
    id: int
    url: str
    status: str
    created_at: datetime
    completed_at: Optional[datetime]
    error_message: Optional[str]
    
    class Config:
        from_attributes = True

class HistoryResponse(BaseModel):
    items: List[HistoryItem]
    total: int
    page: int
    per_page: int
    total_pages: int

@router.get("/", response_model=HistoryResponse)
async def get_scraping_history(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    status_filter: Optional[str] = Query(None),
    days: Optional[int] = Query(None, ge=1),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Build query
    query = db.query(ScrapeJob).filter(ScrapeJob.user_id == current_user.id)
    
    # Apply status filter
    if status_filter:
        query = query.filter(ScrapeJob.status == status_filter)
    
    # Apply date filter
    if days:
        start_date = datetime.utcnow() - timedelta(days=days)
        query = query.filter(ScrapeJob.created_at >= start_date)
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    offset = (page - 1) * per_page
    jobs = query.order_by(ScrapeJob.created_at.desc()).offset(offset).limit(per_page).all()
    
    # Calculate total pages
    total_pages = (total + per_page - 1) // per_page
    
    return HistoryResponse(
        items=[HistoryItem.from_orm(job) for job in jobs],
        total=total,
        page=page,
        per_page=per_page,
        total_pages=total_pages
    )

@router.get("/stats")
async def get_scraping_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Get user's scraping statistics
    total_jobs = db.query(ScrapeJob).filter(ScrapeJob.user_id == current_user.id).count()
    completed_jobs = db.query(ScrapeJob).filter(
        ScrapeJob.user_id == current_user.id,
        ScrapeJob.status == "completed"
    ).count()
    failed_jobs = db.query(ScrapeJob).filter(
        ScrapeJob.user_id == current_user.id,
        ScrapeJob.status == "failed"
    ).count()
    pending_jobs = db.query(ScrapeJob).filter(
        ScrapeJob.user_id == current_user.id,
        ScrapeJob.status.in_(["pending", "running"])
    ).count()
    
    # Get recent activity (last 7 days)
    week_ago = datetime.utcnow() - timedelta(days=7)
    recent_jobs = db.query(ScrapeJob).filter(
        ScrapeJob.user_id == current_user.id,
        ScrapeJob.created_at >= week_ago
    ).count()
    
    return {
        "total_jobs": total_jobs,
        "completed_jobs": completed_jobs,
        "failed_jobs": failed_jobs,
        "pending_jobs": pending_jobs,
        "recent_jobs": recent_jobs,
        "success_rate": (completed_jobs / total_jobs * 100) if total_jobs > 0 else 0
    }

@router.delete("/")
async def clear_history(
    days: Optional[int] = Query(None, ge=1),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Build query for jobs to delete
    query = db.query(ScrapeJob).filter(ScrapeJob.user_id == current_user.id)
    
    if days:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        query = query.filter(ScrapeJob.created_at < cutoff_date)
    
    # Count jobs to be deleted
    jobs_to_delete = query.count()
    
    # Delete jobs
    query.delete()
    db.commit()
    
    return {
        "message": f"Deleted {jobs_to_delete} scraping jobs",
        "deleted_count": jobs_to_delete
    }

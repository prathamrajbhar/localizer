"""
Job Management Routes (Direct execution, no Celery)
"""
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional, List
import uuid
from datetime import datetime
import asyncio

from app.core.db import get_db
from app.services.direct_retrain import DirectRetrainManager
from app.utils.logger import app_logger

router = APIRouter(prefix="/jobs", tags=["Job Management"])

# In-memory job tracking (for production, consider Redis)
active_jobs = {}


@router.post("/retrain")
async def trigger_model_retraining(
    background_tasks: BackgroundTasks,
    domain: str = "general",
    model_type: str = "indicTrans2",
    epochs: int = 3,
    batch_size: int = 16,
    learning_rate: float = 2e-5,
    db: Session = Depends(get_db)
):
    """Trigger model retraining (direct implementation, no Celery)"""
    try:
        # Generate job ID
        job_id = str(uuid.uuid4())

        # Initialize job tracking
        active_jobs[job_id] = {
            "status": "started",
            "started_at": datetime.utcnow().isoformat(),
            "domain": domain,
            "model_type": model_type,
            "epochs": epochs,
            "user_id": None,
            "progress": 0,
            "message": "Initializing retraining..."
        }

        # Start retraining directly (no Celery as per prompt)
        retrain_manager = DirectRetrainManager()

        # Add background task
        background_tasks.add_task(
            run_retraining_job,
            job_id,
            retrain_manager,
            domain,
            model_type,
            epochs,
            batch_size,
            learning_rate,
            db
        )

        app_logger.info(f"Retraining job {job_id} started")

        return {
            "job_id": job_id,
            "status": "started",
            "message": "Model retraining started",
            "domain": domain,
            "model_type": model_type,
            "estimated_duration": f"{epochs * 10} minutes"
        }
    except Exception as e:
        app_logger.error(f"Failed to start retraining job: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start retraining: {str(e)}"
        )


@router.get("/{job_id}")
async def get_job_status(job_id: str):
    """Get status of a running job"""
    if job_id not in active_jobs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    job_info = active_jobs[job_id]
    
    return {
        "job_id": job_id,
        **job_info
    }


@router.get("")
async def list_active_jobs():
    """List all active jobs"""
    jobs = [{"job_id": job_id, **info} for job_id, info in active_jobs.items()]
    
    return {
        "jobs": jobs,
        "total": len(jobs)
    }


@router.delete("/{job_id}")
async def cancel_job(job_id: str):
    """Cancel a running job"""
    if job_id not in active_jobs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    job_info = active_jobs[job_id]
    
    # Mark as cancelled
    active_jobs[job_id]["status"] = "cancelled"
    active_jobs[job_id]["message"] = "Job cancelled by user"
    active_jobs[job_id]["cancelled_at"] = datetime.utcnow().isoformat()
    
    app_logger.info(f"Job {job_id} cancelled")
    
    return {
        "job_id": job_id,
        "status": "cancelled",
        "message": "Job cancellation requested"
    }


async def run_retraining_job(
    job_id: str,
    retrain_manager: DirectRetrainManager,
    domain: str,
    model_type: str,
    epochs: int,
    batch_size: int,
    learning_rate: float,
    db: Session,
    user_id: Optional[int] = None
):
    """Background task to run model retraining"""
    try:
        # Update job status
        active_jobs[job_id]["status"] = "running"
        active_jobs[job_id]["message"] = "Preparing training data..."
        active_jobs[job_id]["progress"] = 10
        
        # Simulate progress updates (replace with actual training progress)
        for progress in [25, 50, 75]:
            if active_jobs[job_id]["status"] == "cancelled":
                app_logger.info(f"Job {job_id} was cancelled")
                return
            
            active_jobs[job_id]["progress"] = progress
            active_jobs[job_id]["message"] = f"Training in progress... {progress}%"
            await asyncio.sleep(2)  # Simulate work
        
        # Run actual retraining
        result = retrain_manager.trigger_retraining(
            domain=domain,
            epochs=epochs,
            languages=None  # Will use default supported languages
        )
        
        # Update completion status
        active_jobs[job_id]["status"] = "completed"
        active_jobs[job_id]["progress"] = 100
        active_jobs[job_id]["message"] = "Retraining completed successfully"
        active_jobs[job_id]["completed_at"] = datetime.utcnow().isoformat()
        active_jobs[job_id]["result"] = result
        
        app_logger.info(f"Job {job_id} completed successfully")
        
    except Exception as e:
        # Update error status
        active_jobs[job_id]["status"] = "failed"
        active_jobs[job_id]["message"] = f"Retraining failed: {str(e)}"
        active_jobs[job_id]["error"] = str(e)
        active_jobs[job_id]["failed_at"] = datetime.utcnow().isoformat()
        
        app_logger.error(f"Job {job_id} failed: {e}")


@router.post("/cleanup")
async def cleanup_completed_jobs():
    """Clean up completed/failed jobs"""
    completed_statuses = ["completed", "failed", "cancelled"]
    jobs_to_remove = [
        job_id for job_id, info in active_jobs.items()
        if info.get("status") in completed_statuses
    ]
    
    for job_id in jobs_to_remove:
        del active_jobs[job_id]
    
    app_logger.info(f"Cleaned up {len(jobs_to_remove)} completed jobs")
    
    return {
        "cleaned_jobs": len(jobs_to_remove),
        "remaining_jobs": len(active_jobs)
    }
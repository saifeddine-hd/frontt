from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from typing import Dict, Any
import uuid
import os
import zipfile
import tempfile
from datetime import datetime
import os

from services.runner import ScanRunner
from models.scan import ScanJob, ScanStatus
from storage.repositories import scan_repository

router = APIRouter(tags=["Scans"], prefix="/scans")

# Configurable max file size (200 MB)
MAX_FILE_SIZE = int(os.getenv("MAX_SCAN_FILE_SIZE", 200 * 1024 * 1024))

@router.post("/")
async def create_scan(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
) -> Dict[str, Any]:
    """Create a new scan job"""
    
    # Validate file type
    if not file.filename or not file.filename.endswith('.zip'):
        raise HTTPException(status_code=400, detail="Only ZIP files are supported")
    
    # Validate file size
    if file.size and file.size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400, 
            detail=f"File too large (max {MAX_FILE_SIZE // (1024*1024)}MB)"
        )
    
    # Create scan job
    job_id = str(uuid.uuid4())
    scan_job = ScanJob(
        id=job_id,
        filename=file.filename,
        status=ScanStatus.PENDING,
        created_at=datetime.utcnow()
    )
    await scan_repository.create(scan_job)
    
    # Save uploaded file temporarily
    temp_dir = tempfile.mkdtemp()
    file_path = os.path.join(temp_dir, file.filename)
    
    with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)
    
    # Start scan in background
    background_tasks.add_task(run_scan_job, job_id, file_path)
    
    return {
        "job_id": job_id,
        "status": "pending",
        "message": "Scan job created successfully"
    }

@router.get("/{job_id}")
async def get_scan_status(job_id: str) -> Dict[str, Any]:
    """Get scan job status"""
    scan_job = await scan_repository.get_by_id(job_id)
    
    if not scan_job:
        raise HTTPException(status_code=404, detail="Scan job not found")
    
    return {
        "job_id": job_id,
        "status": scan_job.status.value,
        "filename": scan_job.filename,
        "created_at": scan_job.created_at.isoformat(),
        "completed_at": scan_job.completed_at.isoformat() if scan_job.completed_at else None,
        "findings_count": scan_job.findings_count or 0,
        "error": scan_job.error
    }

@router.get("/recent")
async def get_recent_scans(limit: int = 10):
    """Return recent scans (file + repository) for dashboard"""
    recent_file_scans = await scan_repository.get_recent(limit=limit)
    
    from storage.repositories import repository_repository
    recent_repo_scans = await repository_repository.get_recent_scans(limit=limit)
    
    combined_scans = recent_file_scans + recent_repo_scans
    combined_scans.sort(key=lambda x: x.created_at if hasattr(x, "created_at") else x.last_scan, reverse=True)
    combined_scans = combined_scans[:limit]
    
    return [
        {
            "id": s.id,
            "filename": getattr(s, "filename", getattr(s, "repository_name", "Repository Scan")),
            "status": getattr(s, "status", getattr(s, "last_scan_status", "pending")).value
            if hasattr(getattr(s, "status", None), "value") else getattr(s, "status", "pending"),
            "created_at": (s.created_at if hasattr(s, "created_at") else s.last_scan).isoformat(),
            "completed_at": getattr(s, "completed_at", getattr(s, "last_scan_completed", None)).isoformat() 
                            if getattr(s, "completed_at", getattr(s, "last_scan_completed", None)) else None,
            "findings_count": getattr(s, "findings_count", 0) or 0,
            "error": getattr(s, "error", getattr(s, "last_scan_error", None))
        }
        for s in combined_scans
    ]

async def run_scan_job(job_id: str, file_path: str):
    """Background task to run the scan"""
    try:
        await scan_repository.update_status(job_id, ScanStatus.RUNNING)
        
        extract_dir = tempfile.mkdtemp()
        with zipfile.ZipFile(file_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
        
        runner = ScanRunner()
        findings = await runner.scan_directory(extract_dir)
        
        from storage.repositories import finding_repository
        for finding in findings:
            finding.job_id = job_id
            await finding_repository.create(finding)
        
        await scan_repository.update_completion(job_id, ScanStatus.COMPLETED, len(findings))
        
    except Exception as e:
        await scan_repository.update_status(job_id, ScanStatus.FAILED, str(e))
    finally:
        import shutil
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
            if 'extract_dir' in locals() and os.path.exists(extract_dir):
                shutil.rmtree(extract_dir)
        except Exception:
            pass

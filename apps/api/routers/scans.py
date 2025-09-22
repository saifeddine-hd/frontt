from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from typing import Dict, Any
import uuid
import os
import zipfile
import tempfile
from datetime import datetime

from services.runner import ScanRunner
from models.scan import ScanJob, ScanStatus
from storage.repositories import scan_repository

router = APIRouter(tags=["Scans"], prefix="/scans")

@router.post("/")
async def create_scan(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
) -> Dict[str, Any]:
    """Create a new scan job"""
    
    # Validate file
    if not file.filename or not file.filename.endswith('.zip'):
        raise HTTPException(status_code=400, detail="Only ZIP files are supported")
    
    if file.size and file.size > 50 * 1024 * 1024:  # 50MB limit
        raise HTTPException(status_code=400, detail="File too large (max 50MB)")
    
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

async def run_scan_job(job_id: str, file_path: str):
    """Background task to run the scan"""
    try:
        # Update status to running
        await scan_repository.update_status(job_id, ScanStatus.RUNNING)
        
        # Extract ZIP file
        extract_dir = tempfile.mkdtemp()
        with zipfile.ZipFile(file_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
        
        # Run the scan
        runner = ScanRunner()
        findings = await runner.scan_directory(extract_dir)
        
        # Save findings to database
        from storage.repositories import finding_repository
        for finding in findings:
            finding.job_id = job_id
            await finding_repository.create(finding)
        
        # Update job status
        await scan_repository.update_completion(
            job_id, 
            ScanStatus.COMPLETED, 
            len(findings)
        )
        
    except Exception as e:
        # Update job with error
        await scan_repository.update_status(
            job_id, 
            ScanStatus.FAILED, 
            str(e)
        )
    finally:
        # Cleanup temporary files
        import shutil
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
            if 'extract_dir' in locals() and os.path.exists(extract_dir):
                shutil.rmtree(extract_dir)
        except Exception:
            pass  # Ignore cleanup errors
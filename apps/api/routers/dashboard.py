from fastapi import APIRouter, Depends, HTTPException, Query
from datetime import datetime, timedelta
from typing import Dict, Any, List
from storage.repositories import scan_repository, finding_repository, repository_repository
from core.security import verify_token

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

@router.get("/stats")
async def get_dashboard_stats(current_user: dict = Depends(verify_token)) -> Dict[str, Any]:
    """Get dashboard statistics"""
    try:
        # Get scan statistics
        total_scans = await scan_repository.count_by_status("completed")
        running_scans = await scan_repository.count_by_status("running") + await scan_repository.count_by_status("pending")
        
        # Get findings statistics
        critical_findings = await finding_repository.count_by_severity("critical")
        
        # Get completed scans in last 30 days
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        completed_scans = await scan_repository.count_completed_since(thirty_days_ago)
        
        return {
            "success": True,
            "data": {
                "total_scans": total_scans,
                "critical_findings": critical_findings,
                "running_scans": running_scans,
                "completed_scans": completed_scans
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get dashboard stats: {str(e)}")

@router.get("/recent-scans")
async def get_recent_scans(
    limit: int = Query(10, ge=1, le=50),
    current_user: dict = Depends(verify_token)
) -> Dict[str, Any]:
    """Get recent scans with findings statistics"""
    try:
        # Get recent file scans
        recent_file_scans = await scan_repository.get_recent(limit=limit//2)
        
        # Get recent repository scans
        recent_repo_scans = await repository_repository.get_recent_scans(limit=limit//2)
        
        enriched_scans = []
        
        # Process file scans
        for scan in recent_file_scans:
            findings_stats = await finding_repository.get_statistics_by_job_id(scan.id)
            scan_dict = {
                "id": scan.id,
                "filename": scan.filename,
                "scan_type": "file",
                "status": scan.status.value if hasattr(scan.status, 'value') else str(scan.status),
                "created_at": scan.created_at.isoformat(),
                "completed_at": scan.completed_at.isoformat() if scan.completed_at else None,
                "findings_count": findings_stats.get("total", 0),
                "critical_count": findings_stats.get("critical", 0),
                "high_count": findings_stats.get("high", 0),
                "medium_count": findings_stats.get("medium", 0),
                "low_count": findings_stats.get("low", 0),
                "error": scan.error
            }
            enriched_scans.append(scan_dict)
        
        # Process repository scans
        for repo in recent_repo_scans:
            scan_dict = {
                "id": repo.id,
                "filename": repo.name,
                "scan_type": "repository",
                "status": repo.last_scan_status or "pending",
                "created_at": (repo.last_scan or repo.created_at).isoformat(),
                "completed_at": repo.last_scan.isoformat() if repo.last_scan else None,
                "findings_count": repo.findings_count or 0,
                "critical_count": 0,  # Could be enhanced with detailed stats
                "high_count": 0,
                "medium_count": 0,
                "low_count": 0,
                "error": None
            }
            enriched_scans.append(scan_dict)
        
        # Sort by creation date and limit
        enriched_scans.sort(key=lambda x: x["created_at"], reverse=True)
        enriched_scans = enriched_scans[:limit]
        
        return {
            "success": True,
            "data": enriched_scans
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get recent scans: {str(e)}")

@router.get("/overview")
async def get_dashboard_overview(current_user: dict = Depends(verify_token)) -> Dict[str, Any]:
    """Get comprehensive dashboard overview"""
    try:
        # Get all statistics in one call
        stats = await get_dashboard_stats(current_user)
        recent_scans = await get_recent_scans(5, current_user)
        
        # Get repository count
        repositories = await repository_repository.get_all()
        active_repos = len([r for r in repositories if r.status == "active"])
        
        return {
            "success": True,
            "data": {
                "stats": stats["data"],
                "recent_scans": recent_scans["data"],
                "repository_count": len(repositories),
                "active_repositories": active_repos
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get dashboard overview: {str(e)}")
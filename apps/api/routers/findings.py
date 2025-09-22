from fastapi import APIRouter, Query, HTTPException
from typing import Dict, Any, List, Optional
import csv
import io

from models.finding import Finding
from storage.repositories import finding_repository
from services.redact import redact_secret

router = APIRouter(tags=["Findings"], prefix="/findings")

@router.get("/")
async def get_findings(
    job_id: str = Query(...),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    severity: Optional[str] = Query(None),
    secret_type: Optional[str] = Query(None)
) -> Dict[str, Any]:
    """Get paginated findings for a scan job"""
    
    findings = await finding_repository.get_by_job_id(
        job_id=job_id,
        page=page,
        size=size,
        severity=severity,
        secret_type=secret_type
    )
    
    total = await finding_repository.count_by_job_id(job_id, severity, secret_type)
    
    # Redact secrets in response
    redacted_findings = []
    for finding in findings:
        finding_dict = finding.dict()
        finding_dict["secret"] = redact_secret(finding.secret)
        redacted_findings.append(finding_dict)
    
    return {
        "findings": redacted_findings,
        "pagination": {
            "page": page,
            "size": size,
            "total": total,
            "pages": (total + size - 1) // size
        }
    }

@router.get("/export/{job_id}")
async def export_findings(job_id: str, format: str = Query("json")) -> Dict[str, Any]:
    """Export findings in various formats"""
    
    findings = await finding_repository.get_all_by_job_id(job_id)
    
    if format == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            "File", "Line", "Secret Type", "Severity", 
            "Secret (Redacted)", "Rule", "Confidence"
        ])
        
        # Write data
        for finding in findings:
            writer.writerow([
                finding.file_path,
                finding.line_number,
                finding.secret_type,
                finding.severity,
                redact_secret(finding.secret),
                finding.rule_id,
                finding.confidence
            ])
        
        return {
            "format": "csv",
            "content": output.getvalue(),
            "filename": f"secrethawk-findings-{job_id}.csv"
        }
    
    else:  # JSON format
        redacted_findings = []
        for finding in findings:
            finding_dict = finding.dict()
            finding_dict["secret"] = redact_secret(finding.secret)
            redacted_findings.append(finding_dict)
        
        return {
            "format": "json",
            "findings": redacted_findings,
            "total": len(redacted_findings)
        }

@router.get("/stats/{job_id}")
async def get_scan_statistics(job_id: str) -> Dict[str, Any]:
    """Get scan statistics"""
    
    stats = await finding_repository.get_statistics_by_job_id(job_id)
    
    return {
        "job_id": job_id,
        "total_findings": stats.get("total", 0),
        "by_severity": {
            "critical": stats.get("critical", 0),
            "high": stats.get("high", 0),
            "medium": stats.get("medium", 0),
            "low": stats.get("low", 0)
        },
        "by_type": stats.get("by_type", {}),
        "files_scanned": stats.get("files_scanned", 0)
    }
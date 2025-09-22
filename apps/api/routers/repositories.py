from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import List, Dict, Any
import uuid
from datetime import datetime

from models.repository import Repository, RepositoryCreate, RepositoryUpdate
from storage.repositories import repository_repository
from services.git_provider import git_provider_service
from services.repository_scanner import repository_scanner
from core.security import verify_token

router = APIRouter(tags=["Repositories"], prefix="/repositories")

@router.post("/")
async def create_repository(
    repo_data: RepositoryCreate,
    background_tasks: BackgroundTasks,
    token: dict = Depends(verify_token)
) -> Dict[str, Any]:
    """Add a new repository to monitor"""
    
    # Create repository object
    repository = Repository(
        id=str(uuid.uuid4()),
        url=repo_data.url,
        provider=repo_data.provider,
        name=repo_data.name,
        token=repo_data.token,  # Will be encrypted in storage
        discord_webhook_url=repo_data.discord_webhook_url,
        webhook_secret=str(uuid.uuid4()),  # Generate webhook secret
        created_at=datetime.utcnow()
    )
    
    # Test repository access
    if not await git_provider_service.test_repository_access(repository):
        raise HTTPException(
            status_code=400,
            detail="Cannot access repository with provided token"
        )
    
    # Save repository
    saved_repo = await repository_repository.create(repository)
    
    # Setup webhook in background
    background_tasks.add_task(
        git_provider_service.setup_webhook,
        saved_repo
    )
    
    # Start initial scan in background
    background_tasks.add_task(
        repository_scanner.scan_repository,
        saved_repo.id
    )
    
    return {
        "id": saved_repo.id,
        "name": saved_repo.name,
        "status": "created",
        "message": "Repository added successfully. Initial scan started."
    }

@router.get("/")
async def list_repositories(
    token: dict = Depends(verify_token)
) -> List[Dict[str, Any]]:
    """List all monitored repositories"""
    
    repositories = await repository_repository.get_all()
    
    return [
        {
            "id": repo.id,
            "name": repo.name,
            "url": str(repo.url),
            "provider": repo.provider,
            "status": repo.status,
            "last_scan": repo.last_scan.isoformat() if repo.last_scan else None,
            "findings_count": repo.findings_count or 0,
            "created_at": repo.created_at.isoformat() if repo.created_at else None
        }
        for repo in repositories
    ]

@router.get("/{repository_id}")
async def get_repository(
    repository_id: str,
    token: dict = Depends(verify_token)
) -> Dict[str, Any]:
    """Get repository details"""
    
    repo = await repository_repository.get_by_id(repository_id)
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    
    return {
        "id": repo.id,
        "name": repo.name,
        "url": str(repo.url),
        "provider": repo.provider,
        "status": repo.status,
        "last_scan": repo.last_scan.isoformat() if repo.last_scan else None,
        "last_scan_status": repo.last_scan_status,
        "findings_count": repo.findings_count or 0,
        "discord_webhook_url": str(repo.discord_webhook_url) if repo.discord_webhook_url else None,
        "created_at": repo.created_at.isoformat() if repo.created_at else None,
        "updated_at": repo.updated_at.isoformat() if repo.updated_at else None
    }

@router.put("/{repository_id}")
async def update_repository(
    repository_id: str,
    repo_update: RepositoryUpdate,
    token: dict = Depends(verify_token)
) -> Dict[str, Any]:
    """Update repository configuration"""
    
    repo = await repository_repository.get_by_id(repository_id)
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    
    # Update repository
    updated_repo = await repository_repository.update(repository_id, repo_update)
    
    return {
        "id": updated_repo.id,
        "message": "Repository updated successfully"
    }

@router.delete("/{repository_id}")
async def delete_repository(
    repository_id: str,
    token: dict = Depends(verify_token)
) -> Dict[str, Any]:
    """Delete a monitored repository"""
    
    repo = await repository_repository.get_by_id(repository_id)
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    
    await repository_repository.delete(repository_id)
    
    return {"message": "Repository deleted successfully"}

@router.post("/{repository_id}/scan")
async def trigger_manual_scan(
    repository_id: str,
    background_tasks: BackgroundTasks,
    token: dict = Depends(verify_token)
) -> Dict[str, Any]:
    """Manually trigger a repository scan"""
    
    repo = await repository_repository.get_by_id(repository_id)
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    
    # Start scan in background
    background_tasks.add_task(
        repository_scanner.scan_repository,
        repository_id
    )
    
    return {
        "message": f"Manual scan triggered for {repo.name}",
        "repository_id": repository_id
    }

@router.post("/{repository_id}/test-webhook")
async def test_discord_webhook(
    repository_id: str,
    token: dict = Depends(verify_token)
) -> Dict[str, Any]:
    """Test Discord webhook configuration"""
    
    repo = await repository_repository.get_by_id(repository_id)
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    
    if not repo.discord_webhook_url:
        raise HTTPException(status_code=400, detail="No Discord webhook URL configured")
    
    # Send test notification
    from services.discord_notifier import discord_notifier
    
    success = await discord_notifier.send_scan_summary(
        str(repo.discord_webhook_url),
        repo,
        0,  # No findings for test
        0,
        0,
        "test-scan"
    )
    
    if success:
        return {"message": "Test notification sent successfully"}
    else:
        raise HTTPException(status_code=400, detail="Failed to send test notification")
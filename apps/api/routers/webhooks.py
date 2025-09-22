from fastapi import APIRouter, Request, HTTPException, BackgroundTasks
from typing import Dict, Any
import hmac
import hashlib
import json

from storage.repositories import repository_repository
from services.repository_scanner import repository_scanner

router = APIRouter(tags=["Webhooks"], prefix="/webhooks")

@router.post("/github/{repository_id}")
async def github_webhook(
    repository_id: str,
    request: Request,
    background_tasks: BackgroundTasks
) -> Dict[str, Any]:
    """Handle GitHub webhook for repository push events"""
    
    try:
        # Get repository
        repo = await repository_repository.get_by_id(repository_id)
        if not repo:
            raise HTTPException(status_code=404, detail="Repository not found")
        
        # Get request body and headers
        body = await request.body()
        signature = request.headers.get("X-Hub-Signature-256")
        event_type = request.headers.get("X-GitHub-Event")
        
        # Verify webhook signature
        if not _verify_github_signature(body, signature, repo.webhook_secret):
            raise HTTPException(status_code=401, detail="Invalid signature")
        
        # Only process push events
        if event_type != "push":
            return {"message": "Event ignored", "event_type": event_type}
        
        # Parse webhook payload
        payload = json.loads(body.decode())
        
        # Check if this is a push to main/master branch
        ref = payload.get("ref", "")
        if not (ref.endswith("/main") or ref.endswith("/master")):
            return {"message": "Push to non-main branch ignored"}
        
        # Trigger scan in background
        background_tasks.add_task(
            repository_scanner.scan_repository_webhook,
            repository_id,
            payload
        )
        
        return {
            "message": "Webhook processed successfully",
            "repository": repo.name,
            "commits": len(payload.get("commits", []))
        }
        
    except Exception as e:
        print(f"Error processing GitHub webhook: {e}")
        raise HTTPException(status_code=500, detail="Webhook processing failed")

@router.post("/gitlab/{repository_id}")
async def gitlab_webhook(
    repository_id: str,
    request: Request,
    background_tasks: BackgroundTasks
) -> Dict[str, Any]:
    """Handle GitLab webhook for repository push events"""
    
    try:
        # Get repository
        repo = await repository_repository.get_by_id(repository_id)
        if not repo:
            raise HTTPException(status_code=404, detail="Repository not found")
        
        # Get request body and headers
        body = await request.body()
        token = request.headers.get("X-Gitlab-Token")
        event_type = request.headers.get("X-Gitlab-Event")
        
        # Verify webhook token
        if token != repo.webhook_secret:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        # Only process push events
        if event_type != "Push Hook":
            return {"message": "Event ignored", "event_type": event_type}
        
        # Parse webhook payload
        payload = json.loads(body.decode())
        
        # Check if this is a push to main/master branch
        ref = payload.get("ref", "")
        if not (ref.endswith("/main") or ref.endswith("/master")):
            return {"message": "Push to non-main branch ignored"}
        
        # Trigger scan in background
        background_tasks.add_task(
            repository_scanner.scan_repository_webhook,
            repository_id,
            payload
        )
        
        return {
            "message": "Webhook processed successfully",
            "repository": repo.name,
            "commits": len(payload.get("commits", []))
        }
        
    except Exception as e:
        print(f"Error processing GitLab webhook: {e}")
        raise HTTPException(status_code=500, detail="Webhook processing failed")

def _verify_github_signature(body: bytes, signature: str, secret: str) -> bool:
    """Verify GitHub webhook signature"""
    if not signature or not secret:
        return False
    
    try:
        # GitHub sends signature as "sha256=<hash>"
        expected_signature = "sha256=" + hmac.new(
            secret.encode(),
            body,
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(signature, expected_signature)
        
    except Exception:
        return False
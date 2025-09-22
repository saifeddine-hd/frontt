import uuid
import tempfile
import shutil
from datetime import datetime
from typing import List, Optional

from models.repository import Repository, RepositoryStatus
from models.scan import ScanJob, ScanStatus
from models.finding import Finding
from services.git_provider import git_provider_service
from services.runner import ScanRunner
from services.discord_notifier import discord_notifier
from storage.repositories import repository_repository, scan_repository, finding_repository

class RepositoryScanner:
    """Service to scan monitored repositories"""
    
    def __init__(self):
        self.scan_runner = ScanRunner()
    
    async def scan_repository(self, repository_id: str) -> Optional[str]:
        """Scan a repository and send notifications"""
        try:
            # Get repository
            repo = await repository_repository.get_by_id(repository_id)
            if not repo:
                print(f"Repository {repository_id} not found")
                return None
            
            print(f"🔍 Starting scan for repository: {repo.name}")
            
            # Update repository status
            await repository_repository.update_scan_status(
                repository_id, 
                "running", 
                datetime.utcnow()
            )
            
            # Create scan job
            scan_job = ScanJob(
                id=str(uuid.uuid4()),
                filename=f"{repo.name}-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}",
                status=ScanStatus.RUNNING,
                created_at=datetime.utcnow()
            )
            
            await scan_repository.create(scan_job)
            
            # Clone repository
            temp_dir = None
            try:
                temp_dir = await git_provider_service.clone_repository(repo)
                
                # Run scan
                findings = await self.scan_runner.scan_directory(temp_dir)
                
                # Save findings
                for finding in findings:
                    finding.job_id = scan_job.id
                    await finding_repository.create(finding)
                
                # Update scan job
                await scan_repository.update_completion(
                    scan_job.id,
                    ScanStatus.COMPLETED,
                    len(findings)
                )
                
                # Update repository
                await repository_repository.update_scan_status(
                    repository_id,
                    "completed",
                    datetime.utcnow(),
                    len(findings)
                )
                
                # Send Discord notifications
                await self._send_notifications(repo, findings, scan_job.id)
                
                print(f"✅ Scan completed for {repo.name}: {len(findings)} findings")
                return scan_job.id
                
            finally:
                # Cleanup temporary directory
                if temp_dir:
                    shutil.rmtree(temp_dir, ignore_errors=True)
                    
        except Exception as e:
            print(f"❌ Error scanning repository {repository_id}: {e}")
            
            # Update repository status to error
            await repository_repository.update_scan_status(
                repository_id,
                "error",
                datetime.utcnow(),
                error=str(e)
            )
            
            return None
    
    async def scan_repository_webhook(self, repository_id: str, webhook_data: dict) -> Optional[str]:
        """Handle webhook-triggered scan"""
        try:
            repo = await repository_repository.get_by_id(repository_id)
            if not repo:
                return None
            
            print(f"🔗 Webhook triggered scan for {repo.name}")
            
            # Extract commit information from webhook
            commits = self._extract_commits_from_webhook(webhook_data, repo.provider)
            
            if commits:
                print(f"📝 Processing {len(commits)} commits")
                # For now, scan the entire repository
                # In future, could implement differential scanning
                return await self.scan_repository(repository_id)
            
            return None
            
        except Exception as e:
            print(f"Error processing webhook for repository {repository_id}: {e}")
            return None
    
    async def _send_notifications(self, repo: Repository, findings: List[Finding], scan_id: str):
        """Send Discord notifications for findings"""
        try:
            # Determine webhook URL (repo-specific or global)
            webhook_url = repo.discord_webhook_url or settings.DISCORD_WEBHOOK_URL
            
            if not webhook_url:
                print("No Discord webhook URL configured")
                return
            
            # Count findings by severity
            critical_count = len([f for f in findings if f.severity == "critical"])
            high_count = len([f for f in findings if f.severity == "high"])
            
            # Send summary notification
            await discord_notifier.send_scan_summary(
                str(webhook_url),
                repo,
                len(findings),
                critical_count,
                high_count,
                scan_id
            )
            
            # Send detailed alert if critical or high findings
            if critical_count > 0 or high_count > 0:
                critical_and_high = [
                    f for f in findings 
                    if f.severity in ["critical", "high"]
                ]
                
                await discord_notifier.send_security_alert(
                    str(webhook_url),
                    repo,
                    critical_and_high,
                    scan_id
                )
            
        except Exception as e:
            print(f"Error sending notifications: {e}")
    
    def _extract_commits_from_webhook(self, webhook_data: dict, provider: str) -> List[dict]:
        """Extract commit information from webhook payload"""
        commits = []
        
        try:
            if provider == "github":
                commits = webhook_data.get("commits", [])
            elif provider == "gitlab":
                commits = webhook_data.get("commits", [])
            
            return commits
            
        except Exception as e:
            print(f"Error extracting commits from webhook: {e}")
            return []

# Singleton instance
repository_scanner = RepositoryScanner()
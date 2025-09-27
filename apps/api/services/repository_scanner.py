import uuid
import tempfile
import shutil
import os
import subprocess
import json
from datetime import datetime
from typing import List, Optional

from models.repository import Repository, RepositoryStatus
from models.scan import ScanJob, ScanStatus
from models.finding import Finding
from services.git_provider import git_provider_service
from services.discord_notifier import discord_notifier
from services.runner import ScanRunner  # Import du scanner complet
from storage.repositories import repository_repository, scan_repository, finding_repository


class RepositoryScanner:
    """Service to scan monitored repositories"""

    def __init__(self):
        # Détection du binaire Gitleaks
        self.gitleaks_path = shutil.which("gitleaks") or r"D:\gitleaks\gitleaks.exe"
        # Note: On n'exige plus que Gitleaks soit présent car on a le scanner regex
        self.scanner = ScanRunner()  # Utilise le même scanner que pour les ZIP
        print(f"Repository scanner initialized. Gitleaks path: {self.gitleaks_path}")

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
                status=ScanStatus.RUNNING,  # Use proper enum
                created_at=datetime.utcnow()
            )
            await scan_repository.create(scan_job)

            # Clone repository
            temp_dir = None
            try:
                print(f"📥 Cloning repository...")
                temp_dir = await git_provider_service.clone_repository(repo)
                print(f"✅ Repository cloned to: {temp_dir}")

                # Run COMPLETE scan (Gitleaks + Regex patterns)
                print(f"🔍 Running complete security scan...")
                findings = await self.scanner.scan_directory(temp_dir)
                print(f"📊 Scan found {len(findings)} potential issues")

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

                # Update repository with current timestamp
                current_time = datetime.utcnow()
                await repository_repository.update_scan_status(
                    repository_id,
                    "completed",
                    current_time,
                    len(findings)
                )

                # Send Discord notifications
                await self._send_notifications(repo, findings, scan_job.id)

                print(f"✅ Scan completed for {repo.name}: {len(findings)} findings at {current_time}")
                return scan_job.id

            finally:
                # Cleanup temporary directory
                if temp_dir and os.path.exists(temp_dir):
                    try:
                        shutil.rmtree(temp_dir, ignore_errors=True)
                        print(f"🧹 Cleaned up temporary directory: {temp_dir}")
                    except Exception as cleanup_error:
                        print(f"Warning: Could not clean up temp directory: {cleanup_error}")

        except Exception as e:
            import traceback
            error_msg = f"Error scanning repository {repository_id}: {str(e)}"
            print(f"❌ {error_msg}")
            print(f"Full traceback: {traceback.format_exc()}")

            # Update repository status to error
            try:
                await repository_repository.update_scan_status(
                    repository_id,
                    "error",
                    datetime.utcnow(),
                    error=str(e)
                )
                
                # Update scan job to failed
                if 'scan_job' in locals():
                    await scan_repository.update_status(scan_job.id, ScanStatus.FAILED, str(e))
            except Exception as update_error:
                print(f"Additional error updating repository status: {update_error}")

            return None

    async def scan_repository_webhook(self, repository_id: str, webhook_data: dict) -> Optional[str]:
        """Handle webhook-triggered scan"""
        try:
            repo = await repository_repository.get_by_id(repository_id)
            if not repo:
                print(f"Repository {repository_id} not found for webhook")
                return None

            print(f"🔗 Webhook triggered scan for {repo.name}")

            # Extract commit information from webhook
            commits = self._extract_commits_from_webhook(webhook_data, repo.provider)

            if commits:
                print(f"📝 Processing {len(commits)} commits")
                # For now, scan the entire repository
                return await self.scan_repository(repository_id)
            else:
                print("No commits found in webhook payload")
                return None

        except Exception as e:
            print(f"Error processing webhook for repository {repository_id}: {e}")
            return None

    async def _send_notifications(self, repo: Repository, findings: List[Finding], scan_id: str):
        """Send Discord notifications for findings"""
        try:
            webhook_url = repo.discord_webhook_url

            if not webhook_url:
                print("No Discord webhook URL configured for this repository")
                return

            # Count findings by severity
            critical_count = len([f for f in findings if f.severity == "critical"])
            high_count = len([f for f in findings if f.severity == "high"])
            medium_count = len([f for f in findings if f.severity == "medium"])
            low_count = len([f for f in findings if f.severity == "low"])

            print(f"📊 Notification summary: {critical_count} critical, {high_count} high, {medium_count} medium, {low_count} low")

            # Send summary notification
            await discord_notifier.send_scan_summary(
                str(webhook_url),
                repo,
                len(findings),
                critical_count,
                high_count,
                scan_id
            )

            # Send detailed alert for critical and high severity issues
            if critical_count > 0 or high_count > 0:
                critical_and_high = [f for f in findings if f.severity in ["critical", "high"]]
                await discord_notifier.send_security_alert(
                    str(webhook_url),
                    repo,
                    critical_and_high,
                    scan_id
                )
                print(f"🚨 Sent security alert for {len(critical_and_high)} critical/high findings")

        except Exception as e:
            print(f"Error sending notifications: {e}")

    def _extract_commits_from_webhook(self, webhook_data: dict, provider: str) -> List[dict]:
        """Extract commit information from webhook payload"""
        commits = []

        try:
            if provider == "github":
                commits = webhook_data.get("commits", [])
                if commits:
                    print(f"GitHub webhook: Found {len(commits)} commits")
                    for commit in commits[:3]:  # Log first 3 commits
                        print(f"  - {commit.get('id', 'unknown')[:8]}: {commit.get('message', 'no message')[:50]}")
            
            elif provider == "gitlab":
                commits = webhook_data.get("commits", [])
                if commits:
                    print(f"GitLab webhook: Found {len(commits)} commits")
                    for commit in commits[:3]:  # Log first 3 commits
                        print(f"  - {commit.get('id', 'unknown')[:8]}: {commit.get('message', 'no message')[:50]}")

            return commits

        except Exception as e:
            print(f"Error extracting commits from webhook: {e}")
            return []

    async def _run_gitleaks_scan(self, repo_path: str) -> List[Finding]:
        """Legacy method - kept for compatibility but not used anymore"""
        print("Warning: _run_gitleaks_scan is deprecated. Use ScanRunner.scan_directory instead.")
        return []

    def get_scan_status(self) -> dict:
        """Get scanner status information"""
        return {
            "gitleaks_available": os.path.isfile(self.gitleaks_path) if self.gitleaks_path else False,
            "gitleaks_path": self.gitleaks_path,
            "scanner_initialized": self.scanner is not None,
            "timestamp": datetime.utcnow().isoformat()
        }


# Singleton instance
repository_scanner = RepositoryScanner()
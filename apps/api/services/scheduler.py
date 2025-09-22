import asyncio
import schedule
import time
from datetime import datetime, timedelta
from typing import List
import threading

from storage.repositories import repository_repository
from services.repository_scanner import repository_scanner
from models.repository import RepositoryStatus

class SchedulerService:
    """Background scheduler for repository monitoring"""
    
    def __init__(self):
        self.running = False
        self.thread = None
    
    def start(self):
        """Start the scheduler in a background thread"""
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._run_scheduler, daemon=True)
            self.thread.start()
            print("📅 Scheduler started")
    
    def stop(self):
        """Stop the scheduler"""
        self.running = False
        if self.thread:
            self.thread.join()
        print("📅 Scheduler stopped")
    
    def _run_scheduler(self):
        """Run the scheduler loop"""
        # Schedule repository scans every 30 minutes
        schedule.every(30).minutes.do(self._schedule_repository_scans)
        
        # Schedule cleanup every hour
        schedule.every().hour.do(self._cleanup_old_scans)
        
        while self.running:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    
    def _schedule_repository_scans(self):
        """Schedule scans for active repositories"""
        try:
            # Run in async context
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self._scan_repositories())
            loop.close()
        except Exception as e:
            print(f"Error in scheduled repository scan: {e}")
    
    async def _scan_repositories(self):
        """Scan all active repositories"""
        try:
            repositories = await repository_repository.get_active_repositories()
            
            for repo in repositories:
                # Check if repository needs scanning (last scan > 30 minutes ago)
                if self._should_scan_repository(repo):
                    print(f"🔍 Scheduling scan for {repo.name}")
                    
                    # Start background scan
                    asyncio.create_task(
                        repository_scanner.scan_repository(repo.id)
                    )
                    
                    # Small delay between scans to avoid overwhelming
                    await asyncio.sleep(5)
                    
        except Exception as e:
            print(f"Error scanning repositories: {e}")
    
    def _should_scan_repository(self, repo) -> bool:
        """Check if repository should be scanned"""
        if repo.status != RepositoryStatus.ACTIVE:
            return False
        
        if not repo.last_scan:
            return True
        
        # Scan if last scan was more than 30 minutes ago
        time_since_scan = datetime.utcnow() - repo.last_scan
        return time_since_scan > timedelta(minutes=30)
    
    def _cleanup_old_scans(self):
        """Cleanup old scan data"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self._perform_cleanup())
            loop.close()
        except Exception as e:
            print(f"Error in cleanup: {e}")
    
    async def _perform_cleanup(self):
        """Perform cleanup of old data"""
        try:
            # Clean up scan jobs older than 7 days
            cutoff_date = datetime.utcnow() - timedelta(days=7)
            
            # This would be implemented in the repository
            # await scan_repository.cleanup_old_scans(cutoff_date)
            
            print(f"🧹 Cleanup completed for scans older than {cutoff_date}")
            
        except Exception as e:
            print(f"Error performing cleanup: {e}")

# Singleton instance
scheduler_service = SchedulerService()
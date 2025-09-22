import aiohttp
import base64
import json
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import tempfile
import os
import shutil

from core.config import settings
from models.repository import Repository, RepositoryProvider

class GitProviderService:
    """Service to interact with Git providers (GitHub, GitLab)"""
    
    def __init__(self):
        self.session = None
    
    async def get_session(self):
        if not self.session:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def close_session(self):
        if self.session:
            await self.session.close()
            self.session = None
    
    async def test_repository_access(self, repo: Repository) -> bool:
        """Test if we can access the repository with provided token"""
        try:
            session = await self.get_session()
            
            if repo.provider == RepositoryProvider.GITHUB:
                url = f"https://api.github.com/repos/{self._extract_repo_path(repo.url)}"
                headers = {
                    "Authorization": f"token {repo.token}",
                    "Accept": "application/vnd.github.v3+json"
                }
            else:  # GitLab
                url = f"https://gitlab.com/api/v4/projects/{self._extract_gitlab_project_id(repo.url)}"
                headers = {
                    "Authorization": f"Bearer {repo.token}",
                    "Content-Type": "application/json"
                }
            
            async with session.get(url, headers=headers) as response:
                return response.status == 200
                
        except Exception as e:
            print(f"Error testing repository access: {e}")
            return False
    
    async def clone_repository(self, repo: Repository) -> str:
        """Clone repository to temporary directory"""
        temp_dir = tempfile.mkdtemp(prefix="secrethawk_")
        
        try:
            if repo.provider == RepositoryProvider.GITHUB:
                clone_url = f"https://{repo.token}@github.com/{self._extract_repo_path(repo.url)}.git"
            else:  # GitLab
                clone_url = f"https://oauth2:{repo.token}@gitlab.com/{self._extract_repo_path(repo.url)}.git"
            
            # Use git clone command
            import subprocess
            result = subprocess.run([
                "git", "clone", "--depth", "1", clone_url, temp_dir
            ], capture_output=True, text=True, timeout=300)
            
            if result.returncode != 0:
                raise Exception(f"Git clone failed: {result.stderr}")
            
            return temp_dir
            
        except Exception as e:
            # Cleanup on error
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
            raise e
    
    async def get_recent_commits(self, repo: Repository, since: datetime) -> List[Dict[str, Any]]:
        """Get recent commits since specified date"""
        try:
            session = await self.get_session()
            
            if repo.provider == RepositoryProvider.GITHUB:
                url = f"https://api.github.com/repos/{self._extract_repo_path(repo.url)}/commits"
                headers = {
                    "Authorization": f"token {repo.token}",
                    "Accept": "application/vnd.github.v3+json"
                }
                params = {"since": since.isoformat()}
            else:  # GitLab
                url = f"https://gitlab.com/api/v4/projects/{self._extract_gitlab_project_id(repo.url)}/repository/commits"
                headers = {
                    "Authorization": f"Bearer {repo.token}",
                    "Content-Type": "application/json"
                }
                params = {"since": since.isoformat()}
            
            async with session.get(url, headers=headers, params=params) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    print(f"Error fetching commits: {response.status}")
                    return []
                    
        except Exception as e:
            print(f"Error getting recent commits: {e}")
            return []
    
    async def setup_webhook(self, repo: Repository) -> bool:
        """Setup webhook for repository"""
        try:
            session = await self.get_session()
            
            webhook_url = f"{settings.BASE_URL}/api/v1/webhooks/{repo.provider}/{repo.id}"
            
            if repo.provider == RepositoryProvider.GITHUB:
                url = f"https://api.github.com/repos/{self._extract_repo_path(repo.url)}/hooks"
                headers = {
                    "Authorization": f"token {repo.token}",
                    "Accept": "application/vnd.github.v3+json"
                }
                payload = {
                    "name": "web",
                    "active": True,
                    "events": ["push"],
                    "config": {
                        "url": webhook_url,
                        "content_type": "json",
                        "secret": repo.webhook_secret
                    }
                }
            else:  # GitLab
                url = f"https://gitlab.com/api/v4/projects/{self._extract_gitlab_project_id(repo.url)}/hooks"
                headers = {
                    "Authorization": f"Bearer {repo.token}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "url": webhook_url,
                    "push_events": True,
                    "token": repo.webhook_secret
                }
            
            async with session.post(url, headers=headers, json=payload) as response:
                return response.status in [200, 201]
                
        except Exception as e:
            print(f"Error setting up webhook: {e}")
            return False
    
    def _extract_repo_path(self, url: str) -> str:
        """Extract owner/repo from URL"""
        # Remove .git suffix and extract path
        clean_url = str(url).replace('.git', '')
        if 'github.com' in clean_url or 'gitlab.com' in clean_url:
            parts = clean_url.split('/')
            return f"{parts[-2]}/{parts[-1]}"
        return ""
    
    def _extract_gitlab_project_id(self, url: str) -> str:
        """Extract GitLab project ID from URL"""
        # For simplicity, use URL encoding of owner/repo
        repo_path = self._extract_repo_path(url)
        return repo_path.replace('/', '%2F')

# Singleton instance
git_provider_service = GitProviderService()
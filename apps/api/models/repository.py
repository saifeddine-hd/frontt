from pydantic import BaseModel, HttpUrl
from enum import Enum
from datetime import datetime
from typing import Optional

class RepositoryProvider(str, Enum):
    GITHUB = "github"
    GITLAB = "gitlab"

class RepositoryStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"

class Repository(BaseModel):
    id: Optional[str] = None
    url: HttpUrl
    provider: RepositoryProvider
    name: str
    token: str  # Encrypted in storage
    status: RepositoryStatus = RepositoryStatus.ACTIVE
    webhook_secret: Optional[str] = None
    discord_webhook_url: Optional[HttpUrl] = None
    last_scan: Optional[datetime] = None
    last_scan_status: Optional[str] = None
    findings_count: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        use_enum_values = True

class RepositoryCreate(BaseModel):
    url: HttpUrl
    provider: RepositoryProvider
    name: str
    token: str
    discord_webhook_url: Optional[HttpUrl] = None

class RepositoryUpdate(BaseModel):
    name: Optional[str] = None
    token: Optional[str] = None
    status: Optional[RepositoryStatus] = None
    discord_webhook_url: Optional[HttpUrl] = None
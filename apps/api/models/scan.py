from pydantic import BaseModel
from enum import Enum
from datetime import datetime
from typing import Optional

class ScanStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class ScanJob(BaseModel):
    id: str
    filename: str
    status: ScanStatus
    created_at: datetime
    completed_at: Optional[datetime] = None
    findings_count: Optional[int] = None
    error: Optional[str] = None
    
    class Config:
        use_enum_values = True
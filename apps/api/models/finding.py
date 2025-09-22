from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class Finding(BaseModel):
    id: Optional[str] = None
    job_id: str
    file_path: str
    line_number: int
    secret_type: str
    secret: str
    severity: str  # critical, high, medium, low
    rule_id: str
    confidence: float
    created_at: Optional[datetime] = None
    
    class Config:
        use_enum_values = True
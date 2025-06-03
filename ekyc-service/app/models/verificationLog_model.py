from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class VerificationLogSchema(BaseModel):
    userId: str
    stepPassed: bool = False
    liveness: Optional[dict] = None
    faceMatch: Optional[dict] = None
    voice: Optional[dict] = None
    timestamp: datetime = datetime.utcnow()

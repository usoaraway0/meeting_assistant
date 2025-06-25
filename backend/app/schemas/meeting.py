from pydantic import BaseModel
from typing import List, Optional

class JobResponse(BaseModel):
    job_id: str
    message: str

class StatusResponse(BaseModel):
    job_id: str
    status: str
    summary: Optional[str] = None
    action_items: Optional[List[str]] = None
    transcript: Optional[str] = None

class AskRequest(BaseModel):
    question: str

class AskResponse(BaseModel):
    answer: str
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class ChatQuery(BaseModel):
    text: str

class ChatResponse(BaseModel):
    answer: str
    sources: List[str] = []

class ChatHistory(BaseModel):
    user_id: str
    query: str
    response: str
    timestamp: datetime

    class Config:
        from_attributes = True 
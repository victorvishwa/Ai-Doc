from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class DocumentBase(BaseModel):
    filename: str
    content: str
    processed_content: str
    uploaded_by: str
    upload_date: datetime

class DocumentCreate(DocumentBase):
    pass

class DocumentResponse(BaseModel):
    id: str
    filename: str
    upload_date: datetime

    class Config:
        from_attributes = True

class DocumentInDB(DocumentBase):
    id: str 
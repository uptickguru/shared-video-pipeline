from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.orm import declarative_base
from pydantic import BaseModel, Field

Base = declarative_base()

# --- SQLAlchemy Models (Database) ---

class JobRecord(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    job_type = Column(String, index=True) # e.g., "video", "text"
    provider = Column(String, index=True) # e.g., "wan", "kling", "gemini", "openai"
    engine = Column(String) # e.g., specific model name
    prompt = Column(Text, nullable=False)
    
    status = Column(String, default="pending", index=True) # pending, queued, processing, completed, failed
    priority = Column(String, default="normal") # normal, high
    emergency = Column(Boolean, default=False)
    direct_to_vast = Column(Boolean, default=False)
    
    asset_path = Column(String, nullable=True)
    error_message = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


# --- Pydantic Models (API) ---

class JobCreateRequest(BaseModel):
    job_type: str = Field(..., description="'video' or 'text'")
    provider: str = Field(..., description="Provider name e.g., 'wan', 'openai'")
    engine: str = Field(..., description="Specific engine/model to use")
    prompt: str = Field(..., description="Prompt for generation")
    priority: str = Field("normal", description="'normal' or 'high'")
    emergency: bool = Field(False, description="Bypass queue wait, go direct")
    direct_to_vast: bool = Field(False, description="Flag for video jobs to go straight to Vast without waiting for a full load if true")

class JobResponse(BaseModel):
    id: int
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True

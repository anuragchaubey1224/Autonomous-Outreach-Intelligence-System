"""
Campaign State Models

Defines the core state schema for campaign execution.
Minimal, focused on what flows through agents.
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field


class Lead(BaseModel):
    """Represents a single lead in the campaign."""
    
    email: EmailStr
    first_name: Optional[str] = None
    company: Optional[str] = None


class Message(BaseModel):
    """Represents a generated message for a lead."""
    
    lead_email: EmailStr
    body: str
    status: str = Field(default="pending", description="pending|approved|sent|failed")


class CampaignState(BaseModel):
    """
    Core state object for campaign execution.
    
    Flows through agents, updated atomically.
    All agents read from and write to this state.
    """
    
    campaign_id: str
    leads: List[Lead]
    messages: List[Message] = Field(default_factory=list)
    status: str = Field(default="initialized", description="initialized|running|completed|failed")
    created_at: datetime

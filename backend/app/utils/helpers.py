"""
Campaign Helper Functions

Simple utilities for campaign initialization and state creation.
"""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List

from app.graph.state import CampaignState, Lead


def create_initial_state(leads_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Initialize a campaign state from raw lead data.
    
    Args:
        leads_data: List of dictionaries with lead info
                   e.g., [{"email": "test@gmail.com", "first_name": "John"}]
    
    Returns:
        Dictionary compatible with CampaignState
    """
    
    # Generate unique campaign ID
    campaign_id = f"camp_{datetime.now().strftime('%Y%m%d')}_{uuid.uuid4().hex[:6]}"
    
    # Get current UTC time
    created_at = datetime.now(timezone.utc)
    
    # Convert lead dicts to Lead objects
    leads = [
        Lead(
            email=lead.get("email"),
            first_name=lead.get("first_name"),
            company=lead.get("company")
        )
        for lead in leads_data
    ]
    
    # Build state dict
    state_dict = {
        "campaign_id": campaign_id,
        "leads": leads,
        "messages": [],
        "status": "initialized",
        "execution_mode": "sync",
        "message_status": {},
        "errors": [],
        "human_approved": False,
        "created_at": created_at,
        "updated_at": created_at,
    }
    
    return state_dict

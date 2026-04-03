from typing import Optional

from app.graph.state import CampaignState

campaign_store: dict[str, CampaignState] = {}


def save_campaign(state: CampaignState) -> None:
    campaign_store[state.campaign_id] = state


def get_campaign(campaign_id: str) -> Optional[CampaignState]:
    return campaign_store.get(campaign_id)


def update_campaign(state: CampaignState) -> None:
    campaign_store[state.campaign_id] = state

from uuid import uuid4

from fastapi import APIRouter
from pydantic import BaseModel


router = APIRouter()


class StartCampaignRequest(BaseModel):
	query: str
	tone: str
	num_leads: int


@router.post("/start-campaign")
def start_campaign(payload: StartCampaignRequest) -> dict[str, str]:
	return {
		"campaign_id": str(uuid4()),
		"status": "started",
	}

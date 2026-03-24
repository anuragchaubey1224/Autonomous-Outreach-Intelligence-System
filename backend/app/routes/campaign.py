from typing import Any, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.agents.lead_agent import lead_agent
from app.agents.message_agent import message_agent
from app.graph.state import CampaignState
from app.utils.helpers import create_initial_state


router = APIRouter()


class StartCampaignRequest(BaseModel):
	leads: list[dict[str, Optional[str]]]


@router.post("/start-campaign")
def start_campaign(payload: StartCampaignRequest) -> dict[str, Any]:
	if not payload.leads:
		raise HTTPException(status_code=400, detail="No leads provided")

	print("Campaign started")

	try:
		initial_state = create_initial_state(payload.leads)
		state = CampaignState(**initial_state)
	except Exception as exc:
		raise HTTPException(status_code=400, detail=f"Invalid input: {exc}") from exc

	state = lead_agent(state)
	print("Leads processed")

	state = message_agent(state)
	print("Messages generated")

	state_data = state.model_dump(mode="json")
	return {
		"campaign_id": state_data["campaign_id"],
		"status": state_data["status"],
		"leads": state_data["leads"],
		"messages": state_data["messages"],
	}

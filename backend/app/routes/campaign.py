import threading
from typing import Any, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.agents.lead_agent import lead_agent
from app.agents.message_agent import generate_text, message_agent
from app.graph.state import CampaignState, transition_to
from app.services.campaign_store import get_campaign, save_campaign, update_campaign
from app.tools.email_tool import send_email
from app.utils.helpers import create_initial_state


router = APIRouter()


class StartCampaignRequest(BaseModel):
	leads: list[dict[str, Optional[str]]]


class ApproveMessagesRequest(BaseModel):
	message_indexes: list[int]


class EditMessageRequest(BaseModel):
	body: str


def send_emails_background(campaign_id: str) -> None:
	print("Background email sending started")
	print(f"Processing campaign: {campaign_id}")

	state = get_campaign(campaign_id)
	if state is None:
		return

	for message in state.messages:
		if message.status != "approved":
			continue

		print(f"Sending email to {message.lead_email}")
		try:
			ok = send_email(
				to_email=str(message.lead_email),
				subject="Quick connect",
				body=message.body,
			)
			if ok:
				message.status = "sent"
				for idx, msg in enumerate(state.messages):
					if msg is message:
						state.message_status[str(idx)] = "sent"
						break
				print("Email sent successfully")
			else:
				print("Email failed")
		except Exception as exc:
			print(f"Email failed: {exc}")
			continue

	if state.status == "sending":
		transition_to(state, "active")

	update_campaign(state)


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

	try:
		transition_to(state, "pending_approval")
	except ValueError as exc:
		raise HTTPException(status_code=400, detail=str(exc)) from exc

	save_campaign(state)
	print("Campaign saved")

	state_data = state.model_dump(mode="json")
	return {
		"campaign_id": state_data["campaign_id"],
		"status": state_data["status"],
		"leads": state_data["leads"],
		"messages": state_data["messages"],
	}


@router.get("/campaigns/{campaign_id}")
def fetch_campaign(campaign_id: str) -> dict[str, Any]:
	state = get_campaign(campaign_id)
	if state is None:
		raise HTTPException(status_code=404, detail="Campaign not found")

	print("Campaign fetched")

	state_data = state.model_dump(mode="json")
	return {
		"campaign_id": state_data["campaign_id"],
		"status": state_data["status"],
		"leads": state_data["leads"],
		"messages": state_data["messages"],
	}


@router.post("/campaigns/{campaign_id}/approve")
def approve_messages(campaign_id: str, payload: ApproveMessagesRequest) -> dict[str, Any]:
	state = get_campaign(campaign_id)
	if state is None:
		raise HTTPException(status_code=404, detail="Campaign not found")

	if not payload.message_indexes:
		raise HTTPException(status_code=400, detail="message_indexes cannot be empty")

	if state.status != "pending_approval":
		raise HTTPException(status_code=400, detail="Messages can only be approved in pending_approval status")

	print("Approving messages")

	approved_messages: list[dict[str, Any]] = []
	total_messages = len(state.messages)

	for index in payload.message_indexes:
		if 0 <= index < total_messages:
			state.messages[index].status = "approved"
			state.message_status[str(index)] = "approved"
			approved_messages.append({
				"index": index,
				"lead_email": str(state.messages[index].lead_email),
				"status": state.messages[index].status,
			})

	state.human_approved = len(approved_messages) > 0

	update_campaign(state)
	print("Messages approved successfully")

	return {
		"campaign_id": state.campaign_id,
		"approved_messages": approved_messages,
		"total_messages": total_messages,
	}


@router.put("/campaigns/{campaign_id}/messages/{index}")
def edit_message(campaign_id: str, index: int, payload: EditMessageRequest) -> dict[str, Any]:
	state = get_campaign(campaign_id)
	if state is None:
		raise HTTPException(status_code=404, detail="Campaign not found")

	if index < 0 or index >= len(state.messages):
		raise HTTPException(status_code=400, detail="Invalid message index")

	print("Editing message")

	state.messages[index].body = payload.body
	state.messages[index].status = "pending"
	state.message_status[str(index)] = "pending"
	state.human_approved = False

	update_campaign(state)
	print("Message updated successfully")

	return {
		"campaign_id": state.campaign_id,
		"updated_message": state.messages[index].model_dump(mode="json"),
	}


@router.post("/campaigns/{campaign_id}/regenerate/{index}")
def regenerate_message(campaign_id: str, index: int) -> dict[str, Any]:
	state = get_campaign(campaign_id)
	if state is None:
		raise HTTPException(status_code=404, detail="Campaign not found")

	if index < 0 or index >= len(state.messages):
		raise HTTPException(status_code=400, detail="Invalid message index")

	if index >= len(state.leads):
		raise HTTPException(status_code=400, detail="No corresponding lead for message index")

	print("Regenerating message")

	lead = state.leads[index]
	first_name = lead.first_name.strip() if isinstance(lead.first_name, str) and lead.first_name.strip() else "there"
	prompt = (
		f"Write a short professional outreach email to {first_name}. "
		"Introduce yourself briefly and ask for a quick chat."
	)

	try:
		new_body = generate_text(prompt)
	except Exception:
		new_body = "Hi, I'd love to connect with you."

	state.messages[index].body = new_body
	state.messages[index].status = "pending"
	state.message_status[str(index)] = "pending"
	state.human_approved = False

	update_campaign(state)
	print("Message regenerated successfully")

	return {
		"campaign_id": state.campaign_id,
		"regenerated_message": state.messages[index].model_dump(mode="json"),
	}


@router.post("/campaigns/{campaign_id}/send")
def send_campaign_messages(campaign_id: str) -> dict[str, Any]:
	state = get_campaign(campaign_id)
	if state is None:
		raise HTTPException(status_code=404, detail="Campaign not found")

	approved_indexes = [
		idx for idx, message in enumerate(state.messages) if message.status == "approved"
	]

	if not approved_indexes:
		raise HTTPException(status_code=400, detail="No approved messages to send")

	if len(approved_indexes) > 5:
		raise HTTPException(status_code=400, detail="Safety limit exceeded: max 5 approved messages per send")

	if state.status != "pending_approval":
		raise HTTPException(status_code=400, detail="Campaign must be in pending_approval status before send")

	if not state.human_approved:
		raise HTTPException(status_code=400, detail="Campaign requires human approval before send")

	try:
		transition_to(state, "sending")
	except ValueError as exc:
		raise HTTPException(status_code=400, detail=str(exc)) from exc

	update_campaign(state)

	thread = threading.Thread(
		target=send_emails_background,
		args=(campaign_id,),
		daemon=True,
	)
	thread.start()

	return {
		"message": "Email sending started in background",
		"campaign_id": state.campaign_id,
	}

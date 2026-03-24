"""Message Agent: generates simple outreach messages per lead."""

from app.graph.state import CampaignState, Message


def generate_text(prompt: str) -> str:
	"""Mock LLM text generator for local development."""
	return (
		"Hi, I am reaching out because I would value a short conversation with you. "
		"If you are open to it, could we schedule a quick chat this week?"
	)


def message_agent(state: CampaignState) -> CampaignState:
	"""
	Generate one outreach message for each lead.

	- Uses first_name if available, otherwise "there"
	- Appends Message objects to state.messages
	- Sets state.status to "messages_generated"
	- Uses fallback body if generate_text raises an exception
	"""
	if not state.leads:
		return state

	for lead in state.leads:
		first_name = lead.first_name.strip() if isinstance(lead.first_name, str) and lead.first_name.strip() else "there"
		prompt = (
			f"Write a short professional outreach email to {first_name}. "
			"Introduce yourself briefly and ask for a quick chat."
		)

		try:
			body = generate_text(prompt)
		except Exception:
			body = "Hi, I'd love to connect with you for a quick discussion."

		state.messages.append(
			Message(
				lead_email=str(lead.email),
				body=body,
				status="pending",
			)
		)

	state.status = "messages_generated"
	return state

"""Lead Agent: cleans and validates incoming leads."""

from app.graph.state import CampaignState, Lead


def _is_simple_valid_email(email: str) -> bool:
	"""Minimal email validation: contains '@' and '.' after '@'."""
	if "@" not in email:
		return False
	local, _, domain = email.partition("@")
	return bool(local) and "." in domain


def lead_agent(state: CampaignState) -> CampaignState:
	"""
	Clean and validate leads in campaign state.

	- Skip invalid emails
	- Deduplicate by normalized email (keep first)
	- Trim whitespace and lowercase email
	- Update state.status to "leads_processed"
	"""
	seen_emails: set[str] = set()
	cleaned_leads: list[Lead] = []

	for lead in state.leads:
		normalized_email = str(lead.email).strip().lower()

		if not _is_simple_valid_email(normalized_email):
			print(f"Skipping invalid email: {lead.email}")
			continue

		if normalized_email in seen_emails:
			continue

		seen_emails.add(normalized_email)
		cleaned_leads.append(
			Lead(
				email=normalized_email,
				first_name=lead.first_name.strip() if isinstance(lead.first_name, str) else lead.first_name,
				company=lead.company.strip() if isinstance(lead.company, str) else lead.company,
			)
		)

	state.leads = cleaned_leads
	state.status = "leads_processed"
	return state

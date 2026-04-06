import email
import imaplib
import os
import time
from email.utils import parseaddr

from dotenv import load_dotenv

from app.agents.decision_agent import classify_reply
from app.services.campaign_store import campaign_store, update_campaign


load_dotenv()


def _extract_reply_text(parsed_email: email.message.Message) -> str:
    """Extract plain-text body from an email message."""
    if parsed_email.is_multipart():
        for part in parsed_email.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition", "")).lower()
            if content_type == "text/plain" and "attachment" not in content_disposition:
                payload = part.get_payload(decode=True)
                if payload:
                    return payload.decode(errors="ignore")
        return ""

    payload = parsed_email.get_payload(decode=True)
    if payload:
        return payload.decode(errors="ignore")
    return ""


def check_replies() -> None:
    """Poll Gmail inbox and mark matching sent messages as replied."""
    print("Checking for replies...")

    email_address = (os.getenv("EMAIL_ADDRESS") or "").strip()
    password = (os.getenv("EMAIL_PASSWORD") or "").replace(" ", "")

    if not email_address or not password:
        print("Reply check skipped: EMAIL_ADDRESS or EMAIL_PASSWORD missing")
        return

    try:
        with imaplib.IMAP4_SSL("imap.gmail.com", 993) as imap:
            imap.login(email_address, password)
            imap.select("inbox")

            status, data = imap.search(None, "ALL")
            if status != "OK" or not data or not data[0]:
                return

            email_ids = data[0].split()[-10:]

            for email_id in email_ids:
                fetch_status, msg_data = imap.fetch(email_id, "(RFC822)")
                if fetch_status != "OK" or not msg_data:
                    continue

                raw_email = msg_data[0][1]
                parsed_email = email.message_from_bytes(raw_email)
                from_header = parsed_email.get("From", "")
                sender_email = parseaddr(from_header)[1].strip().lower()
                reply_text = _extract_reply_text(parsed_email)

                if not sender_email:
                    continue

                for campaign_id, state in list(campaign_store.items()):
                    campaign_updated = False
                    for message_obj in state.messages:
                        if message_obj.status == "sent" and str(message_obj.lead_email).lower() == sender_email:
                            print(f"Reply detected from {sender_email}")
                            message_obj.status = "replied"
                            message_obj.intent = classify_reply(reply_text)
                            print("Message marked as replied")
                            campaign_updated = True

                    if campaign_updated:
                        update_campaign(state)

    except Exception as exc:
        print(f"Reply check failed: {exc}")


def start_reply_listener() -> None:
    """Continuously poll inbox every 30 seconds for replies."""
    while True:
        try:
            check_replies()
        except Exception as exc:
            print(f"Reply listener error: {exc}")
        time.sleep(30)

import os
import smtplib
from email.mime.text import MIMEText

from dotenv import load_dotenv


load_dotenv()


def send_email(to_email: str, subject: str, body: str) -> bool:
	"""Send a single email using Gmail SMTP. Returns True on success, else False."""
	from_email = (os.getenv("EMAIL_ADDRESS") or "").strip()
	# Gmail App Passwords are often copied with spaces; normalize it.
	password = (os.getenv("EMAIL_PASSWORD") or "").replace(" ", "")

	if not from_email or not password:
		print("Email failed: EMAIL_ADDRESS or EMAIL_PASSWORD is missing")
		return False

	if "@" not in to_email or "." not in to_email:
		print(f"Email failed: invalid recipient email '{to_email}'")
		return False

	msg = MIMEText(body)
	msg["Subject"] = subject
	msg["From"] = from_email
	msg["To"] = to_email

	try:
		with smtplib.SMTP("smtp.gmail.com", 587, timeout=20) as server:
			server.ehlo()
			server.starttls()
			server.ehlo()
			server.login(from_email, password)
			server.sendmail(from_email, [to_email], msg.as_string())
		return True
	except Exception as exc:
		print(f"Email failed: {exc}")
		return False

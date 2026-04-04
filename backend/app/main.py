import threading

from fastapi import FastAPI, Response

from dotenv import load_dotenv
import os

load_dotenv()

EMAIL = os.getenv("EMAIL_ADDRESS")
PASSWORD = os.getenv("EMAIL_PASSWORD")

from app.routes.campaign import router as campaign_router
from app.routes.health import router as health_router
from app.tools.email_reader import start_reply_listener


app = FastAPI(title="Autonomous Outreach Intelligence System")

app.include_router(health_router)
app.include_router(campaign_router)

_reply_listener_started = False


@app.on_event("startup")
def start_background_reply_listener() -> None:
	global _reply_listener_started
	if _reply_listener_started:
		return

	thread = threading.Thread(target=start_reply_listener, daemon=True)
	thread.start()
	_reply_listener_started = True


@app.get("/", include_in_schema=False)
def root() -> dict[str, str]:
	return {"status": "ok"}


@app.get("/favicon.ico", include_in_schema=False)
def favicon() -> Response:
	return Response(status_code=204)


@app.get("/apple-touch-icon.png", include_in_schema=False)
@app.get("/apple-touch-icon-precomposed.png", include_in_schema=False)
def apple_touch_icon() -> Response:
	return Response(status_code=204)

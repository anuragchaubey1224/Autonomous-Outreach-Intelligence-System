from fastapi import FastAPI, Response

from app.routes.campaign import router as campaign_router
from app.routes.health import router as health_router


app = FastAPI(title="Autonomous Outreach Intelligence System")

app.include_router(health_router)
app.include_router(campaign_router)


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

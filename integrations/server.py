"""Minimal FastAPI webhook server. Receipt is deterministic; agents run later."""

from __future__ import annotations

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse, PlainTextResponse

from integrations.providers import adyen, gmail, outlook, stripe, xero
from integrations.providers.outlook import validation_response

app = FastAPI(title="Office of the CFO integrations", version="0.1.0")


def _headers(request: Request) -> dict[str, str]:
    return {key: value for key, value in request.headers.items()}


@app.get("/health")
def health():
    return {"ok": True, "mode": "integrations"}


@app.post("/webhooks/stripe")
async def stripe_webhook(request: Request):
    raw = await request.body()
    result = stripe.process_raw(raw, _headers(request))
    if result.status == "rejected":
        return JSONResponse({"error": result.message}, status_code=400)
    return {"received": True, "status": result.status, "payout_id": result.payout_id}


@app.post("/webhooks/adyen")
async def adyen_webhook(request: Request):
    raw = await request.body()
    result = adyen.process_raw(raw, _headers(request))
    if result.status == "rejected":
        return JSONResponse({"error": result.message}, status_code=401)
    # Official guidance: 200/202 within 10s before business logic. We already processed mock work.
    return JSONResponse({"notificationResponse": "[accepted]"}, status_code=200)


@app.post("/webhooks/gmail")
async def gmail_webhook(request: Request):
    raw = await request.body()
    result = gmail.process_raw(raw, _headers(request), require_signature=False)
    if result.status == "rejected":
        return JSONResponse({"error": result.message}, status_code=401)
    return {"received": True, "status": result.status}


@app.post("/webhooks/outlook")
async def outlook_webhook(request: Request):
    token = request.query_params.get("validationToken")
    if token:
        return PlainTextResponse(validation_response(token), media_type="text/plain")
    raw = await request.body()
    result = outlook.process_raw(raw, _headers(request))
    if result.status == "rejected":
        return JSONResponse({"error": result.message}, status_code=401)
    return {"received": True, "status": result.status}


@app.post("/webhooks/xero")
async def xero_webhook(request: Request):
    raw = await request.body()
    result = xero.process_raw(raw, _headers(request))
    if result.status == "rejected":
        return Response(status_code=401)
    return Response(status_code=200)

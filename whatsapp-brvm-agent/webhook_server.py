#!/usr/bin/env python3
"""Serveur webhook WhatsApp: recoit les messages entrants et repond via
l'assistant conversationnel (brvm_agent.assistant), quel que soit le
message envoye par l'utilisateur ("quoi de beau aujourd'hui ?", etc).

A la difference de check_news.py / send_recap.py (qui poussent des alertes
automatiques et doivent tourner sur un cron), ce serveur doit rester actif
en permanence et etre joignable en HTTPS par Meta -- voir le README pour
les options d'hebergement.

Lancement local:
    uvicorn webhook_server:app --host 0.0.0.0 --port 8000
"""
from __future__ import annotations

import hashlib
import hmac
import logging

from fastapi import FastAPI, Request, Response
from fastapi.responses import PlainTextResponse

from brvm_agent import scheduler as brvm_scheduler
from brvm_agent.assistant import answer
from brvm_agent.config import CONFIG
from brvm_agent.subscribers import Subscribers
from brvm_agent.whatsapp import WhatsAppClient

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(title="Agent WhatsApp BRVM")

UNSUBSCRIBE_KEYWORDS = {"stop", "arret", "arrêt", "desabonner", "désabonner"}

WELCOME_MESSAGE = (
    "Bienvenue sur l'agent BRVM ! \U0001F4C8\n\n"
    "Tu es maintenant abonne(e) et tu recevras automatiquement :\n"
    "- une alerte des qu'une nouvelle annonce/communique BRVM est publiee\n"
    "- le recapitulatif + le Bulletin Officiel de la Cote (BOC) a la cloture "
    "de chaque seance\n\n"
    "Tu peux aussi me poser n'importe quelle question sur la BRVM a tout "
    "moment, je te repondrai directement ici.\n\n"
    "Pour te desabonner a tout moment, ecris STOP."
)


@app.on_event("startup")
def _on_startup() -> None:
    brvm_scheduler.start()


@app.on_event("shutdown")
def _on_shutdown() -> None:
    brvm_scheduler.stop()


def _verify_signature(raw_body: bytes, signature_header: str | None) -> bool:
    """Verifie l'en-tete X-Hub-Signature-256 envoye par Meta, pour s'assurer
    que la requete provient bien de WhatsApp (et pas d'un tiers qui
    declencherait des appels payants a l'API Claude / WhatsApp).
    Si WHATSAPP_APP_SECRET n'est pas configure, la verification est
    ignorée (deconseille en production)."""
    if not CONFIG.whatsapp_app_secret:
        logger.warning(
            "WHATSAPP_APP_SECRET non configure: la signature des requetes entrantes "
            "n'est pas verifiee. A eviter en production."
        )
        return True

    if not signature_header or not signature_header.startswith("sha256="):
        return False

    expected = hmac.new(
        CONFIG.whatsapp_app_secret.encode("utf-8"), raw_body, hashlib.sha256
    ).hexdigest()
    provided = signature_header.removeprefix("sha256=")
    return hmac.compare_digest(expected, provided)


@app.get("/webhook")
async def verify_webhook(request: Request) -> Response:
    params = request.query_params
    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")

    if mode == "subscribe" and token == CONFIG.whatsapp_verify_token and CONFIG.whatsapp_verify_token:
        logger.info("Verification du webhook reussie.")
        return PlainTextResponse(challenge or "")

    logger.warning("Echec de verification du webhook (token invalide).")
    return PlainTextResponse("Verification token invalide", status_code=403)


@app.post("/webhook")
async def receive_webhook(request: Request) -> Response:
    raw_body = await request.body()
    signature = request.headers.get("X-Hub-Signature-256")

    if not _verify_signature(raw_body, signature):
        logger.warning("Signature invalide sur une requete webhook entrante -- rejetee.")
        return Response(status_code=403)

    payload = await request.json()

    try:
        _handle_payload(payload)
    except Exception:  # noqa: BLE001
        # On ne remonte jamais d'erreur 5xx a Meta pour un message individuel
        # en echec, sinon Meta reessaie en boucle. On journalise et on
        # acquitte quand meme.
        logger.exception("Erreur lors du traitement d'un message entrant")

    return Response(status_code=200)


def _handle_payload(payload: dict) -> None:
    for entry in payload.get("entry", []):
        for change in entry.get("changes", []):
            value = change.get("value", {})
            for message in value.get("messages", []):
                _handle_message(message)


def _handle_message(message: dict) -> None:
    sender = message.get("from")
    msg_type = message.get("type")

    if not sender:
        return

    client = WhatsAppClient(
        token=CONFIG.whatsapp_token,
        phone_number_id=CONFIG.whatsapp_phone_number_id,
        api_version=CONFIG.whatsapp_api_version,
    )
    subscribers = Subscribers(CONFIG.subscribers_file)

    if msg_type == "text":
        user_text = message.get("text", {}).get("body", "").strip()
        logger.info("Message recu de %s: %s", sender, user_text)

        if user_text.lower() in UNSUBSCRIBE_KEYWORDS:
            subscribers.remove(sender)
            client.send_text(
                to=sender,
                body="Tu es desabonne(e) des alertes BRVM. Ecris-moi n'importe quoi pour te reabonner a tout moment.",
            )
            return

        # Premier message de ce numero -> auto-abonnement + message de bienvenue.
        if subscribers.add(sender):
            client.send_text(to=sender, body=WELCOME_MESSAGE)

        reply_text = answer(user_text)
    else:
        subscribers.add(sender)
        reply_text = (
            "Pour l'instant je ne comprends que le texte. "
            "Pose-moi une question, ex: \"quoi de beau aujourd'hui sur la BRVM ?\""
        )

    # Reponse a un message recu il y a quelques secondes -> toujours dans la
    # fenetre de 24h, le texte libre est donc autorise (pas besoin de template).
    client.send_text(to=sender, body=reply_text)


CONFIG.validate_for_webhook()

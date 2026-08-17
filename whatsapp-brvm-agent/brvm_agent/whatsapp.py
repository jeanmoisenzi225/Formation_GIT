"""Client minimal pour l'API WhatsApp Cloud (Meta for Developers).

Important: pour envoyer un message a un utilisateur en dehors de la fenetre
de 24h suivant son dernier message (ce qui sera systematiquement le cas pour
des alertes automatiques quotidiennes), Meta impose l'utilisation d'un
"message template" pre-approuve. Voir le README pour la marche a suivre.
"""
from __future__ import annotations

import logging

import requests

logger = logging.getLogger(__name__)

REQUEST_TIMEOUT = 30


class WhatsAppClient:
    def __init__(self, token: str, phone_number_id: str, api_version: str = "v20.0"):
        self.token = token
        self.phone_number_id = phone_number_id
        self.api_version = api_version

    @property
    def _base_url(self) -> str:
        return f"https://graph.facebook.com/{self.api_version}/{self.phone_number_id}/messages"

    def _post(self, payload: dict) -> dict:
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }
        response = requests.post(self._base_url, json=payload, headers=headers, timeout=REQUEST_TIMEOUT)
        if not response.ok:
            logger.error("Echec envoi WhatsApp: %s %s", response.status_code, response.text)
        response.raise_for_status()
        return response.json()

    def send_text(self, to: str, body: str) -> dict:
        """Message texte libre. Ne fonctionne que dans la fenetre de 24h
        suivant un message recu de la part de ce destinataire."""
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "text",
            "text": {"body": body, "preview_url": False},
        }
        return self._post(payload)

    def send_template(
        self,
        to: str,
        template_name: str,
        language_code: str,
        body_params: list[str] | None = None,
        header_document_url: str | None = None,
        header_document_filename: str | None = None,
    ) -> dict:
        """Message a partir d'un template approuve par Meta. Fonctionne a
        tout moment, y compris hors fenetre de 24h -- c'est le mode a
        utiliser pour les alertes automatiques.

        Si le template defini dans Meta Business Manager a un en-tete de
        type "Document" (ex: pour joindre le PDF du BOC), passer
        header_document_url pour le renseigner dynamiquement.
        """
        components = []
        if header_document_url:
            components.append(
                {
                    "type": "header",
                    "parameters": [
                        {
                            "type": "document",
                            "document": {
                                "link": header_document_url,
                                "filename": header_document_filename or "document.pdf",
                            },
                        }
                    ],
                }
            )
        if body_params:
            components.append(
                {
                    "type": "body",
                    "parameters": [{"type": "text", "text": p} for p in body_params],
                }
            )
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {"code": language_code},
                "components": components,
            },
        }
        return self._post(payload)

    def send_document_link(self, to: str, document_url: str, filename: str, caption: str = "") -> dict:
        """Envoie un document (ex: le PDF du BOC) depuis son URL publique.
        Comme send_text, necessite la fenetre de 24h."""
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "document",
            "document": {"link": document_url, "filename": filename, "caption": caption},
        }
        return self._post(payload)

#!/usr/bin/env python3
"""A lancer une fois par jour apres la cloture de la seance BRVM
(la seance se termine generalement autour de 15h/16h GMT selon le calendrier
BRVM -- ajuster le cron en consequence). Recupere le dernier Bulletin
Officiel de la Cote (BOC), en extrait un resume chiffre, et l'envoie sur
WhatsApp accompagne du PDF officiel.
"""
from __future__ import annotations

import logging
import sys

from brvm_agent.boc import download_pdf, fetch_latest_boc, format_recap_message, summarize_boc_pdf
from brvm_agent.config import CONFIG
from brvm_agent.state import State
from brvm_agent.whatsapp import WhatsAppClient

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def main() -> int:
    CONFIG.validate_for_sending()
    state = State.load(CONFIG.state_file)

    bulletin = fetch_latest_boc(CONFIG.brvm_base_url)
    if bulletin is None:
        logger.warning("Aucun BOC trouve sur le site BRVM.")
        return 0

    if bulletin.date and bulletin.date == state.last_boc_date:
        logger.info("BOC du %s deja envoye, rien a faire.", bulletin.date)
        return 0

    pdf_bytes = download_pdf(bulletin.pdf_url)
    summary = summarize_boc_pdf(pdf_bytes)
    message = format_recap_message(bulletin, summary)

    client = WhatsAppClient(
        token=CONFIG.whatsapp_token,
        phone_number_id=CONFIG.whatsapp_phone_number_id,
        api_version=CONFIG.whatsapp_api_version,
    )

    for recipient in CONFIG.whatsapp_recipients:
        try:
            if CONFIG.whatsapp_use_templates:
                body_params = [
                    bulletin.title,
                    f"{summary.composite_value or 'N/A'} ({summary.composite_change or 'N/A'})",
                    f"{summary.brvm30_value or 'N/A'} ({summary.brvm30_change or 'N/A'})",
                ]
                client.send_template(
                    to=recipient,
                    template_name=CONFIG.whatsapp_recap_template_name,
                    language_code=CONFIG.whatsapp_template_lang,
                    body_params=body_params,
                    header_document_url=bulletin.pdf_url,
                    header_document_filename=f"BOC_{bulletin.date}.pdf",
                )
            else:
                client.send_text(to=recipient, body=message)
                client.send_document_link(
                    to=recipient,
                    document_url=bulletin.pdf_url,
                    filename=f"BOC_{bulletin.date}.pdf",
                    caption=bulletin.title,
                )
        except Exception:  # noqa: BLE001
            logger.exception("Echec d'envoi du recap vers %s", recipient)

    state.last_boc_date = bulletin.date
    state.save(CONFIG.state_file)
    return 0


if __name__ == "__main__":
    sys.exit(main())

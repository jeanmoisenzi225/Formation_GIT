#!/usr/bin/env python3
"""A lancer regulierement (ex: toutes les 15-30 min via cron) pendant les
heures ouvrees de la BRVM. Recupere les nouvelles annonces publiees sur
brvm.org et envoie une alerte WhatsApp pour chaque annonce non deja
envoyee.
"""
from __future__ import annotations

import logging
import sys

from brvm_agent.config import CONFIG
from brvm_agent.news import fetch_all_news, format_news_message
from brvm_agent.state import State
from brvm_agent.whatsapp import WhatsAppClient

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def main() -> int:
    CONFIG.validate_for_sending()
    state = State.load(CONFIG.state_file)
    client = WhatsAppClient(
        token=CONFIG.whatsapp_token,
        phone_number_id=CONFIG.whatsapp_phone_number_id,
        api_version=CONFIG.whatsapp_api_version,
    )

    items = fetch_all_news(CONFIG.brvm_base_url, CONFIG.brvm_news_categories)
    new_items = [item for item in items if not state.has_sent_news(item.url)]

    if not new_items:
        logger.info("Aucune nouvelle annonce.")
        return 0

    logger.info("%d nouvelle(s) annonce(s) a envoyer.", len(new_items))

    for item in new_items:
        message = format_news_message(item)
        for recipient in CONFIG.whatsapp_recipients:
            try:
                if CONFIG.whatsapp_use_templates:
                    client.send_template(
                        to=recipient,
                        template_name=CONFIG.whatsapp_news_template_name,
                        language_code=CONFIG.whatsapp_template_lang,
                        body_params=[item.company or "BRVM", item.title, item.url],
                    )
                else:
                    client.send_text(to=recipient, body=message)
            except Exception:  # noqa: BLE001
                logger.exception("Echec d'envoi vers %s pour %s", recipient, item.url)
        state.mark_news_sent(item.url)
        state.save(CONFIG.state_file)

    return 0


if __name__ == "__main__":
    sys.exit(main())

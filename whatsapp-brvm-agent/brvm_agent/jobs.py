"""Logique d'envoi partagee entre les scripts CLI (check_news.py,
send_recap.py) et le planificateur integre au webhook
(brvm_agent.scheduler). Les destinataires sont la liste dynamique des
abonnes (brvm_agent.subscribers) + les numeros fixes de WHATSAPP_RECIPIENTS.
"""
from __future__ import annotations

import logging

from .boc import download_pdf, fetch_latest_boc, format_recap_message, summarize_boc_pdf
from .config import CONFIG
from .news import fetch_all_news, format_news_message
from .state import State
from .subscribers import Subscribers
from .whatsapp import WhatsAppClient

logger = logging.getLogger(__name__)


def _recipients() -> list[str]:
    subs = Subscribers(CONFIG.subscribers_file).list_all()
    # dict.fromkeys() deduplique en gardant l'ordre
    return list(dict.fromkeys(subs + CONFIG.whatsapp_recipients))


def _client() -> WhatsAppClient:
    return WhatsAppClient(
        token=CONFIG.whatsapp_token,
        phone_number_id=CONFIG.whatsapp_phone_number_id,
        api_version=CONFIG.whatsapp_api_version,
    )


def _send_with_fallback(
    client: WhatsAppClient,
    recipient: str,
    text: str,
    template_name: str,
    body_params: list[str],
    document_url: str | None = None,
    document_filename: str | None = None,
) -> None:
    """Essaie d'abord un message texte libre (fonctionne uniquement si le
    destinataire a ecrit au bot dans les 24h precedentes). En cas d'echec
    (hors fenetre de 24h), retente automatiquement via le message template
    approuve par Meta, s'il est configure."""
    try:
        client.send_text(to=recipient, body=text)
        if document_url:
            client.send_document_link(
                to=recipient,
                document_url=document_url,
                filename=document_filename or "document.pdf",
                caption="",
            )
        return
    except Exception as exc:  # noqa: BLE001
        logger.info(
            "Envoi en texte libre echoue pour %s (%s) -- tentative via template.",
            recipient,
            exc,
        )

    if not CONFIG.whatsapp_use_templates:
        logger.warning(
            "Message perdu pour %s: hors fenetre de 24h et les templates "
            "sont desactives (WHATSAPP_USE_TEMPLATES=false).",
            recipient,
        )
        return

    try:
        client.send_template(
            to=recipient,
            template_name=template_name,
            language_code=CONFIG.whatsapp_template_lang,
            body_params=body_params,
            header_document_url=document_url,
            header_document_filename=document_filename,
        )
    except Exception:  # noqa: BLE001
        logger.exception("Echec d'envoi (texte et template) vers %s", recipient)


def run_check_news() -> int:
    CONFIG.validate_core()
    recipients = _recipients()
    if not recipients:
        logger.info("Aucun abonne pour le moment, rien a envoyer.")
        return 0

    state = State.load(CONFIG.state_file)
    items = fetch_all_news(CONFIG.brvm_base_url, CONFIG.brvm_news_categories)
    new_items = [item for item in items if not state.has_sent_news(item.url)]

    if not new_items:
        logger.info("Aucune nouvelle annonce.")
        return 0

    logger.info("%d nouvelle(s) annonce(s) a envoyer a %d abonne(s).", len(new_items), len(recipients))
    client = _client()

    for item in new_items:
        message = format_news_message(item)
        for recipient in recipients:
            _send_with_fallback(
                client,
                recipient,
                message,
                template_name=CONFIG.whatsapp_news_template_name,
                body_params=[item.company or "BRVM", item.title, item.url],
            )
        state.mark_news_sent(item.url)
        state.save(CONFIG.state_file)

    return 0


def run_send_recap() -> int:
    CONFIG.validate_core()
    recipients = _recipients()
    if not recipients:
        logger.info("Aucun abonne pour le moment, rien a envoyer.")
        return 0

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
    client = _client()

    body_params = [
        bulletin.title,
        f"{summary.composite_value or 'N/A'} ({summary.composite_change or 'N/A'})",
        f"{summary.brvm30_value or 'N/A'} ({summary.brvm30_change or 'N/A'})",
    ]
    filename = f"BOC_{bulletin.date or 'jour'}.pdf"

    logger.info("Envoi du recap BOC (%s) a %d abonne(s).", bulletin.title, len(recipients))
    for recipient in recipients:
        _send_with_fallback(
            client,
            recipient,
            message,
            template_name=CONFIG.whatsapp_recap_template_name,
            body_params=body_params,
            document_url=bulletin.pdf_url,
            document_filename=filename,
        )

    state.last_boc_date = bulletin.date
    state.save(CONFIG.state_file)
    return 0

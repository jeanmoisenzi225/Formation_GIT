"""Cache en memoire (TTL) des donnees BRVM utilisees comme contexte par
l'assistant conversationnel. Evite de re-scraper brvm.org a chaque message
WhatsApp recu -- les donnees de marche ne changent pas d'une minute a
l'autre.
"""
from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timezone

from . import boc, news

logger = logging.getLogger(__name__)


@dataclass
class BrvmContext:
    generated_at: float
    text: str


_lock = threading.Lock()
_cache: BrvmContext | None = None


def _build_context(base_url: str, categories: list[str]) -> str:
    parts: list[str] = []

    try:
        bulletin = boc.fetch_latest_boc(base_url)
        if bulletin:
            pdf_bytes = boc.download_pdf(bulletin.pdf_url)
            summary = boc.summarize_boc_pdf(pdf_bytes)
            parts.append(boc.format_recap_message(bulletin, summary))
    except Exception:  # noqa: BLE001
        logger.exception("Impossible de recuperer le BOC pour le contexte assistant")

    try:
        items = news.fetch_all_news(base_url, categories)
        items = sorted(items, key=lambda i: i.date or datetime.min.replace(tzinfo=timezone.utc), reverse=True)[:10]
        if items:
            parts.append("Dernieres annonces BRVM:")
            parts.extend(f"- {news.format_news_message(i)}".replace("\n", " | ") for i in items)
    except Exception:  # noqa: BLE001
        logger.exception("Impossible de recuperer les annonces pour le contexte assistant")

    return "\n\n".join(parts) if parts else "(Aucune donnee BRVM disponible pour le moment.)"


def get_context(base_url: str, categories: list[str], ttl_seconds: int) -> str:
    global _cache
    with _lock:
        now = time.time()
        if _cache is not None and (now - _cache.generated_at) < ttl_seconds:
            return _cache.text

        text = _build_context(base_url, categories)
        _cache = BrvmContext(generated_at=now, text=text)
        return text

"""Planificateur integre: permet de faire tourner les alertes news + le
recap BOC en tache de fond, DANS le meme process que le serveur webhook.
C'est ce qui rend le deploiement "un seul service" possible: pas besoin
d'un cron separe -- un unique process, lance en continu, gere a la fois
les messages entrants (webhook) et les envois automatiques.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone

from apscheduler.schedulers.background import BackgroundScheduler

from .config import CONFIG
from .jobs import run_check_news, run_send_recap

logger = logging.getLogger(__name__)

_scheduler: BackgroundScheduler | None = None


def _safe_run(func, name: str) -> None:
    try:
        func()
    except Exception:  # noqa: BLE001
        logger.exception("Erreur dans la tache planifiee %s", name)


def start() -> BackgroundScheduler | None:
    global _scheduler
    if not CONFIG.enable_scheduler:
        logger.info("Planificateur desactive (ENABLE_SCHEDULER=false).")
        return None

    now = datetime.now(timezone.utc)
    scheduler = BackgroundScheduler(timezone="UTC")
    scheduler.add_job(
        _safe_run,
        "interval",
        args=[run_check_news, "check_news"],
        minutes=CONFIG.news_poll_interval_minutes,
        id="check_news",
        max_instances=1,
        next_run_time=now,  # premiere execution quelques secondes apres le demarrage
    )
    scheduler.add_job(
        _safe_run,
        "interval",
        args=[run_send_recap, "send_recap"],
        minutes=CONFIG.boc_poll_interval_minutes,
        id="send_recap",
        max_instances=1,
        next_run_time=now,
    )
    scheduler.start()
    logger.info(
        "Planificateur demarre (news toutes les %d min, BOC verifie toutes les %d min).",
        CONFIG.news_poll_interval_minutes,
        CONFIG.boc_poll_interval_minutes,
    )
    _scheduler = scheduler
    return scheduler


def stop() -> None:
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None

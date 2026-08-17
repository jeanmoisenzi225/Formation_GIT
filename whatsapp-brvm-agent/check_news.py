#!/usr/bin/env python3
"""A lancer regulierement (ex: toutes les 15-30 min via cron), ou laisser
tourner automatiquement via le planificateur integre au webhook
(voir brvm_agent/scheduler.py). Envoie une alerte WhatsApp a tous les
abonnes (brvm_agent/subscribers.py) pour chaque nouvelle annonce BRVM.
"""
from __future__ import annotations

import logging
import sys

from brvm_agent.jobs import run_check_news

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

if __name__ == "__main__":
    sys.exit(run_check_news())

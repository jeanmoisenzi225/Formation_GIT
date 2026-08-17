#!/usr/bin/env python3
"""A lancer regulierement (ex: toutes les 15-30 min via cron), ou laisser
tourner automatiquement via le planificateur integre au webhook
(voir brvm_agent/scheduler.py). Des qu'un nouveau Bulletin Officiel de la
Cote (BOC) est publie par la BRVM, envoie le recap + le PDF a tous les
abonnes (brvm_agent/subscribers.py). Ne renvoie jamais deux fois le meme
bulletin (voir brvm_agent/state.py).
"""
from __future__ import annotations

import logging
import sys

from brvm_agent.jobs import run_send_recap

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

if __name__ == "__main__":
    sys.exit(run_send_recap())

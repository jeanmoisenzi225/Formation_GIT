"""Liste des abonnes aux alertes BRVM (auto-abonnement).

N'importe qui peut s'abonner en envoyant simplement un message WhatsApp au
numero du bot -- WhatsApp ne notifie jamais une entreprise quand quelqu'un
l'ajoute a ses contacts, seul un message declenche un evenement webhook.
C'est donc le premier message recu d'un numero qui vaut abonnement.
"""
from __future__ import annotations

import json
import os
import threading


class Subscribers:
    def __init__(self, path: str):
        self.path = path
        self._lock = threading.Lock()

    def _load(self) -> list[str]:
        if not os.path.exists(self.path):
            return []
        with open(self.path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _save(self, data: list[str]) -> None:
        tmp_path = f"{self.path}.tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp_path, self.path)

    def list_all(self) -> list[str]:
        with self._lock:
            return self._load()

    def add(self, number: str) -> bool:
        """Retourne True si le numero vient d'etre ajoute (nouvel abonne)."""
        with self._lock:
            data = self._load()
            if number in data:
                return False
            data.append(number)
            self._save(data)
            return True

    def remove(self, number: str) -> bool:
        with self._lock:
            data = self._load()
            if number not in data:
                return False
            data.remove(number)
            self._save(data)
            return True

    def is_subscribed(self, number: str) -> bool:
        return number in self.list_all()

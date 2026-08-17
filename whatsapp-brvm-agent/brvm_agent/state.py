"""Petit stockage local JSON pour eviter les doublons de messages.

On y garde:
- les URLs des annonces (news) deja envoyees sur WhatsApp
- la date du dernier BOC (bulletin officiel de la cote) deja envoye
"""
import json
import os
from dataclasses import dataclass, field


@dataclass
class State:
    sent_news_urls: list[str] = field(default_factory=list)
    last_boc_date: str = ""

    @classmethod
    def load(cls, path: str) -> "State":
        if not os.path.exists(path):
            return cls()
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls(
            sent_news_urls=data.get("sent_news_urls", []),
            last_boc_date=data.get("last_boc_date", ""),
        )

    def save(self, path: str) -> None:
        # On garde uniquement les 500 dernieres URLs pour ne pas grossir indefiniment.
        self.sent_news_urls = self.sent_news_urls[-500:]
        tmp_path = f"{path}.tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "sent_news_urls": self.sent_news_urls,
                    "last_boc_date": self.last_boc_date,
                },
                f,
                ensure_ascii=False,
                indent=2,
            )
        os.replace(tmp_path, path)

    def mark_news_sent(self, url: str) -> None:
        if url not in self.sent_news_urls:
            self.sent_news_urls.append(url)

    def has_sent_news(self, url: str) -> bool:
        return url in self.sent_news_urls

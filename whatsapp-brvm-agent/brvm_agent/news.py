"""Recuperation des annonces/actualites publiees par la BRVM.

Le site brvm.org (Drupal) ne propose pas de flux "actualites" classique:
la page /fr/actualites n'est en realite qu'un formulaire d'inscription a la
newsletter. Les vraies actualites (communiques de presse des societes cotees,
franchissements de seuil, changements de dirigeants, notations financieres...)
sont publiees sous forme de tableaux paginables sous:

    https://www.brvm.org/fr/emetteurs/type-annonces/<categorie>

Chaque ligne du tableau contient une date, une societe, un titre et un lien
PDF. C'est cette structure (verifiee en aout 2026) qui est parsee ici.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

REQUEST_TIMEOUT = 30
HEADERS = {"User-Agent": "brvm-whatsapp-agent/1.0 (+veille BRVM automatisee)"}


@dataclass
class NewsItem:
    date: datetime | None
    company: str
    title: str
    url: str
    category: str


def fetch_category(base_url: str, category: str) -> list[NewsItem]:
    """Recupere les annonces d'une categorie (ex: 'communiques')."""
    url = f"{base_url.rstrip('/')}/fr/emetteurs/type-annonces/{category}"
    response = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    items: list[NewsItem] = []
    for row in soup.select("table.views-table tbody tr"):
        title_cell = row.select_one("td.views-field-title")
        company_cell = row.select_one("td.views-field-og-group-ref")
        date_cell = row.select_one("td.views-field-field-date-annonce span.date-display-single")
        link_cell = row.select_one("td.views-field-field-fichier-annonce a")

        if not title_cell or not link_cell or not link_cell.get("href"):
            continue

        date_value = None
        if date_cell and date_cell.get("content"):
            try:
                date_value = datetime.fromisoformat(date_cell["content"])
            except ValueError:
                pass

        items.append(
            NewsItem(
                date=date_value,
                company=company_cell.get_text(strip=True) if company_cell else "",
                title=title_cell.get_text(strip=True),
                url=link_cell["href"],
                category=category,
            )
        )
    return items


def fetch_all_news(base_url: str, categories: list[str]) -> list[NewsItem]:
    all_items: list[NewsItem] = []
    for category in categories:
        try:
            all_items.extend(fetch_category(base_url, category))
        except requests.RequestException as exc:
            logger.warning("Echec de recuperation de la categorie %s: %s", category, exc)
    return all_items


def format_news_message(item: NewsItem) -> str:
    date_str = item.date.strftime("%d/%m/%Y") if item.date else "date inconnue"
    parts = [f"BRVM - Nouvelle annonce ({date_str})"]
    if item.company:
        parts.append(item.company)
    parts.append(item.title)
    parts.append(item.url)
    return "\n".join(parts)

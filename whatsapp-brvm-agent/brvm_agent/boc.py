"""Recuperation et resume du Bulletin Officiel de la Cote (BOC).

Le BOC du jour est publie en PDF sur:
    https://www.brvm.org/fr/bulletins-officiels-de-la-cote

La 1ere page du PDF contient toujours un resume chiffre de la seance
(BRVM Composite, BRVM 30, capitalisation, volumes, plus fortes hausses /
baisses...). On extrait ce texte pour construire un recapitulatif WhatsApp,
en plus d'envoyer le PDF officiel lui-meme.
"""
from __future__ import annotations

import io
import logging
import re
from dataclasses import dataclass
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from pypdf import PdfReader

logger = logging.getLogger(__name__)

REQUEST_TIMEOUT = 30
HEADERS = {"User-Agent": "brvm-whatsapp-agent/1.0 (+veille BRVM automatisee)"}

# ex: "Bulletin Officiel de la Cote du 17 Août 2026"
_FRENCH_BOC_TITLE_RE = re.compile(r"Bulletin Officiel de la Cote du (.+)", re.IGNORECASE)
# ex: boc_20260817_2.pdf -> date 2026-08-17
_BOC_FILENAME_DATE_RE = re.compile(r"boc_(\d{4})(\d{2})(\d{2})_\d+\.pdf")


@dataclass
class BocBulletin:
    title: str
    date: str  # AAAA-MM-JJ, derivee du nom de fichier
    pdf_url: str


@dataclass
class BocSummary:
    composite_value: str | None = None
    composite_change: str | None = None
    brvm30_value: str | None = None
    brvm30_change: str | None = None
    capitalisation: str | None = None
    volume: str | None = None
    valeur_transigee: str | None = None
    top_hausses: list[str] | None = None
    top_baisses: list[str] | None = None


def fetch_latest_boc(base_url: str) -> BocBulletin | None:
    """Retourne le dernier bulletin (version francaise) publie."""
    url = f"{base_url.rstrip('/')}/fr/bulletins-officiels-de-la-cote"
    response = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    for row in soup.select("table.views-table tbody tr"):
        title_cell = row.select_one("td.views-field-title")
        link_cell = row.select_one("td.views-field-field-fichier-boc a")
        if not title_cell or not link_cell or not link_cell.get("href"):
            continue

        title = title_cell.get_text(strip=True)
        match = _FRENCH_BOC_TITLE_RE.match(title)
        if not match:
            # On ignore les entrees non francaises (ex: "Daily Market Report...")
            continue

        pdf_url = link_cell["href"]
        date_match = _BOC_FILENAME_DATE_RE.search(pdf_url)
        date_str = (
            f"{date_match.group(1)}-{date_match.group(2)}-{date_match.group(3)}"
            if date_match
            else ""
        )
        return BocBulletin(title=title, date=date_str, pdf_url=pdf_url)

    return None


def download_pdf(pdf_url: str) -> bytes:
    response = requests.get(pdf_url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    return response.content


def _find_index_value_and_change(lines: list[str], index_label: str) -> tuple[str | None, str | None]:
    for i, line in enumerate(lines):
        if line.strip() == index_label or line.strip().startswith(f"{index_label} "):
            value_match = re.search(rf"{re.escape(index_label)}\s+([\d\s]+,\d+)", line)
            value = value_match.group(1).replace(" ", "") if value_match else None
            change = None
            for lookahead in lines[i : i + 3]:
                change_match = re.search(r"Variation Jour\s+(-?[\d,]+\s*%)", lookahead)
                if change_match:
                    change = change_match.group(1)
                    break
            return value, change
    return None, None


def _find_field(text: str, label_pattern: str) -> str | None:
    # Le champ est suivi de sa propre valeur (nombre a espaces = separateur
    # de milliers) puis, sur la meme ligne, de la variation en % du jour.
    # On capture uniquement la valeur, pas la variation.
    match = re.search(rf"{label_pattern}\s+([\d\s]+?)\s+-?[\d,]+\s*%", text)
    if match:
        return match.group(1).strip()
    return None


def _extract_movers(lines: list[str], header: str, next_header: str, limit: int = 3) -> list[str]:
    movers: list[str] = []
    try:
        start = next(i for i, l in enumerate(lines) if header in l)
    except StopIteration:
        return movers

    for line in lines[start + 1 :]:
        if next_header in line:
            break
        # ex: "CIE CI (CIEC)    5 920 7,34 % 150,85 %"
        if re.search(r"\(\w+\)\s+[\d\s]+\s+-?[\d,]+\s*%", line):
            movers.append(re.sub(r"\s+", " ", line).strip())
        if len(movers) >= limit:
            break
    return movers


def summarize_boc_pdf(pdf_bytes: bytes) -> BocSummary:
    """Extrait les chiffres cles de la 1ere page du BOC. Best-effort:
    si la mise en page change, les champs non trouves restent a None
    plutot que de faire echouer tout le recapitulatif."""
    summary = BocSummary()
    try:
        reader = PdfReader(io.BytesIO(pdf_bytes))
        text = reader.pages[0].extract_text() or ""
    except Exception as exc:  # noqa: BLE001 - on ne veut jamais planter sur un PDF externe
        logger.warning("Impossible de lire le PDF du BOC: %s", exc)
        return summary

    lines = text.split("\n")

    summary.composite_value, summary.composite_change = _find_index_value_and_change(
        lines, "BRVM COMPOSITE"
    )
    summary.brvm30_value, summary.brvm30_change = _find_index_value_and_change(lines, "BRVM 30")

    summary.capitalisation = _find_field(text, r"Capitalisation boursi\w+ \(FCFA\)\(Actions & Droits\)")
    summary.volume = _find_field(text, r"Volume échangé \(Actions & Droits\)")
    summary.valeur_transigee = _find_field(text, r"Valeur transigée \(FCFA\) \(Actions & Droits\)")

    summary.top_hausses = _extract_movers(lines, "PLUS FORTES HAUSSES", "PLUS FORTES BAISSES")
    summary.top_baisses = _extract_movers(lines, "PLUS FORTES BAISSES", "Base = 100")

    return summary


def format_recap_message(bulletin: BocBulletin, summary: BocSummary) -> str:
    lines = [f"BRVM - Recapitulatif de cloture ({bulletin.title})"]

    if summary.composite_value:
        chg = f" ({summary.composite_change})" if summary.composite_change else ""
        lines.append(f"BRVM Composite: {summary.composite_value}{chg}")
    if summary.brvm30_value:
        chg = f" ({summary.brvm30_change})" if summary.brvm30_change else ""
        lines.append(f"BRVM 30: {summary.brvm30_value}{chg}")
    if summary.capitalisation:
        lines.append(f"Capitalisation boursiere (actions): {summary.capitalisation} FCFA")
    if summary.volume:
        lines.append(f"Volume echange: {summary.volume}")
    if summary.valeur_transigee:
        lines.append(f"Valeur transigee: {summary.valeur_transigee} FCFA")

    if summary.top_hausses:
        lines.append("\nPlus fortes hausses:")
        lines.extend(f"  {m}" for m in summary.top_hausses)
    if summary.top_baisses:
        lines.append("\nPlus fortes baisses:")
        lines.extend(f"  {m}" for m in summary.top_baisses)

    lines.append(f"\nBulletin complet: {bulletin.pdf_url}")
    return "\n".join(lines)

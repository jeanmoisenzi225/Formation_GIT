"""Assistant conversationnel: repond a n'importe quel message WhatsApp
entrant (ex: "quoi de beau aujourd'hui ?") en s'appuyant sur les dernieres
donnees BRVM recuperees (annonces + resume du dernier BOC) comme contexte,
via l'API Claude.
"""
from __future__ import annotations

import logging

import anthropic

from .config import CONFIG
from .context_cache import get_context

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """Tu es un assistant WhatsApp specialise sur la BRVM \
(Bourse Regionale des Valeurs Mobilieres, marche boursier regional \
d'Afrique de l'Ouest). Tu discutes avec un investisseur particulier.

Regles:
- Reponds en francais, de maniere concise (c'est un chat WhatsApp, pas un \
rapport -- privilegie des reponses courtes, va a l'essentiel).
- Utilise en priorite le "Contexte BRVM" fourni ci-dessous (annonces \
recentes, resume du dernier bulletin officiel de la cote) pour repondre \
aux questions sur le marche, les societes cotees ou l'actualite boursiere.
- Si le contexte ne contient pas l'information demandee, dis-le \
clairement plutot que d'inventer des chiffres.
- Si la question n'a rien a voir avec la BRVM (salutation, question \
generale...), reponds normalement comme un assistant utile.

Contexte BRVM (donnees recuperees automatiquement sur brvm.org):
{context}
"""


def _client() -> anthropic.Anthropic:
    return anthropic.Anthropic(api_key=CONFIG.anthropic_api_key)


def answer(user_message: str) -> str:
    context = get_context(
        CONFIG.brvm_base_url, CONFIG.brvm_news_categories, CONFIG.brvm_context_ttl_seconds
    )
    system = SYSTEM_PROMPT.format(context=context)

    try:
        response = _client().messages.create(
            model=CONFIG.anthropic_model,
            max_tokens=1024,
            system=system,
            messages=[{"role": "user", "content": user_message}],
        )
    except anthropic.APIStatusError as exc:
        logger.exception("Erreur API Claude: %s", exc)
        return "Desole, je n'arrive pas a repondre pour le moment (erreur technique). Reessaie dans un instant."

    text_parts = [block.text for block in response.content if block.type == "text"]
    return "\n".join(text_parts).strip() or "Desole, je n'ai pas compris ta question."

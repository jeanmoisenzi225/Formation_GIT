import os
from dataclasses import dataclass, field

from dotenv import load_dotenv

load_dotenv()


def _split_csv(value: str) -> list[str]:
    return [v.strip() for v in value.split(",") if v.strip()]


@dataclass(frozen=True)
class Config:
    whatsapp_token: str = os.environ.get("WHATSAPP_TOKEN", "")
    whatsapp_phone_number_id: str = os.environ.get("WHATSAPP_PHONE_NUMBER_ID", "")
    whatsapp_api_version: str = os.environ.get("WHATSAPP_API_VERSION", "v20.0")
    whatsapp_recipients: list[str] = field(
        default_factory=lambda: _split_csv(os.environ.get("WHATSAPP_RECIPIENTS", ""))
    )
    whatsapp_use_templates: bool = os.environ.get("WHATSAPP_USE_TEMPLATES", "true").lower() == "true"
    whatsapp_template_lang: str = os.environ.get("WHATSAPP_TEMPLATE_LANG", "fr")
    whatsapp_news_template_name: str = os.environ.get("WHATSAPP_NEWS_TEMPLATE_NAME", "brvm_news_alert")
    whatsapp_recap_template_name: str = os.environ.get("WHATSAPP_RECAP_TEMPLATE_NAME", "brvm_boc_recap")

    brvm_base_url: str = os.environ.get("BRVM_BASE_URL", "https://www.brvm.org")
    brvm_news_categories: list[str] = field(
        default_factory=lambda: _split_csv(
            os.environ.get(
                "BRVM_NEWS_CATEGORIES",
                "communiques,franchissements-de-seuil,changements-de-dirigeants,notations-financieres",
            )
        )
    )

    state_file: str = os.environ.get("STATE_FILE", "state.json")

    # --- Assistant conversationnel (webhook WhatsApp -> Claude) ---
    anthropic_api_key: str = os.environ.get("ANTHROPIC_API_KEY", "")
    anthropic_model: str = os.environ.get("ANTHROPIC_MODEL", "claude-opus-5")
    whatsapp_verify_token: str = os.environ.get("WHATSAPP_VERIFY_TOKEN", "")
    whatsapp_app_secret: str = os.environ.get("WHATSAPP_APP_SECRET", "")
    brvm_context_ttl_seconds: int = int(os.environ.get("BRVM_CONTEXT_TTL_SECONDS", "900"))

    def validate_for_sending(self) -> None:
        missing = []
        if not self.whatsapp_token:
            missing.append("WHATSAPP_TOKEN")
        if not self.whatsapp_phone_number_id:
            missing.append("WHATSAPP_PHONE_NUMBER_ID")
        if not self.whatsapp_recipients:
            missing.append("WHATSAPP_RECIPIENTS")
        if missing:
            raise RuntimeError(
                "Variables d'environnement manquantes: " + ", ".join(missing)
            )

    def validate_for_webhook(self) -> None:
        missing = []
        if not self.whatsapp_token:
            missing.append("WHATSAPP_TOKEN")
        if not self.whatsapp_phone_number_id:
            missing.append("WHATSAPP_PHONE_NUMBER_ID")
        if not self.whatsapp_verify_token:
            missing.append("WHATSAPP_VERIFY_TOKEN")
        if not self.anthropic_api_key:
            missing.append("ANTHROPIC_API_KEY")
        if missing:
            raise RuntimeError(
                "Variables d'environnement manquantes: " + ", ".join(missing)
            )


CONFIG = Config()

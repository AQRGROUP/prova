from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "sqlite:///./crm.db"

    telegram_bot_token: str = ""
    # Opzionale ma consigliato: Telegram lo rimanda nell'header
    # X-Telegram-Bot-Api-Secret-Token di ogni chiamata al webhook, per
    # verificare che la richiesta arrivi davvero da Telegram.
    telegram_webhook_secret: str = ""

    anthropic_api_key: str = ""

    # Dominio usato per generare l'email aziendale di fallback quando il
    # lavoratore non ne fornisce una propria (es. mario.rossi@<dominio azienda>).
    default_email_fallback_domain: str = ""


settings = Settings()

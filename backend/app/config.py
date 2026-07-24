from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "sqlite:///./crm.db"

    whatsapp_verify_token: str = ""
    whatsapp_access_token: str = ""
    whatsapp_phone_number_id: str = ""

    anthropic_api_key: str = ""

    # Dominio usato per generare l'email aziendale di fallback quando il
    # lavoratore non ne fornisce una propria (es. mario.rossi@<dominio azienda>).
    default_email_fallback_domain: str = ""


settings = Settings()

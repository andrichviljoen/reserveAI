from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AI Actuarial Reserving Suite API"
    supabase_url: str = ""
    supabase_key: str = ""
    openai_api_key: str = ""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()

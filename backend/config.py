from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Ollama
    ollama_host: str = "http://localhost:11434"
    # Using the locally-installed llama3.2 (fast, ~2GB). Upgrade to
    # qwen2.5:7b-instruct for stronger reasoning once pulled.
    ollama_model: str = "llama3.2:latest"
    embed_model: str = "nomic-embed-text"
    llm_temperature: float = 0.3
    llm_max_tokens: int = 400

    # DB
    db_path: str = "axiom.db"

    # Demo business (overridable via onboarding)
    business_name: str = "GlowVeda Skincare"
    business_industry: str = "D2C Skincare"
    business_stage: str = "Series A"


settings = Settings()

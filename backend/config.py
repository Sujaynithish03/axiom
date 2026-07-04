from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Ollama
    ollama_host: str = "http://localhost:11434"
    # Change to qwen2.5:3b if RAM-constrained, or llama3.1:8b as alternative
    ollama_model: str = "qwen2.5:7b-instruct"
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

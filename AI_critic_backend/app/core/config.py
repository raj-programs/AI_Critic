
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str
    groq_api_key: str

    vlm_provider: str = "groq"
    vlm_groq_model: str = "qwen/qwen3.8-27b"
    vlm_ollama_model: str = "qwen3-vl:8b"
    critic_provider: str = "groq"
    critic_groq_model: str = "qwen/qwen3.8-27b"
    critic_ollama_model: str = "qwen3-vl:8b"
    critic_gemini_model: str = "gemini-flash-latest"
    critic_gemini_max_output_tokens: int = 2048
    ollama_base_url: str = "http://localhost:11434"
    gemini_api_key: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()

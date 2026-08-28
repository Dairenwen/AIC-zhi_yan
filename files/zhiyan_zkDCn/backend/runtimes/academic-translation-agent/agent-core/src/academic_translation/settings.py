from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[2] / ".env", extra="ignore"
    )
    ollama_base_url: str = "http://127.0.0.1:11434"
    ollama_translation_model: str = "translategemma:12b"
    ollama_temperature: float = 0
    ollama_num_ctx: int = 8192
    max_parallel_segments: int = 1
    pdf2zh_command: str = ""
    default_output_dir: str = "outputs"


settings = Settings()

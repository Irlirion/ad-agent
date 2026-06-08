from pathlib import Path

from pydantic import SecretStr
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    openai_api_key: SecretStr = SecretStr("<API_KEY>")
    openai_model: str = "google/gemma-4-e2b"
    openai_base_url: str = ""
    segments_data: str = "segments-unlabeled.csv"
    langchain_tracing_v2: bool = False
    langchain_api_key: str = ""

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    @property
    def segments_path(self) -> Path:
        return Path(__file__).resolve().parent.parent / "data" / self.segments_data


settings = Settings()

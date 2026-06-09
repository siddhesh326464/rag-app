from pydantic.v1 import BaseSettings, validator
from typing import Optional
from dotenv import load_dotenv
load_dotenv()

class Settings(BaseSettings):
    # basic configurations
    MAX_PAGES_PER_REQUEST: int = 15
    CHUNK_SIZE: int = 1000
    BATCH_SIZE: int = 50
    MAX_CONTEXT_CHARS: int = 25000
    TOP_K: int = 5

    # vector db setup
    QDRANT_API_KEY: str
    QDRANT_ENDPOINT: str
    QDRANT_COLLECTION: str = "enterprise_rag"
    EMBEDDING_SIZE: int = 768

    # GCP project setup
    PROJECT_ID: str = "enterpricerag-496507"
    LOCATION: str = "us-central1"
    GCP_DOC_AI_LOCATION: str = "us"
    GCP_DOC_AI_PROCESSOR_ID: str = ""
    GCP_RAW_BUCKET: str = ""
    GCP_PROCESSED_BUCKET: str = ""
    RAW_BUCKET: str = "enterpricerag-496507-rag-raw"
    PROCESSED_BUCKET: str = "enterpricerag-496507-rag-processed"

    # LLM settings
    GROK_API_KEY: str
    GROQ_model: str = "llama-3.3-70b-versatile"
    TEMPRATURE: float = 0.0

    # Database
    DB_USER: str = "rag_admin"
    DB_PASS: Optional[str] = None
    DB_PASSWORD: Optional[str] = None
    DB_NAME: str = "rag_memory"
    DB_CONNECTION_NAME: str = ""

    # Redis
    REDIS_HOST: str = ""
    REDIS_PORT: str = "6379"

    # Mode
    LOCAL_MODE: bool = False

    @validator("DB_PASSWORD", always=True, pre=False)
    def set_db_password(cls, v, values):
        """Derive DB_PASSWORD from DB_PASS so both attribute names work."""
        return v or values.get("DB_PASS") or ""

    @validator("RAW_BUCKET", always=True, pre=False)
    def set_raw_bucket(cls, v, values):
        """Use GCP_RAW_BUCKET env var if provided (set by Cloud Run / Terraform)."""
        return values.get("GCP_RAW_BUCKET") or v

    @validator("PROCESSED_BUCKET", always=True, pre=False)
    def set_processed_bucket(cls, v, values):
        """Use GCP_PROCESSED_BUCKET env var if provided (set by Cloud Run / Terraform)."""
        return values.get("GCP_PROCESSED_BUCKET") or v

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()

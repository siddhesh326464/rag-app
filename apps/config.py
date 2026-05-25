from pydantic.v1 import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    MAX_PAGES_PER_REQUEST:int = 15
    CHUNK_SIZE : int = 1500
    BATCH_SIZE : int = 50

    QDRANT_API_KEY : str
    QDRANT_ENDPOINT : str

    PROJECT_ID: str = "enterpricerag-496507"
    LOCATION: str = "us-central1"
    GCP_DOC_AI_LOCATION: str = "us"
    GCP_DOC_AI_PROCESSOR_ID: str
    RAW_BUCKET : str = "rag-data-raw"
    PROCESSED_BUCKET : str = 'rag-data-processed'

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()



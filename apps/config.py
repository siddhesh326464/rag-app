from pydantic.v1 import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    #basic configurations
    MAX_PAGES_PER_REQUEST:int = 15
    CHUNK_SIZE : int = 1000
    BATCH_SIZE : int = 50
    MAX_CONTEXT_CHARS: int = 25000
    TOP_K : int = 5
    LOCAL_MODE : str

    #vectore db setup
    QDRANT_API_KEY : str
    QDRANT_ENDPOINT : str
    QDRANT_COLLECTION : str = "enterprise_rag"
    EMBEDDING_SIZE : int = 768

    #GCP project setup
    PROJECT_ID: str = "enterpricerag-496507"
    LOCATION: str = "us-central1"
    GCP_DOC_AI_LOCATION: str = "us"
    GCP_DOC_AI_PROCESSOR_ID: str
    RAW_BUCKET : str = "rag-data-raw"
    PROCESSED_BUCKET : str = 'rag-data-processed'

    # LLM settings
    GROK_API_KEY : str
    GROQ_model : str = "llama-3.3-70b-versatile"
    TEMPRATURE : float

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()



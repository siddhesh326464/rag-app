import os,sys,uuid,json,logfire,vertexai,tempfile
from typing import List
from google.cloud import storage
from qdrant_client import QdrantClient
from qdrant_client.http import models
from apps.config import settings
from fastapi import FastAPI, Request, BackgroundTasks, HTTPException, status
from apps.ingestion.loaders.pdf import parse_pdf
from apps.ingestion.loaders.html import html_parse
from apps.ingestion.loaders.office import parse_office
from apps.ingestion.loaders.text import parse_text
from apps.ingestion.chunking.splitter import chunk_text
from apps.services.retrieval.embedding import embed_texts


logfire.configure(service_name="enterprise-ingestion-service")

# initialization of vertex ai
vertexai.init(project=settings.PROJECT_ID,location=settings.LOCATION)

#initialize goog;e cloude storage
storage_client = storage.Client(project = settings.PROJECT_ID)

#initialize qadrent vectore DB client
qdrant_client = QdrantClient(
    url=settings.QDRANT_ENDPOINT,
    api_key=settings.QDRANT_API_KEY
)


app = FastAPI()

def process_file(file_path:str,filename:str,source_type:str,skip_raw_upload : bool = False):
    """
    Orchestrates the parsing, chunking, embedding, and indexing of a single file.
    
    Args:
        file_path: Local path to the file
        filename: Original name of the file
        source_type: 'true', 'noisy', etc.
        skip_raw_upload: Set to True if the file is ALREADY in GCS (prevents infinite loops)
    """
    with logfire.span("🚀 Processing File", file=filename, source=source_type):
        try:
            raw_gsc_path = f"{source_type}/{filename}"
            if not skip_raw_upload:
                upload_to_gcs(file_path,settings.RAW_BUCKET,raw_gsc_path)
            else:
                logfire.info(f"⏭️ Skipping RAW upload for {filename} (Already in GCS)")

            ext = filename.lower().split('.')[-1]
            if ext == 'pdf':
                full_text = parse_pdf(file_path)
            elif ext in ['html', 'htm']:
                full_text = html_parse(file_path)
            elif ext == 'txt':
                full_text = parse_text(file_path)
            elif ext in ['docx', 'pptx']:
                full_text = parse_office(file_path)
            else:
                logfire.warning(f"⏩ Skipping unsupported file type: {filename}")
                return

            if not full_text or not full_text.strip():
                logfire.warning(f"⚠️ No text extracted from {filename}")
                return
            chunks = chunk_text(full_text)

            if not chunks:
                logfire.warning("chunks are not extracted")
                return
            
            processed_data = {"filename": filename, "chunks": chunks, "source_type": source_type}
            processed_gcs_path = f"{source_type}/{filename}.json"
            upload_to_gcs(processed_data,settings.PROCESSED_BUCKET,processed_gcs_path,is_json=True)

            #embedding
            with logfire.span("🧠 Vectorizing & Indexing"):
                embeddings = embed_texts(chunks)
                points = []



        except Exception as e:  
            raise e


def upload_to_gcs(data,bucket:str,destination_blob_name:str,is_json : bool = False):
    """
    Uploads a file or JSON data to GCS.
    """
    with logfire.span("☁️ GCS Upload", bucket=bucket, blob=destination_blob_name):
        try:
            bucket = storage_client.bucket(bucket)
            if not bucket:
                logfire.warning("bucket not found")
            blob = bucket.blob(destination_blob_name)
            if is_json:
                blob.upload_from_string(json.dumps(data), content_type='application/json')
            else:
                blob.upload_from_filename(data)
        except Exception as e:
            logfire.error(f"❌ GCS Upload Failed: {e}")

@app.post("/")
async def eventarc_webhook(request: Request, background_tasks: BackgroundTasks):
    """
    Entry point for Google Cloud Eventarc triggers.
    """
    try:
        data = await request.json()

        bucket = data.get("bucket")
        name = data.get("name")

        if not bucket or name:
            logfire.error("❌ Invalid Eventarc payload")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid Eventarc payload")

        logfire.info(f"📡 Eventarc Triggered: {name} in {bucket}")

        if bucket.strip() != settings.RAW_BUCKET:
            logfire.warning(f"Ignoring event from unauthorized bucket: {bucket}")
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="mismatch bucket")

        parts = name.split("/") 
        source_type = parts[0] if len(parts) > 0 else "general"
        filename = parts[-1]

        background_tasks.add_task(process_from_gcs,bucket,name,filename,source_type)
        return {"status": "accepted", "file": name}

    except Exception as e:
        logfire.error(f"❌ Webhook Error: {e}")
        raise e

def process_from_gcs(bucket_name: str, blob_name: str, filename: str, source_type: str):
    """
    Downloads a file from GCS and triggers the processing pipeline.
    """
    with tempfile.NamedTemporaryFile(delete=False,suffix=f"_{filename}") as temp_file:
        try:
            bucket = storage_client.bucket(bucket_name)
            blob = bucket.blob(blob_name)
            blob.download_to_filename(temp_file.name)

            # CRITICAL: We set skip_raw_upload=True to prevent the Infinite Loop!
            process_file(temp_file.name,filename,source_type,skip_raw_upload = True)
        finally:
            if os.path.exists(temp_file.name):
                os.remove(temp_file.name)


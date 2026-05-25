import io,logfire
from pypdf import PdfReader,PdfWriter
from google.cloud import documentai
from apps.config import settings

client = documentai.DocumentProcessorServiceClient()


def parse_pdf(file_path:str):
    """
    Parses a PDF file using Google Cloud Document AI to extract structured text content.
    """
    with logfire.span("Document AI parssing",filename=file_path):
        try:
            reader = PdfReader(file_path)
            total_pages = len(reader.pages)
            logfire.info(f"total pages : {total_pages}")

            name = client.processor_path(
                settings.PROJECT_ID,
                settings.GCP_DOC_AI_LOCATION,
                settings.GCP_DOC_AI_PROCESSOR_ID
            )

            full_text = ""

            if total_pages <= settings.MAX_PAGES_PER_REQUEST:
                with open(file_path,"rb") as f:
                    image_content = f.read()

                full_text = process_document_chunk(image_content,name)
            else:
                logfire.info(f"PDF exceeds {settings.MAX_PAGES_PER_REQUEST} pages. Splitting into chunks...")
                for i in range(0,total_pages,settings.MAX_PAGES_PER_REQUEST):
                    writer = PdfWriter()
                    chunk_end = min(i + settings.MAX_PAGES_PER_REQUEST, total_pages)

                    for page_num in range(i, chunk_end):
                        writer.add_page(reader.pages[page_num])

                    with io.BytesIO() as bytes_stream:
                        writer.write(bytes_stream)
                        chunk_bytes = bytes_stream.getvalue()

                    with logfire.span(f"Processing pages {i+1} to {chunk_end}"):
                        chunk_text = process_document_chunk(chunk_bytes, name)
                        full_text += chunk_text + "\n"
            if not full_text.strip():
                logfire.warning(f"⚠️ Document AI returned empty text for {file_path}")
            else:
                logfire.info(f"✅ Document AI successfully parsed {len(full_text)} characters")

            return full_text
        except Exception as e:
            logfire.error("Document AI failed")
            raise e
        
def process_document_chunk(content,name):
    """Helper function to send a specific byte chunk to Document AI"""
    
    raw_document = documentai.RawDocument(
        content=content, 
        mime_type="application/pdf"
    )

    request = documentai.ProcessRequest(
        name=name, 
        raw_document=raw_document
    )

    result = client.process_document(request=request)
    return result.document.text
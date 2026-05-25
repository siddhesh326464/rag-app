import logfire
from unstructured.partition.auto import partition


def parse_office(file_path:str):
    """
    Parses Office documents (docx, pptx, xlsx, etc.) using Unstructured's partition function.
    """
    with logfire.span("office document parssing",filename = file_path):
        try:
            element = partition(filename=file_path)
            full_text = "\n".join([str(el) for el in element])

            if not full_text.strip():   
                logfire.warning("⚠️ Unstructured parsing returned empty text for {file_path}")
            else:
                logfire.info("✅ Successfully parsed office file: {len(full_text)} characters")

            return full_text

        except Exception as e:
            logfire.error("failed to parse office document")
            raise e
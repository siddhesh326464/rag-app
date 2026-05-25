import logfire,vertexai
from apps.config import settings
from vertexai.language_models import TextEmbeddingModel

model = None

def get_embedding_model():
    """
    Initializes and retrieves the global Vertex AI text embedding model instance.
    """
    global model
    if model is None:
        vertexai.init(project=settings.PROJECT_ID,location=settings.LOCATION)
        model = TextEmbeddingModel.from_pretrained("text-embedding-004")

    return model


def embed_texts(texts:list[str]):
    """
    Embeds a list of text strings in batches.
    """
    model = get_embedding_model()
    if not model:
        logfire.warning("embeding model not fount")
    all_embeddings = []
    for i in range(0,len(texts),settings.BATCH_SIZE):
        batch = texts[i:i+settings.BATCH_SIZE]
        embeddings = model.get_embeddings(batch)
        all_embeddings.extend([e.values for e in embeddings])
    return all_embeddings

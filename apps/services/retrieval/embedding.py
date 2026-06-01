import logfire,vertexai
from apps.config import settings
from vertexai.language_models import TextEmbeddingModel
from fastembed.sparse import SparseTextEmbedding

model = None
sparse_model = None

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


def embed_query(query: str):
    """Embeds a single query string using the stable Vertex AI API."""
    model = get_embedding_model()
    embeddings = model.get_embeddings([query])
    return embeddings[0].values


def get_sparse_embedding_model():
    """
    Initializes and retrieves the global sparse embedding model instance.
    This is a placeholder for future implementation of sparse embeddings.
    """
    global sparse_model
    if sparse_model is None:
        logfire.info("Initializing sparse embedding model...")
        # Initialize your sparse embedding model here
        sparse_model = SparseTextEmbedding(model_name="prithivida/Splade_PP_en_v1")
    return sparse_model


def embed_sparse_query(query:str):
    """
    Embeds a query string using the sparse embedding approach.
    This is a placeholder for future implementation of sparse embeddings.
    """
    sparse_model = get_sparse_embedding_model()
    sparse_embeddings = list(sparse_model.embed([query]))
    query_sparse_vector = sparse_embeddings[0]

    return {
        "indices": query_sparse_vector.indices.tolist(),
        "values": query_sparse_vector.values.tolist()
    }
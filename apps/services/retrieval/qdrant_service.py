import logfire
from qdrant_client import QdrantClient
from qdrant_client.http import models
from apps.config import settings
from apps.services.retrieval.embedding import get_embedding_model, embed_query, embed_sparse_query


qdrant_client=QdrantClient(
    url=settings.QDRANT_ENDPOINT,
    api_key=settings.QDRANT_API_KEY
)


def search_enterprise_knowledge(query:str,limit:int = settings.TOP_K):
    """
    Performs a high-precision search in the enterprise knowledge base.
    Uses the modern query_points interface.
    """
    try:
        query = embed_query(query)


        response = qdrant_client.query_points(
            collection_name=settings.QDRANT_COLLECTION,
            query=query,
            limit=limit,
            with_payload=True
        )

        results = []
        for res in response.points:
            results.append({
                "content": res.payload.get("text", ""),
                "source": res.payload.get("source", "Unknown"),
                "score": res.score
            })

        return results
    
    except Exception as e:
        logfire.error(f"❌ Qdrant Search Failed: {e}")
        return []


# def search_enterprise_knowledge(query:str,limit:int = settings.TOP_K):
#     """
#     Performs a high-precision search in the enterprise knowledge base.
#     Uses the modern query_points interface.
#     """
#     try:
#         sparse_query = query
#         query = embed_query(query)
#         sparse_query = embed_sparse_query(sparse_query)

#         sparse_vectores = models.SparseVectors(
#             indices=sparse_query["indices"],
#             values=sparse_query["values"]   
#         )

#         response = qdrant_client.query_points(
#             collection_name = settings.QDRANT_COLLECTION,
#             prefetch=[
#                 models.Prefetch(
#                     query = query,
#                     using = "dense",
#                     limit=limit * 2
#                 ),

#                 #sparse retrieval can be added in the future as needed

#                 models.Prefetch(
#                     query = sparse_vectores,
#                     using = "sparse",
#                     limit=limit * 2
#                 )
#             ],
#             query = models.FusionQuery(
#                 fusion=models.Fusion.RRF
#             ),
#             limit=limit,
#             with_payload=True,
#         )

#         results = []
#         for res in response.points:
#             results.append({
#                 "content": res.payload.get("text", ""),
#                 "source": res.payload.get("source", "Unknown"),
#                 "score": res.score
#             })

#         return results
#     except Exception as e:
#         logfire.error(f"❌ Qdrant Search Failed: {e}")
#         return []
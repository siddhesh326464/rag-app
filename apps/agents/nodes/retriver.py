import logfire
from apps.agents.state import AgentState
from apps.services.retrieval.qdrant_service import search_enterprise_knowledge
from apps.services.retrieval.ranking_service import rerank_document


def retrive_node(state:AgentState)->dict:
    """
    Fetches and rerank technical documents based on the current state query.

    Queries Qdrant (Bi-Encoder) using the `current_query`, refines the candidate 
    chunks using FlashRank (Cross-Encoder), and returns the updated `documents` list.
    """
    query = state['current_query']

    if query == "CONVERSATIONAL":
        logfire.info("skipping retrival - query is conversational")
        return {
            "documents" : [],
            "status" : "Using conversation history no retrival needed.",
            "plan" : state["plan"] + ["Retrieval Skipped"]
        }
    
    with logfire.span("🔍 Knowledge Retrieval"):
        logfire.info(f"Searching Qdrant for: {query}")
        raw_results = search_enterprise_knowledge(query=query)
        logfire.info(f"Retrieved {len(raw_results)} candidates from Vector DB")

        doc_contents = [doc['content'] for doc in raw_results]

        with logfire.span("⚖️ Semantic Reranking"):
            reranked_contents = rerank_document(query=query,documents=doc_contents,top_n=3)
            logfire.info("Reranking complete. Kept top 5 most relevant chunks.")

        formatted_docs = [f"CONTENT: {doc}" for doc in reranked_contents]
    return {
        "documents":formatted_docs,
        "status" :  f"Found technical context.",
        "plan": state["plan"] + ["Context Retrieved"]
    }

    

import logfire,os
from fastapi import FastAPI, Response
from apps.agents.graph import rag_agent
from apps.schema import QueryRequest
from apps.service import handel_query
from apps.guardrails.rails import initialize_rails



logfire.configure(token=os.getenv("LOGFIRE_TOKEN"))

app = FastAPI(title="Enterprise Agentic RAG API")


@app.on_event("startup")
def startup_event():
    """
    Event handler for application startup. Initializes the guardrails system.
    """
    logfire.info("Starting up the Enterprise Agentic RAG API...")
    initialize_rails()


@app.get("/")
def root():
    """
    Root endpoint to check if the API is running.
    """
    return {"message": "Enterprise Agentic RAG API is up and running!"}


@app.get("/graph")
def view_agent_graph():
    """
    Endpoint to visualize the agent's workflow graph.
    """
    try:
        logfire.info("Visualizing agent graph")
        bytes = rag_agent.get_graph().draw_mermaid_png()
        return Response(content=bytes, media_type="image/png")
    except Exception as e:
        logfire.error(f"Error visualizing graph: {e}")
        return Response(content="Error visualizing graph", status_code=500)
    

@app.post("/query")
def handel_query_view(query_data:QueryRequest):
    """"
    Endpoint to handle user queries. It accepts a query and an optional conversation ID,
    """
    response = handel_query(query_data.query, query_data.conversation_id)
    return response
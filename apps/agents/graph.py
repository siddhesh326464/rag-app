from langgraph.graph import StateGraph,END
from langgraph.checkpoint.memory import MemorySaver
from apps.agents.state import AgentState
from apps.agents.nodes.planner import planner_node
from apps.agents.nodes.responder import final_responder
from apps.agents.nodes.retriver import retrive_node
from apps.agents.nodes.grader import grader_node
from apps.config import settings
import logfire
from langgraph.checkpoint.postgres import PostgresSaver
from psycopg_pool import ConnectionPool

workflow = StateGraph(AgentState)

workflow.add_node("planner",planner_node)
workflow.add_node("retriever", retrive_node)
workflow.add_node("responder",final_responder)
workflow.add_node("grader",grader_node)


#----------- Function for conditional routing -----------------------

def routing(state:AgentState)->str:
    """
    This function acts as the routing logic (conditional edge) following the 
    planner node. It inspects the `current_query` to decide whether the graph 
    can answer the user conversationally using memory or if it needs to route 
    to the retrieval pipeline to fetch fresh technical documentation.
    """
    if state["current_query"] == "CONVERSATIONAL":
        return "responder"
    return "retriever"


def check_retrieval_needed(state:AgentState)->str:
    """
    This function acts as the routing logic (conditional edge) following the 
    grader node. It checks if the grader approved the answer. If rejected and
    retries remain, it routes back to the retriever for another attempt.
    """
    grader_approved = state.get("grader_approved", "")
    retrieval_attempts = state.get("retrieval_attempts", 0)

    if grader_approved == "APPROVED":
        return END
    if retrieval_attempts >= 3:
        return END
    return "retriever"

#----- create edges ----------------

workflow.set_entry_point("planner")
workflow.add_conditional_edges(
    "planner",
    routing,
    {
        "retriever": "retriever",
        "responder": "responder"
    }
)

workflow.add_edge("retriever","responder")

workflow.add_edge("responder", "grader")
workflow.add_conditional_edges(
    "grader",
    check_retrieval_needed,
    {
        "retriever": "retriever",
        END: END
    }
)



# ----------- IMPLEMENT HYBRID MEMORY ---------------
# checkpointer = MemorySaver()

# ------------ Hybrid Memory with Database Logging --------------

def get_checkpointer():
    """
    Returns a persistent Postgres checkpointer in Cloud/Production mode,
    and falls back to in-memory checkpointer in Local mode.
    """
    if settings.LOCAL_MODE:
        logfire.info("Using in-memory checkpointer for local development.")
        checkpointer = MemorySaver()
        return checkpointer
    try:
        conninfo = f"postgresql://{settings.DB_USER}:{settings.DB_PASSWORD}@/{settings.DB_NAME}?host=/cloudsql/{settings.DB_CONNECTION_NAME}"
        pool = ConnectionPool(conninfo, max_size = 10, timeout = 30)

        with pool.connection() as conn:
            checkpointer = PostgresSaver(conn)
            checkpointer.setup()
        checkpointer = PostgresSaver(pool)
        return checkpointer
    except Exception as e:
        logfire.error(f"Error setting up Postgres checkpointer: {e}")
        logfire.info("Falling back to in-memory checkpointer.")
        checkpointer = MemorySaver()
        return checkpointer

checkpointer = get_checkpointer()
rag_agent = workflow.compile(checkpointer=checkpointer)


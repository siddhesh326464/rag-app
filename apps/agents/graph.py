from langgraph.graph import StateGraph,END
from langgraph.checkpoint.memory import MemorySaver
from apps.agents.state import AgentState
from apps.agents.nodes.planner import planner_node
from apps.agents.nodes.responder import final_responder
from apps.agents.nodes.retriver import retrive_node
from apps.agents.nodes.grader import grader_node
from apps.config import settings


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
    retriever node. It checks if the retrieved documents are sufficient to 
    answer the query. If not, it routes back to the retriever for another attempt.
    """
    if state["retrieval_attempts"] >= 3:
        return END
    elif state["grader_approved"] == "REJECTED" and state["retrieval_attempts"] < 3:
        return "retriever"
    else:
        return END

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
checkpointer = MemorySaver()

rag_agent = workflow.compile(checkpointer=checkpointer)


from langchain_groq import ChatGroq
from apps.agents.state import AgentState
from apps.config import settings
import logfire


llm = ChatGroq(
    api_key=settings.GROK_API_KEY,
    model=settings.GROQ_model,
    temperature=settings.TEMPRATURE
)

def planner_node(state:AgentState)->AgentState:
    """
    Analyzes the user query and generates a sequence of execution steps.

    Reads the `current_query` from the state and updates the state with a new 
    list of sub-tasks in `plan` along with an updated operational `status`.
    """
    history = ""
    for msg in state['messages']:
        role = "User" if msg['role'] == "user" else "Assistant"
        history += f"{role} : {msg['content']} \n"

    user_message = state["messages"][-1]["content"] if state["messages"] else ""

    prompt = f"""
    You are an intelligent Assistant Planner. 
    Analyze the conversation history and the latest user message.
    
    CONVERSATION HISTORY:
    {history}
    
    LATEST MESSAGE:
    "{user_message}"
    
    Task:
    1. Respond ONLY with 'CONVERSATIONAL' if the message is a pure greeting (e.g., "hi", "hello"), casual small talk, or a direct question that can be answered entirely using the CONVERSATION HISTORY provided above.
    
    2. If the message is a technical, conceptual, or professional question—including real-world scenarios, platform engineering, infrastructure, Kubernetes, Intel, or Networking—generate a refined search query to fetch relevant industry knowledge, case studies, or architectural patterns.
    
    Output ONLY 'CONVERSATIONAL' or the search query. Avoid referencing "you" in the search query.
    """

    with logfire.span("🧠 Planner Decision"):
        decision = llm.invoke(prompt).content.strip()
        logfire.info(f"Intent identified: {decision}")

    if decision == "CONVERSATIONAL":
        return {
            "current_query": "CONVERSATIONAL",
            "status": "Handling conversationally (using memory)...",
            "plan": ["Intent: Conversational/Memory", "Retrieval: Skipped"]
        }
    return {
        "current_query": decision,
        "status": f"Technical research needed. Searching for: {decision}",
        "plan": ["Intent: Technical", f"Search Term: {decision}"]
    }



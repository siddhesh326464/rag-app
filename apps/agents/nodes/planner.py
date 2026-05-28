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
    You are an intelligent query classifier and search query generator for an Enterprise RAG pipeline.
    
    CONVERSATION HISTORY:
    {history}
    
    LATEST MESSAGE:
    "{user_message}"
    
    Classification Rules:

    Respond ONLY with 'CONVERSATIONAL' if the message is:
    - A greeting (hi, hello, hey, good morning)
    - Pure small talk (how are you, what's your name)
    - A follow-up referencing ONLY the conversation history 
      (e.g., "can you explain that again", "summarize what you said")
    - Completely non-technical with no domain-specific intent

    For ALL other messages — including any question about:
    - Kubernetes, Docker, containers, cloud, DevOps, infrastructure
    - Networking, Intel, platform engineering, system design
    - Any named technology, tool, framework, or architecture
    - Any technical concept, even if it seems basic or general
    → Generate a concise, precise search query to retrieve 
      relevant technical documentation or knowledge.

    IMPORTANT:
    - NEVER classify a technical question as CONVERSATIONAL just because 
      you already know the answer.
    - Domain knowledge in your training does NOT qualify as CONVERSATIONAL.
    - When in doubt, generate a search query.

    Output ONLY 'CONVERSATIONAL' or the search query.
    Do NOT include explanations or any other text.
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



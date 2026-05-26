import logfire
from langchain_groq import ChatGroq
from apps.agents.state import AgentState
from apps.config import settings


responder_llm = ChatGroq(
    api_key=settings.GROK_API_KEY,
    model=settings.GROQ_model,
    temperature=settings.TEMPRATURE
)


def final_responder(state:AgentState)->AgentState:
    """
    Generates the final user-facing response using retrieved context or memory.

    Reads `documents` and `messages` from the state, invokes the language model, 
    and updates the state with the finalized text in `final_ans` and a "completed" `status`.
    """
    user_query = state['current_query']
    history_str = ""
    for msg in state['messages'][:-1]:
        role = "User" if msg["role"] == "user" else "Assistant"
        history_str += f"{role} : {msg['content']}\n"
    
    user_msg = state["messages"][-1]["content"] if state["messages"] else ""

    if user_query == "CONVERSATIONAL":
        logfire.info("Generating conversational response using memory.")
        prompt = f"""
        You are a friendly and helpful Enterprise AI Assistant.
        Answer the user's latest message using the CONVERSATION HISTORY below.
        
        CONVERSATION HISTORY:
        {history_str}
        
        LATEST MESSAGE:
        "{user_msg}"
        """
    else:
        logfire.info("Generating technical RAG response.")
        full_context = ""

        for doc in state["documents"]:
            if len(full_context) + len(doc) < settings.MAX_CONTEXT_CHARS:
                full_context += doc + "\n\n"
            else:
                logfire.warning("Context truncated to fit Groq TPM limits.")
                break 

        prompt = f"""
        You are a Senior Technical Architect. 
        Answer the question using the TECHNICAL CONTEXT provided. 
        
        TECHNICAL CONTEXT:
        {full_context}
        
        CONVERSATION HISTORY:
        {history_str}
        
        USER QUESTION:
        "{user_msg}"
        """

    with logfire.span("✍️ LLM Synthesis"):
        try:
            response = responder_llm.invoke(prompt)
            return{
                "status":"Completed",
                "final_ans":response.content,
                "messages" : [{"role": "assistant", "content": response.content}]
            }
        except Exception as e:
            logfire.error(f"LLM Generation failed: {e}")
            raise e

        
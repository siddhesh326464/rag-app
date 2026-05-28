import logfire,os
from apps.agents.graph import rag_agent


def handel_query(query:str,conversation_id:str):
    """
    This function serves as the main handler for incoming user queries. It takes the query and conversation ID,
    constructs the initial state for the agent, and runs the agent to get a response.
    """
    try:
        logfire.info(f"Handling query: {query} for conversation_id: {conversation_id}")
        initial_state = {
            "messages" : [{"role":"user","content":query}],
            "current_query":query,
            "documents":[],
            "plan":["Start"],
            "status":"Initializing Graph......",
        }

        config = {"configurable": {"thread_id": conversation_id}}
        final_output = rag_agent.invoke(initial_state, config=config)
        return {
            "question": query,
            "answer": final_output.get("final_ans"),
            "thought_process": final_output.get("plan"),
            "status": final_output.get("status"),
            "sources": final_output.get("documents",[])
        }
    except Exception as e:
        logfire.error(f"Error handling query: {e}")
        return "Sorry, an error occurred while processing your query."
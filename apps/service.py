import logfire,os
from apps.agents.graph import rag_agent
from fastapi import HTTPException
from apps.guardrails.rails import guard
from apps.services.gcp.redis_scemantic_cache import search_in_cache, initialize_cache, add_to_cache


def handel_query(query:str,conversation_id:str):
    """
    This function serves as the main handler for incoming user queries. It takes the query and conversation ID,
    constructs the initial state for the agent, and runs the agent to get a response.
    """
    try:
        # checking semantic cache first
        cache_response = search_in_cache(query)
        if cache_response:
            logfire.info(f"cache hit for query: {query}")
            return {
                "question": query,
                "answer": cache_response,
                "thought_process": "Answer retrieved from semantic cache.",
                "status": "Cache Hit",
                "sources": []
            }
        logfire.info(f"Handling query: {query} for conversation_id: {conversation_id}")
        initial_state = {
            "messages" : [{"role":"user","content":query}],
            "current_query":query,
            "documents":[],
            "plan":["Start"],
            "status":"Initializing Graph......",
            "retrieval_attempts": 0,
            "grader_approved": "",
        }

        config = {"configurable": {"thread_id": conversation_id}}
        try:
            rail_fired, rail_response = guard(query)
            if rail_fired:
                logfire.warning(f"Guardrail triggered for query: {query}. Response: {rail_response}")
                return {
                    "question": query,
                    "answer": rail_response,
                    "thought_process": "Guardrail triggered. Query blocked.",
                    "status": "Guardrail Triggered",
                    "sources": []
                }
        except Exception as e:
            logfire.error(f"Error in guardrail check: {e}")
            raise HTTPException(status_code=500, detail="Error in guardrail check")
        final_output = rag_agent.invoke(initial_state, config=config)

        # adding to cache if answer is present in final output
        if final_output.get("answer"):
            add_to_cache(query, final_output.get("answer", ""))
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
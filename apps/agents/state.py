from typing import TypedDict,List,Annotated
import operator

class AgentState(TypedDict):    
    """
    Tracks the global state of the agentic RAG pipeline.

    Maintains the appending message log, current processing target, retrieved 
    document context, dynamic execution steps, system status, and the final response string.
    """
    messages : Annotated[List[dict],operator.add]
    current_query : str
    documents : List[str]
    plan : List[str]
    status : str
    final_ans : str
    retrieval_attempts : int
    grader_approved : str
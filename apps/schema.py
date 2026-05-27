from pydantic import BaseModel
from typing import Optional


class QueryRequest(BaseModel):
    query : str
    conversation_id : Optional[str] = "default_conversation"
    
from pydantic import BaseModel

class ChatRequest(BaseModel):
    message: str
    session_id: str

class SnippetRequest(BaseModel):
    snippet_id: str
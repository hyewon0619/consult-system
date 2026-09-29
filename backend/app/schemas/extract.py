from pydantic import BaseModel

class ExtractRequest(BaseModel):
    text: str
    topic_code: str

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class CaseResult(BaseModel):
    rank: int
    id: str = Field(..., alias="eng_inci_id")
    title: str = Field(..., alias="success_story_title")
    score: float
    matched_keywords: List[str] = Field(default_factory=list)
    contents: Dict[str, Any] = Field(default_factory=dict, description="원본 상세 데이터 전체")

    class Config:
        populate_by_name = True


class SearchRequest(BaseModel):
    text: str
    category: str
    customer_address: Optional[str] = None
    authority_name: Optional[str] = None

from pydantic import BaseModel
from typing import Any, Dict

class FullReportRequest(BaseModel):
    persona_data: Any  # Step 2에서 추출된 데이터
    example_case: Dict[str, Any]  # Step 3에서 선택된 유사 사례
    office: str
    specialty: str
    status: str
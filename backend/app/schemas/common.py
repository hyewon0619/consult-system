from pydantic import BaseModel, Field, field_validator
from typing import Optional, Literal, Any

def clean_numeric_string(v: Any) -> int:
    if isinstance(v, str):
        v = v.replace(',', '').strip()
        try: return int(v)
        except ValueError: return -1
    return v if isinstance(v, int) else -1

class 고객_기본_정보(BaseModel):
    성함: Optional[str] = Field(None, description="고객(의뢰인)의 이름")
    성별: Literal['남', '여', '모름'] = Field("모름")
    연락처: Optional[str] = Field(None, description="전화번호 (모르면 [확인필요])")
    주소: Optional[str] = Field(None, description="대한민국에서 거주하는 지역 (모르면 [확인필요])")
    관할_기관: Optional[str] = Field(None, description="사건 관련 관할 기관 (경찰서, 검찰청, 법원 등)")
    
class 상담_설정_정보(BaseModel):
    변호사_조력_원하는_부분: Optional[str] = Field(None)
    변호사_선임_의사: Literal["변호사 선임 희망", "변호사 선임 고려", "상담 후 검토", "모름"] = Field("모름")
    비용_안내_여부: Literal['예', '아니오', '모름'] = "모름"

class 상담_결과_요약(BaseModel):
    기타_사실관계_및_특이사항: Optional[str] = Field(None)

class Module_Identity(BaseModel):
    고객_정보: 고객_기본_정보
    상담_설정: 상담_설정_정보

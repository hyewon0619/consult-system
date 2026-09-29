from app.common.config import settings

from pydantic import BaseModel, Field
from typing import List, Literal, Dict, Optional, ClassVar
from app.common.registry import register_topic

# --- 하위 모듈 스키마 정의 ---
class 상대방_인적사항(BaseModel):
    이름: Optional[str] = Field(default=None, description="성명 모를 경우 null")
    나이: Optional[int] = Field(default=None, description="나이 모를 경우 null")
    전화번호: Optional[str] = Field(default=None, description="연락처 모를 경우 null")
    주소: Optional[str] = Field(default=None, description="주소 모를 경우 null")

class 피해_내역_상세(BaseModel):
    발생_원인: Optional[str] = Field(default=None, description="사고 경위 상세")
    적극손해_금액: Optional[str] = Field(default=None, description="예: '2,000,000'")
    적극손해_상세: Optional[str] = Field(default=None)
    소극손해_금액: Optional[str] = Field(default=None)
    소극손해_상세: Optional[str] = Field(default=None)
    총_합계: Optional[str] = Field(default=None)
1
class 증거_및_정황(BaseModel):
    증거_유무: Optional[Literal["예", "아니오", "불명확"]] = Field(default="불명확")
    증거_목록: List[str] = Field(default_factory=list)

# --- 모듈 조합용 스키마 (get_required_modules 대응) ---

class Module_Defendant(BaseModel):
    상대방_인적사항: 상대방_인적사항

class Module_Damage(BaseModel):
    피해_내역: 피해_내역_상세

class Module_Evidence(BaseModel):
    증거_및_정황: 증거_및_정황

# --- 메인 템플릿 등록 ---

@register_topic("손해배상")
class T_CIV_001_Payload(BaseModel):
    """
    주제: 민사(손해배상)
    템플릿 ID: T-CIV-001
    """
    상대방_인적사항: 상대방_인적사항
    피해_내역: 피해_내역_상세
    증거_및_정황: 증거_및_정황

    @classmethod
    def get_required_modules(cls):
        return [
            ("DEFENDANT", Module_Defendant),
            ("DAMAGE", Module_Damage),
            ("EVIDENCE", Module_Evidence)
        ]

    @classmethod
    def assemble(cls, results_dict: dict):
        # 여러 모듈에서 온 결과를 하나로 합침
        return cls(**results_dict)

    PROMPTS: ClassVar[Dict[str, Dict[str, str]]] = {
        "DEFENDANT": {
            "system": "당신은 손해배상 사건의 '상대방 정보 식별' 전문가입니다. 피해를 입힌 가해자(상대방)의 인적사항을 정확히 추출하십시오.",
            "rules": """
            1. 인적사항 식별: [Original Text]에서 상대방의 이름, 나이, 연락처, 주소 정보를 찾으십시오.
            2. **엄격한 근거주의**: [Original Text]에 명시되지 않은 정보는 추측하여 채우지 말고 반드시 null로 기재하십시오. 
            3. 화자 구분: 피해를 입은 본인을 '의뢰인', 피해를 입힌 대상자를 '상대방'으로 명확히 구분하십시오.
            4. 결측치 처리: 정보가 없으면 반드시 키를 포함하고 null로 기재하십시오.
            """,
            "format": """{ "상대방_인적사항": { "이름": "str|null", "나이": "int|null", "전화번호": "str|null", "주소": "str|null" } }""",
            "example": """{ "상대방_인적사항": { "이름": "김철수", "나이": null, "전화번호": "010-1234-5678", "주소": null } }"""
        },

        "DAMAGE": {
            "system": f"당신은 {settings.FIRM_NAME}의 '피해 규모 분석' 전문가입니다. 발생 원인과 손해액을 법률적 기준에 따라 분류하십시오.",
            "rules": """
            1. 발생 원인: 사고 경위를 육하원칙에 의거하여 상세히 서술하되, [Original Text]에 없는 사실을 지어내지 마십시오. (최대 3문장 내외)
            2. **금액 산출 및 포맷**: 
               - 모든 금액은 반드시 3자리마다 콤마(,)가 포함된 문자열로 기재하십시오. (예: "2,000,000")
               - 숫자 단위 변환 주의: '5000만원' -> "50,000,000", '1억' -> "100,000,000"으로 정확히 환산하십시오.
            3. 적극/소극 손해 구분:
               - 적극손해: 치료비, 수리비 등 직접 지출된 비용
               - 소극손해: 일실수입(사고로 인해 벌지 못한 돈) 등 간접적 손해
               - 정보가 없거나 불분명하면 '금액' 필드에 null을 기재하십시오.
            4. **산술 일치성**: [총_합계]는 반드시 [적극손해_금액] + [소극손해_금액]의 합계여야 합니다. 텍스트상 합계가 명시되지 않았다면 계산 가능한 범위 내에서 합산하십시오.
            """,
            "format": """{ "피해_내역": { "발생_원인": "str", "적극손해_금액": "str|null", "적극손해_상세": "str", "소극손해_금액": "str|null", "소극손해_상세": "str", "총_합계": "str|null" } }""",
            "example": """{ "피해_내역": { "발생_원인": "2024년 1월 1일 서초역 인근에서 상대방 차량이 의뢰인의 차량 후미를 추돌함.", "적극손해_금액": "1,500,000", "적극손해_상세": "차량 수리비 120만원 및 병원 진단비 30만원", "소극손해_금액": "500,000", "소극손해_상세": "3일간의 휴업 손해", "총_합계": "2,000,000" } }"""
        },

        "EVIDENCE": {
            "system": "당신은 '증거 자산 검토' 전문가입니다. 소송에 활용 가능한 증거 유무와 목록을 식별하십시오.",
            "rules": """
            1. 증거 유무: [예, 아니오, 불명확] 중 하나를 선택하십시오. 텍스트에 증거 제출 언급이 있다면 "예", 아예 없다면 "불명확"을 기본값으로 합니다.
            2. 증거 목록: 텍스트에서 명시적으로 언급된 증거(블랙박스, 진단서, 영수증, 카톡 캡처 등)만 리스트에 넣으십시오. **주관적인 견해나 추측되는 증거는 넣지 마십시오.**
            """,
            "format": """{ "증거_및_정황": { "증거_유무": "예/아니오/불명확", "증거_목록": ["str"] } }""",
            "example": """{ "증거_및_정황": { "증거_유무": "예", "증거_목록": ["현장 사진", "수리비 영수증"] } }"""
        }
    }
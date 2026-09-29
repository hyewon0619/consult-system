from app.common.config import settings

from pydantic import BaseModel, Field
from typing import List, Literal, ClassVar, Dict, Optional
from app.common.registry import register_topic

class 자녀_정보(BaseModel):
    전체_자녀수: Optional[int] = Field(default=None, description="정보 모를 경우 null")
    미성년_자녀수: Optional[int] = Field(default=None, description="정보 모를 경우 null")

class 인적_사항(BaseModel):
    직업: Optional[str] = Field(default=None, description="직업 모를 경우 null")
    소득_유형: Optional[Literal["연봉", "월급"]] = Field(default=None, description="유형 모를 경우 null")
    소득: Optional[str] = Field(default=None, description="소득 모를 경우 null, 예: '6,500,000'")
    세금_유형: Optional[Literal["세전", "세후"]] = Field(default=None, description="유형 모를 경우 null")

class 재산_항목(BaseModel):
    구분: Literal["자산", "부채"]
    명의: Optional[Literal["의뢰인", "배우자", "공동", "제3자"]] = Field(default=None)
    항목명: str
    가액원: Optional[str] = Field(default=None, description="가액 모를 경우 null, 예: '1,200,000,000'")

class 이혼_사유_상세(BaseModel):
    핵심_원인_카테고리: Optional[Literal[
        "부정행위(외도)", 
        "악의적 유기", 
        "부당한 대우(폭행/폭언)", 
        "직계존속에 대한 부당한 대우", 
        "생사 불명", 
        "기타 혼인을 계속하기 어려운 사유", 
        "성격 차이"
    ]] = Field(default=None, description="판단 불가시 null")
    
    구체적_파탄_경위: Optional[str] = Field(
        default=None, 
        description="육하원칙에 따른 상세 사유. 정보 부족시 null"
    )

class Module_Relationship(BaseModel):
    자녀수: 자녀_정보
    혼인기간_년: Optional[int] = None
    혼인기간_개월: Optional[int] = None
    이혼_의사: Optional[Literal["일방적", "쌍방"]] = None
    이혼_사유: 이혼_사유_상세
    양육권_희망: Optional[Literal["배우자", "의뢰인", "쌍방", "자녀 없음"]] = None

class Module_Income(BaseModel):
    의뢰인: 인적_사항
    배우자: 인적_사항

class Module_Assets(BaseModel):
    재산목록_및_가액: List[재산_항목]

@register_topic("이혼")
class T_FAM_001_Payload(BaseModel):
    """
    주제: 이혼
    템플릿 ID: T-FAM-001
    """
    자녀수: 자녀_정보
    혼인기간_년: Optional[int] = None
    혼인기간_개월: Optional[int] = None
    의뢰인: 인적_사항
    배우자: 인적_사항
    재산목록_및_가액: List[재산_항목] = Field(default_factory=list)
    이혼_의사: Optional[Literal["일방적", "쌍방"]] = None
    이혼_사유: 이혼_사유_상세
    양육권_희망: Optional[Literal["배우자", "의뢰인", "쌍방", "자녀 없음"]] = None

    @classmethod
    def get_required_modules(cls):
        return [
            ("RELATIONSHIP", Module_Relationship),
            ("INCOME", Module_Income),
            ("ASSETS", Module_Assets)
        ]

    @classmethod
    def assemble(cls, results_dict: dict):
        return cls(**results_dict)

    PROMPTS: ClassVar[Dict[str, Dict[str, str]]] = {
        "RELATIONSHIP": {
            "system": "당신은 가사 소송 전문가입니다. 혼인 기간, 자녀 유무, 이혼 의사 등 소송의 핵심이 되는 인적 사실관계를 추출합니다.",
            "rules": """
            **정보가 없어도 반드시 키를 포함하고 null을 넣으십시오**
            1. 자녀: 자녀가 없다면 전체_자녀수와 미성년_자녀수를 0으로 명시하고, 양육권_희망은 "자녀 없음"을 선택하십시오.
            2. 이혼 의사: 한 쪽이라도 이혼을 거부한다면 "일방적"으로 기재하십시오.
            3. 혼인 기간: 년과 개월을 각각 분리하여 기재하십시오. 정보가 불명확할 경우 null로 기재하십시오.
            4. 이혼 사유 작성:
               - [핵심_원인_카테고리]는 법적 사유 중 하나를 택하되, 알 수 없으면 null입니다.
               - [구체적_파탄_경위]는 [Original Text]에 명시된 사실에만 근거하여 절대로 지어내지 말고 이혼 사유를 두 문장 내로 서술하십시오.
            """,
            "format": """{
            "자녀수": { "전체_자녀수": "int | null", "미성년_자녀수": "int | null" },
            "혼인기간_년": "int | null", "혼인기간_개월": "int | null",
            "이혼_의사": "일방적 / 쌍방 / null",
            "이혼_사유": {
                    "핵심_원인_카테고리": "부정행위(외도)", "악의적 유기", "부당한 대우(폭행/폭언)", "직계존속에 대한 부당한 대우", "생사 불명", "기타 혼인을 계속하기 어려운 사유", "성격 차이" / null",
                    "구체적_파탄_경위": "문자열 (최소 2문장 이상 상세 서술)"
                },
            "양육권_희망": "쌍방 / 의뢰인 / 배우자 / 자녀 없음 / null"
            }""",
            "example": """{
            "자녀수": { "전체_자녀수": 1, "미성년_자녀수": 0 },
            "혼인기간_년": 2, "혼인기간_개월": null,
            "이혼_의사": "쌍방", 
            "이혼_사유": {
                "핵심_원인_카테고리": "부당한 대우(폭행/폭언)",
                "구체적_파탄_경위": "상세히 기술..."
            }
            "양육권_희망": "의뢰인"
            }"""
        },

        "INCOME": {
            "system": f"당신은 {settings.FIRM_NAME}의 '소득 지표 분석' 전문가입니다. 의뢰인과 배우자의 직업(job), 소득, 세금 유형을 정확히 작성하십시오.",
            "rules": """
            1. 화자 구분: '저', '제가'는 의뢰인, 그 상대방은 배우자로 구분합니다.
                - 의뢰인과 배우자의 직업을 [Original Text]에서 추론하여 반드시 정확하게 작성하십시오. 정보가 불명확하면 null로 기재하십시오.
            2. 연봉/월급: 소득이 없거나 알 수 없는 경우, 소득_유형과 세금_유형은 반드시 null로 기재하십시오.
            3. 결측치 vs 0원 구분:
               - "수입이 없다", "무직이다", "놀고 있다"라고 명시한 경우에만 "0"으로 표기하십시오.
               - 소득 언급이 없거나 불명확한 경우에는 반드시 null로 표기하십시오.
            4. 금액 포맷: 소득(income)이 [Original Text]에 명시된 경우에만 3자리마다 콤마(,)를 찍은 문자열로 반환하십시오. (예: "6,500,000")
                - 예) '6500' -> 65,000,000
            5. 달러 환산: 달러는 1300원 환율 적용 후 원화로 표기하십시오.
            """,            
            "format": """{
                "의뢰인": { "직업": "str | null", "소득_유형": "연봉/월급 | null", "소득": "str | null", "세금_유형": "세전/세후 | null" },
                "배우자": { "직업": "str | null", "소득_유형": "연봉/월급 | null", "소득": "str | null", "세금_유형": "세전/세후 | null" }
            }""",
            "example": """{
                "의뢰인": { "직업": "IT 엔지니어", "소득 유형": "모름", "소득": "6,000,000", "세금 유형": "세후" },
                "배우자": { "직업": "공무원", "소득 유형": "연봉", "소득": 65,000,000, "세금 유형": "null" }
            }""",
        },

        "ASSETS": {
            "system": "당신은 재산 분할 전문가입니다. [Original Text]를 기반으로 상담 내용에 언급된 자산과 부채 목록을 추출하세요.",
            "rules": """
            1. 반드시 [Original Text]에 언급된 재산(stock) 항목만 기재하십시오. 알 수 없는 항목은 포함하지 마십시오.
            2. 대상: 부동산, 예적금, 보험, 가상자산, 대여금(빌려준 돈) 등 (단순 월급(생활비) 등 현금 흐름은 포함하지 마십시오.).
            3. 부채: 대출, 빚 등은 구분값을 "부채"로 설정하십시오.
            4. [매우 중요] 한국어 숫자 변환:
               - 단위가 '천만원'일 경우 0이 7개 붙습니다. (10,000,000)
               - 예) '6000만원' -> 6,000,000(X) 틀림 -> 60,000,000(O) 정답
               - 예) '오천만원' -> 50,000,000
               - 예) '16억' -> 1,600,000,000
               - 모든 결과는 3자리 콤마 포맷을 적용하십시오. ("20,000,000")
            5. 결측치 처리: 가액이나 명의를 알 수 없는 경우 null을 반환하십시오.
            
            """,
            "format": """{
            "재산목록_및_가액": [
                { "구분": "자산/부채", "명의": "의뢰인/배우자/공동/제3자 | null", "항목명": "str", "가액원": "str | null" }
            ]
            }""",
            "example": """{
            "재산목록_및_가액": [
                { "구분": "자산", "명의": "공동", "항목명": "아파트", "가액원": "null" },
                { "구분": "자산", "명의": "의뢰인", "항목명": "대여금", "가액원": "20,000,000" },
                { "구분": "부채", "명의": null, "항목명": "주택담보대출", "가액원": "450,000,000" }
            ]
            }"""
        },
    }
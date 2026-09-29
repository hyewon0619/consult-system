import re
from pydantic import BaseModel, Field
from typing import List, Literal, ClassVar, Dict, Optional

try:
    from app.common.registry import register_topic
except ImportError:
    # 테스트를 위해 데코레이터가 없어도 동작하도록 더미 함수 생성
    def register_topic(name):
        def decorator(cls):
            return cls
        return decorator

def extract_date(text: Optional[str]) -> str:
    """
    날짜 추출 함수:
    1. 구체적인 날짜(YYYY년 MM월 DD일)가 있으면 'YYYY-MM-DD'로 변환.
    2. '어제', '오늘', '지난주' 등의 표현이면 변환 없이 그대로 반환.
    """
    if not text or text == "null":
        return "없음"

    # 1. 구체적인 날짜 패턴 (YYYY년 MM월 DD일, YYYY.MM.DD 등) 감지 시 포맷팅
    date_pattern = r"(\d{4})[년.\s-]*(\d{1,2})[월.\s-]*(\d{1,2})[일.\s]*"
    match = re.search(date_pattern, text)

    if match:
        year = match.group(1)
        month = match.group(2).zfill(2)
        day = match.group(3).zfill(2)
        return f"{year}-{month}-{day}"

    # 2. 이미 YYYY-MM-DD 형식이면 그대로 반환
    if re.search(r"\d{4}-\d{2}-\d{2}", text):
        return text.strip()

    # 3. 날짜 패턴이 없으면(예: "어제", "사고 당일") 원본 텍스트 그대로 반환
    return text.strip()


def extract_location(text: Optional[str]) -> str:
    """
    장소 추출 함수:
    LLM이 이미 짧게 추출해준 경우(50자 미만) 그대로 반환하고,
    긴 문장일 경우에만 정규식으로 주소를 찾습니다.
    """
    if not text or text == "null":
        return "없음"

    if len(text) < 50:
        return text

    # 긴 텍스트인 경우 주소 패턴 찾기 시도
    location_pattern = r"([가-힣]+(?:시|도|특별시|광역시))\s+([가-힣]+(?:구|군|시))\s+([가-힣]+(?:동|읍|면))"
    match = re.search(location_pattern, text)

    if match:
        return match.group(0)

    return "없음"

class 사건_상대방_정보(BaseModel):
    이름: Optional[str] = Field(default=None)
    나이: Optional[int] = Field(default=None)
    전화번호: Optional[str] = Field(default=None)
    주소_또는_소재지: Optional[str] = Field(default=None, alias="주소")
    관계: Optional[str] = Field(default=None, description="피의자와의 관계")


class 범죄_사실관계_상세(BaseModel):
    죄명: Optional[str] = Field(default=None)
    발생_원인: Optional[str] = Field(default=None, description="사건의 핵심 원인(요약)")
    발생_경위: Optional[str] = Field(default=None, description="시간 순서에 따른 상세 상황")
    사건발생일: Optional[str] = Field(default=None)
    사건발생지: Optional[str] = Field(default=None)
    피해_내용: Optional[str] = Field(default=None)
    피해_금액: Optional[str] = Field(default=None)


class 절차_진행_현황(BaseModel):
    신고_여부: Optional[Literal["신고전", "신고완료", "불송치", "수사중", "재판중", "확정"]] = Field(default=None)
    관할기관: Optional[str] = Field(default=None)
    현재_단계_설명: Optional[str] = Field(default=None)


class 증거_및_정황(BaseModel):
    증거_유무: Optional[Literal["예", "아니오", "불명확"]] = Field(default=None)
    증거_목록: List[str] = Field(default_factory=list)


class 합의_및_리스크(BaseModel):
    합의_여부: Optional[Literal["합의전", "진행중", "완료", "불가"]] = Field(default=None)
    변호사_선임의사: Optional[Literal["선임희망", "고려", "검토", "모름"]] = Field(default=None)
    맞고소_가능성: Optional[bool] = Field(default=None)
    특이_리스크: Optional[str] = Field(default=None)


class Prompt_Result_Criminal(BaseModel):
    상대방_정보: 사건_상대방_정보
    # LLM이 추출한 Raw Data를 담는 딕셔너리
    피해_내역: Dict[str, Optional[str]] = Field(description="발생_원인, 발생_경위, 적극손해, 소극손해, 총_합계, 사건발생일, 사건발생지, 피해_내용")
    증거_및_정황: 증거_및_정황


@register_topic("기타")
class T_CRI_001_Payload(BaseModel):
    """
    주제: 형사 (일반/교통/기타)
    템플릿 ID: T-CRI-001
    """
    상대방: Optional[사건_상대방_정보] = Field(default=None)
    사실관계: Optional[범죄_사실관계_상세] = Field(default=None)
    절차정보: Optional[절차_진행_현황] = Field(default=None)
    증거정보: Optional[증거_및_정황] = Field(default=None)
    리스크정보: Optional[합의_및_리스크] = Field(default=None)

    @classmethod
    def get_required_modules(cls):
        return [
            ("CRIMINAL_PAYLOAD", Prompt_Result_Criminal)
        ]

    @classmethod
    def assemble(cls, results_dict: dict):
        opponent_data = results_dict.get("상대방_정보", {})
        damage_info = results_dict.get("피해_내역", {})
        evidence_data = results_dict.get("증거_및_정황", {})

        # 1. 발생 원인
        cause_text = damage_info.get("발생_원인", "없음")

        # 2. 발생 경위 (중복 방지)
        raw_details = damage_info.get("발생_경위")
        if not raw_details or raw_details.strip() == cause_text.strip():
            final_details = "없음"
        else:
            final_details = raw_details

        raw_damage_content = damage_info.get("피해_내용")
        if not raw_damage_content:
            details = []
            if damage_info.get("적극손해"): details.append(f"직접피해: {damage_info.get('적극손해')}")
            if damage_info.get("소극손해"): details.append(f"간접피해: {damage_info.get('소극손해')}")
            raw_damage_content = " / ".join(details) if details else cause_text

        raw_date = damage_info.get("사건발생일")
        if not raw_date: raw_date = cause_text
        사건발생일_final = extract_date(raw_date)

        raw_location = damage_info.get("사건발생지")
        if not raw_location: raw_location = cause_text
        사건발생지_final = extract_location(raw_location)

        피해금액 = damage_info.get("피해_금액", damage_info.get("총_합계", "없음"))

        target_fact = 범죄_사실관계_상세(
            발생_원인=cause_text,
            발생_경위=final_details,
            피해_내용=raw_damage_content,
            피해_금액=피해금액,
            죄명=None,
            사건발생일=사건발생일_final,
            사건발생지=사건발생지_final
        )

        return cls(
            상대방=사건_상대방_정보(**opponent_data) if opponent_data else None,
            사실관계=target_fact,
            절차정보=None,
            증거정보=증거_및_정황(**evidence_data) if evidence_data else None,
            리스크정보=None
        )

    PROMPTS: ClassVar[Dict[str, Dict[str, str]]] = {
        "CRIMINAL_PAYLOAD": {
            "system": "당신은 법률 상담 녹취록 분석 전문가입니다. 의뢰인의 진술을 토대로 사실관계를 명확히 구분(누가 가해자인지)하여 JSON으로 추출합니다.",
            "rules": """
            [상대방 정보 규칙]
            1. 이름/나이 불명확 시 null.

            [피해 내역 및 사실관계 규칙]
            2. 발생_원인: 사고의 핵심 원인을 '주어(누가)'를 명시하여 1문장 요약. (문맥상 의뢰인이 가해자인지 피해자인지 정확히 파악할 것)
            3. 발생_경위: 사건의 전후 사정 서술. (발생_원인과 완전히 동일하게 작성하지 말 것)
            4. **사건발생일**: **원본 텍스트에 있는 표현 그대로 추출**하십시오.
               - 예: '어제', '오늘', '지난주', '2024년 5월 1일' 등.
               - 임의로 날짜를 계산해서 변환하지 마십시오.
            5. 사건발생지: 유추 가능한 지역명(예: 평택).
            6. 피해_내용: 차량 파손 부위, 인명 피해 등 구체적 서술.

            [증거 규칙]
            7. 증거_유무: 예/아니오/불명확
            8. 증거_목록: 구체적 명사 리스트
            """,
            "format": """{
                "상대방_정보": {
                    "이름": "str | null",
                    "나이": "int | null",
                    "전화번호": "str | null",
                    "주소": "str | null"
                },
                "피해_내역": {
                    "발생_원인": "str",
                    "발생_경위": "str | null",
                    "사건발생일": "str (예: 어제, 2024년 5월 1일)",
                    "사건발생지": "str",
                    "피해_내용": "str", 
                    "적극손해": "str | null",
                    "소극손해": "str | null",
                    "총_합계": "str | null"
                },
                "증거_및_정황": {
                    "증거_유무": "예 / 아니오 / 불명확",
                    "증거_목록": "list | null"
                }
            }""",
            "example": """{
                "상대방_정보": { "이름": null, "나이": null, "전화번호": null, "주소": null },
                "피해_내역": {
                    "발생_원인": "의뢰인의 졸음운전 및 중앙선 침범",
                    "발생_경위": "음주 후 졸음운전을 하던 중 중앙선을 침범하여 반대편 차량을 충격하였으나 이를 인지하지 못하고 귀가함",
                    "사건발생일": "어제",
                    "사건발생지": "평택",
                    "피해_내용": "의뢰인 차량 앞 범퍼 파손 및 상대 차량 운전석 측 충격",
                    "적극손해": null,
                    "소극손해": null,
                    "총_합계": null
                },
                "증거_및_정황": { "증거_유무": "예", "증거_목록": ["블랙박스"] }
            }"""
        }
    }

#성범죄
@register_topic("성범죄")
class T_CRI_002_Payload(BaseModel):
    """
    주제: 형사 (성범죄/강간/추행)
    템플릿 ID: T-CRI-002
    """
    상대방: Optional[사건_상대방_정보] = Field(default=None)
    사실관계: Optional[범죄_사실관계_상세] = Field(default=None)
    절차정보: Optional[절차_진행_현황] = Field(default=None)
    증거정보: Optional[증거_및_정황] = Field(default=None)
    리스크정보: Optional[합의_및_리스크] = Field(default=None)

    @classmethod
    def get_required_modules(cls):
        return [
            ("SEXUAL_CRIME_PAYLOAD", Prompt_Result_Criminal)
        ]

    @classmethod
    def assemble(cls, results_dict: dict):
        opponent_data = results_dict.get("상대방_정보", {})
        damage_info = results_dict.get("피해_내역", {})
        evidence_data = results_dict.get("증거_및_정황", {})

        cause_text = damage_info.get("발생_원인", "없음")

        raw_details = damage_info.get("발생_경위")
        if not raw_details or raw_details.strip() == cause_text.strip():
            final_details = "없음"
        else:
            final_details = raw_details

        raw_damage_content = damage_info.get("피해_내용")
        if not raw_damage_content:
            raw_damage_content = cause_text

        raw_date = damage_info.get("사건발생일")
        if not raw_date: raw_date = cause_text
        사건발생일_final = extract_date(raw_date)

        raw_location = damage_info.get("사건발생지")
        if not raw_location: raw_location = cause_text
        사건발생지_final = extract_location(raw_location)

        target_fact = 범죄_사실관계_상세(
            발생_원인=cause_text,
            발생_경위=final_details,
            피해_내용=raw_damage_content,
            피해_금액=None,
            죄명=None,
            사건발생일=사건발생일_final,
            사건발생지=사건발생지_final
        )

        return cls(
            상대방=사건_상대방_정보(**opponent_data) if opponent_data else None,
            사실관계=target_fact,
            절차정보=None,
            증거정보=증거_및_정황(**evidence_data) if evidence_data else None,
            리스크정보=None
        )

    PROMPTS: ClassVar[Dict[str, Dict[str, str]]] = {
        "SEXUAL_CRIME_PAYLOAD": {
            "system": "당신은 성범죄 전문 법률 상담 분석가입니다. 의뢰인의 진술을 토대로 사건의 강제성, 관계, 피해 사실을 정확하게 파악하여 JSON으로 추출합니다.",
            "rules": """
                [상대방 정보 규칙]
                1. **관계**: 피의자와 피해자의 관계를 명확한 단어로 명시하십시오.
                   - (예: 직장 상사, 전 연인, **소개팅 상대방**, **처음 본 남성**, 모르는 사람 등)
                   - 줄임말(예: ~남, ~녀)보다는 '남성', '여성', '남자', '여자' 등으로 풀어서 쓰십시오.
                2. 신상정보가 불명확하면 null.

                [사실관계 및 피해 내역 규칙]
                3. **발생_원인**: 사건의 핵심 혐의(강간, 준강간, 강제추행 등)와 직접적인 원인 행위를 1문장 요약.
                   - 예: "술에 취해 항거불능 상태인 의뢰인을 모텔로 데려가 간음함"
                4. **발생_경위**: 사건 전후 상황을 육하원칙으로 서술.
                   - 중요 체크 포인트: **음주 여부, 폭행/협박 여부, 동의 여부, 장소 이동 경위**.
                5. **사건발생일**: **원본 텍스트에 있는 표현 그대로 추출**하십시오. (임의 변환 금지)
                6. **사건발생지**: 구체적 장소 (예: 홍대 인근 모텔, 피의자의 자취방, 지하철 등).
                7. **피해_내용**: 구체적인 피해 사실.
                   - 신체적 접촉 부위, 성관계 여부, 상해 발생 여부, 불법 촬영 여부 등.

                [증거 규칙]
                8. 증거_목록: CCTV, 카카오톡/문자 내역, 통화 녹음, 해바라기센터 키트, 산부인과 진단서, 숙박업소 결제 내역 등.
                """,
            "format": """{
                    "상대방_정보": {
                        "이름": "str | null",
                        "나이": "int | null",
                        "전화번호": "str | null",
                        "주소": "str | null",
                        "관계": "str | null"
                    },
                    "피해_내역": {
                        "발생_원인": "str",
                        "발생_경위": "str | null",
                        "사건발생일": "str (예: 어제, 2024년 5월 1일)",
                        "사건발생지": "str",
                        "피해_내용": "str", 
                        "적극손해": "null",
                        "소극손해": "null",
                        "총_합계": "null"
                    },
                    "증거_및_정황": {
                        "증거_유무": "예 / 아니오 / 불명확",
                        "증거_목록": "list | null"
                    }
                }""",
            "example": """{
                    "상대방_정보": { 
                        "이름": "김OO", 
                        "나이": null, 
                        "전화번호": null, 
                        "주소": null,
                        "관계": "직장 상사"
                    },
                    "피해_내역": {
                        "발생_원인": "직장 회식 후 만취한 피해자를 숙박업소로 데려가 준강간함",
                        "발생_경위": "2차 회식에서 필름이 끊길 정도로 술을 마셨는데, 눈을 떠보니 모텔이었고 옷이 벗겨져 있었음. 상대방은 합의하에 했다고 주장하나 기억이 전혀 없음.",
                        "사건발생일": "지난주 금요일 밤",
                        "사건발생지": "강남역 인근 모텔",
                        "피해_내용": "심신상실 상태에서의 간음 피해, 성기 통증 및 정신적 충격",
                        "적극손해": null,
                        "소극손해": null,
                        "총_합계": null
                    },
                    "증거_및_정황": { 
                        "증거_유무": "예", 
                        "증거_목록": ["숙박업소 CCTV", "카드 결제 내역", "사건 직후 주고받은 카톡"] 
                    }
                }"""
        }
    }
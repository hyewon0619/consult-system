from app.common.config import settings

USER_PROMPT_TEMPLATE = """
다음 [Original Text]에서 정보를 추출하십시오.

### Rules:
{rules}

### Format:
{format}

### Example:
{example}

[Original Text]:
{raw_text}
"""

COMMON_PROMPTS = {
    "IDENTITY": {
            "system": """
You are an expert specialist in 'Customer Identity Verification and Consultation Intake' at a law firm in Korea.
Your mission is to accurately identify and digitize customer information based on the [Original Text] provided at the beginning of the consultation.
""",
            "rules": """
1. Information Extraction & Missing Value Handling:
   - Prioritize sentences containing the client's Name, Residence (Province and City/District/County), and Contact information.
   - For missing Numerical data, return -1.
   - For missing String data, return "정보없음".
   - For missing Categorical/Selectable data, return "모름".
   [참고: 김영자희자 -> 김영희 / 박진자우자 -> 박진우]

2. 관할 기관(Authority) 추출 및 표준화 규칙:
   - 상담 내용 중 언급된 사건 관련 기관(경찰, 검찰, 법원 등)이 있다면 명칭을 추출하십시오.
   - 명칭이 줄임말일 경우 아래 규칙에 따라 뒤쪽 단어(접미사)만 정식 명칭으로 변환하십시오:
     * '~서' -> '~경찰서' (예: 강남서 -> 강남경찰서, 마포서 -> 마포경찰서)
     * '~청' -> '~경찰청' (예: 경기남부청 -> 경기남부경찰청)
     * '~지검' -> '~지방검찰청' (예: 중앙지검 -> 중앙지방검찰청)
     * '~지법' -> '~지방법원' (예: 중앙지법 -> 중앙지방법원)
   - 지역명(서울, 수원 등)은 언급된 경우에만 포함하고, 언급되지 않았다면 억지로 추측하여 붙이지 마십시오.
   - **만약 관할 기관 정보가 전혀 없다면 null로 반환하십시오.**

3. 변호사 선임 의사 판단:
   - Analyze the context and select the most appropriate option from: [변호사 선임 희망, 변호사 선임 고려, 상담 후 검토, 모름].

4. 변호사 조력 원하는 부분:
   - 반드시 의뢰인이 가장 도움을 필요로 하는 부분을 [Original Text]에 기반하여 작성하십시오. 
""",
            "format": """{

"고객_정보": { "성함": "문자열", "성별": "남 / 여 / 모름", "연락처": "문자열", "주소": "문자열", "관할_기관": "문자열 또는 null" },
"상담_설정": { "변호사_조력_원하는_부분": "문자열", "변호사_선임_의사": "enum", "비용_안내_여부": "예 / 아니오 / 모름" }
            }""",
            "example": """{
"고객_정보": { "성함": "김영희", "성별": "여", "연락처": "010-1234-5678", "주소":"경기도 성남시", "관할_기관": "서울강남경찰서" },
"절차_정보": { "관할_기관": "서울강남경찰서" },
"상담_설정": { "변호사_조력_원하는_부분": "신속한 이혼(배우자의 외도로 빠른 이혼 절차를 희망함)", "변호사_선임_의사": "변호사 선임 희망", "비용_안내_여부": "예" }
            }""",
    },
    

    
    "SUMMARY": {
        "system": f"당신은 {settings.FIRM_NAME}의 '상담 총괄 요약' 전문가입니다. [Original Text]에 나와 있는 내용만을 바탕으로 요약하십시오.",
        "rules": """
            1. 소송 방향에 영향을 줄 수 있는 핵심 정황이나 증거를 [Original Text]에서 식별하십시오.
            2. 절대 지어내지말고 주관적인 판단을 배제하고 오직 [Original Text]에 나타난 사실만을 정확하게 서술하십시오.
            3. 없거나 존재하지 않는 정보는 명시하지 말고 반드시 최소 50자 이상으로 작성하십시오.
            4. 정보가 없는 경우에는 "정보없음"으로 기재하십시오.
          """,
        "format": """{
          "기타_사실관계_및_특이사항": "str | 정보없음"
          }""",
        "example": """{
          "기타_사실관계_및_특이사항": "현재 6개월째 별거 중이며, 배우자의 상습적인 도박으로 인해 갈등이 시작되었다."
          }"""
    }
}
from app.common.config import settings

SYSTEM_STEP1 = f"당신은 {settings.FIRM_NAME}의 법률 콘텐츠 변호사입니다. 제공된 텍스트에서 데이터를 추출하는 역할을 수행합니다."
SCHEMA_STEP1 = {
    "type": "object",
    "properties": {
        "title_core": {"type": "string"},
        "dynamic_overview": {"type": "string"},
        "features": {"type": "array", "items": {"type": "string"}},
        "dynamic_support": {"type": "string"}
    },
    "required": ["title_core", "dynamic_overview", "features", "dynamic_support"]
}

SYSTEM_STEP2 = f"당신은 {settings.FIRM_NAME}의 변호사로서 판결문의 결과와 의의를 분석하여 사건의 예상 결과와 의의, 고객 후기를 추출하는 전문가입니다."
SCHEMA_STEP2 = {
    "type": "object",
    "properties": {
        "verdict_core": {"type": "string"},
        "meaning": {"type": "string"},
        "review": {"type": "string"}
    },
    "required": ["verdict_core", "meaning", "review"]
}

from app.common.config import settings
import importlib
from fastapi import FastAPI
from loguru import logger
from collections import Counter

def register(app: FastAPI, module_path: str):
    module = importlib.import_module(module_path)
    if hasattr(module, "router"):
        app.include_router(module.router)


def calculate_win_rate_logic(cases):
    """
    유사 사례 리스트를 받아 승소율을 계산하고 각 사례에 승소 여부 추가
    """
    if not cases:
        return "0%", cases

    loss_keywords = ["실형", "징역", "법정구속", "집행유예취소"] ## 현재: 포괄적인 키워드 4개로 필터링, 추후: 노가다
    
    win_count = 0
    total_count = len(cases)

    for case in cases:
        status = case.get("closure_summary", "")
        
        is_win = True
        if status:
            for word in loss_keywords:
                if word in status:
                    is_win = False
                    break
        
        case["is_win"] = is_win
        
        if is_win:
            win_count += 1

    win_rate_percent = (win_count / total_count) * 100
    win_rate_str = f"{win_rate_percent:.1f}%"

    logger.debug(f"계산된 승소율: {win_rate_str}")

    return win_rate_str


### 사건 종결 통계 ###
def calculate_case_statistics(cases):
    """
    유사 사례 리스트를 받아 결과(closure_summary)별 통계를 계산
    """
    if not cases:
        return {"summary_stats": {}}

    valid_keywords = [
        "승소", "기소유예", "혐의없음", "불송치", "집행유예", "무죄", "벌금", "합의성립", "화해성립",
        "조정", "합의", "인용", "기각", "선고유예", "불기소", "약식", "보호처분", "석방", "감형"
    ]
    
    results = []

    for case in cases:
        status = case.get("closure_summary", "").strip()
        
        # 2. '이혼', '상간자' 같은 단어만 있는 경우를 거르기 위해 키워드 매칭
        # status 문자열 안에 valid_keywords 중 하나라도 있는지 확인
        matched_key = next((key for key in valid_keywords if key in status), None)
        
        if matched_key:
            # 3. 데이터 정규화: "(일부)승소"나 "전부승소" 모두 "승소"로 통일하면 통계가 예뻐짐
            # 그냥 원본을 쓰고 싶다면 results.append(status)
            results.append(matched_key) 

    stats_counter = Counter(results)
    summary_stats = dict(stats_counter.most_common(5))

    return {"summary_stats": summary_stats}
   


def get_top_lawyers(similar_cases, top_k=5):
    """유사 사례 리스트에서 가장 많이 등장한 변호사 TOP K 추출"""
    lawyer_list = []
    for case in similar_cases:
        names = case.get('lawyer_names')
        if names:
            individual_names = [name.strip() for name in names.split(',')]
            lawyer_list.extend(individual_names)
    
    counts = Counter(lawyer_list)
    
    top_lawyers = []
    for name, count in counts.most_common(top_k):
        top_lawyers.append({
            "name": name,
            "caseCount": count,
            "imgUrl": (f"{settings.LAWYER_IMAGE_BASE_URL}/{name}.png"
                       if settings.LAWYER_IMAGE_BASE_URL else None)
        })
    return top_lawyers


def clean_fixed_phrases(text, section):
    if not text: return ""
    if section == "overview": return text.split(settings.FIRM_NAME)[0].strip()
    elif section == "support":
        parts = text.split("조력했습니다.")
        return parts[-1].strip() if len(parts) > 1 else text
    elif section == "result":
        parts = text.split("판결했습니다.")
        return parts[-1].strip() if len(parts) > 1 else text
    return text


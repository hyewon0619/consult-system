import requests
import json
import asyncio
import re

from typing import List

from loguru import logger
from fastapi import APIRouter
from fastapi import UploadFile, File
from fastapi.responses import StreamingResponse

from app.schemas.search_task import SearchRequest
from app.schemas.extract import ExtractRequest
from app.schemas.report import FullReportRequest

from app.common.config import settings
from app.prompts.persona_prompts import LegalPromptFactory, get_legal_schema
from app.prompts.report_prompts import SCHEMA_STEP1, SCHEMA_STEP2, SYSTEM_STEP1, SYSTEM_STEP2

from app.common.utils import calculate_win_rate_logic, get_top_lawyers, clean_fixed_phrases
from app.crud.read import fetch_cases_from_db_bulk, get_authority_statistics, get_authority_statistics_by_city
from app.core.engine import extract_full_legal_data
from app.services.llm_service import fetch_llm, get_reranked_results
from app.services.cal_amount import get_amount_static_by_periods
from app.services.search_engine import LegalESSearch
from app.common.utils import calculate_case_statistics

router = APIRouter()
legal_search = LegalESSearch(categories=['이혼', '형사', '손해배상'])

@router.post("/consult/extract")
async def proxy_extract_legal_data(request: ExtractRequest):
    result = await extract_full_legal_data(request.topic_code, request.text)
    return {"success": True, "data": result.model_dump()}


@router.post("/consult/transcribe")
async def transcribe(files: List[UploadFile] = File(...)):
    logger.info("[STT] STT 전사 시작")
    all_text = ""
    
    for file in files:
        url = f"{settings.GROK_API_URL}/transcribe"
        file_data = {"file": (file.filename, await file.read(), file.content_type)}
        response = requests.post(url, files=file_data, timeout=300)
        response.raise_for_status()
        
        transcribed_text = response.json().get("text", "")

        clean_text = re.sub(r'[^\w\s.]', '', transcribed_text)
        clean_text = re.sub(r'\.{2,}', '.', clean_text)
        clean_text = re.sub(r'(\S+)\1{3,}', r'\1', clean_text)

        all_text += clean_text + " "
        logger.success(f"[STT] STT 전사 완료: {all_text[:50]}...")
    
    return {
        "success": True, 
        "text": all_text.strip()
    }


@router.post("/consult/search-case")
# TODO: category -> cate_id로 변환 후 전달, personal schema 값을 cate_id에 major category에 따라서 분류하기
async def search_case(request: SearchRequest):
    """스트리밍 방식으로 중간 결과를 클라이언트에 실시간 푸시"""
    async def generate():
        try:
            category = request.category
            input_text = request.text
            logger.info(f"[{category}] 유사 사례 검색 시작")

            if category == "기타":
                category = "형사"

            # 변호사 페르소나 생성 및 푸시
            yield f"data: {json.dumps({'type': 'status', 'message': '사건을 분석하고 있어요...'}, ensure_ascii=False)}\n\n"
            
            factory = LegalPromptFactory(category)
            lawyer_cfg = factory.get_lawyer_config()
            lawyer_schema = get_legal_schema("lawyer", category)
            lawyer_persona = await fetch_llm(
                system_prompt=lawyer_cfg["system"],
                user_instructions=lawyer_cfg["instructions"],
                input_text=input_text,
                schema=lawyer_schema
            )
            logger.debug(f"변호사 페르소나 데이터: {lawyer_persona}")
            
            # 변호사 페르소나 푸시
            yield f"data: {json.dumps({'type': 'persona_lawyer', 'data': lawyer_persona}, ensure_ascii=False)}\n\n"

            # 일반인 페르소나 생성 및 푸시
            yield f"data: {json.dumps({'type': 'status', 'message': '의뢰인의 입장을 정리하고 있어요...'}, ensure_ascii=False)}\n\n"
            
            layperson_cfg = factory.get_layperson_config()
            layperson_schema = get_legal_schema("layperson", category)
            layperson_persona = await fetch_llm(
                system_prompt=layperson_cfg["system"],
                user_instructions=layperson_cfg["instructions"],
                input_text=input_text,
                schema=layperson_schema
            )
            logger.debug(f"일반인 페르소나 데이터: {layperson_persona}")
            
            # 일반인 페르소나 푸시
            yield f"data: {json.dumps({'type': 'persona_layperson', 'data': layperson_persona}, ensure_ascii=False)}\n\n"

            # 페르소나 병합
            merged_persona = {
                "state": lawyer_persona.get("state"),
                "persona_lawyer": lawyer_persona.get("persona_lawyer"),
                "persona_layperson": layperson_persona.get("persona_layperson"),
            }

            # 유사 사례 검색
            yield f"data: {json.dumps({'type': 'status', 'message': '유사 사례를 찾고 있어요...'}, ensure_ascii=False)}\n\n"
            
            # payload = {
            #     "category": category,
            #     "query": f"{merged_persona['persona_lawyer']} {merged_persona['persona_layperson']}",
            #     "top_k": settings.SEARCH_TOP_K,
            #     "score_threshold": settings.SEARCH_SCORE_THRESHOLD
            # }

            auth_stats = {
                "auth_count": None,
                "incident_count": None,
                "matched_org": request.authority_name
            }

            city_flag = False

            if request.authority_name:
                stats = await get_authority_statistics(request.authority_name)
                auth_stats.update(stats)

            elif request.customer_address and request.customer_address != "정보없음":
                logger.debug(f"고객 주소 기반으로 관할 통계 조회 시도: {request.customer_address}")
                stats = await get_authority_statistics_by_city(request.customer_address, category)
                auth_stats.update(stats)
                city_flag = True
            
            # url = f"{settings.GROK_API_URL}/search-case"
            # response = requests.post(url, json=payload, timeout=300)
            # response.raise_for_status()
            # search_data = response.json()

            rerank_query = f"{merged_persona['persona_lawyer']} {merged_persona['persona_layperson']}"

            # API 요청 대신 로컬 메서드 호출
            search_data = legal_search.search(
                category=category, 
                query_text=rerank_query, 
                top_k=settings.SEARCH_TOP_K
            )
            
            logger.debug(f"[{category}] 유사 사례 검색 응답 데이터: {search_data[0:1]}...")

            yield f"data: {json.dumps({'type': 'status', 'message': 'AI가 한번 더 확인하고 있어요...'}, ensure_ascii=False)}\n\n"
            
            final_search_data = await get_reranked_results(rerank_query, search_data, top_n=10)

            logger.debug(f"[{category}] 유사 사례 리랭킹 데이터 구조: {final_search_data[0:1]}...")
            
            yield f"data: {json.dumps({'type': 'status', 'message': '사례 상세 정보를 조회하고 있어요...'}, ensure_ascii=False)}\n\n"
            
            db_idx_list = [res['db_idx'] for res in search_data]
            similar_cases_raw = await fetch_cases_from_db_bulk(db_idx_list)
            case_dict = {case.get('unified_pk'): case for case in similar_cases_raw}

            similar_cases = []
            for res in final_search_data:
                case = case_dict.get(res['db_idx'])
                if not case: continue
                
                if res.get('is_reranked'):
                    display_score = round(res['rerank_score'] * 100, 1)
                else:
                    rrf_score = res.get('score', 0)
                    display_score = round(min(100.0, (rrf_score / 0.0328) * 100), 1)
                
                case['score'] = display_score
                case['is_reranked'] = res.get('is_reranked', False)
                similar_cases.append(case)
            
            total_count = len(similar_cases)
            win_rate = calculate_win_rate_logic(similar_cases)
            top_lawyers = get_top_lawyers(similar_cases, 5)
            case_stats = calculate_case_statistics(similar_cases)
            amount_summary = await get_amount_static_by_periods(category)
            
            logger.success(f"[{category}] 유사 사례 {len(similar_cases)}건 검색 및 정렬 완료")
            
            final_result = {
                "type": "final",
                "data": {
                    "success": True,
                    "persona": merged_persona,
                    "similar_cases": similar_cases[:3],
                    "total_count": total_count,
                    "summary_stats": case_stats["summary_stats"],
                    "win_rate": win_rate,
                    "top_lawyers": top_lawyers,
                    "authority_stats": auth_stats,
                    "city_flag": city_flag,
                    "personal_data": merged_persona,
                    "amount_stats": amount_summary
                }
            }
            yield f"data: {json.dumps(final_result, ensure_ascii=False)}\n\n"

        except Exception as e:
            logger.error(f"Error during streaming: {str(e)}")
            error_msg = {
                "type": "error",
                "message": str(e)
            }
            yield f"data: {json.dumps(error_msg, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.post("/generate-full-report")
async def api_generate_full_report(request: FullReportRequest):
    persona_data = request.persona_data
    example_case = request.example_case
    office = request.office
    specialty = request.specialty
    status = request.status

    logger.info(f"페르소나 데이터로 리포트 작성 시작 {example_case}")

    case_id = request.example_case.get('unified_pk', 'N/A')

    contents = example_case.get('contents', {})
    clean_ex = {
        "title": example_case.get('title', '').replace(" 조력 사례", ""),
        "summary": clean_fixed_phrases(contents.get('lawyerSearchReasonSectionSubContent1', ''), "overview"),
        "features": contents.get('caseIssueSectionSubContent1', ''),
        "action": clean_fixed_phrases(contents.get('supportContentContent', ''), "support"),
        "result": clean_fixed_phrases(example_case.get('case_result', ''), "result"),
        "meaning": contents.get('caseResultMeaningSectionContent', '')
    }

    user_prompt_1 = f"""
[지시사항]
유사 사례의 구조와 전문적인 법률 용어를 사용하여 제목, 사건의 개요, 사건의 특징, 변호사 조력 내용을 추출하세요.
사건이 끝났다고 가정하고 반드시 전부 과거형으로 작성하세요.
*Example*과 동일한 format으로 작성하세요.

[Rule]
1. 제목은 "~한 사례" 형식으로 작성하세요.
1. 사건의 개요는 2문장 이상 구체적으로 서술형으로 작성하세요.
2. 사건의 특징은 변호사로서 2~3개의 특징으로 과거형으로 구체적으로 서술하세요.
3. 제목이나 콜론(:) 없이 서술형으로 작성하세요.
3. 변호사 조력 내용은 2문장 이상 구체적으로 예상되는 조력 내용을 과거형으로 작성하세요.

[분석할 현재 상담 데이터]
{persona_data}

[Example]
제목: {clean_ex['title']}
사건의 개요: {clean_ex['summary']}
사건의 특징: {clean_ex['features']}
변호사 조력 내용: {clean_ex['action']}
    """

    user_prompt_2 = f"""
[지시사항]
유사 사례의 구조와 전문적인 법률 용어를 사용하여 결과와 법률적 의의를 추측하세요.
사건이 끝났다고 가정하고 반드시 전부 과거형으로 작성하세요.
*Example*과 동일한 format으로 작성하세요.

[Rule]
1. 사건 결과는 변호사 조력으로 법원이 어떻게 판결했는지 간결하게 과거형으로 작성하세요.
2. 사건 결과의 의의는 변호사로서 법률적 관점에서 2문장 이상 구체적으로 서술형으로 작성하세요.
3. 고객 후기는 실제 고객이 남긴 것처럼 사건이 끝났다고 가정하고 1문장 이상 진솔하게 작성하세요.

[분석할 현재 상담 데이터]
{persona_data}

[Example]
사건 결과: {clean_ex['result']}
결과의 의의: {clean_ex['meaning']}
    """

    res1_task = fetch_llm(SYSTEM_STEP1, user_prompt_1, "", SCHEMA_STEP1)
    res2_task = fetch_llm(SYSTEM_STEP2, user_prompt_2, "", SCHEMA_STEP2)

    data1, data2 = await asyncio.gather(res1_task, res2_task)

    final_report = {
        "title": data1.get('title_core'),
        "overview": f"{data1.get('dynamic_overview')} {settings.FIRM_NAME} {office}는 {status} 신분인 의뢰인을 대리했습니다.",
        "features": data1.get('features', []),
        "support": f"{settings.FIRM_NAME} {office}의 {specialty} 변호사는 아래와 같이 조력했습니다. {data1.get('dynamic_support')}",
        "verdict": f"{settings.FIRM_NAME} {office}의 {specialty} 변호사 조력으로 법원은 아래와 같이 판결했습니다. {data2.get('verdict_core')}",
        "meaning": data2.get('meaning'),
        "review": data2.get('review')
    }

    return {
        "success": True,
        "data": {
            "caseId": case_id, # 참조 판례 ID 포함
            "title_core": data1.get('title_core'),
            "dynamic_overview": data1.get('dynamic_overview'),
            "features": data1.get('features', []),
            "dynamic_support": data1.get('dynamic_support'),
            "verdict_core": data2.get('verdict_core'),
            "meaning": data2.get('meaning'),
            "review": data2.get('review')
        }
    }
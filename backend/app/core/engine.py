from app.services.llm_service import run_module_call
from app.prompts.common_prompts import COMMON_PROMPTS 
from app.schemas.common import Module_Identity, 상담_결과_요약, 고객_기본_정보, 상담_설정_정보, 상담_결과_요약
from app.common.registry import topic_model_registry
from pydantic import create_model
from loguru import logger

import app.prompts.divorce_prompts
import app.prompts.civil_prompts
import app.prompts.crime_prompts

def create_full_model(topic_code: str):
    payload_class = topic_model_registry.get(topic_code)
    
    if not payload_class:
        raise ValueError(f"주제 코드 '{topic_code}'에 해당하는 모델을 찾을 수 없습니다.")

    return create_model(
        f"LegalConsultation_{topic_code}",
        주제_코드=(str, topic_code),
        고객_정보=(고객_기본_정보, ...),
        상담_설정=(상담_설정_정보, ...),
        상담_요약=(상담_결과_요약, ...),
        상세_내용=(payload_class, ...)
    )


async def extract_full_legal_data(topic_code: str, raw_text: str):
    PayloadClass = topic_model_registry.get(topic_code)
    
    logger.info(f"Extracting legal data for topic_code: {topic_code}")
    res_id = await run_module_call(COMMON_PROMPTS["IDENTITY"], Module_Identity, raw_text)

    logger.debug(f"추출된 고객 정보: {res_id.고객_정보}")

    if PayloadClass is None:
        available_keys = list(topic_model_registry.keys())
        raise ValueError(f"정의되지 않은 topic_code: '{topic_code}'. 등록된 키: {available_keys}")

    extracted_fragments = {}
    modules = PayloadClass.get_required_modules()
    
    for i, (module_key, module_model) in enumerate(modules, start=2):
        res = await run_module_call(PayloadClass.PROMPTS[module_key], module_model, raw_text)
        extracted_fragments.update(res.model_dump())

        logger.debug(f"[{i}/{len(modules)+2}] 추출된 모듈 '{module_key}': {res.model_dump()}")

    res_sum = await run_module_call(COMMON_PROMPTS["SUMMARY"], 상담_결과_요약, raw_text)
    logger.debug(f"추출된 상담 요약: {res_sum.model_dump()}")

    
    detailed_info = PayloadClass.assemble(extracted_fragments)
    FullModel = create_full_model(topic_code)
    
    return FullModel(
        주제_코드=topic_code,
        고객_정보=res_id.고객_정보,
        상담_설정=res_id.상담_설정,
        상담_요약=res_sum,
        상세_내용=detailed_info
    )
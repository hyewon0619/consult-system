import httpx

from loguru import logger
from typing import List, Dict, Any
from app.common.config import settings


async def fetch_llm(system_prompt: str, user_instructions: str, input_text: str, schema: dict) -> dict:
    url = f"{settings.GROK_API_URL}/generate"
    user_content = f"### [지시 사항]\n{user_instructions}\n\n### [상담내용]\n{input_text}"
    
    payload = {
        "system": system_prompt,
        "user": user_content,
        "response_schema": schema
    }
    
    async with httpx.AsyncClient(timeout=300.0) as client:
        response = await client.post(url, json=payload)
        response.raise_for_status()
        
        return response.json()


async def run_module_call(prompt_config: dict, response_model, raw_text: str):
    system_prompt = f"{prompt_config['system']}\n\n반드시 유효한 JSON만 응답하십시오."
    user_instructions = f"Rules: {prompt_config.get('rules', '')}\nFormat: {prompt_config.get('format', '')}\nExample: {prompt_config.get('example', '')}"

    result_json = await fetch_llm(
        system_prompt=system_prompt,
        user_instructions=user_instructions,
        input_text=raw_text,
        schema=response_model.model_json_schema()
    )
    
    return response_model.model_validate(result_json)


async def get_reranked_results(query: str, search_data: List[Dict[str, Any]], top_n: int = 10) -> List[Dict[str, Any]]:
    """
    상위 N개의 결과에 대해 리랭킹
    """
    if not search_data:
        return []

    top_candidates = search_data[:top_n]
    others = search_data[top_n:]

    passages = [res.get('summary', '') for res in top_candidates]
    payload = {
        "query": query,
        "passages": passages
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{settings.GROK_API_URL}/rerank", 
                json=payload, 
                timeout=30.0
            )
            response.raise_for_status()
            rerank_scores = response.json().get("scores", [])

        # 점수 매칭
        for i, score in enumerate(rerank_scores):
            top_candidates[i]['rerank_score'] = float(score)
            top_candidates[i]['is_reranked'] = True

        # 리랭킹 점수 기준 정렬
        top_candidates.sort(key=lambda x: x.get('rerank_score', 0), reverse=True)
        
    except Exception as e:
        logger.error(f"Reranking failed: {str(e)}")
        for res in top_candidates:
            res['is_reranked'] = False

    return top_candidates + others
from loguru import logger
import json
import re
from app.db.session import AsyncSessionLocal
from sqlalchemy import text


async def fetch_cases_from_db_bulk(db_idx_list: list[int]) -> list[dict]:
    """
    Docstring for fetch_cases_from_db_bulk
    :type db_idx_list: list[int]
    """

    if not db_idx_list:
        return []

    # 이제 'async with'와 'await'를 마음껏 쓸 수 있습니다!
    async with AsyncSessionLocal() as db:
        try:
            sql = text("""
                SELECT 
                    unified_pk,
                    original_id,
                    category_id,
                    case_title,
                    case_summary,
                    case_feature,
                    case_assistance,
                    case_result,
                    closure_summary,
                    case_significance,
                    meta_keywords,
                    client_status,
                    authorities,
                    lawyer_names,
                    source
                FROM v_integrated_cases
                WHERE unified_pk IN :pk_list
            """)
            
            result = await db.execute(sql, {"pk_list": db_idx_list})
            rows = result.mappings().all()
            
            return [dict(row) for row in rows]
            
        except Exception as e:
            print(f"Error fetching bulk cases from view: {e}")
            return []
            

# TODO: category 값을 id로 변경해서 가져오기 (현재는 임시로 small_category로)
async def fetch_pricing_data_by_category_name(category_name: str) -> list[dict]:
    """
    특정 소분류 명칭(small_category)에 해당하는 모든 약정금 및 성공보수, 소가 데이터를 가져옴
    """
    
    async with AsyncSessionLocal() as db:
        try:
            sql = text("""
                SELECT 
                    eng_inci_id,
                    payment_amount,
                    payment_actual_date,
                    reward_amount,
                    reward_actual_date,
                    engagement_soga,
                    incident_soga,
                    small_category,
                    major_category
                FROM v_incident_pricing
                WHERE small_category = :cat_name
            """)
            
            result = await db.execute(sql, {"cat_name": category_name})
            rows = result.mappings().all()
            
            return [dict(row) for row in rows]
            
        except Exception as e:
            logger.error(f"Error fetching pricing data for category '{category_name}': {e}")
            return []
        


## 처분권자 관련 함수 - 기관명
async def get_authority_statistics(org_name: str):
    if not org_name or org_name == "정보없음":
        return {"auth_count": 0, "incident_count": 0, "matched_org": None, "auth_details": []}

    async with AsyncSessionLocal() as db:
        query = get_base_auth_query("a.organization LIKE :org_pattern")
        result = await db.execute(query, {"org_pattern": f"%{org_name}%"})
        row = result.fetchone()

        if not row or row.auth_count == 0:
            return {"auth_count": 0, "incident_count": 0, "matched_org": org_name, "auth_details": []}

        auth_details = parse_auth_raw_details(row.auth_raw_details)
        
        return {
            "auth_count": row.auth_count,
            "incident_count": row.incident_count or 0,
            "matched_org": org_name, # 혹은 row 데이터에서 추출
            "auth_details": auth_details
        }



## 처분권자 관련 함수 - 지역명
# TODO: category 값을 id로 변경해서 가져오기 (현재는 임시로 small_category로)
async def get_authority_statistics_by_city(address: str, category: str):
    if not address or address == "정보없음":
        return {"auth_count": 0, "incident_count": 0, "matched_org": "지역 정보 없음", "auth_details": []}

    major_category = await get_major_category(category)
    
    # 키워드 추출 (행정구역 단위)
    keywords = re.findall(r'([가-힣]+)(?:시|도|구|군)', address) or [address.split()[0]]
    search_steps = [keywords] if len(keywords) < 2 else [keywords, [keywords[1]], [keywords[0]]]

    async with AsyncSessionLocal() as db:
        for step_keywords in search_steps:
            # 동적 WHERE 절 생성
            where_clause = " AND ".join([f"a.organization LIKE :kw_{i}" for i in range(len(step_keywords))])
            params = {f"kw_{i}": f"%{kw}%" for i, kw in enumerate(step_keywords)}
            
            query = get_base_auth_query(where_clause)
            result = await db.execute(query, params)
            row = result.fetchone()

            if row and row.auth_count > 0:
                all_details = parse_auth_raw_details(row.auth_raw_details)
                
                # 카테고리 유효성 필터링
                valid_details = [
                    d for d in all_details 
                    if is_valid_authority_by_category(d['organization'], major_category)
                ]
                
                if not valid_details:
                    continue

                return {
                    "auth_count": len(valid_details),
                    "incident_count": row.incident_count or 0,
                    "matched_org": f"{' '.join(step_keywords)} 지역",
                    "auth_details": valid_details
                }

        return {"auth_count": 0, "incident_count": 0, "matched_org": f"{' '.join(keywords)}", "auth_details": []}


def parse_traits_from_json(comment_str):
    """JSON 문자열에서 특성 정보를 파싱하고 지정된 키워드를 필터링하는 함수"""
    filter_keywords = ["ㅇ", "없음", ".", "정보 없음", "정보없음", "데이터 없음", "n/a", "N/A", "알수없음"]
    
    def clean_text(text):
        if not text:
            return "정보 없음"
        
        cleaned = text.strip()
        
        if cleaned in filter_keywords or not cleaned:
            return "정보 없음"
        
        return cleaned

    personal, work = "정보 없음", "정보 없음"
    
    try:
        data = json.loads(comment_str)
        if isinstance(data, dict):
            personal = clean_text(data.get("개인특성"))
            work = clean_text(data.get("업무특성"))
    except (json.JSONDecodeError, TypeError):
        pass
        
    return personal, work


async def get_major_category(category_name: str) -> str:
    """ykos.incident_category 테이블에서 소분류에 해당하는 대분류를 가져옴"""
    async with AsyncSessionLocal() as db:
        sql = text("SELECT major_category FROM ykos.incident_category WHERE small_category = :cat_name")
        result = await db.execute(sql, {"cat_name": category_name})
        row = result.fetchone()
        return row[0] if row else None
        

def is_valid_authority_by_category(organization: str, major_category: str) -> bool:
    """대분류별 금지 키워드 리스트를 통한 기관 유효성 검사"""
    if not organization or not major_category:
        return True
        
    org = organization.strip()
    
    EXCLUDED_KEYWORDS = {
        '형사': ['가정'],
        '민사': ['검찰', '경찰'],
        '가사': ['검찰', '경찰']
    }
    
    forbidden_list = EXCLUDED_KEYWORDS.get(major_category, [])
    
    if any(keyword in org for keyword in forbidden_list):
        return False
            
    return True

def parse_auth_raw_details(raw_details: str) -> list:
    """SQL의 GROUP_CONCAT 결과를 리스트 객체로 변환"""
    if not raw_details:
        return []
    
    auth_list = []
    for item in raw_details.split(';;'):
        parts = item.split('|')
        # 이름, 기관, 부서, 직책, 코멘트 최소 5개 필드 확인
        if len(parts) >= 5:
            name, org, dept, job, comment_str = [p.strip() for p in parts[:5]]
            
            if name and name not in ('없음', '.'):
                personal, work = parse_traits_from_json(comment_str)
                auth_list.append({
                    "name": name,
                    "organization": org,
                    "department": dept,
                    "job": job,
                    "personal_trait": personal,
                    "work_trait": work
                })
    return auth_list

def get_base_auth_query(where_clause: str):
    """공통 SQL 쿼리 템플릿"""
    return text(f"""
        SELECT 
            COUNT(DISTINCT a.auth_id) AS auth_count,
            COUNT(DISTINCT eia.eng_inci_id) AS incident_count,
            GROUP_CONCAT(DISTINCT 
                CASE 
                    WHEN a.name IS NOT NULL AND a.name NOT IN ('', '없음', '.')
                    THEN CONCAT(
                        a.name, '|', 
                        a.organization, '|', 
                        COALESCE(a.department, '미기입'), '|', 
                        COALESCE(a.job_type, '미기입'), '|', 
                        COALESCE(eia.comment, '{{}}')
                    )
                END
                SEPARATOR ';;'
            ) AS auth_raw_details
        FROM ykos.authority a
        LEFT JOIN ykos.engagement_incident_authority eia ON a.auth_id = eia.auth_id
        WHERE {where_clause}
    """)
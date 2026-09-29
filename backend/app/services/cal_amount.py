from app.crud.read import fetch_pricing_data_by_category_name
from datetime import datetime, timedelta
import pandas as pd


def calculate_metrics(series):
    valid_data = series[series > 0]
    if valid_data.empty:
        return None
        
    q1 = valid_data.quantile(0.25)
    q3 = valid_data.quantile(0.75)
    iqr = q3 - q1
    lower_bound = q1 - 1.5 * iqr
    upper_bound = q3 + 1.5 * iqr

    refined = valid_data[(valid_data >= lower_bound) & (valid_data <= upper_bound)]

    if refined.empty: return None

    count = int(len(refined))
    confidence = get_confidence_stats(count)

    return {
        "count": int(len(refined)),
        "min": int(refined.min()),
        "max": int(refined.max()),
        "median": int(refined.median()),   
        "lower_25": int(refined.quantile(0.25)),
        "upper_75": int(refined.quantile(0.75)),
        "mean": int(refined.mean()),
        "confidence": confidence
    }


def get_confidence_stats(n, population_size=10000):
    # 95%(±5%) : 383, 95%(±10%) : 96, 90%(±10%) : 68
    if n >= 383:
        return {"level": "95%", "error": "±5%", "label": "매우 높음"}
    elif n >= 96:
        return {"level": "95%", "error": "±10%", "label": "높음"}
    elif n >= 68:
        return {"level": "90%", "error": "±10%", "label": "보통"}
    else:
        return {"level": "미달", "error": "-", "label": "참고용(데이터 부족)"}


async def get_amount_static_by_periods(category: str):
    raw_data = await fetch_pricing_data_by_category_name(category_name=category)
    if not raw_data:
        print(f"DEBUG: [{category}] raw_data가 없습니다.")
        return None

    df = pd.DataFrame(raw_data)
    print(f"\n" + "="*50)
    print(f"DEBUG: [{category}] 분석 시작")
    print(f"DEBUG: 전체 원본 데이터 개수: {len(df)}개")

    df['payment_amount'] = pd.to_numeric(df['payment_amount'], errors='coerce').fillna(0)
    df['reward_amount'] = pd.to_numeric(df['reward_amount'], errors='coerce').fillna(0)
    df['incident_soga'] = pd.to_numeric(df['incident_soga'], errors='coerce').fillna(0)
    
    df['payment_actual_date'] = pd.to_datetime(df['payment_actual_date'])
    df['reward_actual_date'] = pd.to_datetime(df['reward_actual_date'])
    
    major_cat = df['major_category'].iloc[0] if not df.empty else "알수없음"
    is_civil = major_cat == "민사"
    print(f"DEBUG: Major Category: {major_cat} (민사여부: {is_civil})")

    if is_civil:
        df['reward_ratio'] = df.apply(
            lambda row: row['reward_amount'] / row['incident_soga'] 
            if row['incident_soga'] > 0 and row['reward_amount'] > 0 else None, 
            axis=1
        )
        valid_ratio_count = df['reward_ratio'].notnull().sum()
        print(f"DEBUG: 비율 계산 가능 데이터(성공보수>0 & 소가>0): {valid_ratio_count}개")
        if valid_ratio_count > 0:
            print(f"DEBUG: 비율 샘플(상위 3개): {df['reward_ratio'].dropna().head(3).tolist()}")

    now = datetime.now()
    periods = [2, 4, 6, 8, 10, 12]
    stats_history = {}

    for month in periods:
        start_date = now - timedelta(days=month * 30)
        target_df = df[df['payment_actual_date'] >= start_date]
        
        print(f"--- DEBUG: 최근 {month}개월 구간 ({start_date.date()} 이후) ---")
        print(f"DEBUG: 구간 데이터 개수: {len(target_df)}개")
        
        p_metrics = calculate_metrics(target_df['payment_amount'])
        r_metrics = calculate_metrics(target_df['reward_amount'])
        
        period_stats = {
            "payment": p_metrics,
            "reward": r_metrics,
        }

        if is_civil:
            period_stats["soga"] = calculate_metrics(target_df['incident_soga'])
            
            valid_ratios = target_df['reward_ratio'].dropna()
            print(f"DEBUG: 구간 내 유효 비율 개수: {len(valid_ratios)}개")
            
            if not valid_ratios.empty:
                q1 = valid_ratios.quantile(0.25)
                q3 = valid_ratios.quantile(0.75)
                iqr = q3 - q1
                refined_ratios = valid_ratios[(valid_ratios >= q1 - 1.5 * iqr) & 
                                              (valid_ratios <= q3 + 1.5 * iqr)]
                
                
                if not refined_ratios.empty:
                    median_val = float(refined_ratios.median())
                    period_stats["reward_to_soga_ratio"] = median_val
                else:
                    period_stats["reward_to_soga_ratio"] = 0
            else:
                period_stats["reward_to_soga_ratio"] = 0

        stats_history[f"{month}m"] = period_stats

    # 최종 결과 구조 생성
    result = {
        "category": category,
        "major_category": major_cat,
        "overall": {
            "payment": calculate_metrics(df['payment_amount']),
            "reward": calculate_metrics(df['reward_amount']),
        },
        "periods": stats_history
    }

    if is_civil:
        result["overall"]["soga"] = calculate_metrics(df['incident_soga'])
        
        overall_valid = df['reward_ratio'].dropna()
        if not overall_valid.empty:
            q1, q3 = overall_valid.quantile([0.25, 0.75])
            iqr = q3 - q1
            refined_overall = overall_valid[(overall_valid >= q1 - 1.5 * iqr) & 
                                            (overall_valid <= q3 + 1.5 * iqr)]
            final_median = float(refined_overall.median())
            result["overall"]["reward_to_soga_ratio"] = final_median
            print(f"DEBUG: [Overall] 최종 중간값: {final_median}")
        else:
            result["overall"]["reward_to_soga_ratio"] = 0
            print("DEBUG: [Overall] 유효 비율 데이터 없음")

    print(f"="*50 + "\n")
    return result
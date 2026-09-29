"""합성 샘플 데이터 생성기.

이 저장소는 공개본이라 실제 사건 데이터를 담지 않는다. 대신 운영 데이터와
**구조만 동일한** 가짜 데이터를 만들어 두고, 그것으로 전체 파이프라인이
돌아가는 것을 보인다.

만들어지는 것:
  scripts/old_case.json                     승소사례 원본 (load_old_cases.py 입력)
  legal_search_assets/{cat}.index           FAISS 벡터 인덱스
  legal_search_assets/{cat}_metadata.json   인덱스와 행 순서가 1:1 대응하는 메타

등장하는 인물·기관·사건번호는 전부 조합해 만든 것이다. 실존하는 사람이나
사건과 일치하는 것이 있다면 우연이다.

실행:
    cd backend && python scripts/generate_sample_data.py
"""

from __future__ import annotations

import json
import random
from pathlib import Path

import numpy as np

SEED = 20260929
N_CASES = 300
N_ASSETS = {"divorce": 120, "compensation": 80, "criminal": 60}
EMBED_DIM = 1024  # KURE-v1 출력 차원

BACKEND_DIR = Path(__file__).resolve().parent.parent
ASSETS_DIR = BACKEND_DIR / "legal_search_assets"
CASES_PATH = BACKEND_DIR / "scripts" / "old_case.json"

# --- 어휘 재료 (전부 가공) -------------------------------------------------

SURNAMES = list("김이박최정강조윤장임한오서신권황안송류전")
GIVEN = ["민준", "서연", "도윤", "하은", "지호", "수아", "예준", "지우",
         "시윤", "채원", "건우", "다은", "현우", "유진", "준서", "소율"]

OFFICES = ["중앙", "동부", "서부", "남부", "북부", "해안", "산남", "강변"]

CATEGORIES = {
    "divorce": ("이혼", ["재산분할", "양육권", "위자료", "면접교섭", "상간소송"]),
    "compensation": ("손해배상", ["교통사고", "의료과실", "공사하자", "명예훼손"]),
    "criminal": ("형사", ["사기", "상해", "음주운전", "횡령", "무고"]),
}

RESULTS = ["전부승소", "일부승소", "조정성립", "청구기각", "무혐의", "집행유예"]
PROCESS_STEPS = ["상담", "소장접수", "변론", "선고", "확정"]

FEATURES = [
    "혼인기간이 길고 기여도 다툼이 핵심인 사건",
    "상대방이 재산을 은닉한 정황이 있는 사건",
    "미성년 자녀의 양육 환경이 쟁점인 사건",
    "과실 비율 산정이 쟁점인 사건",
    "손해액 입증 자료가 부족한 사건",
    "초범이고 피해 회복이 이루어진 사건",
    "증거가 진술에 크게 의존하는 사건",
]


def _person(rng: random.Random) -> str:
    return rng.choice(SURNAMES) + rng.choice(GIVEN)


def _case_no(rng: random.Random, kor: str) -> str:
    code = {"이혼": "드단", "손해배상": "가단", "형사": "고단"}[kor]
    return f"{rng.randint(2019, 2025)}{code}{rng.randint(1000, 99999)}"


def _summary(rng: random.Random, kor: str, sub: str) -> str:
    who = _person(rng)
    return (
        f"의뢰인 {who} 씨는 {sub} 쟁점으로 {kor} 사건을 의뢰했다. "
        f"담당 변호사는 {rng.choice(FEATURES)}으로 보고 "
        f"{rng.choice(['조정', '변론', '증거보전', '감정신청'])} 절차를 우선 진행했다."
    )


# --- 승소사례 원본 ---------------------------------------------------------

def build_cases(rng: random.Random) -> list[dict]:
    rows = []
    for i in range(1, N_CASES + 1):
        eng = rng.choice(list(CATEGORIES))
        kor, subs = CATEGORIES[eng]
        sub = rng.choice(subs)
        office = rng.choice(OFFICES)
        lawyers = ", ".join(_person(rng) for _ in range(rng.randint(1, 3)))
        result = rng.choice(RESULTS)
        title = f"[{kor}] {sub} 사건에서 {result}를 이끌어낸 사례"

        rows.append({
            "id": i,
            "title": title,
            "result": result,
            "description": _summary(rng, kor, sub),
            "metaTitle": title,
            "metaDescription": f"{kor} {sub} 사건 {result} 사례",
            "metaKeywords": ",".join([kor, sub, result]),
            "content": _summary(rng, kor, sub),
            "pinned": rng.random() < 0.05,
            "subTitle": f"{office} 사무소 {sub} 사건",
            "thumbnailPath": None,
            "thumbnails": [],
            "lawyers": lawyers,
            "businessCategory": {"name": kor},
            "subType": sub,
            "businessCategories": [{"name": kor}, {"name": sub}],
            "hashTags": [kor, sub],
            "contents": [{"type": "text", "value": _summary(rng, kor, sub)}],
            "centerSeq": rng.randint(1, 30),
            "businessProcess": [{"step": s} for s in PROCESS_STEPS],
            "branchInformationId": rng.randint(1, 30),
            "processStep": rng.choice(PROCESS_STEPS),
            "publishedAt": f"{rng.randint(2021, 2025)}-"
                           f"{rng.randint(1, 12):02d}-{rng.randint(1, 28):02d}T00:00:00Z",
        })
    return rows


# --- 검색 자산 (FAISS + 메타) ----------------------------------------------

def build_assets(rng: random.Random, nprng: np.random.Generator) -> None:
    try:
        import faiss
    except ImportError:
        raise SystemExit(
            "faiss 가 필요하다. `poetry install` 후 다시 실행할 것.\n"
            "(faiss-cpu 를 쓰는 경우에도 import 이름은 faiss 다.)"
        )

    ASSETS_DIR.mkdir(parents=True, exist_ok=True)

    for eng, n in N_ASSETS.items():
        kor, subs = CATEGORIES[eng]

        meta = []
        for i in range(n):
            sub = rng.choice(subs)
            meta.append({
                "db_idx": i + 1,
                "summary": _summary(rng, kor, sub),
                "feature": rng.choice(FEATURES),
                "source": _case_no(rng, kor),
            })

        # 정규화된 임의 벡터. 실제 임베딩이 아니므로 검색 결과에 의미는 없고,
        # 파이프라인이 끝까지 도는지 확인하는 용도다.
        vecs = nprng.normal(size=(n, EMBED_DIM)).astype("float32")
        vecs /= np.linalg.norm(vecs, axis=1, keepdims=True)

        index = faiss.IndexFlatIP(EMBED_DIM)
        index.add(vecs)
        faiss.write_index(index, str(ASSETS_DIR / f"{eng}.index"))

        with open(ASSETS_DIR / f"{eng}_metadata.json", "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)

        print(f"  {eng:13s} 벡터 {n:4d}건  ->  {eng}.index / {eng}_metadata.json")


def main() -> None:
    rng = random.Random(SEED)
    nprng = np.random.default_rng(SEED)

    print("승소사례 생성 중...")
    cases = build_cases(rng)
    CASES_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CASES_PATH, "w", encoding="utf-8") as f:
        json.dump(cases, f, ensure_ascii=False, indent=2)
    print(f"  {len(cases)}건  ->  {CASES_PATH.relative_to(BACKEND_DIR)}")

    print("검색 자산 생성 중...")
    build_assets(rng, nprng)

    print("\n완료. 이어서 아래를 실행하면 된다.")
    print("  python scripts/load_old_cases.py   # DB 적재")
    print("  python gen_es_index.py             # Elasticsearch 색인")


if __name__ == "__main__":
    main()

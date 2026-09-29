import os
import json
import faiss
from pathlib import Path
from dotenv import load_dotenv
from elasticsearch import Elasticsearch, helpers

load_dotenv()

ES_HOST = os.getenv("ES_HOST", "http://localhost:9200")
es = Elasticsearch(ES_HOST)

CURRENT_DIR = Path(__file__).parent
BASE_PATH = Path(os.getenv("BASE_PATH", CURRENT_DIR / "legal_search_assets"))
USER_DICT_PATH = Path(os.getenv("USER_DICT_PATH", CURRENT_DIR / "user_dict.txt"))

CAT_MAP = {'divorce': '이혼', 'compensation': '손해배상', 'criminal': '형사'}

def load_user_words(file_path=USER_DICT_PATH):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print(f"경고: 사용자 사전 파일을 찾을 수 없습니다. ({file_path})")
        return []

def create_es_index_with_nori(category_name, actual_dims=1024):
    """사용자 사전을 포함한 Nori 분석기 설정과 매핑 적용"""
    user_words = load_user_words()
    
    settings = {
        "analysis": {
            "analyzer": {
                "nori_analyzer": {
                    "type": "custom",
                    "tokenizer": "nori_user_dict",
                    "filter": ["nori_readingform", "lowercase"]
                }
            },
            "tokenizer": {
                "nori_user_dict": {
                    "type": "nori_tokenizer",
                    "decompound_mode": "mixed",
                    "user_dictionary_rules": user_words
                }
            }
        }
    }

    mappings = {
        "properties": {
            "db_idx": {"type": "keyword"},
            "summary": {"type": "text", "analyzer": "nori_analyzer"},
            "feature": {"type": "text", "analyzer": "nori_analyzer"},
            "source": {"type": "keyword"},
            "embedding_vector": {
                "type": "dense_vector",
                "dims": actual_dims,
                "index": True,
                "similarity": "cosine"
            }
        }
    }

    if es.indices.exists(index=category_name):
        es.indices.delete(index=category_name)
    
    es.indices.create(index=category_name, settings=settings, mappings=mappings)
    print(f"Nori 분석기가 적용된 인덱스 생성 완료: [{category_name}]")

def migrate_final():
    for eng_name, kor_name in CAT_MAP.items():
        index_path = BASE_PATH / f"{eng_name}.index"
        meta_path = BASE_PATH / f"{eng_name}_metadata.json"

        if not index_path.exists(): 
            print(f"파일 없음 건너뜀: {index_path}")
            continue

        print(f"[{kor_name}] 마이그레이션 시작...")
        try:
            index = faiss.read_index(str(index_path))
            actual_dims = index.d
            
            with open(meta_path, "r", encoding="utf-8") as f:
                meta_list = json.load(f)

            create_es_index_with_nori(kor_name, actual_dims)

            actions = []
            for i in range(index.ntotal):
                try:
                    if hasattr(index, 'index'):
                        vector = index.index.reconstruct(i).tolist()
                    else:
                        vector = index.reconstruct(i).tolist()
                except: continue
                
                meta = meta_list[i]
                actions.append({
                    "_index": kor_name,
                    "_id": str(meta["db_idx"]),
                    "_source": {
                        "db_idx": str(meta["db_idx"]),
                        "summary": meta.get("summary", ""),
                        "feature": meta.get("feature", ""),
                        "source": meta.get("source", ""),
                        "embedding_vector": vector
                    }
                })

                if len(actions) >= 100 or i == index.ntotal - 1:
                    helpers.bulk(es, actions)
                    actions = []
            print(f"[{kor_name}] 총 {index.ntotal}건 전송 완료!")

        except Exception as e:
            print(f"[{kor_name}] 오류 발생: {e}")

if __name__ == "__main__":
    migrate_final()
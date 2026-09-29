from elasticsearch import Elasticsearch
from sentence_transformers import SentenceTransformer
from app.common.config import settings
from loguru import logger
import json
from collections import defaultdict


class LegalESSearch:
    def __init__(self, categories):
        self.model = SentenceTransformer(settings.EMBEDDING_MODEL_NAME, device="cpu")
        self.es = Elasticsearch(settings.ES_HOST)
        self.categories = categories

    def _get_rrf_scores(self, hits, rrf_dict, rank_constant=60):
        """검색 결과 리스트의 순위를 바탕으로 RRF 점수를 누적합니다."""
        for rank, hit in enumerate(hits, start=1):
            doc_id = hit['_id']
            score = 1.0 / (rank + rank_constant)
            
            if doc_id not in rrf_dict:
                rrf_dict[doc_id] = {'score': 0.0, 'source': hit['_source']}
            
            rrf_dict[doc_id]['score'] += score

    def search(self, category, query_text, top_k=None):
        if top_k is None:
            top_k = settings.SEARCH_TOP_K
        
        query_vector = self.model.encode(query_text).tolist()

        window_size = 100 
        
        keyword_res = self.es.search(
            index=category,
            query={"multi_match": {"query": query_text, "fields": ["summary", "feature"]}},
            size=window_size
        )
        
        knn_res = self.es.search(
            index=category,
            knn={
                "field": "embedding_vector",
                "query_vector": query_vector,
                "k": window_size,
                "num_candidates": window_size * 10
            },
            size=window_size
        )

        rrf_map = {} # { doc_id: {score: float, source: dict} }
        
        self._get_rrf_scores(keyword_res['hits']['hits'], rrf_map)
        self._get_rrf_scores(knn_res['hits']['hits'], rrf_map)

        sorted_results = sorted(
            rrf_map.items(), 
            key=lambda x: x[1]['score'], 
            reverse=True
        )[:top_k]

        final_results = []
        for doc_id, data in sorted_results:
            score = data['score']
            
            if score < settings.SEARCH_SCORE_THRESHOLD:
                continue

            source = data['source']
            final_results.append({
                'db_id': doc_id,
                'db_idx': int(source.get('db_idx', 0)),
                'summary': source.get('summary'),
                'feature': source.get('feature'),
                'source': source.get('source'),
                'rrf_score': round(float(score), 4)
            })

        # 디버깅용 로그
        if final_results:
            logger.debug(f"Hybrid Search Top 1 Score: {final_results[0]['rrf_score']}")

        return final_results
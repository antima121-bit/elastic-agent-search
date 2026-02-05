"""
Hybrid search combining BM25 (keyword) and kNN (semantic) search
"""
from typing import List, Dict, Any, Optional
from elasticsearch import Elasticsearch
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from config.elasticsearch import es_config
from src.indexing.embeddings import embedding_generator


class HybridSearch:
    """
    Hybrid search combining traditional keyword search (BM25) 
    with semantic vector search (kNN) using Reciprocal Rank Fusion (RRF)
    """
    
    def __init__(self):
        self.client = es_config.get_client()
        self.index_name = es_config.index_name
    
    def search(
        self,
        query: str,
        top_k: int = 10,
        semantic_weight: float = 0.5,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Perform hybrid search combining keyword and semantic search
        
        Args:
            query: Search query text
            top_k: Number of results to return
            semantic_weight: Weight for semantic search (0-1), keyword weight = 1 - semantic_weight
            filters: Optional filters
            
        Returns:
            List of search results with combined scores
        """
        # Generate query embedding for semantic search
        query_vector = embedding_generator.encode_query(query)
        
        # Build keyword search query (BM25)
        keyword_query = {
            "bool": {
                "should": [
                    {
                        "multi_match": {
                            "query": query,
                            "fields": ["title^3", "description^2", "tags"],
                            "type": "best_fields",
                            "fuzziness": "AUTO"
                        }
                    }
                ]
            }
        }
        
        # Add filters to keyword query
        if filters:
            keyword_query["bool"]["filter"] = self._build_filters(filters)
        
        # Build kNN query for semantic search
        knn_query = {
            "field": "combined_vector",
            "query_vector": query_vector,
            "k": top_k,
            "num_candidates": top_k * 3
        }
        
        # Add same filters to kNN
        if filters:
            knn_query["filter"] = self._build_filters(filters)
        
        # Execute hybrid search using Elasticsearch's native RRF
        # Note: In production, you might use custom scoring
        response = self.client.search(
            index=self.index_name,
            query=keyword_query,
            knn=knn_query,
            size=top_k,
            _source={
                "excludes": ["*_vector"]
            },
            # Elasticsearch automatically combines scores
            rank={
                "rrf": {
                    "window_size": 50,
                    "rank_constant": 20
                }
            }
        )
        
        # Process results
        results = []
        for hit in response['hits']['hits']:
            result = {
                'id': hit['_id'],
                'score': hit['_score'],
                **hit['_source']
            }
            results.append(result)
        
        return results
    
    def _build_filters(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Build Elasticsearch filter queries"""
        must_clauses = []
        
        if 'min_price' in filters or 'max_price' in filters:
            range_filter = {"range": {"price": {}}}
            if 'min_price' in filters:
                range_filter["range"]["price"]["gte"] = filters['min_price']
            if 'max_price' in filters:
                range_filter["range"]["price"]["lte"] = filters['max_price']
            must_clauses.append(range_filter)
        
        if 'category' in filters:
            must_clauses.append({"term": {"category": filters['category']}})
        
        if 'brand' in filters:
            must_clauses.append({"term": {"brand": filters['brand']}})
        
        if 'min_rating' in filters:
            must_clauses.append({"range": {"rating": {"gte": filters['min_rating']}}})
        
        return must_clauses
    
    def explain_search(self, query: str, doc_id: str) -> Dict[str, Any]:
        """
        Explain why a document matched the hybrid query
        Useful for debugging and understanding search behavior
        """
        query_vector = embedding_generator.encode_query(query)
        
        keyword_query = {
            "multi_match": {
                "query": query,
                "fields": ["title^3", "description^2", "tags"]
            }
        }
        
        response = self.client.explain(
            index=self.index_name,
            id=doc_id,
            query=keyword_query
        )
        
        return response


if __name__ == "__main__":
    # Test hybrid search
    searcher = HybridSearch()
    
    test_queries = [
        ("winter jacket hiking", None),
        ("laptop programming", {"max_price": 1500}),
        ("coffee gift", {"min_rating": 4.5})
    ]
    
    for query, filters in test_queries:
        print(f"\n🔍 Hybrid Search: {query}")
        if filters:
            print(f"   Filters: {filters}")
        results = searcher.search(query, top_k=3, filters=filters)
        for idx, result in enumerate(results, 1):
            print(f"  {idx}. {result['title']} (score: {result['score']:.3f})")
            print(f"     ${result['price']} | ⭐ {result['rating']}")

"""
Vector search implementation using Elasticsearch kNN
"""
from typing import List, Dict, Any, Optional
from elasticsearch import Elasticsearch
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from config.elasticsearch import es_config
from src.indexing.embeddings import embedding_generator


class VectorSearch:
    """Semantic search using vector embeddings and kNN"""
    
    def __init__(self):
        self.client = es_config.get_client()
        self.index_name = es_config.index_name
    
    def search(
        self,
        query: str,
        top_k: int = 10,
        min_score: float = 0.5,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Perform semantic vector search
        
        Args:
            query: Search query text
            top_k: Number of results to return
            min_score: Minimum similarity score threshold
            filters: Optional filters (e.g., price range, category)
            
        Returns:
            List of search results with scores
        """
        # Generate query embedding
        query_vector = embedding_generator.encode_query(query)
        
        # Build kNN query
        knn_query = {
            "field": "combined_vector",
            "query_vector": query_vector,
            "k": top_k,
            "num_candidates": top_k * 2  # Oversample for better recall
        }
        
        # Add filters if provided
        if filters:
            knn_query["filter"] = self._build_filters(filters)
        
        # Execute search
        response = self.client.search(
            index=self.index_name,
            knn=knn_query,
            size=top_k,
            _source={
                "excludes": ["*_vector"]  # Don't return vectors in results
            }
        )
        
        # Process results
        results = []
        for hit in response['hits']['hits']:
            if hit['_score'] >= min_score:
                result = {
                    'id': hit['_id'],
                    'score': hit['_score'],
                    **hit['_source']
                }
                results.append(result)
        
        return results
    
    def _build_filters(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build Elasticsearch filter query from filter dict
        
        Args:
            filters: Dictionary of filters
            
        Returns:
            Elasticsearch filter query
        """
        must_clauses = []
        
        # Price range filter
        if 'min_price' in filters or 'max_price' in filters:
            range_filter = {"range": {"price": {}}}
            if 'min_price' in filters:
                range_filter["range"]["price"]["gte"] = filters['min_price']
            if 'max_price' in filters:
                range_filter["range"]["price"]["lte"] = filters['max_price']
            must_clauses.append(range_filter)
        
        # Category filter
        if 'category' in filters:
            must_clauses.append({"term": {"category": filters['category']}})
        
        # Brand filter
        if 'brand' in filters:
            must_clauses.append({"term": {"brand": filters['brand']}})
        
        # Rating filter
        if 'min_rating' in filters:
            must_clauses.append({
                "range": {"rating": {"gte": filters['min_rating']}}
            })
        
        return {"bool": {"must": must_clauses}} if must_clauses else {}


if __name__ == "__main__":
    # Test vector search
    searcher = VectorSearch()
    
    test_queries = [
        "affordable winter jackets for hiking",
        "laptop for programming under $1000",
        "gifts for coffee lovers"
    ]
    
    for query in test_queries:
        print(f"\n🔍 Query: {query}")
        results = searcher.search(query, top_k=3)
        for idx, result in enumerate(results, 1):
            print(f"  {idx}. {result['title']} (score: {result['score']:.3f})")
            print(f"     Price: ${result['price']}, Rating: {result['rating']}")

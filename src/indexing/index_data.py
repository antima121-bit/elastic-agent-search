"""
Elasticsearch index creation and data indexing
"""
from typing import List, Dict, Any
from elasticsearch import Elasticsearch, helpers
from tqdm import tqdm
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from config.elasticsearch import es_config
from src.indexing.embeddings import embedding_generator


class ProductIndexer:
    """Index products with vector embeddings into Elasticsearch"""
    
    def __init__(self):
        self.client = es_config.get_client()
        self.index_name = es_config.index_name
        
    def create_index(self):
        """
        Create Elasticsearch index with vector search capabilities
        """
        index_mapping = {
            "settings": {
                "number_of_shards": 1,
                "number_of_replicas": 0,
                "index": {
                    "knn": True,
                    "knn.algo_param.ef_search": 100
                }
            },
            "mappings": {
                "properties": {
                    "id": {"type": "keyword"},
                    "title": {
                        "type": "text",
                        "analyzer": "standard"
                    },
                    "description": {
                        "type": "text",
                        "analyzer": "standard"
                    },
                    "category": {"type": "keyword"},
                    "brand": {"type": "keyword"},
                    "price": {"type": "float"},
                    "rating": {"type": "float"},
                    "tags": {"type": "keyword"},
                    # Vector fields for semantic search
                    "title_vector": {
                        "type": "dense_vector",
                        "dims": embedding_generator.embedding_dim,
                        "index": True,
                        "similarity": "cosine"
                    },
                    "description_vector": {
                        "type": "dense_vector",
                        "dims": embedding_generator.embedding_dim,
                        "index": True,
                        "similarity": "cosine"
                    },
                    "combined_vector": {
                        "type": "dense_vector",
                        "dims": embedding_generator.embedding_dim,
                        "index": True,
                        "similarity": "cosine"
                    }
                }
            }
        }
        
        # Delete index if exists
        if self.client.indices.exists(index=self.index_name):
            print(f"Deleting existing index: {self.index_name}")
            self.client.indices.delete(index=self.index_name)
        
        # Create new index
        print(f"Creating index: {self.index_name}")
        self.client.indices.create(index=self.index_name, body=index_mapping)
        print("✅ Index created successfully with vector search capabilities")
    
    def index_products(self, products: List[Dict[str, Any]]):
        """
        Index products with vector embeddings
        
        Args:
            products: List of product dictionaries
        """
        print(f"\nIndexing {len(products)} products...")
        
        # Generate embeddings for all products
        titles = [p['title'] for p in products]
        descriptions = [p['description'] for p in products]
        combined_texts = [f"{p['title']}. {p['description']}" for p in products]
        
        print("Generating title embeddings...")
        title_vectors = embedding_generator.encode(titles)
        
        print("Generating description embeddings...")
        description_vectors = embedding_generator.encode(descriptions)
        
        print("Generating combined embeddings...")
        combined_vectors = embedding_generator.encode(combined_texts)
        
        # Prepare bulk indexing
        actions = []
        for idx, product in enumerate(products):
            doc = {
                **product,
                "title_vector": title_vectors[idx],
                "description_vector": description_vectors[idx],
                "combined_vector": combined_vectors[idx]
            }
            
            action = {
                "_index": self.index_name,
                "_id": product['id'],
                "_source": doc
            }
            actions.append(action)
        
        # Bulk index
        print("Bulk indexing documents...")
        success, failed = helpers.bulk(self.client, actions, raise_on_error=False)
        print(f"✅ Indexed {success} products successfully")
        if failed:
            print(f"❌ Failed to index {failed} products")
        
        # Refresh index
        self.client.indices.refresh(index=self.index_name)
        print("✅ Index refreshed")


if __name__ == "__main__":
    # Test connection
    if not es_config.test_connection():
        print("Failed to connect to Elasticsearch. Please check your configuration.")
        exit(1)
    
    # Create indexer
    indexer = ProductIndexer()
    
    # Create index
    indexer.create_index()
    
    print("\n✅ Setup complete! Ready to index products.")
    print(f"Index name: {indexer.index_name}")

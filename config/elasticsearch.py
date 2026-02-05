"""
Elasticsearch connection and configuration utilities
"""
import os
from elasticsearch import Elasticsearch
from dotenv import load_dotenv

load_dotenv()


class ElasticsearchConfig:
    """Configuration for Elasticsearch connection"""
    
    def __init__(self):
        self.url = os.getenv("ELASTICSEARCH_URL", "http://localhost:9200")
        self.cloud_id = os.getenv("ELASTICSEARCH_CLOUD_ID")
        self.api_key = os.getenv("ELASTICSEARCH_API_KEY")
        self.index_name = os.getenv("INDEX_NAME", "products_vector_search")
        
    def get_client(self) -> Elasticsearch:
        """
        Create and return Elasticsearch client
        
        Returns:
            Elasticsearch client instance
        """
        if self.cloud_id and self.api_key:
            # Elastic Cloud connection
            return Elasticsearch(
                cloud_id=self.cloud_id,
                api_key=self.api_key
            )
        else:
            # Local connection
            return Elasticsearch(
                hosts=[self.url],
                verify_certs=False
            )
    
    def test_connection(self) -> bool:
        """
        Test Elasticsearch connection
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            client = self.get_client()
            info = client.info()
            print(f"✅ Connected to Elasticsearch {info['version']['number']}")
            return True
        except Exception as e:
            print(f"❌ Connection failed: {str(e)}")
            return False


# Singleton instance
es_config = ElasticsearchConfig()

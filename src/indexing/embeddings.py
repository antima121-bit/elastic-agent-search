"""
Vector embedding generation using sentence transformers
"""
import os
from typing import List, Union
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

load_dotenv()


class EmbeddingGenerator:
    """Generate vector embeddings for text using sentence transformers"""
    
    def __init__(self, model_name: str = None):
        """
        Initialize embedding generator
        
        Args:
            model_name: Name of the sentence transformer model
        """
        self.model_name = model_name or os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
        print(f"Loading embedding model: {self.model_name}")
        self.model = SentenceTransformer(self.model_name)
        self.embedding_dim = self.model.get_sentence_embedding_dimension()
        print(f"✅ Model loaded. Embedding dimension: {self.embedding_dim}")
    
    def encode(self, texts: Union[str, List[str]]) -> Union[List[float], List[List[float]]]:
        """
        Generate embeddings for text(s)
        
        Args:
            texts: Single text string or list of texts
            
        Returns:
            Vector embedding(s) as list of floats
        """
        if isinstance(texts, str):
            # Single text
            embedding = self.model.encode(texts, convert_to_numpy=True)
            return embedding.tolist()
        else:
            # Multiple texts
            embeddings = self.model.encode(texts, convert_to_numpy=True, show_progress_bar=True)
            return embeddings.tolist()
    
    def encode_query(self, query: str) -> List[float]:
        """
        Generate embedding for search query
        
        Args:
            query: Search query text
            
        Returns:
            Query vector embedding
        """
        return self.encode(query)


# Singleton instance
embedding_generator = EmbeddingGenerator()

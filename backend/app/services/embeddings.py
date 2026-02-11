import logging
import os
from typing import List
import openai
from ..core.config import settings

logger = logging.getLogger(__name__)

class EmbeddingService:
    def __init__(self):
        self.provider = settings.EMBEDDING_PROVIDER
        self.model = None
        
        if self.provider == "openai" and settings.OPENAI_API_KEY:
            openai.api_key = settings.OPENAI_API_KEY
            logger.info("Using OpenAI embeddings.")
        else:
            logger.info("Using Local SentenceTransformer embeddings.")
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer('all-MiniLM-L6-v2')

    def generate_embedding(self, text: str) -> List[float]:
        if not text:
            return []
            
        try:
            if self.provider == "openai" and settings.OPENAI_API_KEY:
                text = text.replace("\n", " ")
                return openai.Embedding.create(input=[text], model="text-embedding-ada-002")['data'][0]['embedding']
            else:
                if self.model:
                     embedding = self.model.encode(text)
                     return embedding.tolist()
                return []
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            return []

    def get_dimension(self) -> int:
        if self.provider == "openai" and settings.OPENAI_API_KEY:
            return 1536
        return 384

embedding_service = EmbeddingService()

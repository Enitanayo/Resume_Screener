from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.models import Distance, VectorParams
from ..core.config import settings
import uuid
import logging

logger = logging.getLogger(__name__)

class VectorStore:
    def __init__(self):
        self._client = None
        self.collection_name = "candidates"

    @property
    def client(self):
        if not self._client:
            self._client = QdrantClient(url=settings.QDRANT_URL, api_key=settings.QDRANT_API_KEY)
            self._ensure_collection()
        return self._client

    def _ensure_collection(self):
        from .embeddings import embedding_service
        desired_dim = embedding_service.get_dimension()
        try:
            info = self._client.get_collection(self.collection_name)
            if info.config.params.vectors.size != desired_dim:
                logger.warning(f"Collection dimension mismatch (Expected: {desired_dim}, Got: {info.config.params.vectors.size}). Recreating collection...")
                self._client.delete_collection(self.collection_name)
                # Helper to re-create immediately? or let recursion/error handling logic work?
                # The generic except block below would catch and create.
                # raising Exception to trigger the except block below
                raise Exception("Collection deleted due to dimension mismatch")
        except Exception:
            # Create collection if not exists or was deleted
            logger.info(f"Creating Qdrant collection: {self.collection_name} with dim {desired_dim}")
            self._client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=desired_dim, distance=Distance.COSINE),
            )

    def upsert_embedding(self, embedding: list[float], metadata: dict) -> str:
        """
        Upserts an embedding into Qdrant. Returns the vector ID (UUID).
        """
        vector_id = str(uuid.uuid4())
        
        self.client.upsert(
            collection_name=self.collection_name,
            points=[
                models.PointStruct(
                    id=vector_id,
                    vector=embedding,
                    payload=metadata
                )
            ]
        )
        return vector_id

    def search_vectors(self, query_embedding: list[float], top_k: int = 10, filter_metadata: dict = None) -> list:
        """
        Search for similar vectors. 
        Returns list of (id, score, metadata).
        """
        response = self.client.query_points(
            collection_name=self.collection_name,
            query=query_embedding,
            limit=top_k,
            query_filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key=k,
                        match=models.MatchValue(value=v)
                    ) for k, v in (filter_metadata or {}).items()
                ]
            ),
            with_payload=True
        )
        
        results = []
        for hit in response.points:
            results.append({
                "id": hit.id,
                "score": hit.score,
                "metadata": hit.payload
            })
        return results

    def delete_embeddings_for_candidate(self, candidate_id: str):
        # Implementation depends on storing candidate_id in payload
        self.client.delete(
            collection_name=self.collection_name,
            points_selector=models.FilterSelector(
                filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="candidate_id",
                            match=models.MatchValue(value=candidate_id)
                        )
                    ]
                )
            )
        )

vector_store = VectorStore()

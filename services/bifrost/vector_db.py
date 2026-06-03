from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
import uuid
import os

class RAGVectorStore:
    def __init__(self, vector_size=384): 
        self.vector_size = vector_size # Ezt el kell mentenünk a törlés utáni újraalkotáshoz!
        qdrant_url = os.getenv("QDRANT_URL", ":memory:")
        print(f"Bifrost VectorStore csatlakozás: {qdrant_url}")
        
        if qdrant_url == ":memory:":
            self.client = QdrantClient(qdrant_url)
        else:
            self.client = QdrantClient(url=qdrant_url)
            
        self.collection_name = "knowledge_base"
        self._ensure_collection()

    def _ensure_collection(self):
        """Létrehozza a kollekciót, ha még nem létezik."""
        collections_response = self.client.get_collections()
        collection_names = [c.name for c in collections_response.collections]
        
        if self.collection_name not in collection_names:
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=self.vector_size, distance=Distance.COSINE),
            )

    def clear_database(self):
        """Teljesen kiüríti a korábbi dokumentumokat a tudásbázisból."""
        self.client.delete_collection(collection_name=self.collection_name)
        self._ensure_collection()
        print("🧹 Qdrant tudásbázis sikeresen kiürítve a korábbi adatoktól!")

    def upload_chunks(self, processed_chunks, embeddings):
        """Feltölti a chunkokat és a hozzájuk tartozó vektorokat."""
        points = []
        for i, chunk in enumerate(processed_chunks):
            points.append(PointStruct(
                id=str(uuid.uuid4()),
                vector=embeddings[i].tolist(),
                payload={
                    "text": chunk.get('content', ''),
                    "type": chunk.get('type', 'ismeretlen'),
                    "source": chunk.get('chunk_id', 'n/a'),
                    "qa_score": chunk.get('metadata', {}).get('qa_score', 0)
                }
            ))
        
        if points:
            self.client.upsert(collection_name=self.collection_name, points=points)
            print(f"✅ {len(points)} chunk sikeresen indexelve a Qdrant-ban.")
        return len(points)

    def search(self, query_vector, limit=3):
        """Keresés a tudásbázisban."""
        results = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_vector.tolist(),
            limit=limit
        )
        return results
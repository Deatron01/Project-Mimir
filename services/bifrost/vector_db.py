from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
import uuid
import os

class RAGVectorStore:
    # A korábbi kódodban 384 dimenziót használtál az e5-base-hez
    def __init__(self, vector_size=384): 
        qdrant_url = os.getenv("QDRANT_URL", ":memory:")
        print(f"Bifrost VectorStore csatlakozás: {qdrant_url}")
        
        if qdrant_url == ":memory:":
            self.client = QdrantClient(qdrant_url)
        else:
            self.client = QdrantClient(url=qdrant_url)
            
        self.collection_name = "knowledge_base"
        
        # Létrehozzuk a kollekciót, ha még nem létezik
        if not self.client.collection_exists(self.collection_name):
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
            )

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
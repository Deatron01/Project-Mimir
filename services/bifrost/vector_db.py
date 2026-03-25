from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
import uuid

class RAGVectorStore:
    def __init__(self, vector_size=384): # Az e5-base modell 384 dimenziós
        self.client = QdrantClient(":memory:") # Helyi memória-adatbázis
        self.collection_name = "knowledge_base"
        
        self.client.recreate_collection(
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
                    "text": chunk['content'],
                    "type": chunk['type'],
                    "source": chunk['chunk_id']
                }
            ))
        
        self.client.upsert(collection_name=self.collection_name, points=points)
        print(f"✅ {len(points)} chunk sikeresen indexelve a Qdrant-ban.")

    def search(self, query_vector, limit=3):
        """Keresés a tudásbázisban."""
        results = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_vector.tolist(),
            limit=limit
        )
        return results
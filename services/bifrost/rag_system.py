import torch
import uuid
from pipeline import RAGPipeline
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

class IntegratedRAGSystem:
    def __init__(self):
        self.pipeline = RAGPipeline(device='cuda')
        self.vector_size = 768  # E5-base dimenziója
        self.qdrant = QdrantClient(":memory:")
        self.collection_name = "unified_knowledge"
        
        if self.qdrant.collection_exists(self.collection_name):
            self.qdrant.delete_collection(self.collection_name)
            
        self.qdrant.create_collection(
            collection_name=self.collection_name,
            vectors_config=VectorParams(size=self.vector_size, distance=Distance.COSINE),
        )

    def _get_embedding(self, texts, is_query=False):
        prefix = "query: " if is_query else "passage: "
        prefixed_texts = [prefix + t for t in texts]
        
        with torch.no_grad():
            inputs = self.pipeline.chunker.tokenizer(prefixed_texts, padding=True, truncation=True, return_tensors='pt', max_length=512).to('cuda')
            outputs = self.pipeline.chunker.model(**inputs)
            mask = inputs['attention_mask']
            token_embeddings = outputs.last_hidden_state
            input_mask_expanded = mask.unsqueeze(-1).expand(token_embeddings.size()).float()
            embeddings = (torch.sum(token_embeddings * input_mask_expanded, 1) / torch.clamp(input_mask_expanded.sum(1), min=1e-9)).cpu().numpy()
        return embeddings

    def ingest_file(self, file_path_or_text, file_ext, percentile=85.0, target_size=1000):
        chunks = self.pipeline.process_document(file_path_or_text, file_ext, percentile=percentile, target_size=target_size)
        
        if not chunks: return

        texts = [c['content'] for c in chunks]
        embeddings = self._get_embedding(texts)

        points = []
        for i, chunk in enumerate(chunks):
            points.append(PointStruct(
                id=str(uuid.uuid4()),
                vector=embeddings[i].tolist(),
                payload={
                    "text": chunk['content'],
                    "type": chunk['type'],
                    "source": file_path_or_text if file_ext == "pdf" else "manual_input",
                    "qa_score": chunk['metadata'].get('qa_score')
                }
            ))
        
        self.qdrant.upsert(collection_name=self.collection_name, points=points)
        return len(points)
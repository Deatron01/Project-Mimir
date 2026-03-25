from router import AgenticRouter
from chunker import ContextualChunker
from judge import LLMJudge

class RAGPipeline:
    def __init__(self, device='cuda'):
        self.router = AgenticRouter()
        self.chunker = ContextualChunker(device=device)
        self.judge = LLMJudge()

    def process_document(self, document_text, file_extension, percentile=85.0, target_size=1000):
        routed_blocks = self.router.route_document(document_text, file_extension)
        final_chunks = []

        for i, block in enumerate(routed_blocks):
            block_type = block['type']
            content = block['content']
            
            # Kódblokkokat nem tördelünk tovább szemantikailag
            if block_type in ['code_block', 'code_snippet', 'code_error']:
                final_chunks.append({
                    "chunk_id": f"chunk_{i}",
                    "type": block_type,
                    "content": content,
                    "metadata": {"qa_score": 10}
                })
                continue

            # Narratív szövegek okos tördelése
            if block_type in ['narrative', 'markdown_section'] and len(content.strip()) > 50:
                semantic_chunks, _, threshold = self.chunker.embed_and_chunk(
                    content, 
                    method='percentile', 
                    threshold_val=percentile,
                    target_chunk_chars=target_size
                )
                
                # Első darab minőségellenőrzése (mintavétel)
                score = self.judge.evaluate_coherence(semantic_chunks[0])
                
                # Ha a minőség gyenge, fallback egy sűrűbb tördelésre
                if score < 7:
                    semantic_chunks, _, _ = self.chunker.embed_and_chunk(
                        content, method='std', threshold_val=1.5, target_chunk_chars=target_size
                    )

                for j, s_chunk in enumerate(semantic_chunks):
                    final_chunks.append({
                        "chunk_id": f"chunk_{i}_{j}",
                        "type": block_type,
                        "content": s_chunk,
                        "metadata": {"qa_score": score, "base_threshold": round(threshold, 4)}
                    })
            else:
                # Nagyon rövid blokkokat egyben hagyjuk
                final_chunks.append({"chunk_id": f"chunk_{i}_0", "type": block_type, "content": content, "metadata": {"qa_score": 10}})

        return final_chunks
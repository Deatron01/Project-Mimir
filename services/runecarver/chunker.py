import torch
import numpy as np
import re
from transformers import AutoTokenizer, AutoModel
from sklearn.metrics.pairwise import cosine_distances

class ContextualChunker:
    def __init__(self, model_name='intfloat/multilingual-e5-base', device='cuda'):
        print(f"Modell betöltése a {device.upper()}-ra: {model_name}...")
        self.device = device
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        dtype = torch.float16 if str(device).startswith('cuda') else torch.float32
        self.model = AutoModel.from_pretrained(model_name, torch_dtype=dtype).to(device)
        self.model.eval()

    def _get_sentence_spans(self, text):
        """
        Mondatokra bontás intelligensebb módon, elkerülve a változó szélességű look-behind hibát.
        """
        sentences = []
        # Olyan pontokat keresünk, amelyek után szóköz és nagybetű áll (mondatkezdés gyanúja)
        # A split() helyett finditer-t használunk, hogy megmaradjanak a pozíciók
        # Ez a regex megbízhatóan működik magyar és angol szövegekkel is.
        sentence_endings = re.compile(r'([^.!?\n]+[.!?\n]*)')
        
        for match in sentence_endings.finditer(text):
            span = match.group()
            # Utólagos finomítás: ha a szakasz túl rövid (pl. csak egy "dr."), 
            # akkor megpróbálhatnánk összefűzni, de az alap felosztáshoz ez a legstabilabb.
            start = match.start()
            clean_span = span.strip()
            if clean_span:
                end = start + len(span)
                sentences.append((clean_span, start, end))
        
        return sentences

    def _legacy_sentence_embeddings(self, text, sentences):
        """Eredeti viselkedés: az egész szöveg EGY menetben, max. 512 tokenig.
        A 512. token utáni mondatok nullvektort kapnak (csak összehasonlító kísérlethez)."""
        # 1. Tokenizálás és Beágyazás
        inputs = self.tokenizer(text, return_tensors='pt', truncation=True, max_length=512, return_offsets_mapping=True)
        offsets = inputs.pop('offset_mapping')[0].cpu().numpy()
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        
        with torch.no_grad():
            outputs = self.model(**inputs)
            token_embeddings = outputs.last_hidden_state[0]

        # 2. Precíziós Mean Pooling mondatonként
        sentence_embeddings = []
        for (sentence_text, char_start, char_end) in sentences:
            token_indices = [idx for idx, (o_start, o_end) in enumerate(offsets) 
                             if o_start < char_end and o_end > char_start and (o_start != o_end)]
            
            if token_indices:
                pool = token_embeddings[token_indices].mean(dim=0).cpu().numpy()
                sentence_embeddings.append(pool)
            else:
                sentence_embeddings.append(np.zeros(token_embeddings.shape[1]))
        return sentence_embeddings

    def _windowed_sentence_embeddings(self, text, sentences, max_tokens=510):
        """Mondatbeágyazás hosszú szövegre: a mondatokat <= 512 tokenes ablakokba csoportosítjuk
        (mondathatáron vágva), ablakonként futtatjuk a modellt, és mondatonként átlagolunk.
        Rövid (<= 512 token) szövegnél ez egyetlen ablak, azaz ugyanaz, mint a régi viselkedés."""
        lengths = [len(self.tokenizer(st, add_special_tokens=False)["input_ids"]) for st, _, _ in sentences]
        windows, current, current_len = [], [], 0
        for idx, n_tok in enumerate(lengths):
            if current and current_len + n_tok > max_tokens:
                windows.append(current)
                current, current_len = [], 0
            current.append(idx)
            current_len += n_tok
        if current:
            windows.append(current)

        hidden = self.model.config.hidden_size
        sentence_embeddings = [None] * len(sentences)
        for win in windows:
            w_start = sentences[win[0]][1]
            w_end = sentences[win[-1]][2]
            inputs = self.tokenizer(text[w_start:w_end], return_tensors='pt', truncation=True, max_length=512,
                                    return_offsets_mapping=True)
            offsets = inputs.pop('offset_mapping')[0].cpu().numpy()
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            with torch.no_grad():
                token_embeddings = self.model(**inputs).last_hidden_state[0]
            for idx in win:
                _, c_start, c_end = sentences[idx]
                a, b = c_start - w_start, c_end - w_start
                token_indices = [t for t, (o_s, o_e) in enumerate(offsets) if o_s < b and o_e > a and o_s != o_e]
                if token_indices:
                    sentence_embeddings[idx] = token_embeddings[token_indices].float().mean(dim=0).cpu().numpy()
                else:
                    sentence_embeddings[idx] = np.zeros(hidden, dtype=np.float32)
        return sentence_embeddings

    def embed_and_chunk(self, text, method='percentile', threshold_val=85.0, target_chunk_chars=800, encoder='window'):
        sentences = self._get_sentence_spans(text)
        if len(sentences) <= 1:
            return [sentences[0][0]] if sentences else [text], [], 0.0

        # 1-2. Mondatonkénti beágyazás (encoder="window": hosszú szövegre is jó; "legacy": régi, 512 tokenre vágott)
        if encoder == 'legacy':
            sentence_embeddings = self._legacy_sentence_embeddings(text, sentences)
        else:
            sentence_embeddings = self._windowed_sentence_embeddings(text, sentences)

        # 3. Koszinusz távolságok számítása
        distances = []
        for i in range(len(sentence_embeddings) - 1):
            dist = cosine_distances(sentence_embeddings[i].reshape(1, -1), 
                                    sentence_embeddings[i+1].reshape(1, -1))[0][0]
            distances.append(dist)

        # 4. Alap küszöb (Threshold) kiszámítása
        if method == 'percentile':
            base_threshold = np.percentile(distances, threshold_val)
        else:
            base_threshold = np.mean(distances) + (threshold_val * np.std(distances))

        # 5. OKOS DARABOLÁS (Soft-Limit logika)
        chunks = []
        current_chunk = [sentences[0][0]]
        current_length = len(sentences[0][0])
        
        for i, dist in enumerate(distances):
            # Soft-limit: Ha közeledünk a célmérethez, érzékenyebbé válunk
            size_ratio = current_length / target_chunk_chars
            effective_threshold = base_threshold / (size_ratio if size_ratio > 1 else 1)
            
            if dist > effective_threshold:
                chunks.append(" ".join(current_chunk))
                current_chunk = [sentences[i + 1][0]]
                current_length = len(sentences[i + 1][0])
            else:
                current_chunk.append(sentences[i + 1][0])
                current_length += len(sentences[i + 1][0])

        if current_chunk:
            chunks.append(" ".join(current_chunk))

        return chunks, distances, base_threshold
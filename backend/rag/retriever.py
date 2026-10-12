"""Search brochure chunks. Always restricted to ONE vehicle, so answers never mix cars up."""
import json
import re
from functools import lru_cache

import numpy as np

from rag.config import CHUNKS_FILE, VECTORS_FILE
from rag.embeddings import embed_texts, gemini_available

STOPWORDS = {"the", "a", "an", "is", "it", "does", "do", "this", "that", "of", "in", "on", "for", "and",
             "to", "how", "what", "which", "are", "has", "have", "with", "car", "me", "can", "i", "be", "there"}


def _tokens(text):
    words = re.findall(r"[a-z0-9]+", text.lower())
    return {w[:-1] if w.endswith("s") and len(w) > 3 else w for w in words if w not in STOPWORDS}


class Retriever:
    def __init__(self):
        self.chunks = json.loads(CHUNKS_FILE.read_text(encoding="utf-8"))
        self.vectors = None
        if VECTORS_FILE.exists():
            v = np.load(VECTORS_FILE)
            self.vectors = v / np.linalg.norm(v, axis=1, keepdims=True)

    def section_text(self, vehicle_id, section):
        for c in self.chunks:
            if c["vehicle_id"] == vehicle_id and c["section"] == section:
                return c["text"]
        return None

    def search(self, query, vehicle_id, k=4):
        idx = [i for i, c in enumerate(self.chunks) if c["vehicle_id"] == vehicle_id]
        if not idx:
            return []
        if self.vectors is not None and gemini_available():
            q = np.array(embed_texts([query], "RETRIEVAL_QUERY")[0], dtype="float32")
            scores = self.vectors[idx] @ (q / np.linalg.norm(q))
            min_score = 0.0
        else:   # keyword fallback: share of the question's words found in the chunk
            q = _tokens(query)
            scores = np.array([len(q & _tokens(self.chunks[i]["embed_text"])) / max(len(q), 1) for i in idx])
            min_score = 0.0
        order = np.argsort(scores)[::-1][:k]
        return [{**self.chunks[idx[o]], "score": round(float(scores[o]), 3)} for o in order if scores[o] > min_score]


@lru_cache(maxsize=1)
def get_retriever():
    return Retriever()

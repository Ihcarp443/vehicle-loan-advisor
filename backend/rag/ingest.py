"""Build the vector store from the brochures. Run once (and again whenever a brochure changes):
    cd backend && python -m rag.ingest"""
import json

import numpy as np

from rag.chunking import chunk_brochure
from rag.config import BROCHURE_DIR, CHUNKS_FILE, STORE_DIR, VECTORS_FILE
from rag.embeddings import embed_texts, gemini_available


def build_store():
    chunks = []
    for path in sorted(BROCHURE_DIR.glob("*.md")):
        chunks += chunk_brochure(path)
    STORE_DIR.mkdir(parents=True, exist_ok=True)
    CHUNKS_FILE.write_text(json.dumps(chunks, indent=1), encoding="utf-8")

    if gemini_available():
        vectors = np.array(embed_texts([c["embed_text"] for c in chunks]), dtype="float32")
        np.save(VECTORS_FILE, vectors)
        mode = f"embeddings saved ({vectors.shape[1]} dimensions)"
    else:
        VECTORS_FILE.unlink(missing_ok=True)
        mode = "NO embeddings (GEMINI_API_KEY not set); keyword search will be used"
    print(f"{len(chunks)} chunks from {len({c['vehicle_id'] for c in chunks})} brochures; {mode}")
    return len(chunks)


if __name__ == "__main__":
    build_store()

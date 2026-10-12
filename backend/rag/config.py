"""Paths shared by the RAG code. Override with environment variables when running in Docker."""
import os
from pathlib import Path

ROOT = Path(os.getenv("PROJECT_ROOT", Path(__file__).resolve().parents[2]))
BROCHURE_DIR = Path(os.getenv("BROCHURE_DIR", ROOT / "data" / "documents" / "vehicles"))
STORE_DIR = Path(os.getenv("VECTORSTORE_DIR", ROOT / "vectorstore"))
CHUNKS_FILE = STORE_DIR / "vehicle_chunks.json"
VECTORS_FILE = STORE_DIR / "vehicle_embeddings.npy"

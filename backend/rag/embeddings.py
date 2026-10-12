"""Thin wrapper around the Gemini API for embeddings and text generation.
Model names come from env variables; check Google's docs for the current names."""
import os
from dotenv import load_dotenv
load_dotenv()   
EMBED_MODEL = os.getenv("EMBED_MODEL", "gemini-embedding-001")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")


def gemini_available():
    return bool(os.getenv("GEMINI_API_KEY"))


def _client():
    from google import genai
    return genai.Client(api_key=os.environ["GEMINI_API_KEY"])


def embed_texts(texts, task="RETRIEVAL_DOCUMENT"):
    """task: RETRIEVAL_DOCUMENT for chunks, RETRIEVAL_QUERY for the user's question."""
    from google.genai import types
    client = _client()
    vectors = []
    for i in range(0, len(texts), 50):
        resp = client.models.embed_content(model=EMBED_MODEL, contents=texts[i:i + 50],
                                           config=types.EmbedContentConfig(task_type=task))
        vectors += [e.values for e in resp.embeddings]
    return vectors


def generate_text(prompt):
    return _client().models.generate_content(model=GEMINI_MODEL, contents=prompt).text

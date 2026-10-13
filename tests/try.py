# import os
# from dotenv import load_dotenv
# load_dotenv()

# EMBED_MODEL = os.getenv("EMBED_MODEL", "gemini-embedding-001")
# GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

# def gemini_available():
#     return bool(os.getenv("GEMINI_API_KEY"))

# def _client():
#     from google import genai
#     return genai.Client(api_key=os.environ["GEMINI_API_KEY"])

# def embed_texts(texts, task="RETRIEVAL_DOCUMENT"):
#     """task: RETRIEVAL_DOCUMENT for chunks, RETRIEVAL_QUERY for the user's question."""
#     from google.genai import types
#     client = _client()
#     vectors = []
#     for i in range(0, len(texts), 50):
#         resp = client.models.embed_content(
#             model=EMBED_MODEL,
#             contents=texts[i:i + 50],
#             config=types.EmbedContentConfig(task_type=task)
#         )
#         vectors += [e.values for e in resp.embeddings]
#     return vectors

# def generate_text(prompt):
#     client = _client()
#     resp = client.models.generate_content(model=GEMINI_MODEL, contents=prompt)
#     return resp.text


# if gemini_available():
#     print("Gemini API key found, testing...")

#     # Test embedding
#     emb = embed_texts(["Vehicle loan advisor test"])
#     print("Embedding length:", len(emb[0]))

#     # Test generation
#     txt = generate_text("Explain loan-to-value ratio in simple terms.")
#     print("Generated text:", txt)
# else:
#     print("No GEMINI_API_KEY set in environment.")
from pathlib import Path

def print_structure(root_dir):
    root = Path(root_dir)
    for path in sorted(root.rglob("*")):
        depth = len(path.relative_to(root).parts)
        print("    " * depth + path.name)

# Example: print current working directory structure
print_structure(Path.cwd())

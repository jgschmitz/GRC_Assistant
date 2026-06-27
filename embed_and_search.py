"""
embed_and_search.py - end-to-end demo of the AI layer:
  1. embed policy chunks with Voyage (voyage-4-large, 1024 dims) and upsert them
  2. run a version-aware $vectorSearch for a natural-language question

Requires .env with MONGODB_URI and VOYAGE_API_KEY, plus the vector index from
scripts/create_indexes.py.

Usage:
  python scripts/embed_and_search.py index            # embed + upsert sample chunks
  python scripts/embed_and_search.py search "how do we protect backups?"
"""
from __future__ import annotations

import os

import typer
from dotenv import load_dotenv

load_dotenv()
app = typer.Typer(add_completion=False)

SAMPLE_CHUNKS = [
    {"_id": "POL-111#c01", "policyId": "POL-111", "version": 4,
     "text": "All production data stores must encrypt data at rest using AES-256."},
    {"_id": "POL-111#c02", "policyId": "POL-111", "version": 4,
     "text": "Encrypted backups must be stored in a separate access-controlled bucket."},
    {"_id": "POL-111#c03", "policyId": "POL-111", "version": 4,
     "text": "Encryption keys must be rotated every 90 days under the key management standard."},
]


def _voyage():
    import voyageai

    key = os.getenv("VOYAGE_API_KEY")
    if not key:
        typer.echo("VOYAGE_API_KEY not set. Copy .env.example to .env first.", err=True)
        raise typer.Exit(1)
    return voyageai.Client(api_key=key)


def _db():
    from pymongo import MongoClient

    uri = os.getenv("MONGODB_URI")
    if not uri:
        typer.echo("MONGODB_URI not set. Copy .env.example to .env first.", err=True)
        raise typer.Exit(1)
    return MongoClient(uri)[os.getenv("DB_NAME", "grc_assistant")]


def embed(texts: list[str], input_type: str) -> list[list[float]]:
    client = _voyage()
    model = os.getenv("VOYAGE_MODEL", "voyage-4-large")
    dims = int(os.getenv("EMBEDDING_DIMENSIONS", "1024"))
    result = client.embed(texts, model=model, input_type=input_type, output_dimension=dims)
    return result.embeddings


@app.command()
def index():
    db = _db()
    vectors = embed([c["text"] for c in SAMPLE_CHUNKS], input_type="document")
    for chunk, vector in zip(SAMPLE_CHUNKS, vectors):
        doc = {**chunk, "embedding": vector}
        db.policy_chunks.replace_one({"_id": doc["_id"]}, doc, upsert=True)
    typer.echo(f"embedded + upserted {len(SAMPLE_CHUNKS)} chunks into policy_chunks")


@app.command()
def search(question: str, version: int = 4, limit: int = 3):
    db = _db()
    query_vector = embed([question], input_type="query")[0]
    pipeline = [
        {
            "$vectorSearch": {
                "index": "vector_index",
                "path": "embedding",
                "queryVector": query_vector,
                "numCandidates": 100,
                "limit": limit,
                "filter": {"version": version},
            }
        },
        {"$project": {"text": 1, "policyId": 1, "score": {"$meta": "vectorSearchScore"}}},
    ]
    for hit in db.policy_chunks.aggregate(pipeline):
        typer.echo(f"[{hit['score']:.3f}] {hit['policyId']}: {hit['text']}")


if __name__ == "__main__":
    app()

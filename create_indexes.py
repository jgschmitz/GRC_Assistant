"""
create_indexes.py - create Atlas Vector Search indexes + supporting btree indexes
for the converted collections.

Requires a real Atlas connection (.env with MONGODB_URI). Vector Search indexes are
only available on MongoDB Atlas, not a local mongod.

Usage:
  python scripts/create_indexes.py
"""
from __future__ import annotations

import os

import typer
from dotenv import load_dotenv

load_dotenv()
app = typer.Typer(add_completion=False)

CHUNK_COLLECTIONS = ["policy_chunks", "standard_chunks", "control_chunks", "risk_record_chunks"]


def vector_index_definition(dimensions: int) -> dict:
    return {
        "fields": [
            {"type": "vector", "path": "embedding", "numDimensions": dimensions, "similarity": "cosine"},
            {"type": "filter", "path": "policyId"},
            {"type": "filter", "path": "version"},
        ]
    }


@app.command()
def main():
    from pymongo import ASCENDING, MongoClient
    from pymongo.operations import SearchIndexModel

    uri = os.getenv("MONGODB_URI")
    if not uri:
        typer.echo("MONGODB_URI not set. Copy .env.example to .env first.", err=True)
        raise typer.Exit(1)

    dimensions = int(os.getenv("EMBEDDING_DIMENSIONS", "1024"))
    client = MongoClient(uri)
    db = client[os.getenv("DB_NAME", "grc_assistant")]

    # Standard indexes for operational lookups.
    db.policies.create_index([("version", ASCENDING)])
    db.risk_records.create_index([("classification.severity", ASCENDING)])
    db.risk_records.create_index([("policyRefs", ASCENDING)])
    typer.echo("created standard btree indexes")

    # Atlas Vector Search indexes (one per chunk collection).
    definition = vector_index_definition(dimensions)
    for name in CHUNK_COLLECTIONS:
        model = SearchIndexModel(definition=definition, name="vector_index", type="vectorSearch")
        try:
            db[name].create_search_index(model=model)
            typer.echo(f"created vector_index on {name} ({dimensions} dims)")
        except Exception as exc:  # index may already exist
            typer.echo(f"skip {name}: {exc}")

    client.close()


if __name__ == "__main__":
    app()

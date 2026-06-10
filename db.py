"""MongoDB connection and seeding helpers for the contacts project.

Flat module by design: the domain (one collection, 11 documents) does not
justify a repository pattern.
"""

import json
import os
from pathlib import Path

from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database

DEFAULT_URI = "mongodb://localhost:27017"
DB_NAME = "contatti"
COLLECTION_NAME = "contatti"
DATASET_PATH = Path(__file__).parent / "data" / "contatti.json"


def get_client(uri: str | None = None, **kwargs: object) -> MongoClient:
    """Return a client for `uri`, the MONGO_URI env var, or the local default.

    Extra keyword arguments are forwarded to MongoClient (e.g. the tests
    pass a short serverSelectionTimeoutMS to fail fast when Mongo is down).
    """
    return MongoClient(uri or os.environ.get("MONGO_URI", DEFAULT_URI), **kwargs)


def get_db(client: MongoClient, name: str = DB_NAME) -> Database:
    return client[name]


def get_collection(db: Database, name: str = COLLECTION_NAME) -> Collection:
    return db[name]


def seed_collection(collection: Collection, dataset_path: Path = DATASET_PATH) -> int:
    """Reset `collection` to the dataset state and return the document count.

    Drops the collection, creates the unique {Nome, Cognome} index (an
    integrity constraint: created BEFORE the import so a dataset containing
    duplicates fails loudly), then imports the JSON array at `dataset_path`.
    Same semantics as the docker seed (docker/seed.sh).
    """
    collection.drop()
    collection.create_index({"Nome": 1, "Cognome": 1}, unique=True)
    with open(dataset_path, encoding="utf-8") as f:
        collection.insert_many(json.load(f))
    return collection.count_documents({})

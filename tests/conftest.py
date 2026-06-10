"""Test fixtures: a dedicated, reseeded-per-test MongoDB collection.

State management by design (issue #5): tests run on their own database
(`contatti_test`), reseeded from the dataset before each test and dropped
afterwards — fully independent from the `contatti` database populated by
the docker seed, so `docker compose up` + `pytest` never interfere.
"""

import pytest
from pymongo.collection import Collection
from pymongo.errors import ServerSelectionTimeoutError

from contacts import db

TEST_DB = "contatti_test"


@pytest.fixture()
def contatti() -> Collection:
    client = db.get_client(serverSelectionTimeoutMS=2000)
    try:
        client.admin.command("ping")
    except ServerSelectionTimeoutError:
        pytest.fail(
            "MongoDB non raggiungibile (MONGO_URI o localhost:27017): "
            "avviare prima l'ambiente con 'docker compose up -d'"
        )
    collection = db.get_collection(db.get_db(client, TEST_DB))
    db.seed_collection(collection)
    yield collection
    client.drop_database(TEST_DB)
    client.close()

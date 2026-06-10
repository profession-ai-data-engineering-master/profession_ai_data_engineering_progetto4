"""Rubrica contatti su MongoDB — soluzione del progetto.

Runs the 6 queries and the 2 updates of the assignment against a standalone
MongoDB (default: the one started by ``docker compose up``).

Usage:
    python solution.py

The connection URI can be overridden via the ``MONGO_URI`` env var
(default ``mongodb://localhost:27017``).
"""

import json
import os
from pprint import pprint

from pymongo import MongoClient, ReturnDocument

MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017")
DATASET = os.path.join(os.path.dirname(__file__), "data", "contatti.json")


def header(title: str) -> None:
    print(f"\n=== {title} ===")


client = MongoClient(MONGO_URI)

# --- Setup: reset database, unique index, import -------------------------
# The unique index on {Nome, Cognome} is an integrity constraint
# (anti-duplicates, it backs the upsert below), created BEFORE the import
# so a dataset with duplicates would fail loudly.
client.drop_database("contatti")
contatti = client["contatti"]["contatti"]
contatti.create_index({"Nome": 1, "Cognome": 1}, unique=True)
with open(DATASET, encoding="utf-8") as f:
    contatti.insert_many(json.load(f))
header("Setup")
print(f"{contatti.count_documents({})} contatti importati, indice univoco creato")

# --- Query 1: tutti i contatti della società WebCorp ----------------------
header("Contatti della società WebCorp")
pprint(list(contatti.find({"Società": "WebCorp"}, {"_id": 0})))

# --- Query 2: contatti con più di un numero di telefono -------------------
# Numero_di_cellulare is heterogeneous (string or list): $cond + $isArray
# treats the string case as size 0 instead of erroring out.
header("Contatti con più di un numero di telefono")
pprint(
    list(
        contatti.find(
            {
                "$expr": {
                    "$gt": [
                        {
                            "$cond": [
                                {"$isArray": "$Numero_di_cellulare"},
                                {"$size": "$Numero_di_cellulare"},
                                0,
                            ]
                        },
                        1,
                    ]
                }
            },
            {"_id": 0, "Nome": 1, "Cognome": 1},
        )
    )
)

# --- Query 3: numeri di telefono dei contatti con tag "lavoro" ------------
# Aggregation pipeline: $unwind flattens the number lists so the result is
# one phone number per row regardless of the string/list shape.
header('Numeri di telefono dei contatti con tag "lavoro"')
pprint(
    list(
        contatti.aggregate(
            [
                {"$match": {"Tag": {"$in": ["lavoro"]}}},
                {"$project": {"_id": 0, "Numero_di_cellulare": 1}},
                {"$unwind": "$Numero_di_cellulare"},
            ]
        )
    )
)

# --- Query 4: contatti senza profilo social --------------------------------
# $exists: false on the nested path matches both documents having
# Altri_contatti without Profilo_social and documents without the
# Altri_contatti subdocument at all — consistent with the assignment.
header("Contatti senza profilo social")
pprint(
    list(
        contatti.find(
            {"Altri_contatti.Profilo_social": {"$exists": False}},
            {"_id": 0, "Nome": 1, "Cognome": 1},
        )
    )
)

# --- Query 5: conteggio amici stretti / non amici stretti ------------------
# Group by value without coalescing missing fields to False: if a document
# lacked Amici_stretti it would surface as an _id: None group, keeping the
# absence of information visible (hypothetical here: the field is always
# present in this dataset).
header("Conteggio amici stretti / non amici stretti")
pprint(
    list(
        contatti.aggregate(
            [
                {"$project": {"Amici_stretti": 1}},
                {"$group": {"_id": "$Amici_stretti", "Conteggio": {"$sum": 1}}},
                {"$sort": {"_id": -1}},
            ]
        )
    )
)

# --- Query 6: media chiamate ultimo mese degli amici stretti ----------------
header("Media chiamate ultimo mese degli amici stretti")
pprint(
    list(
        contatti.aggregate(
            [
                {"$match": {"Amici_stretti": True}},
                {
                    "$group": {
                        "_id": 1,
                        "Media_chiamate_amici_stretti": {
                            "$avg": "$Chiamate_ultimo_mese"
                        },
                    }
                },
            ]
        )
    )
)

# --- Update 1: aggiungere il numero 345678902 a Simone Azzurri --------------
# Update pipeline with $concatArrays: the field is first normalized to a
# list with the same $isArray/$cond pattern used in query 2 (it may be a
# string or a list), then the new number is appended. No upsert: this is an
# update of an existing contact — with upsert, a typo in the name would
# create a partial phantom document.
header("Aggiunta del numero 345678902 a Simone Azzurri")
pprint(
    contatti.find_one_and_update(
        filter={"Nome": "Simone", "Cognome": "Azzurri"},
        update=[
            {
                "$set": {
                    "Numero_di_cellulare": {
                        "$concatArrays": [
                            {
                                "$cond": [
                                    {"$isArray": "$Numero_di_cellulare"},
                                    "$Numero_di_cellulare",
                                    ["$Numero_di_cellulare"],
                                ]
                            },
                            ["345678902"],
                        ]
                    }
                }
            }
        ],
        return_document=ReturnDocument.AFTER,
        projection={"_id": 0},
    )
)

# --- Update 2: inserire il contatto di Mary Salgado --------------------------
# Here upsert IS correct: insert-if-absent keyed on the unique index fields,
# so re-running the script does not create duplicates.
header("Inserimento del contatto Mary Salgado")
pprint(
    contatti.find_one_and_update(
        filter={"Nome": "Mary", "Cognome": "Salgado"},
        update={
            "$set": {
                "Numero_di_cellulare": "346679933",
                "Altri_contatti.Indirizzo": "Via 25 Aprile 3, Firenze",
            }
        },
        upsert=True,
        return_document=ReturnDocument.AFTER,
        projection={"_id": 0},
    )
)

client.close()

"""The 6 queries and 2 updates of the assignment as reusable functions.

Each function takes the target collection explicitly (easy to point at a
test collection) and mirrors the MQL of solution.py: $expr/$cond/$isArray
for the heterogeneous string|list phone field, $unwind to flatten numbers,
$group/$avg for the aggregations.
"""

from typing import Any

from pymongo import ReturnDocument
from pymongo.collection import Collection

# Normalize Numero_di_cellulare to a list: the dataset stores it either as
# a single string or as a list of strings. Shared by queries and updates so
# there is exactly one way to handle the string|list case.
_PHONES_AS_ARRAY = {
    "$cond": [
        {"$isArray": "$Numero_di_cellulare"},
        "$Numero_di_cellulare",
        ["$Numero_di_cellulare"],
    ]
}


def by_company(contatti: Collection, company: str) -> list[dict[str, Any]]:
    """All contacts of `company`."""
    return list(contatti.find({"Società": company}, {"_id": 0}))


def with_multiple_numbers(contatti: Collection) -> list[dict[str, Any]]:
    """Name and surname of contacts having more than one phone number."""
    return list(
        contatti.find(
            {"$expr": {"$gt": [{"$size": _PHONES_AS_ARRAY}, 1]}},
            {"_id": 0, "Nome": 1, "Cognome": 1},
        )
    )


def phones_by_tag(contatti: Collection, tag: str) -> list[str]:
    """Phone numbers (flattened, one per row) of contacts tagged `tag`."""
    docs = contatti.aggregate(
        [
            {"$match": {"Tag": {"$in": [tag]}}},
            {"$project": {"_id": 0, "Numero_di_cellulare": 1}},
            {"$unwind": "$Numero_di_cellulare"},
        ]
    )
    return [doc["Numero_di_cellulare"] for doc in docs]


def without_social(contatti: Collection) -> list[dict[str, Any]]:
    """Name and surname of contacts without a social profile.

    $exists: false on the nested path matches both documents whose
    Altri_contatti lacks Profilo_social and documents without the
    Altri_contatti subdocument at all.
    """
    return list(
        contatti.find(
            {"Altri_contatti.Profilo_social": {"$exists": False}},
            {"_id": 0, "Nome": 1, "Cognome": 1},
        )
    )


def count_close_friends(contatti: Collection) -> dict[bool | None, int]:
    """Contact count grouped by the Amici_stretti value.

    Documents missing the field (none in this dataset) would surface under
    the None key: absence of information is kept visible, not coalesced to
    False.
    """
    docs = contatti.aggregate(
        [
            {"$project": {"Amici_stretti": 1}},
            {"$group": {"_id": "$Amici_stretti", "Conteggio": {"$sum": 1}}},
            {"$sort": {"_id": -1}},
        ]
    )
    return {doc["_id"]: doc["Conteggio"] for doc in docs}


def avg_calls_close_friends(contatti: Collection) -> float | None:
    """Average calls in the last month among close friends (None if none)."""
    docs = list(
        contatti.aggregate(
            [
                {"$match": {"Amici_stretti": True}},
                {
                    "$group": {
                        "_id": 1,
                        "Media": {"$avg": "$Chiamate_ultimo_mese"},
                    }
                },
            ]
        )
    )
    return docs[0]["Media"] if docs else None


def add_number(
    contatti: Collection, nome: str, cognome: str, number: str
) -> dict[str, Any] | None:
    """Append `number` to an EXISTING contact, returning the updated document.

    Update pipeline with $concatArrays: the field is first normalized to a
    list (string|list), then the number is appended — the result is always
    a flat list. No upsert: a typo in the name must return None, not create
    a partial phantom document.
    """
    return contatti.find_one_and_update(
        filter={"Nome": nome, "Cognome": cognome},
        update=[
            {
                "$set": {
                    "Numero_di_cellulare": {
                        "$concatArrays": [_PHONES_AS_ARRAY, [number]]
                    }
                }
            }
        ],
        return_document=ReturnDocument.AFTER,
        projection={"_id": 0},
    )


def upsert_contact(
    contatti: Collection, nome: str, cognome: str, fields: dict[str, Any]
) -> dict[str, Any]:
    """Insert-or-update the contact keyed on the unique index fields.

    Here upsert IS correct: insert-if-absent on {Nome, Cognome}, so calling
    it twice does not create duplicates.
    """
    return contatti.find_one_and_update(
        filter={"Nome": nome, "Cognome": cognome},
        update={"$set": fields},
        upsert=True,
        return_document=ReturnDocument.AFTER,
        projection={"_id": 0},
    )

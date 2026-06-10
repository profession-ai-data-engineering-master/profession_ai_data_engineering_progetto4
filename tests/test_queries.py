"""Assertions on the expected results (oracles computed from the dataset)
for the 6 queries and the 2 updates, plus the 3 regression tests required
by issue #5."""

import pytest
from pymongo.errors import DuplicateKeyError

import queries


def names(docs: list[dict]) -> set[tuple[str, str]]:
    return {(d["Nome"], d["Cognome"]) for d in docs}


# --- The 6 queries ---------------------------------------------------------


def test_by_company_webcorp(contatti):
    result = queries.by_company(contatti, "WebCorp")
    assert names(result) == {("Marco", "Bianchi"), ("Alessia", "Moretti")}


def test_with_multiple_numbers(contatti):
    result = queries.with_multiple_numbers(contatti)
    assert names(result) == {
        ("Laura", "Rossi"),
        ("Chiara", "Marroni"),
        ("Alessia", "Moretti"),
    }


def test_phones_by_tag_lavoro(contatti):
    result = queries.phones_by_tag(contatti, "lavoro")
    assert sorted(result) == sorted(
        ["348123456", "349654321", "347098765", "321654987"]
    )


def test_without_social(contatti):
    result = queries.without_social(contatti)
    assert len(result) == 8
    # everyone except the 3 contacts having a Profilo_social
    assert names(result).isdisjoint(
        {("Laura", "Rossi"), ("Sara", "Gialli"), ("Elena", "Viola")}
    )


def test_count_close_friends(contatti):
    assert queries.count_close_friends(contatti) == {False: 6, True: 5}


def test_avg_calls_close_friends(contatti):
    # (10 + 15 + 12 + 20 + 25) / 5 = 82 / 5
    assert queries.avg_calls_close_friends(contatti) == pytest.approx(16.4)


# --- The 2 updates ----------------------------------------------------------


def test_add_number_to_simone(contatti):
    result = queries.add_number(contatti, "Simone", "Azzurri", "345678902")
    assert result is not None
    assert result["Numero_di_cellulare"] == ["345678901", "345678902"]


def test_upsert_inserts_mary(contatti):
    fields = {
        "Numero_di_cellulare": "346679933",
        "Altri_contatti.Indirizzo": "Via 25 Aprile 3, Firenze",
    }
    result = queries.upsert_contact(contatti, "Mary", "Salgado", fields)
    assert result["Numero_di_cellulare"] == "346679933"
    assert result["Altri_contatti"] == {"Indirizzo": "Via 25 Aprile 3, Firenze"}
    assert contatti.count_documents({}) == 12


def test_upsert_is_idempotent(contatti):
    fields = {"Numero_di_cellulare": "346679933"}
    queries.upsert_contact(contatti, "Mary", "Salgado", fields)
    queries.upsert_contact(contatti, "Mary", "Salgado", fields)
    assert contatti.count_documents({"Nome": "Mary", "Cognome": "Salgado"}) == 1


# --- Regression tests (issue #5) ---------------------------------------------


def test_regression_append_stays_flat(contatti):
    """Appending to an already-list field must extend it, not nest it
    (protects the #14 fix: $concatArrays + string->array normalization)."""
    queries.add_number(contatti, "Simone", "Azzurri", "345678902")
    result = queries.add_number(contatti, "Simone", "Azzurri", "345678903")
    assert result["Numero_di_cellulare"] == [
        "345678901",
        "345678902",
        "345678903",
    ]


def test_regression_without_social_nested_exists(contatti):
    """$exists: false on the nested path must match BOTH documents whose
    Altri_contatti lacks Profilo_social (Marco Bianchi) AND documents
    without the Altri_contatti subdocument at all (Antonio Grigi)."""
    result = names(queries.without_social(contatti))
    assert len(result) == 8
    assert ("Marco", "Bianchi") in result  # subdocument without the field
    assert ("Antonio", "Grigi") in result  # no subdocument at all


def test_regression_unique_index_blocks_duplicates(contatti):
    with pytest.raises(DuplicateKeyError):
        contatti.insert_one({"Nome": "Marco", "Cognome": "Bianchi"})


def test_regression_add_number_unknown_contact_is_none(contatti):
    """No upsert on the append: a typo in the name must return None and
    must NOT create a partial phantom document."""
    assert queries.add_number(contatti, "Simone", "Azzuri", "999") is None
    assert contatti.count_documents({}) == 11

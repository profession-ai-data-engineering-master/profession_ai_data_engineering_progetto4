"""Rubrica contatti su MongoDB — soluzione del progetto.

Thin runner over the data module (db.py + queries.py): runs the 6 queries
and the 2 updates of the assignment against a standalone MongoDB (default:
the one started by ``docker compose up``).

Usage:
    python solution.py

The connection URI can be overridden via the ``MONGO_URI`` env var
(default ``mongodb://localhost:27017``).
"""

from pprint import pprint

import db
import queries


def header(title: str) -> None:
    print(f"\n=== {title} ===")


def main() -> None:
    client = db.get_client()
    contatti = db.get_collection(db.get_db(client))

    header("Setup")
    count = db.seed_collection(contatti)
    print(f"{count} contatti importati, indice univoco creato")

    header("Contatti della società WebCorp")
    pprint(queries.by_company(contatti, "WebCorp"))

    header("Contatti con più di un numero di telefono")
    pprint(queries.with_multiple_numbers(contatti))

    header('Numeri di telefono dei contatti con tag "lavoro"')
    pprint(queries.phones_by_tag(contatti, "lavoro"))

    header("Contatti senza profilo social")
    pprint(queries.without_social(contatti))

    header("Conteggio amici stretti / non amici stretti")
    pprint(queries.count_close_friends(contatti))

    header("Media chiamate ultimo mese degli amici stretti")
    pprint(queries.avg_calls_close_friends(contatti))

    header("Aggiunta del numero 345678902 a Simone Azzurri")
    pprint(queries.add_number(contatti, "Simone", "Azzurri", "345678902"))

    header("Inserimento del contatto Mary Salgado")
    pprint(
        queries.upsert_contact(
            contatti,
            "Mary",
            "Salgado",
            {
                "Numero_di_cellulare": "346679933",
                "Altri_contatti.Indirizzo": "Via 25 Aprile 3, Firenze",
            },
        )
    )

    client.close()


if __name__ == "__main__":
    main()

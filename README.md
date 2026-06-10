# Gestione di una rubrica di contatti con MongoDB

[![CI](https://github.com/profession-ai-data-engineering-master/profession_ai_data_engineering_progetto4/actions/workflows/ci.yml/badge.svg)](https://github.com/profession-ai-data-engineering-master/profession_ai_data_engineering_progetto4/actions/workflows/ci.yml)

Rubrica di contatti document-oriented su **MongoDB**: 6 query e 2 update su un dataset volutamente eterogeneo (campi opzionali, telefoni string|array), con ambiente Docker riproducibile, modulo dati tipizzato, test con oracoli espliciti e CI.

Progetto 4 del [Master in Data Engineering di ProfessionAI](https://github.com/profession-ai-data-engineering-master).

## Avvio rapido

Prerequisiti: Docker (Desktop su Windows/macOS) e Python 3.11+.

```shell
docker compose up -d
```

Un comando: avvia un **MongoDB 7 standalone** su `localhost:27017` e, quando il database è pronto (healthcheck), un servizio one-shot di **seed** che azzera la collection `contatti`, crea l'indice univoco `{Nome: 1, Cognome: 1}` (vincolo di integrità anti-duplicati, creato *prima* dell'import così un dataset con duplicati fallirebbe rumorosamente) e importa gli 11 contatti di [`data/contatti.json`](data/contatti.json). Il seed gira a ogni `up`: lo stato riparte sempre dal dataset originale.

Poi, per eseguire soluzione e test:

```shell
pip install -e ".[dev]"
python solution.py   # le 6 query + 2 update, risultati a video
pytest               # 13 test su un DB dedicato contatti_test
```

Per spegnere: `docker compose down`. La connessione è parametrizzata via env `MONGO_URI` (default `mongodb://localhost:27017`).

## Architettura

```
docker compose
├── mongo   (mongo:7 standalone, healthcheck)   ←  MONGO_URI
└── seed    (one-shot: drop → indice univoco → import dataset)
                                                     │
db.py        connessione + seed_collection() ────────┘
queries.py   le 6 query + 2 update come funzioni tipizzate
solution.py  runner: esegue tutto e stampa i risultati
tests/       fixture su DB contatti_test (riseminato a ogni test)
.github/     CI: ruff check + format + pytest su service container mongo:7
```

- **[`db.py`](db.py)** — connessione (`MONGO_URI` da env) e `seed_collection()`: stessa semantica del seed Docker, riusata dalle fixture dei test.
- **[`queries.py`](queries.py)** — le query della consegna come funzioni che ricevono la collection esplicitamente; la gestione del campo telefono string|array vive in un'unica normalizzazione `$isArray`/`$cond` condivisa da query e append.
- **[`solution.py`](solution.py)** — runner sottile del modulo: nessuna logica MongoDB fuori da `db.py`/`queries.py`.
- **[`tests/`](tests)** — 13 test con oracoli calcolati dal dataset e 3 regressioni mirate (append piatto, `$exists` annidato, `DuplicateKeyError` sul duplicato); ogni test risemina e droppa il proprio DB `contatti_test`, indipendente dal seed Docker.
- **[`.github/workflows/ci.yml`](.github/workflows/ci.yml)** — lint (`ruff check`, `ruff format --check`) e test su ogni push/PR, con MongoDB come service container.

## Esempi di output

Estratti di `python solution.py`:

```text
=== Contatti con più di un numero di telefono ===
[{'Cognome': 'Rossi', 'Nome': 'Laura'},
 {'Cognome': 'Marroni', 'Nome': 'Chiara'},
 {'Cognome': 'Moretti', 'Nome': 'Alessia'}]

=== Numeri di telefono dei contatti con tag "lavoro" ===
['348123456', '349654321', '347098765', '321654987']

=== Conteggio amici stretti / non amici stretti ===
{False: 6, True: 5}

=== Media chiamate ultimo mese degli amici stretti ===
16.4

=== Aggiunta del numero 345678902 a Simone Azzurri ===
{'Cognome': 'Azzurri',
 'Nome': 'Simone',
 'Numero_di_cellulare': ['345678901', '345678902'],
 ...}
```

L'append a Simone è il caso interessante: il campo parte come stringa e diventa una **lista piatta** — la normalizzazione string→array avviene nella stessa update pipeline (`$concatArrays` + `$isArray`/`$cond`), senza upsert (un refuso nel nome ritorna `None` invece di creare un documento fantasma).

## Scelte di modellazione

Il dataset è volutamente piccolo (11 documenti): il valore qui non è applicare tecniche di scala, ma dichiarare i compromessi di modellazione — incluso **quando una tecnica non serve**.

- **Chiave naturale `{Nome, Cognome}`** — è la chiave usata da indice univoco e upsert, e non è robusta: due omonimi sono un falso duplicato. In produzione si userebbe un id surrogato o il telefono normalizzato come chiave candidata; qui resta come vincolo dimostrativo, dichiaratamente imperfetto.
- **Indice univoco come vincolo, non come ottimizzazione** — su 11 documenti un indice non cambia nulla in termini di performance; `{Nome: 1, Cognome: 1}` esiste solo come **vincolo di integrità** (anti-duplicati, abilita l'upsert di Mary Salgado). Con dati reali si indicizzerebbero i campi di ricerca effettivi (`Società`, `Tag`).
- **`Numero_di_cellulare` string|array** — il dataset è eterogeneo: a volte stringa singola, a volte lista. La normalizzazione ad array avviene in un solo punto (il pattern `$isArray`/`$cond` condiviso tra query e append in `queries.py`), così non esistono modi diversi di gestire lo stesso caso. Un'alternativa più strutturale sarebbe un validatore `$jsonSchema` sulla collection, qui non implementato per non aggiungere cerimonia a un dataset dimostrativo.
- **`Amici_stretti` e i valori mancanti** — il conteggio raggruppa per valore senza assumere `False` per un eventuale campo assente: un documento senza il campo finirebbe in un gruppo `None`, lasciando **visibile l'assenza di informazione** invece di mascherarla con un default. In questo dataset il campo è sempre presente, quindi è una scelta di principio, non un comportamento osservato.
- **"Senza social" e `$exists: false` su path annidato** — il filtro `Altri_contatti.Profilo_social: {$exists: false}` intercetta sia chi ha `Altri_contatti` senza `Profilo_social`, sia chi non ha proprio il sottodocumento: entrambi i casi sono "senza social" per la consegna.
- **Embedding vs referencing** — `Altri_contatti` è embedded perché viene sempre letto insieme al contatto (località dei dati, nessun accesso indipendente). Il referencing avrebbe senso con entità condivise tra documenti (es. un'anagrafica società), che qui non esistono.

## Struttura del repository

```
├── docker-compose.yml      # mongo:7 + servizio seed (healthcheck, depends_on)
├── docker/seed.sh          # drop → indice univoco → mongoimport
├── data/contatti.json      # il dataset (11 contatti), versionato
├── db.py                   # connessione + seed_collection()
├── queries.py              # 6 query + 2 update, funzioni tipizzate
├── solution.py             # runner della soluzione
├── tests/                  # conftest (fixture contatti_test) + test_queries
├── pyproject.toml          # dipendenze pinnate, config ruff e pytest
└── .github/workflows/ci.yml
```

## La consegna

**DigitalConnect** è un'azienda che offre soluzioni digitali per la gestione di contatti e relazioni aziendali. I suoi servizi includono la creazione e gestione di rubriche personalizzate per aziende, facilitando l'organizzazione e l'analisi dei contatti in base a diverse caratteristiche e interazioni. Con una crescente necessità di strumenti di CRM avanzati, DigitalConnect ha identificato l'opportunità di sfruttare le potenzialità di MongoDB per la gestione dinamica dei contatti: una rubrica che memorizza ogni contatto come documento JSON, con informazioni disomogenee che spaziano dai dettagli personali alle interazioni lavorative.

Le richieste della consegna:

1. **Creazione del database e della collection**, con import dei contatti forniti in formato JSON.
2. **Interrogazione dei dati**:
   * trovare tutti i contatti associati alla società WebCorp;
   * identificare i contatti con più di un numero di telefono;
   * estrarre solo i numeri di telefono dei contatti con tag "lavoro";
   * riportare nome e cognome dei contatti senza propri social;
   * contare quanti contatti sono etichettati come "amici stretti" e quanti no;
   * calcolare il numero medio di chiamate effettuate nell'ultimo mese dai contatti "amici stretti".
3. **Aggiornamenti ai dati**:
   * aggiungere a Simone Azzurri il numero 345678902;
   * aggiungere un nuovo documento per Mary Salgado, con numero 346679933 e indirizzo Via 25 Aprile 3, Firenze.

Ogni contatto ha chiavi come Nome, Cognome, Numero di cellulare, Società, Data di compleanno, Tag, Altri contatti (sottodocumento con email, indirizzo, profilo social), Chiamate nell'ultimo mese, Amici stretti.

## Dataset

Il dataset originale è scaricabile da [S3](https://proai-datasets.s3.eu-west-3.amazonaws.com/contatti.json); una copia è versionata in [`data/contatti.json`](data/contatti.json), così l'ambiente locale funziona anche offline.

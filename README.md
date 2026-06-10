# Gestione di una rubrica di contatti con MongoDB

**DigitalConnect** è un'azienda che offre soluzioni digitali per la gestione di contatti e relazioni aziendali. I suoi servizi includono la creazione e gestione di rubriche personalizzate per aziende, facilitando l’organizzazione e l’analisi dei contatti in base a diverse caratteristiche e interazioni. Con una crescente necessità di strumenti di CRM avanzati, DigitalConnect ha identificato l’opportunità di sfruttare le potenzialità di MongoDB per la gestione dinamica dei contatti.

Molte aziende si trovano a dover gestire enormi database di contatti, con informazioni disomogenee che spaziano dai dettagli personali alle interazioni lavorative. Le soluzioni tradizionali spesso non sono in grado di gestire la complessità di dati non strutturati, specialmente quando le aziende desiderano un sistema flessibile che permetta ricerche e analisi avanzate.

DigitalConnect vuole offrire una soluzione dinamica, scalabile e facilmente interrogabile.

## Soluzione Proposta

DigitalConnect ha sviluppato una **rubrica di contatti gestita tramite MongoDB**, che consente alle aziende di organizzare, filtrare e analizzare i contatti in modo efficace. Il progetto prevede la creazione di un database MongoDB dedicato, con una collection che memorizza i contatti in formato JSON, rappresentando ogni contatto come un documento complesso. I dati contengono informazioni come nome, cognome, numero di telefono, email, indirizzo e tag di classificazione.

## Fasi del Processo

1. **Creazione del Database e della Collection**: Imposta un nuovo database MongoDB con una collection dove verranno importati i documenti rappresentativi dei contatti.

2. **Importazione dei Dati**: I contatti, forniti in formato JSON, vengono caricati nella collection. Un esempio di documento potrebbe essere:

   * Nome: Marco
   * Cognome: Bianchi
   * Numero di cellulare: 348123456
   * Società: WebCorp
   * Data di nascita: 22 marzo 1985
   * Tag: lavoro, tech
   * Altri contatti: email (lista), indirizzo (via Roma 10, Milano)
   * Numero di chiamate nell’ultimo mese: 8
   * Amici stretti: false

3. **Interrogazione dei Dati**: Si eseguono una serie di query per analizzare i dati, rispondendo a domande specifiche come:

   * Trovare tutti i contatti associati alla società WebCorp.
   * Identificare i contatti con più di un numero di telefono.
   * Estrarre solo i numeri di telefono dei contatti con tag “lavoro”.
   * Riportare nome e cognome dei contatti senza propri social.
   * Contare quanti contatti sono etichettati come “amici stretti” e quanti no.
   * Calcolare il numero medio di chiamate effettuate nell’ultimo mese dai contatti “amici stretti”.

4. **Aggiornamenti ai Dati**: Si aggiungono nuove informazioni al database:

   * Aggiungi a Simone Azzurri il numero 345678902
   * Aggiungi un nuovo documento contenente il contatto di Mary Salgado con numero 346679933 e indirizzo Via 25 Aprile 3, Firenze

## Struttura del Documento JSON

Ogni contatto viene memorizzato come un documento JSON con diverse chiavi:

* **Nome e Cognome**: Identificano il contatto.
* **Numero di telefono**: Utilizzato per contattare direttamente la persona.
* **Società**: Indica l’azienda di appartenenza.
* **Data di nascita**: Utile per filtri o auguri.
* **Tag**: Classificano il contatto (es. “lavoro”, “tech”).
* **Altri contatti**: Documenti embedded contenenti email e indirizzo.
* **Interazioni recenti**: Numero di chiamate effettuate nell’ultimo mese.
* **Amici stretti**: Booleano per indicare un rapporto più stretto.

## Vantaggi per l’Azienda

La rubrica basata su MongoDB offre numerosi vantaggi:

* **Flessibilità dei Dati**: MongoDB consente di memorizzare dati complessi e disomogenei grazie alla struttura document-based, ideale per contatti con informazioni variabili.
* **Scalabilità**: La soluzione può crescere con l’aumentare del numero di contatti, mantenendo performance elevate anche con dataset di grandi dimensioni.
* **Facilità di Ricerca**: Grazie alle capacità di query avanzate di MongoDB, è possibile eseguire ricerche rapide e specifiche su attributi come tag, numero di interazioni o relazioni personali.
* **Analisi Dati**: Le query permettono di ottenere insights preziosi sulle relazioni, come chi sono i contatti più attivi, i più stretti o quelli classificati in base a particolari settori.

## Valore Aggiunto

La soluzione di **DigitalConnect** consente alle aziende di avere un controllo totale sui loro contatti, offrendo una rubrica digitale che non solo organizza i dati ma permette di estrarre informazioni utili per il business. Grazie alla flessibilità di MongoDB, la soluzione è altamente personalizzabile e può essere adattata a diverse necessità, offrendo al tempo stesso potenza e semplicità nella gestione e analisi dei contatti.

## Dataset

Il dataset è scaricabile da qui: [https://proai-datasets.s3.eu-west-3.amazonaws.com/contatti.json](https://proai-datasets.s3.eu-west-3.amazonaws.com/contatti.json)

Una copia è versionata in [`data/contatti.json`](data/contatti.json): l'ambiente locale funziona anche offline.

## Ambiente locale (Docker)

Prerequisito: Docker (Desktop su Windows/macOS).

```shell
docker compose up -d
```

Avvia un **MongoDB 7 standalone** su `localhost:27017` e, quando il database è pronto (healthcheck), un servizio one-shot di **seed** che:

1. azzera la collection `contatti` del database `contatti`;
2. crea l'indice univoco `{ Nome: 1, Cognome: 1 }` (vincolo di integrità anti-duplicati);
3. importa gli 11 contatti di `data/contatti.json`.

Il seed gira a ogni `up`: lo stato riparte sempre dal dataset originale (comodo per rieseguire gli esercizi da zero). Per spegnere:

```shell
docker compose down
```

## Soluzione

La soluzione è lo script [`solution.py`](solution.py), runner del modulo dati ([`db.py`](db.py) + [`queries.py`](queries.py)): esegue le 6 query e i 2 update della consegna contro il MongoDB locale e ne stampa i risultati.

### Scelte di modellazione

Il dataset è volutamente piccolo (11 documenti): il valore qui non è applicare tecniche di scala, ma dichiarare i compromessi di modellazione — incluso **quando una tecnica non serve**.

- **Chiave naturale `{Nome, Cognome}`** — è la chiave usata da indice univoco e upsert, e non è robusta: due omonimi sono un falso duplicato. In produzione si userebbe un id surrogato o il telefono normalizzato come chiave candidata; qui resta come vincolo dimostrativo, dichiaratamente imperfetto.
- **Indice univoco come vincolo, non come ottimizzazione** — su 11 documenti un indice non cambia nulla in termini di performance; `{Nome: 1, Cognome: 1}` esiste solo come **vincolo di integrità** (anti-duplicati, abilita l'upsert di Mary Salgado). Con dati reali si indicizzerebbero i campi di ricerca effettivi (`Società`, `Tag`).
- **`Numero_di_cellulare` string|array** — il dataset è eterogeneo: a volte stringa singola, a volte lista. La normalizzazione ad array avviene in un solo punto (il pattern `$isArray`/`$cond` condiviso tra query e append in `queries.py`), così non esistono modi diversi di gestire lo stesso caso. Un'alternativa più strutturale sarebbe un validatore `$jsonSchema` sulla collection, qui non implementato per non aggiungere cerimonia a un dataset dimostrativo.
- **`Amici_stretti` e i valori mancanti** — il conteggio raggruppa per valore senza assumere `False` per un eventuale campo assente: un documento senza il campo finirebbe in un gruppo `None`, lasciando **visibile l'assenza di informazione** invece di mascherarla con un default. In questo dataset il campo è sempre presente, quindi è una scelta di principio, non un comportamento osservato.
- **"Senza social" e `$exists: false` su path annidato** — il filtro `Altri_contatti.Profilo_social: {$exists: false}` intercetta sia chi ha `Altri_contatti` senza `Profilo_social`, sia chi non ha proprio il sottodocumento: entrambi i casi sono "senza social" per la consegna.
- **Embedding vs referencing** — `Altri_contatti` è embedded perché viene sempre letto insieme al contatto (località dei dati, nessun accesso indipendente). Il referencing avrebbe senso con entità condivise tra documenti (es. un'anagrafica società), che qui non esistono.

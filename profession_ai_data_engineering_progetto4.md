## Creazione Indice Univoco per Nome e Cognome

Come da specifiche creo un indice univolo per garantire l'integrità dei dati

```python
contatti.create_index(
    { "Nome": 1, "Cognome": 1 },
    unique = True
)
```

```shell
db['contatti'].createIndex(
    { Nome: 1, Cognome: 1 },
    { unique: true }
)
```

## Trovare tutti i contatti associati alla società WebCorp.

Ho utilizzato semplicemente un find:

```python
list(contatti.find({'Società': 'WebCorp'}))
```

```shell
db['contatti'].find({ "Società": "WebCorp" })
```

## Identificare i contatti con più di un numero di telefono.

Uso \$cond come un case..when in sql per distinguere Array dalle stringe per non ottenere errore:

```python
list(contatti.find(
    {
        "$expr": {
            "$gt": [
                { "$cond": [
                    { "$isArray": "$Numero_di_cellulare" },
                    { "$size": "$Numero_di_cellulare" },
                    0
                ]},
                1
            ]
        }
    },
    {
        "_id": 0,
        "Nome": 1,
        "Cognome": 1,
    }
))
```

```shell
db['contatti'].find(
    {
        $expr: {
            $gt: [
                { $cond: [
                    { $isArray: "$Numero_di_cellulare" },
                    { $size: "$Numero_di_cellulare" },
                    0
                ]},
                1
            ]
        }
    },
    {
        _id: 0,
        Nome: 1,
        Cognome: 1
    }
)
```

## Estrarre solo i numeri di telefono dei contatti con tag “lavoro”.

Utilizzo Aggregate invece di find perchè consente anche di strasformare i dati attraverso degli stage invece di filtrarli e proiettarli solamente. Nel caso specifico l'ho usato per appiattire i numeri di telefono nel caso ve ne sia più d'uno in una lista interna al documento.

```python
list(contatti.aggregate([
    { "$match": { "Tag": { "$in": ["lavoro"] } } },
    { "$project": { "_id": 0, "Numero_di_cellulare": 1 } },
    { "$unwind": "$Numero_di_cellulare" }
]))
```

```shell
db['contatti'].aggregate([
    { $match: { Tag: { $in: ["lavoro"] } } },
    { $project: { _id: 0, Numero_di_cellulare: 1 } },
    { $unwind: "$Numero_di_cellulare" }
])
```

## Riportare nome e cognome dei contatti senza propri social.

Filtro per esistenza del campo profilo social e poi proietto nome e cognome.

```python
list(contatti.find({"Altri_contatti.Profilo_social": {"$exists": False}}, {"_id": 0, "Nome": 1, "Cognome": 1}))
```

```shell
db['contatti'].find(
    { "Altri_contatti.Profilo_social": { $exists: false } },
    { _id: 0, Nome: 1, Cognome: 1 }
)
```

## Contare quanti contatti sono etichettati come “amici stretti” e quanti no.

Per farlo utilizzo aggregate. Inizialmente proietto solo il campo amici stretti. Successivamente gruppo per tale campo ed effettuo il count per valore. Infine effettuo il sort. Non filtro o verifico la presenza del campo per intercettare eventuali mancanze di valore da riportare come None. Inizialmente avevo pensato di considerarli falsi ma dopo averci riflettuto l'assenza di informazione è più appropriata.

```python
list(contatti.aggregate([
    { "$project": { "Amici_stretti": 1 } },
    { "$group": {
            "_id": "$Amici_stretti",
            "Conteggio": { "$sum": 1 }
            }
        },
    { "$sort": { "_id": -1 } }
]))
```

```shell
db['contatti'].aggregate([
    { $project: { Amici_stretti: 1 } },
    { $group: {
            _id: "$Amici_stretti",
            Conteggio: { $sum: 1 }
        }
    },
    { $sort: { _id: -1 } }
])
```

### Calcolare il numero medio di chiamate effettuate nell’ultimo mese dai contatti “amici stretti”.

Uso sempre la funzione aggregate. Nella trasformazione filtro prima i contatti con amici stretti a True
e successivamente ne calcolo la media.

```python
list(contatti.aggregate([
    {"$match":{"Amici_stretti": True}},
    {"$group":{
        "_id":1,
        "Media_chiamate_amici_stretti": { "$avg": "$Chiamate_ultimo_mese" }
            }
        },
    ]))
```

```shell
db['contatti'].aggregate([
    { $match : { Amici_stretti: true} },
    { $group: {
            _id: 1,
            Media_chiamate_amici_stretti: { $avg: "$Chiamate_ultimo_mese" }
        }
    },
])
```

## Aggiungi a Simone Azzurri il numero 345678902

Per il caso specifico utilizzo un file and update, utilizzando il campo del documento presente e unendolo al nuovo numero in una lista per mantenere una struttura omologa ad altri documenti con più numeri di telefono.

```python
contatti.find_one_and_update(
    filter={
        "Nome": "Simone",
        "Cognome": "Azzurri"
    },
    update=[ {
        "$set": {
            "Numero_di_cellulare":
            ["$Numero_di_cellulare", "345678902"],
        }
    } ],
    upsert=True,
    return_document=ReturnDocument.AFTER
)
```

```shell
db['contatti'].findOneAndUpdate(
    { Nome: "Simone", Cognome: "Azzurri" },
    [ { $set: { Numero_di_cellulare: [ "$Numero_di_cellulare", "345678902" ] } } ],
    { upsert: true, returnNewDocument: true }
)
```

## Aggiungi un nuovo documento contenente il contatto di Mary Salgado con numero 346679933 e indirizzo Via 25 Aprile 3, Firenze

Per svolgere questo esercizio utilizzo un upsert invece di una semplice insert per assicurarmi di non avere duplicazioni accidentali. Per il filtro mi baso sui campi che compongono l'indice univoco da me creato.

```python
contatti.find_one_and_update(
    filter={
        "Nome": "Mary",
        "Cognome": "Salgado"
    },
    update={
        "$set": {
            "Numero_di_cellulare": "346679933",
            "Altri_contatti.Indirizzo": "Via 25 Aprile 3, Firenze"
        }
    },
    upsert=True,
    return_document=ReturnDocument.AFTER
)
```

```shell
db['contatti'].findOneAndUpdate(
    { Nome: "Mary", Cognome: "Salgado" },
    { $set: { Numero_di_cellulare: "346679933", "Altri_contatti.Indirizzo": "Via 25 Aprile 3, Firenze" } },
    { upsert: true, returnNewDocument: true }
)
```

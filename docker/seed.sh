#!/usr/bin/env bash
# Seed of the "contatti" collection: reset, unique index, then import.
# The unique index is created BEFORE the import so it acts as an integrity
# gate: a dataset containing duplicate {Nome, Cognome} pairs fails loudly.
set -euo pipefail

HOST="${MONGO_HOST:-mongo}"
DB="contatti"
COLLECTION="contatti"
DATASET="/seed/contatti.json"

mongosh --quiet --host "$HOST" "$DB" --eval "
  db.getCollection('$COLLECTION').drop();
  db.getCollection('$COLLECTION').createIndex({ Nome: 1, Cognome: 1 }, { unique: true });
"

mongoimport --host "$HOST" --db "$DB" --collection "$COLLECTION" \
  --jsonArray --file "$DATASET"

COUNT=$(mongosh --quiet --host "$HOST" "$DB" \
  --eval "db.getCollection('$COLLECTION').countDocuments()")
echo "Seed completed: $COUNT documents in $DB.$COLLECTION"

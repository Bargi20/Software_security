import json
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# Percorso assoluto o relativo del file .env
ENV_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env")

# Carica le variabili dal file .env specificato
load_dotenv(dotenv_path=ENV_PATH)

# Lettura della variabile d'ambiente dal file .env
DB_URL = os.getenv("SUPABASE_DB_URL")
if not DB_URL:
    raise ValueError(f"La variabile d'ambiente SUPABASE_DB_URL non è impostata nel file {ENV_PATH}")

OUTPUT_JSON = "prob_table.json"

def parse_bool(v):
    if v is None:
        return -1
    return 1 if v == 1 or v is True or str(v).lower() == "true" else 0

# Connessione a Supabase/PostgreSQL
conn = psycopg2.connect(DB_URL, cursor_factory=RealDictCursor)
cursor = conn.cursor()

cursor.execute("""
    SELECT
        id,
        "nomeProva",
        prob1,
        prob2,
        prob3,
        probabilita_condizionata,
        "idEvento1_id",
        "idEvento2_id",
        "idEvento3_id"
    FROM "Ledger_Logistic_probabilita_condizionate"
    ORDER BY id
""")

rows = []
for r in cursor.fetchall():
    rows.append({
        "id": r["id"],
        "nomeProva": r["nomeProva"].strip(),
        "prob": [
            parse_bool(r["prob1"]),
            parse_bool(r["prob2"]),
            parse_bool(r["prob3"])
        ],
        "p_cond": int(float(r["probabilita_condizionata"]) * 100),
        "eventi": [
            r["idEvento1_id"],
            r["idEvento2_id"],
            r["idEvento3_id"]
        ]
    })

out = {
    "scale": 100,
    "rows": rows
}

with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
    json.dump(out, f, indent=2, ensure_ascii=False)

cursor.close()
conn.close()

print(f"[OK] JSON creato da DB: {OUTPUT_JSON}")

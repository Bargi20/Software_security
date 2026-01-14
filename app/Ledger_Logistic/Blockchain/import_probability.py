import os
import json
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# -------------------------
# CONFIGURAZIONE
# -------------------------
ENV_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env")
load_dotenv(dotenv_path=ENV_PATH)

DB_URL = os.getenv("SUPABASE_DB_URL")
if not DB_URL:
    raise ValueError(f"La variabile d'ambiente SUPABASE_DB_URL non è impostata nel file {ENV_PATH}")

OUTPUT_JSON = "prob_table.json"

# -------------------------
# FUNZIONI
# -------------------------
def bool_to_str(v):
    """Converte i valori booleani in True/False o None vuoto"""
    if v is None or str(v).strip() == "" or v == -1:
        return None
    return True if str(v).lower() in ["1", "true", "t", "yes"] else False

# -------------------------
# ESECUZIONE
# -------------------------
def main():
    try:
        # Connessione al DB
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

        # Parsing righe in formato JSON come CSV
        data = []
        for r in cursor.fetchall():
            data.append({
                "id": r["id"],
                "nomeProva": r["nomeProva"].strip() if r["nomeProva"] else "",
                "prob1": bool_to_str(r["prob1"]),
                "prob2": bool_to_str(r["prob2"]),
                "prob3": bool_to_str(r["prob3"]),
                "probabilita_condizionata": r["probabilita_condizionata"].strip() if r["probabilita_condizionata"] else "",
                "idEvento1_id": r["idEvento1_id"],
                "idEvento2_id": r["idEvento2_id"],
                "idEvento3_id": r["idEvento3_id"]
            })

        # Salvataggio JSON
        with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print(f"[OK] JSON creato da DB e salvato in {OUTPUT_JSON}")
        print

    except Exception as e:
        print(f"[ERRORE] Connessione o query fallita: {e}")

    finally:
        if 'cursor' in locals() and cursor is not None:
            cursor.close()
        if 'conn' in locals() and conn is not None:
            conn.close()

if __name__ == "__main__":
    main()

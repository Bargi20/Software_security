import os
import json
import sys
import django

# -------------------------
# SETUP DJANGO
# -------------------------

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")) # Due livelli sopra rispetto alla posizione di questo file
#print(f"BASE_DIR impostato a: {BASE_DIR}")
sys.path.insert(0, BASE_DIR)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "software_security.settings")
django.setup()

from Ledger_Logistic.models import Probabilita_condizionate

OUTPUT_JSON = "prob_table.json"

# -------------------------
# ESECUZIONE
# -------------------------
def main():
    try:
        tabella = (
            Probabilita_condizionate.objects
            .order_by("id")
            .values(
                "id",
                "nomeProva",
                "evento1",
                "evento2",
                "evento3",
                "probabilita_condizionata",
                "idEvento1_id",
                "idEvento2_id",
                "idEvento3_id",
            )
        )
        # for p in tabella:
        #     print(p)
        

        data = []
        for r in tabella:
            record = {
                "id": r["id"],
                "nomeProva": r["nomeProva"].strip() if r["nomeProva"] else "",
                "evento1": r["evento1"].strip() if r["evento1"] else "",
                "evento2": r["evento2"].strip() if r["evento2"] else "",
                "evento3": r["evento3"].strip() if r["evento3"] else "",
                "probabilita_condizionata": r["probabilita_condizionata"],
                "idEvento1_id": r["idEvento1_id"],
                "idEvento2_id": r["idEvento2_id"],
                "idEvento3_id": r["idEvento3_id"],
            }
            data.append(record)

        with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print(f"[OK] JSON creato → {OUTPUT_JSON}")

    except Exception as e:
        print(f"[ERRORE] Export fallito: {e}")

if __name__ == "__main__":
    main()

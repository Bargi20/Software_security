import os
import sys
import django
import json

# -------------------------------------------------------------------
# Configurazione Django
# -------------------------------------------------------------------
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, BASE_DIR)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "software_security.settings")
django.setup()

from django.conf import settings
from web3.middleware import ExtraDataToPOAMiddleware
from besu import connect_to_besu, get_account
from import_probability import main as import_probability

# -------------------------------------------------------------------
# Funzioni Blockchain
# -------------------------------------------------------------------

def carica_contratto_ledger():
    """Carica ABI e indirizzo del contratto Oracolo dal deployment"""
    PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
    DEPLOY_PATH = os.path.join(PROJECT_ROOT, "ignition", "deployments", "chain-1338")

    abi_path = os.path.join(DEPLOY_PATH, "Oracolo_abi.json")
    address_path = os.path.join(DEPLOY_PATH, "Oracolo_address.json")

    if not os.path.exists(abi_path):
        raise FileNotFoundError(f"ABI non trovato: {abi_path}")
    if not os.path.exists(address_path):
        raise FileNotFoundError(f"Address non trovato: {address_path}")

    with open(abi_path, "r", encoding="utf-8") as f:
        contract_abi = json.load(f)
    with open(address_path, "r", encoding="utf-8") as f:
        contract_address = json.load(f)["Oracolo"]

    return contract_abi, contract_address


def invia_tabella_json_su_besu(file_path):
    """Invia l'intera tabella dei record JSON in un'unica transazione"""

    # Leggi JSON
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            records = json.load(f)
    except Exception as e:
        raise ValueError(f"Errore nel caricare il file JSON: {e}")

    if not records:
        raise Exception("Il file JSON è vuoto.")

    # Connessione a Besu
    web3 = connect_to_besu()
    web3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)

    private_key = settings.BESU_PRIVATE_KEYS[0]
    account = get_account(private_key)

    contract_abi, contract_address = carica_contratto_ledger()
    contract = web3.eth.contract(address=contract_address, abi=contract_abi)

    # genera il payload della tabella da mandare come transazione
    tabella = []
    for r in records:
        prob1Exists = r.get("prob1") is not None
        prob2Exists = r.get("prob2") is not None
        prob3Exists = r.get("prob3") is not None
        tabella.append([
            int(r["id"]),
            r["nomeProva"],
            bool(r["prob1"]) if prob1Exists else False,
            bool(prob1Exists),
            bool(r["prob2"]) if prob2Exists else False,
            bool(prob2Exists),
            bool(r["prob3"]) if prob3Exists else False,
            bool(prob3Exists),
            r["probabilita_condizionata"],
            int(r["idEvento1_id"]),
            int(r["idEvento2_id"]),
            int(r["idEvento3_id"])
        ])

    tx_function = contract.functions.addRecords(tabella)
    nonce = web3.eth.get_transaction_count(account.address, block_identifier='latest')
    tx = tx_function.build_transaction({
        'from': account.address,
        'nonce': nonce,
        'gas': 8000000,       
        'gasPrice': 20 * 10**9
    })

    signed_txn = web3.eth.account.sign_transaction(tx, private_key)
    try:
        tx_hash = web3.eth.send_raw_transaction(signed_txn.raw_transaction)
        print(f"[OK] Tabella inviata in un'unica transazione: {tx_hash.hex()}")
        return tx_hash.hex()
    except Exception as e:
        raise Exception(f"Errore nell'invio della transazione: {e}")


def leggi_tabella_da_besu():
    """Legge tutti i record dal contratto Oracolo"""
    web3 = connect_to_besu()
    web3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)

    contract_abi, contract_address = carica_contratto_ledger()
    contract = web3.eth.contract(address=contract_address, abi=contract_abi)

    try:
        records = contract.functions.getRecords().call()
        return records
    except Exception as e:
        raise Exception(f"Errore nel leggere i record dal contratto: {e}")


# -------------------------------------------------------------------
# MAIN
# -------------------------------------------------------------------

if __name__ == "__main__":
    print("=== IMPORT PROBABILITÀ DAL DATABASE ===")
    try:
        import_probability()
        print("[OK] File JSON generato correttamente dal database")
    except Exception as e:
        print(f"[ERRORE] Import dal database fallito: {e}")
        exit(1)

    JSON_PATH = "prob_table.json"

    print("\n=== INVIO TABELLA SU BESU ===")
    try:
        tx_hash = invia_tabella_json_su_besu(JSON_PATH)
    except Exception as e:
        print(f"[ERRORE] Invio su Besu fallito: {e}")
        exit(1)

    print("\n=== VERIFICA TRANSAZIONE ===")
    web3 = connect_to_besu()
    receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
    if receipt.status == 1:
        print(f"[OK] Transazione confermata: {tx_hash}")
    else:
        print(f"[ERRORE] Transazione fallita: {tx_hash}")

    print("\n=== LETTURA TABELLA DAL CONTRATTO ===")
    records = leggi_tabella_da_besu()
    print(f"Record caricati: {len(records)}")
    for r in records:
        print(r)

import os
import sys
import django
import json

# -------------------------------------------------------------------
# Configurazione Django
# -------------------------------------------------------------------

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")) # Due livelli sopra rispetto alla posizione di questo file
#print(f"BASE_DIR impostato a: {BASE_DIR}")
sys.path.insert(0, BASE_DIR)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "software_security.settings")
django.setup() # Inizializza l'ambiente Django per prendere le variabili d'ambiente nel file settings.py

from django.conf import settings
from web3.middleware import ExtraDataToPOAMiddleware
from Ledger_Logistic.Blockchain.besu import connect_to_besu, get_account
from Ledger_Logistic.Blockchain.import_probability import main as import_probability

# -------------------------------------------------------------------
# Funzioni Blockchain
# -------------------------------------------------------------------

def load_contract():
    """Carica ABI e indirizzo del contratto Oracolo dal deployment"""
    PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
    DEPLOY_PATH = os.path.join(PROJECT_ROOT, "ignition", "deployments", "chain-1338")

    abi_path = os.path.join(DEPLOY_PATH, "Oracolo_abi.json")
    address_path = os.path.join(DEPLOY_PATH, "Oracolo_address.json")

    if not os.path.exists(abi_path):
        raise FileNotFoundError(f"ABI non trovato: {abi_path}")
    if not os.path.exists(address_path):
        raise FileNotFoundError(f"Address non trovato: {address_path}")

    # Carica ABI e indirizzo dai rispettivi JSON
    with open(abi_path, "r", encoding="utf-8") as f:
        contract_abi = json.load(f)
    with open(address_path, "r", encoding="utf-8") as f:
        contract_address = json.load(f)["Oracolo"]

    return contract_abi, contract_address


def invia_tabella(file_path):
    """Invia la tabella al contratto prendendo solo i due booleani presenti in ogni record."""

    # Leggi JSON
    with open(file_path, "r", encoding="utf-8") as f:
        records = json.load(f)

    if not records:
        raise Exception("Il file JSON è vuoto.")

    web3 = connect_to_besu()
    private_key = settings.BESU_PRIVATE_KEYS[0]
    account = get_account(private_key)

    contract_abi, contract_address = load_contract()
    contract = web3.eth.contract(address=contract_address, abi=contract_abi)

    tabella = []
    for r in records:
        
        tabella.append([
            int(r["id"]),
            r["nomeProva"],
            r["evento1"],
            r["evento2"],
            r["evento3"],
            int(r["probabilita_condizionata"]),
            int(r["idEvento1_id"]),
            int(r["idEvento2_id"]),
            int(r["idEvento3_id"])
        ])

    if not tabella:
        raise Exception("Nessun record valido da inviare.")

    # Invio al contratto
    tx_function = contract.functions.addRecords(tabella)
    tx = tx_function.build_transaction({
        'from': account.address,
        'nonce': web3.eth.get_transaction_count(account.address, block_identifier='latest'),
        'gas': 8000000,
        'gasPrice': 0
    })

    signed_txn = web3.eth.account.sign_transaction(tx, private_key)
    tx_hash = web3.eth.send_raw_transaction(signed_txn.raw_transaction)
    print(f"[OK] Tabella inviata: {tx_hash.hex()}")
    return tx_hash.hex()


def leggi_tabella_da_besu(tx_hash: str):
    web3 = connect_to_besu()
    #web3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)

    # Carica ABI e indirizzo del contratto
    contract_abi, contract_address = load_contract()
    contract = web3.eth.contract(address=contract_address, abi=contract_abi)

    try:
        # Ottieni il receipt della transazione
        # receipt = web3.eth.get_transaction_receipt(tx_hash)

        # Leggi i record esattamente al blocco della transazione
        # Se chiami contract.functions.getRecords().call() senza specificare il blocco, stai leggendo lo stato corrente del contratto.
        # Tra il momento in cui invii la tabella e il momento in cui leggi, qualcun altro potrebbe aver scritto nuovi record o modificato l’array.
        # In quel caso, i dati letti potrebbero non corrispondere a quelli appena inviati.
        # Specificando block_identifier=receipt.blockNumber, chiedi a Web3 di leggere i dati come erano subito dopo quel blocco, cioè dopo la tua transazione. Questo ti garantisce coerenza.
        records = contract.functions.getRecords().call()
        return records
    except Exception as e:
        raise Exception(f"Errore nel leggere i record dal contratto dalla tx {tx_hash}: {e}")

def getA_ij(gps: str, strProva: str, prob1: str, prob2: str, prob3: str):
    web34 = connect_to_besu()
    # Carica ABI e indirizzo del contratto
    contract_abi, contract_address = load_contract()
    contract = web34.eth.contract(address=contract_address, abi=contract_abi)

    try:
        # Ottieni il receipt della transazione
        # receipt2 = web34.eth.get_transaction_receipt(tx_hash)

        # Leggi i record esattamente al blocco della transazione
        # Se chiami contract.functions.getRecords().call() senza specificare il blocco, stai leggendo lo stato corrente del contratto.
        # Tra il momento in cui invii la tabella e il momento in cui leggi, qualcun altro potrebbe aver scritto nuovi record o modificato l’array.
        # In quel caso, i dati letti potrebbero non corrispondere a quelli appena inviati.
        # Specificando block_identifier=receipt.blockNumber, chiedi a Web3 di leggere i dati come erano subito dopo quel blocco, cioè dopo la tua transazione. Questo ti garantisce coerenza.
        record2 = contract.functions.getA_ij(gps, strProva, prob1, prob2, prob3).call()
        return record2
    except Exception as e:
        raise Exception(f"Errore nel leggere i record dal contratto dalla tx {tx_hash}: {e}")


# -------------------------------------------------------------------
# MAIN
# -------------------------------------------------------------------

def main():
    
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
        tx_hash = invia_tabella(JSON_PATH)
    except Exception as e:
        print(f"[ERRORE] Invio su Besu fallito: {e}")
        exit(1)

    #print("\n=== VERIFICA TRANSAZIONE ===")
    web3 = connect_to_besu()
    receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
    if receipt.status == 1:
        print(f"[OK] Transazione confermata: {tx_hash}")
    else:
        print(f"[ERRORE] Transazione fallita: {tx_hash}")

    print("\n=== LETTURA TABELLA DAL CONTRATTO (al blocco della transazione) ===")
    records = leggi_tabella_da_besu(tx_hash)
    
    
    # print("\n=== record c_ij ===")
    # record = getA_ij("Fattura emessa", "false", "", "true", "")
    for p in records:
        print(p)

#   questa è la funzione che viene chiamata quando il gestore vuole verificare un reclamo. Qui si prende la spedizione associata al reclamo e si calcola la probabilità dell'evento del reclamo
def calcola_probabilita(id_reclamo):
    from Ledger_Logistic.models import Spedizione, Reclamo, Evento
    from django.forms.models import model_to_dict
    
    reclamo = Reclamo.objects.get(id=id_reclamo)
    spedizione = model_to_dict(Spedizione.objects.get(id=id_reclamo))
    # Si prendono tutte le prove della spedizione (in stringhe lowercase)
    prove = [str(spedizione[prova]).lower() for prova in ['traffico', 'veicolo_disponibile', 'meteo_sfavorevole', 'conferma_del_gestore_di_pagamento', 'fattura_emessa', 'gps', 'conferma_cliente', 'disponibilita_corriere']]

    evento1 = model_to_dict(Evento.objects.get(id=reclamo.evento1_id))
    
    if reclamo.evento2_id:
        evento2 = model_to_dict(Evento.objects.get(id=reclamo.evento2_id))
        return evento1, evento2, prove
    else :
        return evento1, prove

if __name__ == "__main__":
    main()
        
    
    
    

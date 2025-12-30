import hashlib
import json
import os
from web3.middleware import ExtraDataToPOAMiddleware
from django.conf import settings
from .BesuConnection import connect_to_besu


def carica_contratto_dal_json():
    # Definisci il percorso del file JSON ABI e Address
    project_root = os.path.dirname(os.path.abspath(__file__))  # Percorso del file corrente (in questo caso, dentro 'blockchain')

    # Definisci il percorso del file JSON ABI e Address
    abi_path = os.path.join(project_root, "../../../ignition/deployments/chain-1338/Spedizione_abi.json")
    address_path = os.path.join(project_root, "../../../ignition/deployments/chain-1338/Spedizione_address.json")

    # Carica l'ABI
    with open(abi_path, 'r') as abi_file:
        contract_abi = json.load(abi_file)

    # Carica l'indirizzo
    with open(address_path, 'r') as address_file:
        contract_address = json.load(address_file)["Spedizione"]

    return contract_abi, contract_address


def invia_spedizione_su_besu(file_path):
    # Leggi il file JSON contenente tutte le spedizioni
    try:
        with open(file_path, "r") as f:
            spedizioni = json.load(f)
    except Exception as e:
        raise ValueError(f"Errore nel caricare il file JSON: {str(e)}")

    # Se non ci sono spedizioni, solleva un errore
    if not spedizioni:
        raise Exception("Non ci sono spedizioni nel file JSON.")

    # Prendi l'ultima spedizione
    ultima_spedizione = spedizioni[-1]

    # Estrai i dati dall'ultima spedizione
    descrizione = ultima_spedizione.get("descrizione")
    indirizzo_consegna = ultima_spedizione.get("indirizzo_consegna")
    citta = ultima_spedizione.get("citta")
    cap = ultima_spedizione.get("cap")
    provincia = ultima_spedizione.get("provincia")
    grandezza = ultima_spedizione.get("grandezza")

    # Calcola un ID unico (UUID)
    hash_input = (descrizione + indirizzo_consegna + citta + cap + provincia + grandezza).encode('utf-8')
    id_spedizione = hashlib.sha256(hash_input).hexdigest()  # Usa SHA-256 per generare un ID unico  

    # Carica l'ABI e l'indirizzo del contratto
    contract_abi, contract_address = carica_contratto_dal_json()

    # Connetti a Besu
    web3 = connect_to_besu()

    # Aggiungi il middleware PoA
    web3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)

    # Ottieni l'account usando la chiave privata
    private_key = settings.BESU_PRIVATE_KEYS[0]  # Usa la prima chiave privata nella lista
    account = web3.eth.account.from_key(private_key)

    # Ottieni il contratto
    contract = web3.eth.contract(address=contract_address, abi=contract_abi)

    # Converte l'ID della spedizione in bytes
    id_spedizione_bytes = bytes.fromhex(id_spedizione.replace("0x", "")) 

    # Ottieni il nonce per l'account
    try:
        nonce = web3.eth.get_transaction_count(account.address, block_identifier='latest')
    except Exception as e:
        raise Exception(f"Errore nel recupero del nonce: {str(e)}")

    # Crea il 'data' della transazione manualmente (usando la funzione del contratto)
    function = contract.functions.creaSpedizione(
        id_spedizione_bytes,
        descrizione,
        indirizzo_consegna,
        citta,
        cap,
        provincia,
        grandezza
    )

    data = function._encode_transaction_data()  # Ottieni i dati della transazione codificati

    # Definisci i parametri per la transazione
    transaction = {
        'from': account.address,
        'to': contract_address,
        'data': data,
        'gas': 2000000,
        'gasPrice': 20 * 10**9,  # 20 Gwei in Wei
        'nonce': nonce,
    }

    # Firma la transazione usando web3.eth.account
    signed_txn = web3.eth.account.sign_transaction(transaction, private_key)

    # Invia la transazione
    try:
        tx_hash = web3.eth.send_raw_transaction(signed_txn.raw_transaction)
        return tx_hash
    except Exception as e:
        raise Exception(f"Errore durante l'invio della transazione: {str(e)}")

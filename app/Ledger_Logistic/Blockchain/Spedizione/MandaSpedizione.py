import hashlib
import json
import os
from web3.middleware import ExtraDataToPOAMiddleware
from django.conf import settings
from ..BesuConnection import connect_to_besu, get_account


def carica_contratto_dal_json():
    # Definisci il percorso del file JSON ABI e Address
    base_path = "../ignition/deployments/chain-1338"
    
    # Costruisci i percorsi completi per i file ABI e Address
    abi_path = os.path.join(base_path, "Spedizione_abi.json")
    address_path = os.path.join(base_path, "Spedizione_address.json")


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
    metodo_pagamento = ultima_spedizione.get("metodo_pagamento")

    # Calcola un ID unico per la spedizione
    hash_input = (descrizione + indirizzo_consegna + citta + cap + provincia + grandezza + metodo_pagamento).encode('utf-8')
    id_spedizione = hashlib.sha256(hash_input).hexdigest()  # Usa SHA-256 per generare un ID unico
    
    #print(f"id_spedizione: {id_spedizione}")  

    # Carica l'ABI e l'indirizzo del contratto
    contract_abi, contract_address = carica_contratto_dal_json()

    #print(f"contract_address: {contract_address}")
    web3 = connect_to_besu()

    # Aggiungi il middleware PoA (fonte: stackoverflow)
    web3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)

    # Ottieni l'account usando la chiave privata
    private_key = settings.BESU_PRIVATE_KEYS[0]  # Usa la prima chiave privata nella lista
    account = get_account(private_key) #funzione in BesuConnection.py che prende la prima chiave privata e ritorna l'account

    # Ottieni il contratto
    contract = web3.eth.contract(address=contract_address, abi=contract_abi)

    # Converte l'ID della spedizione in bytes
    id_spedizione_bytes = bytes.fromhex(id_spedizione.replace("0x", "")) 
    
    #print(f"id_spedizione_bytes: {id_spedizione_bytes}")


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

    # Ottieni i dati della transazione codificati
    data = function._encode_transaction_data()  

    # Definisci i parametri per la transazione
    transaction = {
        'from': account.address,
        'to': contract_address,
        'data': data,
        'gas': 2000000,
        'gasPrice': 20 * 10**9,  # 20 Gwei in Wei
        'nonce': web3.eth.get_transaction_count(account.address, block_identifier='latest'),
    }

    # Firma la transazione usando la chiave privata
    signed_txn = web3.eth.account.sign_transaction(transaction, private_key)

    # Invia la transazione
    try:
        tx_hash = web3.eth.send_raw_transaction(signed_txn.raw_transaction)
        return tx_hash
    except Exception as e:
        raise Exception(f"Errore durante l'invio della transazione: {str(e)}")

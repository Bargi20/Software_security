import json
import os
import time
import requests
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
    # Leggi il file JSON contenente la spedizione
    try:
        with open(file_path, "r") as f:
            spedizione = json.load(f)
    except Exception as e:
        raise ValueError(f"Errore nel caricare il file JSON: {str(e)}")

    # Se non c'è nessuna spedizione, errore
    if not spedizione:
        raise Exception("Non c'è nessuna spedizione nel file JSON.")

    # Accedi alla spedizione nel file
    
    spedizione = spedizione[-1] 
    
    # Estrai i dati dall'ultima spedizione
    id_spedizione = spedizione["id_spedizione"]
    descrizione = spedizione["descrizione"]
    indirizzo_consegna = spedizione["indirizzo_consegna"]
    citta = spedizione["citta"]
    cap = spedizione["cap"]
    provincia = spedizione["provincia"]
    grandezza = spedizione["grandezza"]
    metodo_pagamento = spedizione["metodo_pagamento"]
    
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


    # Crea il 'data' della transazione manualmente (usando la funzione del contratto)
    function = contract.functions.creaSpedizione(
        id_spedizione,
        descrizione,
        indirizzo_consegna,
        citta,
        cap,
        provincia,
        grandezza,
        metodo_pagamento
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
        # print(f"Transazione inviata con hash:\n {tx_hash.hex()}\n")
        # print(f"Dettagli della transazione:")
        # {transaction_details(tx_hash.hex())}
        # print(f"\nDati della transazione:\n {shipping_data(tx_hash.hex())}\n")
        return tx_hash
    except Exception as e:
        raise Exception(f"Errore durante l'invio della transazione: {str(e)}")

def transaction_details(tx_hash):
    # Prepara la richiesta JSON-RPC
    data = {
        "jsonrpc": "2.0",
        "method": "eth_getTransactionReceipt",
        "params": [tx_hash],
        "id": 1
    }

    while True:
        try:
            # Esegui la richiesta POST al nodo Besu
            response = requests.post(os.getenv('BESU_RPC_URL'), json=data, headers={"Content-Type": "application/json"})

            # Verifica che la risposta sia valida
            if response.status_code == 200:
                receipt = response.json()

                # Verifica che la risposta contenga il campo "result" con dati validi
                result = receipt.get('result')
                if result and result.get('blockHash') and result.get('blockNumber'):
                    print(f"Block Hash: {result.get('blockHash')}")
                    print(f"Block Number: {int(result.get('blockNumber', '0x0'), 16)}")
                    print(f"Status: {result.get('status')}")
                    print(f"From: {result.get('from')}")
                    print(f"To: {result.get('to')}")
                    print(f"Gas Used: {int(result.get('gasUsed', '0x0'), 16)}")
                    print(f"Effective Gas Price: {int(result.get('effectiveGasPrice', '0x0'), 16)}")
                    break  # Esci dal ciclo se la transazione è valida
            else:
                print(f"\nErrore nella richiesta: {response.status_code} - {response.text}")

            # Aspetta 5 secondi prima di fare un nuovo tentativo
            time.sleep(5)

        except requests.exceptions.RequestException as e:
            print(f"\nErrore durante la richiesta: {e}")
            break  # Se c'è un errore, fermati



# Funzione per leggere i dati della transazione
def shipping_data(tx_hash):
    web3 = connect_to_besu()  # Connessione al nodo Besu

    try:
        # Recupera i dettagli della transazione tramite l'hash
        tx_details = web3.eth.get_transaction(tx_hash)

        if not tx_details:
            raise ValueError("Transazione non trovata")

        # Estrai i dati della transazione
        data = tx_details['input']  # Dati della transazione

        # Carica ABI e contratto
        contract_abi, contract_address = carica_contratto_dal_json()

        # Se i dati non sono vuoti (significa che è una transazione a contratto)
        if data != "0x":
            # Inizializza il contratto con l'ABI e l'indirizzo
            contract = web3.eth.contract(address=contract_address, abi=contract_abi)
            
            # Decodifica i dati della transazione con la funzione appropriata
            decoded_data = contract.decode_function_input(data)  # Qui usiamo decode_function_input correttamente

            return {'data': decoded_data}
        else:
            # Se non c'è `data`, è una transazione ETH semplice
            return {'data': None}

    except Exception as e:
        raise Exception(f"Errore nel recuperare o decodificare la transazione: {str(e)}")
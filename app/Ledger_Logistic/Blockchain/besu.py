import os
import time
import requests
from web3 import Web3
from django.conf import settings

# Funzione per connettersi al nodo Besu
def connect_to_besu():
    besu_url = settings.BESU_RPC_URL  # Leggi dal settings
    web3 = Web3(Web3.HTTPProvider(besu_url))
    
    return web3

# Funzione per ottenere il primo account disponibile dalla lista di chiavi private
def get_account(private_key):
    web3 = connect_to_besu() 
    account = web3.eth.account.from_key(private_key)  # Usa la chiave privata passata
    return account


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

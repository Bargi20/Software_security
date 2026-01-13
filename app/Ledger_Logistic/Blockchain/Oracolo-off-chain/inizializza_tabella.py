import csv
import json
import os
from web3 import Web3
from django.conf import settings
from ..besu import connect_to_besu, get_account, carica_contratto_dal_json

private_key = settings.BESU_PRIVATE_KEYS[0]  # Usa la prima chiave privata nella lista
account = get_account(private_key)

# Connessione al nodo
w3 = connect_to_besu()

contract_abi, contract_address = carica_contratto_dal_json()
contract = Web3.eth.contract(address=contract_address, abi=contract_abi)

# --- LETTURA CSV ---
eventA_list = []
eventB_list = []
probabilities_list = []

with open('/mnt/data/75b37484-2931-493e-b153-c3ef4c3cbb4f.csv', newline='') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        # Adatta i nomi delle colonne al tuo CSV
        eventA_list.append(int(row['event_a']))
        eventB_list.append(int(row['event_b']))
        probabilities_list.append(int(float(row['probability']) * 10000))  # es. 0.75 -> 7500

# --- COSTRUZIONE TRANSAZIONE ---
nonce = w3.eth.get_transaction_count(account.address)
txn = contract.functions.initializeProbabilities(
    eventA_list,
    eventB_list,
    probabilities_list
).build_transaction({
    'from': account.address,
    'nonce': nonce,
    'gas': 500_000 + len(eventA_list) * 10_000,  # stima gas
    'gasPrice': w3.to_wei('50', 'gwei'),
})

signed_txn = w3.eth.account.sign_transaction(txn, private_key=PRIVATE_KEY)
tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
print(f'Transaction sent: {tx_hash.hex()}')

# opzionale: attendi conferma
receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
print(f'Transaction mined in block: {receipt.blockNumber}')

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
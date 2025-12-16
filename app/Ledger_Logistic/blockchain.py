from web3 import Web3
import json
import os
from pathlib import Path
from django.conf import settings

# Configurazione connessione blockchain
BLOCKCHAIN_URL = os.getenv('BLOCKCHAIN_URL', 'http://localhost:8545')
CONTRACT_ADDRESS = os.getenv('CONTRACT_ADDRESS')
ACCOUNT_ADDRESS = os.getenv('ACCOUNT_ADDRESS')
PRIVATE_KEY = os.getenv('PRIVATE_KEY')

# Inizializza Web3
w3 = Web3(Web3.HTTPProvider(BLOCKCHAIN_URL))

# Path all'ABI del contratto
BASE_DIR = Path(__file__).resolve().parent.parent.parent
CONTRACT_ABI_PATH = BASE_DIR / 'artifacts' / 'contracts' / 'ordine.sol' / 'ordine.json'

def load_contract_abi():
    """Carica l'ABI del contratto dal file JSON"""
    try:
        with open(CONTRACT_ABI_PATH, 'r') as f:
            contract_json = json.load(f)
            return contract_json['abi']
    except FileNotFoundError:
        raise Exception(f"File ABI non trovato: {CONTRACT_ABI_PATH}")

def get_contract():
    """Ritorna l'istanza del contratto"""
    if not CONTRACT_ADDRESS:
        raise Exception("CONTRACT_ADDRESS non configurato nel file .env")
    
    abi = load_contract_abi()
    checksum_address = w3.to_checksum_address(CONTRACT_ADDRESS)
    return w3.eth.contract(address=checksum_address, abi=abi)

def is_connected():
    """Verifica se la connessione blockchain è attiva"""
    return w3.is_connected()

def send_transaction(contract_function, *args):
    """
    Invia una transazione al contratto smart contract
    
    Args:
        contract_function: La funzione del contratto da chiamare
        *args: Argomenti da passare alla funzione
    
    Returns:
        tuple: (success: bool, _ : str or None, error: str or None)
    """
    if not ACCOUNT_ADDRESS or not PRIVATE_KEY:
        return False, None, "ACCOUNT_ADDRESS o PRIVATE_KEY non configurati"
    
    try:
        # Costruisci la transazione
        tx = contract_function(*args).build_transaction({
            'from': ACCOUNT_ADDRESS,
            'nonce': w3.eth.get_transaction_count(ACCOUNT_ADDRESS),
            'gas': 2000000,
            'gasPrice': w3.eth.gas_price
        })
        
        # Firma la transazione
        signed_tx = w3.eth.account.sign_transaction(tx, PRIVATE_KEY)
        
        # Invia la transazione
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        
        # Attendi la conferma
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        
        if receipt['status'] == 1:
            return True, tx_hash.hex(), None
        else:
            return False, None, "Transazione fallita"
            
    except Exception as e:
        return False, None, str(e)
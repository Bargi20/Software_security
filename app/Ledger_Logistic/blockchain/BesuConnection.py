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

import os
import sys
import django

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, BASE_DIR)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "software_security.settings")
django.setup()

from Ledger_Logistic.models import Spedizione, Reclamo, Evento
from django.forms.models import model_to_dict
from Ledger_Logistic.Blockchain.besu import connect_to_besu, load_contract

# Questa è la funzione che viene chiamata quando il gestore vuole verificare un reclamo. Qui si prende la spedizione associata al reclamo e si calcola la probabilità dell'evento del reclamo

def calcola_probabilita(id_reclamo):
    
    reclamo = Reclamo.objects.get(id=id_reclamo)
    # La spedizione contiene i valori delle prove
    spedizione = model_to_dict(Spedizione.objects.get(id=id_reclamo))
    
    probPriori = list(Evento.objects.values_list('probabilita_priori', flat=True))
    evento1 = model_to_dict(Evento.objects.get(id=reclamo.evento1_id))
    evento2 = model_to_dict(Evento.objects.get(id=reclamo.evento2_id))
    
    # Calcolo delle probabilità per l'evento spedizione fallita
    if (reclamo.evento2_id is None) & (reclamo.evento1_id == 1):
        web3 = connect_to_besu()
        abi, address = load_contract()
        contract = web3.eth.contract(address=address, abi=abi)
        contract.functions.prob_spedizione_fallita(evento1, str(spedizione['gps']).lower(), str(spedizione['veicolo_disponibile']).lower(), str(spedizione['traffico']).lower(), str(spedizione['conferma_cliente']).lower(), (spedizione['disponibilita_corriere']).lower(), probPriori[0], probPriori[1], probPriori[2])
        
calcola_probabilita(1)
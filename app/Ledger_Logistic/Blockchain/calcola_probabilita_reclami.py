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
from Ledger_Logistic.Blockchain.export_probability import main as export_prob

# Questa è la funzione che viene chiamata quando il gestore vuole verificare un reclamo. Qui si prende la spedizione associata al reclamo e si calcola la probabilità dell'evento del reclamo

def calcola_probabilita(id_reclamo, bool_evento1, bool_evento2):
    # Prendo il reclamo in base all'id
    reclamo = Reclamo.objects.get(id=id_reclamo)
    # Prendo la spedizione in base al reclamo, la quale contiene i valori delle prove
    spedizione = model_to_dict(Spedizione.objects.get(id=reclamo.spedizione.id))

    prob_priori = list(Evento.objects.values_list('probabilita_priori', flat=True))

    export_prob()
    web3 = connect_to_besu()
    abi, address = load_contract()
    contract = web3.eth.contract(address=address, abi=abi)
    
    # Calcolo delle probabilità per l'evento spedizione fallita
    if (reclamo.evento2_id is None) & (reclamo.evento1_id == 1):
        probabilita = contract.functions.prob_spedizione_fallita(
        str(bool_evento1).lower(), 
        str(spedizione['gps']).lower(),
        str(spedizione['veicolo_disponibile']).lower(),
        str(spedizione['traffico']).lower(),
        str(spedizione['conferma_cliente']).lower(),
        str(spedizione['disponibilita_corriere']).lower(),
        prob_priori[0], # Probabilità a priori del primo evento (spedizione fallita)
        prob_priori[1],# Probabilità a priori del secondo evento (pagamento fallito)
        prob_priori[2]).call() # Probabilità a priori del terzo evento (ritardo di consegna)
        
    # Calcolo evento pagamento fallito e ritardo di consegna insieme
    elif (reclamo.evento2_id == 3) & (reclamo.evento1_id == 2):
        probabilita = contract.functions.prob_pagamento_fallito_e_ritardo_consegna(
        str(bool_evento1).lower(),
        str(bool_evento2).lower(),
        str(spedizione['conferma_cliente']).lower(),
        prob_priori[0],
        prob_priori[1],
        prob_priori[2]).call()
        
    # Calcolo evento pagamento fallito
    elif (reclamo.evento2_id is None) & (reclamo.evento1_id == 2):
        probabilita = contract.functions.prob_pagamento_fallito(
        str(bool_evento1).lower(),
        str(spedizione['conferma_cliente']).lower(),
        str(spedizione['fattura_emessa']).lower(),
        str(spedizione['conferma_del_gestore_di_pagamento']).lower(),
        prob_priori[0],
        prob_priori[1],
        prob_priori[2]).call()
        
    # Calcolo evento ritardo di consegna
    else:
        probabilita = contract.functions.prob_ritardo_consegna(
        str(bool_evento1).lower(),
        str(spedizione['gps']).lower(),
        str(spedizione['veicolo_disponibile']).lower(),
        str(spedizione['traffico']).lower(),
        str(spedizione['conferma_cliente']).lower(),
        str(spedizione['disponibilita_corriere']).lower(),
        str(spedizione['meteo_sfavorevole']).lower(),
        prob_priori[0],
        prob_priori[1],
        prob_priori[2]).call()
        
    return (probabilita[0]/probabilita[1])

from django.shortcuts import render

def home(request):
    # Se l'utente cerca un pacco (logica base)
    tracking_code = request.GET.get('tracking_code')
    context = {
        'company_name': 'Ledger Logistic',
        'tracking_code': tracking_code
    }
    return render(request, 'Ledger_Logistic/home.html', context)  
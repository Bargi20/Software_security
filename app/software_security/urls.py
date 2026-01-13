"""
URL configuration for software_security project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include

from Ledger_Logistic import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('servizi/', views.servizi, name='servizi'),
    path('chi-siamo/', views.chi_siamo, name='chi_siamo'),
    path('contatti/', views.contatti, name='contatti'),
    path('login/', views.custom_login, name='login'),
    path('verify-otp/', views.verify_otp, name='verify_otp'),
    path('resend-otp/', views.resend_otp, name='resend_otp'),
    path('logout/', views.custom_logout, name='logout'),
    path('register/', views.register, name='register'),
    path('reset-password/', views.reset_password_request, name='reset_password'),
    path('reset-password/verify-otp/', views.reset_password_verify_otp, name='reset_password_verify_otp'),
    path('reset-password/new/', views.reset_password_new, name='reset_password_new'),
    path('dashboard/cliente/', views.dashboard_cliente, name='dashboard_cliente'),
    path('dashboard/corriere/', views.dashboard_corriere, name='dashboard_corriere'),
    path('dashboard/gestore/', views.dashboard_gestore, name='dashboard_gestore'),
    path('dashboard/cliente/spedizione/crea/', views.crea_spedizione, name='crea_spedizione'),
    path('dashboard/cliente/spedizione/conferma-pagamento/', views.conferma_pagamento, name='conferma_pagamento'),
    path('dashboard/cliente/spedizione/pagamento-confermato/', views.pagamento_confermato, name='pagamento_confermato'),
    path('dashboard/cliente/spedizione/pagamento-fallito/', views.pagamento_fallito, name='pagamento_fallito'),
    path('dashboard/corriere/spedizione/completa/<str:codice_tracciamento>/', views.completa_consegna, name='completa_consegna'),
    path('dashboard/corriere/spedizione/accetta/<str:codice_tracciamento>/', views.accetta_spedizione, name='accetta_spedizione'),
    path('dashboard/corriere/spedizione/rifiuta/<str:codice_tracciamento>/', views.rifiuta_spedizione, name='rifiuta_spedizione'),
    path('dashboard/gestore/assegna-spedizioni/', views.assegna_spedizioni, name='assegna_spedizioni'),
    path('dashboard/cliente/fattura/<int:spedizione_id>/', views.scarica_fattura, name='scarica_fattura'),
    path('dashboard/cliente/spedizioni/conferma-cliente/<int:spedizione_id>/', views.conferma_consegna_cliente, name='conferma_consegna_cliente'),
    # ------ RECLAMI ------
    path('dashboard/gestore/gestione_reclami/', views.view_gestione_reclami, name='gestione_reclami'),
    path('dashboard/gestore/gestione_reclami/<int:id_reclamo>', views.gestisci_reclamo, name='gestisci_reclamo'),
    path('dashboard/cliente/spedizioni/reclami/<int:spedizione_id>/', views.invia_reclamo, name='reclami_spedizione'),
    # ------ GESTIONE SPEDIZIONI ------
    path('dashboard/gestore/gestione_spedizioni', views.gestione_spedizioni, name='gestione_spedizioni'),
    path('dashboard/gestore/gestione_spedizioni/dettaglio/<int:spedizione_id>', views.dettaglio_spedizione, name='dettaglio_spedizione')
]

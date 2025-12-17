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
from django.urls import path

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
    path('spedizione/crea/', views.crea_spedizione, name='crea_spedizione'),
    path('blockchain/invia-prova/<int:prova_id>/', views.invia_probabilita_blockchain, name='invia_prova_blockchain'),
    path('blockchain/invia-tutte/', views.invia_tutte_probabilita_blockchain, name='invia_prob_blockchain'),
]

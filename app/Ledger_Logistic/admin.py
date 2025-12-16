from django.contrib import admin
from django_otp.admin import OTPAdminSite
from django_otp.decorators import otp_required
from .models import Utente, TentativiDiLogin, CodiceOTP

# Usa admin normale, non OTP
# admin.site.__class__ = OTPAdminSite

# Personalizza i titoli dell'admin
admin.site.site_header = "Amministrazione Ledger Logistics"
admin.site.site_title = "Ledger Logistics"
admin.site.index_title = "Pannello di Amministrazione"

# Registra i modelli
@admin.register(Utente)
class UtenteAdmin(admin.ModelAdmin):
    list_display = ['email', 'username', 'is_staff', 'is_active', 'date_joined']
    search_fields = ['email', 'username']
    list_filter = ['is_staff', 'is_active', 'date_joined']

@admin.register(TentativiDiLogin)
class TentativiDiLoginAdmin(admin.ModelAdmin):
    list_display = ['email', 'failed_attempts', 'is_blocked', 'otp_failed_attempts', 'otp_is_blocked', 'last_attempt']
    search_fields = ['email']
    list_filter = ['is_blocked', 'otp_is_blocked']
    readonly_fields = ['last_attempt']

@admin.register(CodiceOTP)
class CodiceOTPAdmin(admin.ModelAdmin):
    list_display = ['utente', 'codice', 'creato_il', 'scade_il', 'usato']
    search_fields = ['utente__email']
    list_filter = ['usato', 'creato_il']
    readonly_fields = ['creato_il']

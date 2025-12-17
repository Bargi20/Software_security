from django.contrib import admin
from django_otp.admin import OTPAdminSite
from django_otp.decorators import otp_required
from .models import Utente, TentativiDiLogin, CodiceOTP, MessaggioContatto, Spedizione

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

@admin.register(MessaggioContatto)
class MessaggioContattoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'email', 'servizio', 'data_invio', 'letto')
    list_filter = ('letto', 'servizio', 'data_invio')
    search_fields = ('nome', 'email', 'messaggio')
    readonly_fields = ('data_invio',)
    actions = ['mark_as_read']
    
    def mark_as_read(self, request, queryset):
        queryset.update(letto=True)
        self.message_user(request, f'{queryset.count()} messaggi segnati come letti.')
    mark_as_read.short_description = 'Segna come letto'


@admin.register(Spedizione)
class SpedizioneAdmin(admin.ModelAdmin):
    list_display = ('codice_tracciamento', 'cliente', 'citta', 'grandezza', 'stato', 'corriere', 'data_creazione')
    list_filter = ('stato', 'grandezza', 'data_creazione', 'provincia')
    search_fields = ('codice_tracciamento', 'cliente__email', 'cliente__username', 'citta', 'indirizzo_consegna', 'descrizione')
    readonly_fields = ('codice_tracciamento', 'data_creazione', 'data_aggiornamento')
    autocomplete_fields = ['cliente', 'corriere']
    
    fieldsets = (
        ('Informazioni Spedizione', {
            'fields': ('codice_tracciamento', 'cliente', 'stato', 'corriere')
        }),
        ('Indirizzo di Consegna', {
            'fields': ('indirizzo_consegna', 'citta', 'cap', 'provincia')
        }),
        ('Dettagli Pacco', {
            'fields': ('grandezza', 'descrizione')
        }),
        ('Timestamp', {
            'fields': ('data_creazione', 'data_aggiornamento'),
            'classes': ('collapse',)
        }),
    )

from django.contrib import admin
from django_otp.admin import OTPAdminSite
from django_otp.decorators import otp_required
from .models import Utente, TentativiDiLogin, CodiceOTP
import os
from django.utils.html import format_html
from django.conf import settings
from .models import Utente, TentativiDiLogin, CodiceOTP, Spedizione

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


class FileViewerAdmin(admin.ModelAdmin):
    """Admin custom per visualizzare e gestire contratti Solidity"""
    change_list_template = 'admin/file_viewer_changelist.html'
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False
    
    def has_change_permission(self, request, obj=None):
        return True
    
    def changelist_view(self, request, extra_context=None):
        folder_path = os.path.join(settings.BASE_DIR, '..', 'contracts')
        folder_path = os.path.abspath(folder_path)
        
        files_data = []
        if os.path.isdir(folder_path):
            for filename in sorted(os.listdir(folder_path)):
                if filename.endswith('.sol'):
                    file_path = os.path.join(folder_path, filename)
                    if os.path.isfile(file_path):
                        size = os.path.getsize(file_path)
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                content = f.read()
                        except Exception as e:
                            content = f'Errore lettura: {str(e)}'
                        
                        files_data.append({
                            'name': filename,
                            'path': file_path,
                            'size': size,
                            'size_kb': round(size / 1024, 2),
                            'full_content': content,
                            'lines': content.count('\n') + 1,
                            'url_param': filename.replace('.sol', '')
                        })
        else:
            files_data = [{'error': f'Cartella non trovata: {folder_path}'}]
        
        extra_context = extra_context or {}
        extra_context['files'] = files_data
        extra_context['title'] = 'Contratti Solidity'
        extra_context['folder'] = folder_path
        return super().changelist_view(request, extra_context)

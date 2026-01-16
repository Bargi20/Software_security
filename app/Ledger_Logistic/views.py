import json
import random
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth import authenticate, login as django_login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from dotenv import load_dotenv
import stripe
import os
from .models import Spedizione, TentativiDiLogin, TentativiRecuperoPassword, CodiceOTP,Evento, Reclamo
from django.utils import timezone
from django.db import IntegrityError
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import ensure_csrf_cookie
from django.http import HttpResponse, JsonResponse, FileResponse
from django.urls import reverse
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
import random, string
load_dotenv()


# Ottieni il modello User personalizzato
Utente = get_user_model()

# Costanti
COMPANY_NAME = 'Ledger Logistic'
STRIPE_CURRENCY = 'eur'
SPEDIZIONE_IMPORTI_CENT = {
    'piccolo': 500,  # €5.00
    'medio': 1000,   # €10.00
    'grande': 2000   # €20.00
}
ACTION_MSG = 'Accesso negato. Non hai i permessi per accedere a questa dashboard.'
LEDGER_LOGISTIC_CREASPEDIZIONE_URL = "Ledger_Logistic/crea_spedizione.html"
LEDGER_LOGISTIC_INVIARECLAMO_URL = "Ledger_Logistic/invia_reclamo.html"


def _get_stripe_api_key():
    """Recupera la chiave Stripe dalle variabili d'ambiente."""
    return os.getenv('STRIPE_SECRET_KEY', '').strip()


def _calcola_importo_pagamento(grandezza):
    """Restituisce l'importo in centesimi in base alla grandezza."""
    return SPEDIZIONE_IMPORTI_CENT.get(grandezza)


def home(request):
    # Se l'utente cerca un spedizione (logica base)
    tracking_code = request.GET.get('tracking_code')
    context = {
        'tracking_code': tracking_code
    }
    return render(request, 'Ledger_Logistic/home.html', context)


def servizi(request):
    """Vista per la pagina servizi"""
    return render(request, 'Ledger_Logistic/servizi.html')


def chi_siamo(request):
    """Vista per la pagina chi siamo"""
    context = {
        'company_name': COMPANY_NAME
    }
    return render(request, 'Ledger_Logistic/chi_siamo.html', context)


def contatti(request):
    """Vista per la pagina contatti con form"""
    context = {
        'company_name': COMPANY_NAME
    }
    
    if request.method == 'POST':
        # Recupera i dati del form
        nome = request.POST.get('nome', '').strip()
        email = request.POST.get('email', '').strip()
        telefono = request.POST.get('telefono', '').strip()
        servizio = request.POST.get('servizio', '')
        messaggio = request.POST.get('messaggio', '').strip()
        
        # Validazione
        if not nome or not email or not messaggio:
            messages.error(request, 'Nome, email e messaggio sono obbligatori.')
            return render(request, 'Ledger_Logistic/contatti.html', context)
        
        try:
            # Salva nel database
            from .models import MessaggioContatto
            MessaggioContatto.objects.create(
                nome=nome,
                email=email,
                telefono=telefono,
                servizio=servizio,
                messaggio=messaggio
            )
            
            messages.success(
                request,
                f'Grazie {nome}! Abbiamo ricevuto il tuo messaggio e ti contatteremo presto all\'indirizzo {email}.'
            )
        except Exception as e:
            messages.error(request, f'Errore durante l\'invio del messaggio: {str(e)}')
    
    return render(request, 'Ledger_Logistic/contatti.html', context)


def custom_login(request):
    """
    Vista di login personalizzata con contatore di tentativi falliti.
    Blocca l'utente dopo 5 tentativi falliti per 30 minuti.
    Dopo la password corretta, richiede SEMPRE l'OTP.
    """
    root = "Ledger_Logistic/login.html"
    
    # GET request - mostra il form
    if request.method != 'POST':
        return render(request, root)
    
    # POST request - processa il login
    email = request.POST.get('email', '').strip()
    password = request.POST.get('password', '')
    
    # Verifica che i campi non siano vuoti
    if not email or not password:
        messages.error(request, 'Email e password sono obbligatori.')
        return render(request, root)
    
    # Recupera o crea un record di tentativo di login
    login_attempt, _ = TentativiDiLogin.objects.get_or_create(email=email)
    
    # Controlla se l'account è bloccato
    if login_attempt.is_account_blocked():
        remaining_time = (login_attempt.blocked_until - timezone.now()).seconds // 60
        messages.error(
            request, 
            f'Account bloccato per troppi tentativi falliti. '
            f'Riprova tra {remaining_time} minuti.'
        )
        return render(request, root, {
            'blocked': True,
            'remaining_time': remaining_time,
            'email': email
        })
    
    # Verifica che l'utente esista tramite email
    try:
        user_exists = Utente.objects.filter(email=email).exists()
        if not user_exists:
            login_attempt.increment_failed_attempts()
            remaining_attempts = 5 - login_attempt.failed_attempts
            messages.error(request, f'Email non trovata. Ti rimangono {remaining_attempts} tentativi.')
            return render(request, root, {
                'email': email,
                'remaining_attempts': remaining_attempts,
                'failed_attempts': login_attempt.failed_attempts
            })
        
    except Exception:
        messages.error(request, 'Errore durante la verifica dell\'utente.')
        return render(request, root)
    
    # Tenta l'autenticazione con email e password
    user = authenticate(request, email=email, password=password)
    
    if user is not None:
        # Password corretta - SEMPRE richiedi OTP
        # Genera e invia codice OTP via email
        codice_otp = CodiceOTP.genera_codice(user)
        
        # Invia email con codice
        try:
            send_mail(
                subject=f'Codice OTP - {COMPANY_NAME}',
                message=f'Il tuo codice OTP è: {codice_otp.codice}\n\nValido per 5 minuti.\n\nSe non hai richiesto questo accesso, ignora questa email.',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )
            
            # Salva l'email nella sessione per la verifica OTP
            request.session['otp_user_email'] = user.email
            request.session['otp_verified'] = False
            
            # Reset contatore password fallite
            login_attempt.reset_attempts()
            
            messages.info(request, f'📧 Codice OTP inviato a {email}')
            return redirect('verify_otp')
            
        except Exception as e:
            messages.error(request, f'Errore nell\'invio dell\'email: {str(e)}')
            return render(request, root)
    else:
        # Login fallito - incrementa il contatore
        login_attempt.increment_failed_attempts()
        remaining_attempts = 5 - login_attempt.failed_attempts
        
        if login_attempt.is_blocked:
            messages.error(
                request,
                'Account bloccato per troppi tentativi falliti. '
                'Riprova tra 30 minuti.'
            )
        else:
            messages.warning(
                request,
                f'Password errata. '
                f'Ti rimangono {remaining_attempts} tentativi.'
            )
        
        return render(request, root, {
            'email': email,
            'remaining_attempts': remaining_attempts,
            'failed_attempts': login_attempt.failed_attempts
        })


# ============= OTP VERIFICATION HELPER FUNCTIONS =============

def _check_otp_session(request):
    """Verifica se la sessione OTP è valida"""
    if 'otp_user_email' not in request.session:
        messages.error(request, 'Sessione scaduta. Effettua nuovamente il login.')
        return None
    return request.session.get('otp_user_email')


def _check_otp_blocked(login_attempt, request):
    """Verifica se l'OTP è bloccato per troppi tentativi"""
    if not login_attempt.is_otp_blocked():
        return False
    
    remaining_time = (login_attempt.otp_blocked_until - timezone.now()).seconds // 60
    messages.error(
        request,
        f'Troppi tentativi OTP falliti. Account bloccato per {remaining_time} minuti.'
    )
    _clear_otp_session(request)
    return True


def _clear_otp_session(request):
    """Pulisce i dati OTP dalla sessione"""
    if 'otp_user_email' in request.session:
        del request.session['otp_user_email']
    if 'otp_verified' in request.session:
        del request.session['otp_verified']


def _get_latest_otp_code(user):
    """Recupera il codice OTP più recente non usato"""
    return CodiceOTP.objects.filter(
        utente=user,
        usato=False
    ).order_by('-creato_il').first()


def _handle_correct_otp(request, user, login_attempt):
    """Gestisce il caso di codice OTP corretto"""
    login_attempt.reset_otp_attempts()
    django_login(request, user)
    request.session['otp_verified'] = True
    _clear_otp_session(request)
    
    # Reindirizza in base al ruolo dell'utente
    if user.ruolo == 'cliente':
        return redirect('dashboard_cliente')
    elif user.ruolo == 'corriere':
        return redirect('dashboard_corriere')
    elif user.ruolo == 'gestore':
        return redirect('dashboard_gestore')
    else:
        # Default fallback
        return redirect('home')


def _handle_incorrect_otp(request, login_attempt, user):
    """Gestisce il caso di codice OTP errato"""
    login_attempt.increment_otp_failed_attempts()
    remaining_attempts = 5 - login_attempt.otp_failed_attempts
    
    if login_attempt.otp_is_blocked:
        messages.error(
            request,
            '🚫 Troppi tentativi falliti. Account bloccato per 30 minuti.'
        )
        _clear_otp_session(request)
        return redirect('login')
    
    # Genera e invia nuovo codice OTP
    try:
        codice_otp = CodiceOTP.genera_codice(user)
        send_mail(
            subject='Nuovo Codice OTP - Ledger Logistic',
            message=f'Hai inserito un codice errato. Il tuo nuovo codice OTP è: {codice_otp.codice}\n\nValido per 5 minuti.\n\nTi rimangono {remaining_attempts} tentativi.\n\nSe non hai richiesto questo accesso, ignora questa email.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
        messages.error(
            request,
            f'❌ Codice OTP non valido. Ti abbiamo inviato un nuovo codice. Tentativi rimasti: {remaining_attempts}'
        )
    except Exception:
        messages.error(
            request,
            f'❌ Codice OTP non valido. Ti rimangono {remaining_attempts} tentativi.'
        )
    
    return None


def _process_otp_verification(request, email, codice_inserito):
    """Processa la verifica del codice OTP"""
    try:
        user = Utente.objects.get(email=email)
    except Utente.DoesNotExist:
        messages.error(request, 'Utente non trovato.')
        return redirect('login')
    
    login_attempt, _ = TentativiDiLogin.objects.get_or_create(email=email)
    ultimo_codice = _get_latest_otp_code(user)
    
    if ultimo_codice and ultimo_codice.verifica(codice_inserito):
        return _handle_correct_otp(request, user, login_attempt)
    
    return _handle_incorrect_otp(request, login_attempt, user)


# ============= MAIN OTP VERIFICATION VIEW =============

def verify_otp(request):
    """Vista per verificare il codice OTP con contatore tentativi"""
    # Early return se sessione non valida
    email = _check_otp_session(request)
    if email is None:
        return redirect('login')
    
    # Recupera il record dei tentativi
    login_attempt, _ = TentativiDiLogin.objects.get_or_create(email=email)
    
    # Early return se OTP è bloccato
    if _check_otp_blocked(login_attempt, request):
        return redirect('login')
    
    # Processa POST request
    if request.method == 'POST':
        codice_inserito = request.POST.get('otp_code', '').strip()
        receipt = _process_otp_verification(request, email, codice_inserito)
        if receipt:
            return receipt
    
    # Calcola tentativi rimanenti e mostra form
    otp_remaining_attempts = 5 - login_attempt.otp_failed_attempts
    
    return render(request, 'Ledger_Logistic/verify_otp.html', {
        'email': email,
        'otp_remaining_attempts': otp_remaining_attempts,
        'otp_failed_attempts': login_attempt.otp_failed_attempts
    })


def resend_otp(request):
    """Vista per reinviare il codice OTP"""
    # Verifica sessione
    email = _check_otp_session(request)
    if email is None:
        messages.error(request, 'Sessione scaduta. Effettua nuovamente il login.')
        return redirect('login')
    
    try:
        user = Utente.objects.get(email=email)
        login_attempt, _ = TentativiDiLogin.objects.get_or_create(email=email)
        
        # Verifica se è bloccato
        if _check_otp_blocked(login_attempt, request):
            return redirect('login')
        
        # Genera e invia nuovo codice
        codice_otp = CodiceOTP.genera_codice(user)
        send_mail(
            subject='Nuovo Codice OTP - Ledger Logistic',
            message=f'Hai richiesto un nuovo codice OTP: {codice_otp.codice}\n\nValido per 5 minuti.\n\nSe non hai richiesto questo accesso, ignora questa email.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
        
        messages.success(request, f'✅ Nuovo codice OTP inviato a {email}')
        
    except Utente.DoesNotExist:
        messages.error(request, 'Utente non trovato.')
        return redirect('login')
    except Exception as e:
        messages.error(request, f'Errore nell\'invio del codice: {str(e)}')
    
    return redirect('verify_otp')


def custom_logout(request):
    """Vista personalizzata per il logout"""
    logout(request)
    messages.info(request, 'Logout effettuato con successo.')
    return redirect('home')


# ============= HELPER FUNCTIONS FOR REGISTRATION =============

def _validate_username(username):
    """Valida il formato dello username"""
    if not username or len(username) < 3:
        return 'Lo username deve essere lungo almeno 3 caratteri.'
    return None


def _validate_email(email):
    """Valida il formato dell'email"""
    if not email or '@' not in email:
        return 'Inserisci un indirizzo email valido.'
    return None


def _validate_password(password):
    """Valida il formato della password"""
    if not password or len(password) < 8:
        return 'La password deve essere lunga almeno 8 caratteri.'
    return None


def _validate_password_match(password, password_confirm):
    """Verifica che le password coincidano"""
    if password != password_confirm:
        return 'Le password non coincidono.'
    return None


def _check_username_exists(username):
    """Controlla se lo username esiste già"""
    if Utente.objects.filter(username=username).exists():
        return 'Questo username è già in uso.'
    return None


def _check_email_exists(email):
    """Controlla se l'email è già registrata"""
    if Utente.objects.filter(email=email).exists():
        return 'Questa email è già registrata.'
    return None


def _validate_registration_data(username, email, password, password_confirm):
    """
    Valida tutti i dati di registrazione.
    Ritorna una lista di errori (vuota se tutto ok).
    """
    errors = []
    
    # Validazione formato
    error = _validate_username(username)
    if error:
        errors.append(error)
    
    error = _validate_email(email)
    if error:
        errors.append(error)
    
    error = _validate_password(password)
    if error:
        errors.append(error)
    
    error = _validate_password_match(password, password_confirm)
    if error:
        errors.append(error)
    
    # Validazione unicità (solo se i formati sono validi)
    if not errors:
        error = _check_username_exists(username)
        if error:
            errors.append(error)
        
        error = _check_email_exists(email)
        if error:
            errors.append(error)
    
    return errors


def _create_user_account(username, email, password, first_name, last_name, phone_number, address, data_nascita):
    """
    Crea un nuovo account utente.
    Ritorna (success: bool, error_message: str or None)
    """
    try:
        # Usa il manager del modello personalizzato
        user = Utente.objects.create_user(
            email=email,
            username=username,
            password=password,
            first_name=first_name,
            last_name=last_name,
            phone_number=phone_number,
            address=address,
            data_nascita=data_nascita
        )
        
        # Verifica che l'utente sia stato creato correttamente
        if user and user.pk:
            return True, None
        else:
            return False, 'Errore durante la creazione dell\'account.'
            
    except IntegrityError as e:
        return False, f'Errore di integrità: {str(e)}'
    except Exception as e:
        return False, f'Errore imprevisto: {str(e)}'


# ============= MAIN REGISTRATION VIEW =============

def register(request):
    """
    Vista per la registrazione di nuovi utenti.
    Valida i dati e crea un nuovo account.
    """
    root = "Ledger_Logistic/register.html"
    
    # GET request - mostra il form
    if request.method != 'POST':
        return render(request, root)
    
    # POST request - processa la registrazione
    username = request.POST.get('username', '').strip()
    email = request.POST.get('email', '').strip()
    password = request.POST.get('password', '')
    password_confirm = request.POST.get('password_confirm', '')
    first_name = request.POST.get('first_name', '').strip()
    last_name = request.POST.get('last_name', '').strip()
    phone_number = request.POST.get('phone_number', '').strip()
    address = request.POST.get('address', '').strip()
    data_nascita = request.POST.get('data_nascita', None)
    
    # Valida i dati
    errors = _validate_registration_data(username, email, password, password_confirm)
    
    # Se ci sono errori, ritorna al form con i messaggi
    if errors:
        for error in errors:
            messages.error(request, error)
        return render(request, root, {
            'username': username,
            'email': email,
            'first_name': first_name,
            'last_name': last_name,
            'phone_number': phone_number,
            'address': address,
            'data_nascita': data_nascita
        })
    
    # Crea l'utente
    success, error_message = _create_user_account(
        username, email, password, first_name, last_name,
        phone_number, address, data_nascita
    )
    
    # Gestisci il risultato
    if not success:
        messages.error(request, error_message)
        return render(request, root)
    
    messages.success(
        request,
        f'✅ Account creato con successo! Benvenuto {username}, puoi ora effettuare il login con la tua email.'
    )
    return redirect('login')




def reset_password_request(request):
    """
    Vista per richiedere il recupero password.
    Permette all'utente di inserire la propria email.
    Blocca dopo 5 tentativi falliti per 30 minuti.
    """
    root = "Ledger_Logistic/reset_password.html"
    
    # GET request - mostra il form
    if request.method != 'POST':
        return render(request, root)
    
    # POST request - processa la richiesta
    email = request.POST.get('email', '').strip()
    
    # Verifica che l'email non sia vuota
    if not email:
        messages.error(request, 'L\'email è obbligatoria.')
        return render(request, root)
    
    # Validazione formato email
    import re
    email_regex = r'^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_regex, email):
        messages.error(request, '❌ Formato email non valido. L\'email deve contenere @ e un dominio valido (es: utente@dominio.com)')
        return render(request, root, {'email': email})
    
    # Recupera o crea un record di tentativo di recupero
    recovery_attempt, _ = TentativiRecuperoPassword.objects.get_or_create(email=email)
    
    # Controlla se l'account è bloccato
    if recovery_attempt.is_account_blocked():
        remaining_time = (recovery_attempt.blocked_until - timezone.now()).seconds // 60
        messages.error(
            request, 
            f'Troppi tentativi falliti. Riprova tra {remaining_time} minuti.'
        )
        return render(request, root, {
            'blocked': True,
            'remaining_time': remaining_time,
            'email': email
        })
    
    # Verifica che l'email esista nel database
    try:
        user = Utente.objects.filter(email=email).first()
        
        if not user:
            # Email non valida - incrementa tentativi
            recovery_attempt.increment_failed_attempts()
            remaining_attempts = 5 - recovery_attempt.failed_attempts
            
            messages.error(
                request, 
                f'Email non valida. Ti rimangono {remaining_attempts} tentativi.'
            )
            return render(request, root, {
                'email': email,
                'remaining_attempts': remaining_attempts,
                'failed_attempts': recovery_attempt.failed_attempts
            })
        
        # Email valida - reset tentativi email e genera OTP
        recovery_attempt.reset_attempts()
        
        # Genera e invia codice OTP
        codice_otp = CodiceOTP.genera_codice(user)
        
        try:
            send_mail(
                subject='Codice OTP - Recupero Password - Ledger Logistic',
                message=f'Il tuo codice OTP per il recupero password è: {codice_otp.codice}\n\nValido per 5 minuti.\n\nSe non hai richiesto il recupero password, ignora questa email.',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )
            
            # Salva l'email nella sessione per la verifica OTP
            request.session['reset_password_email'] = user.email
            request.session['reset_password_otp_verified'] = False
            
            messages.success(request, f'📧 Codice OTP inviato a {email}')
            return redirect('reset_password_verify_otp')
            
        except Exception as e:
            messages.error(request, f'Errore nell\'invio dell\'email: {str(e)}')
            return render(request, root)
        
    except Exception as e:
        messages.error(request, f'Errore durante la verifica: {str(e)}')
        return render(request, root)


# ============= HELPER FUNCTIONS FOR PASSWORD RESET OTP =============

def _check_reset_password_session(request):
    """Verifica se la sessione di reset password è valida"""
    if 'reset_password_email' not in request.session:
        messages.error(request, 'Sessione scaduta. Richiedi nuovamente il recupero password.')
        return None
    return request.session.get('reset_password_email')


def _get_user_and_recovery_attempt(email):
    """Recupera utente e tentativo di recupero"""
    try:
        user = Utente.objects.get(email=email)
        recovery_attempt = TentativiRecuperoPassword.objects.get(email=email)
        return user, recovery_attempt, None
    except (Utente.DoesNotExist, TentativiRecuperoPassword.DoesNotExist):
        return None, None, 'Errore di sessione. Riprova.'


def _check_recovery_otp_blocked(recovery_attempt):
    """Verifica se l'OTP di recupero è bloccato"""
    if recovery_attempt.is_otp_blocked():
        remaining_time = (recovery_attempt.otp_blocked_until - timezone.now()).seconds // 60
        return True, remaining_time
    return False, 0


def _validate_reset_otp_code(user):
    """Valida il codice OTP per reset password"""
    ultimo_otp = CodiceOTP.objects.filter(
        utente=user,
        usato=False
    ).order_by('-creato_il').first()
    
    if not ultimo_otp:
        return None, 'Nessun codice OTP valido trovato. Richiedi un nuovo codice.'
    
    if not ultimo_otp.is_valido():
        return None, 'Il codice OTP è scaduto. Richiedi un nuovo codice.'
    
    return ultimo_otp, None


def _handle_correct_reset_otp(request, recovery_attempt):
    """Gestisce OTP corretto per reset password"""
    recovery_attempt.reset_otp_attempts()
    request.session['reset_password_otp_verified'] = True
    messages.success(request, '✅ Codice OTP verificato! Ora puoi impostare una nuova password.')
    return redirect('reset_password_new')


def _clear_reset_password_session(request):
    """Pulisce la sessione di reset password"""
    if 'reset_password_email' in request.session:
        del request.session['reset_password_email']
    if 'reset_password_otp_verified' in request.session:
        del request.session['reset_password_otp_verified']


def _handle_incorrect_reset_otp(request, recovery_attempt):
    """Gestisce OTP errato per reset password"""
    recovery_attempt.increment_otp_failed_attempts()
    remaining_attempts = 5 - recovery_attempt.otp_failed_attempts
    
    if recovery_attempt.otp_is_blocked:
        messages.error(request, '🚫 Troppi tentativi falliti. Account bloccato per 30 minuti.')
        _clear_reset_password_session(request)
        return redirect('reset_password'), None
    
    messages.error(request, f'❌ Codice OTP errato. Ti rimangono {remaining_attempts} tentativi.')
    return None, remaining_attempts


def reset_password_verify_otp(request):
    """Vista per verificare il codice OTP durante il recupero password"""
    root = "Ledger_Logistic/reset_password_verify_otp.html"
    
    # Early return se sessione non valida
    email = _check_reset_password_session(request)
    if email is None:
        return redirect('reset_password')
    
    # Recupera utente e tentativo
    user, recovery_attempt, error = _get_user_and_recovery_attempt(email)
    if error:
        messages.error(request, error)
        _clear_reset_password_session(request)
        return redirect('reset_password')
    
    # Verifica blocco OTP
    is_blocked, remaining_time = _check_recovery_otp_blocked(recovery_attempt)
    if is_blocked:
        messages.error(request, f'Troppi tentativi OTP falliti. Riprova tra {remaining_time} minuti.')
        return render(request, root, {
            'blocked': True,
            'remaining_time': remaining_time,
            'email': email
        })
    
    # GET request
    if request.method != 'POST':
        return render(request, root, {'email': email})
    
    # POST request - verifica OTP
    codice_inserito = request.POST.get('otp', '').strip()
    
    if not codice_inserito:
        messages.error(request, 'Il codice OTP è obbligatorio.')
        return render(request, root, {'email': email})
    
    # Valida codice
    ultimo_otp, error_msg = _validate_reset_otp_code(user)
    if error_msg:
        messages.error(request, error_msg)
        return render(request, root, {'email': email})
    
    # Verifica codice
    if ultimo_otp.verifica(codice_inserito):
        return _handle_correct_reset_otp(request, recovery_attempt)
    
    # OTP errato
    receipt, remaining_attempts = _handle_incorrect_reset_otp(request, recovery_attempt)
    if receipt:
        return receipt
    
    return render(request, root, {
        'email': email,
        'remaining_attempts': remaining_attempts,
        'otp_failed_attempts': recovery_attempt.otp_failed_attempts
    })


def _validate_password_fields(new_password, confirm_password):
    """Valida che i campi password siano compilati e corrispondano"""
    errors = []
    
    if not new_password or not confirm_password:
        errors.append('Entrambi i campi sono obbligatori.')
        return errors
    
    if new_password != confirm_password:
        errors.append('Le password non corrispondono.')
    
    return errors


def _validate_password_strength(password):
    """Valida la complessità della password secondo i requisiti di sicurezza"""
    import re
    
    errors = []
    if len(password) < 8:
        errors.append('La password deve essere lunga almeno 8 caratteri')
    if not re.search(r'[A-Z]', password):
        errors.append('Deve contenere almeno una lettera maiuscola')
    if not re.search(r'[a-z]', password):
        errors.append('Deve contenere almeno una lettera minuscola')
    if not re.search(r'\d', password):
        errors.append('Deve contenere almeno un numero')
    if not re.search(r'[!@#$%^&*(),.?":{}|<>+]', password):
        errors.append('Deve contenere almeno un carattere speciale (!@#$%^&*(),.?":{}|<>+)')
    
    return errors


def _update_user_password(email, new_password):
    """Aggiorna la password dell'utente"""
    try:
        user = Utente.objects.get(email=email)
        user.set_password(new_password)
        user.save()
        return True, None
    except Utente.DoesNotExist:
        return False, 'Errore: utente non trovato.'
    except Exception as e:
        return False, f'Errore durante l\'aggiornamento della password: {str(e)}'


def reset_password_new(request):
    """Vista per impostare una nuova password dopo verifica OTP"""
    root = "Ledger_Logistic/reset_password_new.html"
    
    if 'reset_password_email' not in request.session or not request.session.get('reset_password_otp_verified'):
        messages.error(request, 'Sessione scaduta o OTP non verificato. Riprova.')
        return redirect('reset_password')
    
    email = request.session.get('reset_password_email')
    
    if request.method != 'POST':
        return render(request, root, {'email': email})
    
    new_password = request.POST.get('new_password', '').strip()
    confirm_password = request.POST.get('confirm_password', '').strip()
    
    # Valida i campi base
    field_errors = _validate_password_fields(new_password, confirm_password)
    if field_errors:
        for error in field_errors:
            messages.error(request, error)
        return render(request, root, {'email': email})
    
    # Valida la complessità della password
    strength_errors = _validate_password_strength(new_password)
    if strength_errors:
        for error in strength_errors:
            messages.error(request, f'❌ {error}')
        return render(request, root, {'email': email})
    
    # Aggiorna la password
    success, error_message = _update_user_password(email, new_password)
    
    if not success:
        messages.error(request, error_message)
        if 'utente non trovato' in error_message:
            return redirect('reset_password')
        return render(request, root, {'email': email})
    
    _clear_reset_password_session(request)
    messages.success(
        request,
        '✅ Password aggiornata con successo! Ora puoi effettuare il login con la nuova password.'
    )
    return redirect('login')


@staff_member_required
@require_POST
def download_contract(request):
    """Scarica un file contratto"""
    data = json.loads(request.body)
    filepath = data.get('filepath', '')
    
    if os.path.isfile(filepath) and filepath.endswith('.sol'):
        return FileResponse(open(filepath, 'rb'), as_attachment=True)
    return JsonResponse({'error': 'File non trovato'}, status=404)


def assegna_spedizione_a_corriere(corriere):
    """Assegna un spedizione disponibile al corriere specificato"""
    from .models import Spedizione
    
    # Cerca un spedizione in attesa o in elaborazione senza corriere assegnato
    spedizione_disponibile = Spedizione.objects.filter(
        corriere__isnull=True,
        stato__in=['in_attesa', 'in_elaborazione']
    ).order_by('data_creazione').first()
    
    if spedizione_disponibile:
        spedizione_disponibile.corriere = corriere
        spedizione_disponibile.stato = 'in_consegna'
        spedizione_disponibile.disponibilita_corriere = True
        spedizione_disponibile.save()
        return spedizione_disponibile
    
    return None


def assegna_spedizioni(request):
    if request.method == "POST":
        spedizione_id = request.POST.get("spedizione_id")
        corriere_id = request.POST.get("corriere_id")

        # Se non è stato selezionato alcun corriere → non fare nulla
        if not corriere_id:
            return redirect("assegna_spedizioni")

        spedizione = get_object_or_404(Spedizione, id=spedizione_id)
        corriere = get_object_or_404(Utente, id=corriere_id, ruolo="corriere")

        # Assegna
        spedizione.corriere = corriere
        spedizione.stato = "in_consegna"
        spedizione.disponibilita_corriere = True
        spedizione.save()

        return redirect("assegna_spedizioni")

    # GET
    spedizioni = Spedizione.objects.filter(
        corriere__isnull=True,
        stato__in=["in_attesa", "in_elaborazione"]
    )

    # Recupera solo corrieri disponibili (senza spedizioni in consegna)
    corrieri_con_spedizioni = Spedizione.objects.filter(
        stato='in_consegna'
    ).values_list('corriere_id', flat=True)
    
    corrieri = Utente.objects.filter(
        ruolo="corriere",
        is_active=True
    ).exclude(id__in=corrieri_con_spedizioni)

    return render(request, "Ledger_Logistic/assegna_spedizioni.html", {
        "spedizioni": spedizioni,
        "corrieri": corrieri,
    })

# ============= DASHBOARD VIEWS =============

@login_required
def dashboard_cliente(request):
    """Dashboard per utenti con ruolo 'cliente'"""
    # Verifica che l'utente abbia il ruolo cliente

    if request.user.ruolo != 'cliente':
        messages.error(request, ACTION_MSG)
        # Reindirizza alla dashboard corretta in base al ruolo
        if request.user.ruolo == 'corriere':
            return redirect('dashboard_corriere')
        elif request.user.ruolo == 'gestore':
            return redirect('dashboard_gestore')
        else:
            return redirect('home')
    
    # Importa il modello Spedizione
    from .models import Spedizione
    
    # Recupera tutte le spedizione del cliente
    spedizione = Spedizione.objects.filter(cliente=request.user).order_by('-data_creazione')
    
    # Calcola le statistiche
    spedizione_attive = spedizione.filter(stato__in=['in_attesa', 'in_elaborazione']).count()
    spedizione_consegnate = spedizione.filter(stato='consegnato').count()
    spedizione_in_transito = spedizione.filter(stato__in=['in_transito', 'in_consegna']).count()
    spedizione_totali = spedizione.count()
    
    # Filtro per spedizione in corso
    filtro_grandezza = request.GET.get('filtro_grandezza', '')
    spedizione_in_corso = spedizione.filter(stato__in=['in_attesa', 'in_elaborazione', 'in_transito', 'in_consegna']).order_by('-data_creazione')
    
    if filtro_grandezza:
        spedizione_in_corso = spedizione_in_corso.filter(grandezza=filtro_grandezza)
    
    # spedizione passate (senza paginazione server-side)
    spedizione_passate = spedizione.filter(stato__in=['consegnato', 'annullato']).order_by('-data_aggiornamento')
    
    context = {
        'company_name': COMPANY_NAME,
        'user': request.user,
        'spedizioni_attive': spedizione_attive,
        'spedizioni_consegnate': spedizione_consegnate,
        'spedizioni_in_transito': spedizione_in_transito,
        'spedizioni_totali': spedizione_totali,
        'spedizioni_in_corso': spedizione_in_corso,   # <- plural
        'spedizioni_passate': spedizione_passate,     # <- plural
        'filtro_grandezza': filtro_grandezza
    }
    return render(request, 'Ledger_Logistic/dashboard_cliente.html', context)


def trova_corriere_disponibile():
    """Trova un corriere disponibile (senza pacchi in consegna)"""
    from .models import Spedizione, Utente
    from django.db.models import Count, Q
    
    # Trova tutti i corrieri
    corrieri = Utente.objects.filter(ruolo='corriere', is_active=True)
    
    # Per ogni corriere, conta quanti pacchi ha in consegna
    corrieri_disponibili = []
    for corriere in corrieri:
        pacchi_in_consegna = Spedizione.objects.filter(
            corriere=corriere,
            stato='in_consegna'
        ).count()
        
        if pacchi_in_consegna == 0:
            corrieri_disponibili.append(corriere)
    
    # Ritorna il primo corriere disponibile (o None)
    return corrieri_disponibili[0] if corrieri_disponibili else None


@login_required
def dashboard_corriere(request):
    """Dashboard per utenti con ruolo 'corriere'"""
    # Verifica che l'utente abbia il ruolo corriere
    if request.user.ruolo != 'corriere':
        messages.error(request, ACTION_MSG)
        # Reindirizza alla dashboard corretta in base al ruolo
        if request.user.ruolo == 'cliente':
            return redirect('dashboard_cliente')
        elif request.user.ruolo == 'gestore':
            return redirect('dashboard_gestore')
        else:
            return redirect('home')
    
    # Importa il modello Spedizione
    from .models import Spedizione
    
    # Recupera le spedizione assegnate al corriere
    spedizione_assegnate = Spedizione.objects.filter(corriere=request.user).order_by('-data_creazione')
    
    # Calcola le statistiche
    consegne_oggi = spedizione_assegnate.filter(
        data_creazione__date=timezone.now().date()
    ).count()
    
    consegne_completate = spedizione_assegnate.filter(stato='consegnato').count()
    consegne_in_corso = spedizione_assegnate.filter(
        stato__in=['in_transito', 'in_consegna']
    ).count()
    
    # Consegne del mese corrente
    consegne_mese = spedizione_assegnate.filter(
        data_creazione__month=timezone.now().month,
        data_creazione__year=timezone.now().year
    ).count()
    
    # spedizione in corso (per la sezione collegamento)
    spedizione_in_corso = spedizione_assegnate.filter(
        stato__in=['in_transito', 'in_consegna']
    ).order_by('-data_creazione')
    
    # spedizione passate (completate o annullate)
    spedizione_passate = spedizione_assegnate.filter(
        stato__in=['consegnato', 'annullato']
    ).order_by('-data_aggiornamento')
    
    context = {
        'company_name': COMPANY_NAME,
        'user': request.user,
        'consegne_oggi': consegne_oggi,
        'consegne_completate': consegne_completate,
        'consegne_in_corso': consegne_in_corso,
        'consegne_mese': consegne_mese,
        'spedizioni_in_corso': spedizione_in_corso,
        'spedizioni_passate': spedizione_passate,
    }

    return render(request, 'Ledger_Logistic/dashboard_corriere.html', context)


@login_required
def dashboard_gestore(request):
    """Dashboard per utenti con ruolo 'gestore'"""
    # Verifica che l'utente abbia il ruolo gestore
    if request.user.ruolo != 'gestore':
        messages.error(request, ACTION_MSG)
        # Reindirizza alla dashboard corretta in base al ruolo
        if request.user.ruolo == 'cliente':
            return redirect('dashboard_cliente')
        elif request.user.ruolo == 'corriere':
            return redirect('dashboard_corriere')
        else:
            return redirect('home')
    
    from .models import Spedizione, Utente
    from django.db.models import Count, Q
    
    corrieri_attivi= Utente.objects.filter(ruolo='corriere', is_active=True).count()
    corrieri_totali= Utente.objects.filter(ruolo='corriere').count()
    
    # spedizione in attesa di approvazione (stato in_attesa o in_elaborazione)
    spedizione_in_attesa = Spedizione.objects.filter(
        stato__in=['in_attesa', 'in_elaborazione']
    ).select_related('cliente', 'corriere').order_by('data_creazione')
    
    # Storico di tutte le spedizione (completate, annullate, in transito, in consegna)
    spedizione_storico = Spedizione.objects.filter(
        stato__in=['in_transito', 'in_consegna', 'consegnato', 'annullato']
    ).select_related('cliente', 'corriere').order_by('-data_aggiornamento')
    
    spedizioni_oggi = Spedizione.objects.filter(stato='in_consegna').count()
    tempo_medio_consegna = calcola_tempo_medio_consegna()
    
    # Statistiche
    totale_spedizione = Spedizione.objects.count()
    spedizione_attive = Spedizione.objects.filter(
        stato__in=['in_attesa', 'in_elaborazione', 'in_transito', 'in_consegna']
    ).count()
    spedizione_completate = Spedizione.objects.filter(stato='consegnato').count()
    totale_utenti = Utente.objects.filter(is_active=True).count()
    
    # Calcola tasso di successo
    if totale_spedizione > 0:
        tasso_successo = round((spedizione_completate / totale_spedizione) * 100, 1)
    else:
        tasso_successo = 0
    
    context = {
        'company_name': COMPANY_NAME,
        'user': request.user,
        'spedizione_in_attesa': spedizione_in_attesa,
        'spedizione_storico': spedizione_storico,
        'totale_spedizione': totale_spedizione,
        'spedizione_attive': spedizione_attive,
        'spedizione_completate': spedizione_completate,
        'totale_utenti': totale_utenti,
        'tasso_successo': tasso_successo,
        'corrieri_attivi': corrieri_attivi,
        'corrieri_totali': corrieri_totali,
        'spedizioni_oggi': spedizioni_oggi,
        'tempo_medio_consegna': tempo_medio_consegna,
    }
    return render(request, 'Ledger_Logistic/dashboard_gestore.html', context)

from django.db.models import Avg, F, ExpressionWrapper, DurationField


def calcola_tempo_medio_consegna():
    media = (
        Spedizione.objects
        .filter(stato='consegnato') #prendo tutte le spedizioni "consegnato"
        .annotate(
            durata=ExpressionWrapper(
                F('data_aggiornamento') - F('data_creazione'), # differenza fra data di aggiornamento (consegnato) e data di creazione (default "in_attesa")
                output_field=DurationField()
            )
        )
        .aggregate(media=Avg('durata')) #fa la media fra tutte le durate di tutte le spedizioni
    )

    return media['media'].days if media['media'] else 0

# ============= SPEDIZIONE VIEWS =============

def _build_spedizione_form_context(request, **form_data):
    """Costruisce il contesto per il form di creazione spedizione"""
    context = {
        'company_name': COMPANY_NAME,
        'user': request.user
    }
    context.update(form_data)
    return context


def _validate_spedizione_form(indirizzo_consegna, citta, cap, provincia, grandezza, descrizione, metodo_pagamento):
    """Valida i dati del form di spedizione. Ritorna lista di errori."""
    errors = []
    
    if not indirizzo_consegna:
        errors.append('L\'indirizzo di consegna è obbligatorio.')
    if not citta:
        errors.append('La città è obbligatoria.')
    if not cap:
        errors.append('Il CAP è obbligatorio.')
    elif len(cap) != 5 or not cap.isdigit():
        errors.append('Il CAP deve essere di 5 cifre.')
    if not provincia:
        errors.append('La provincia è obbligatoria.')
    elif len(provincia) != 2:
        errors.append('La provincia deve essere di 2 caratteri (es: MI, RM).')
    if not grandezza or grandezza not in ['piccolo', 'medio', 'grande']:
        errors.append('Seleziona una grandezza valida per il pacco.')
    if not descrizione:
        errors.append('La descrizione dell\'ordine è obbligatoria.')
    if metodo_pagamento not in ['carta', 'cash']:
        errors.append('Seleziona un metodo di pagamento valido.')
    
    return errors


def _process_stripe_payment(request, grandezza, form_context, form_data):
    """Processa il pagamento Stripe. Ritorna la response o None se successo."""
    root = LEDGER_LOGISTIC_CREASPEDIZIONE_URL
    
    stripe_api_key = _get_stripe_api_key()
    if not stripe_api_key:
        messages.error(request, 'Pagamento non disponibile: configurare STRIPE_SECRET_KEY nel file .env.')
        return render(request, root, form_context)

    stripe.api_key = stripe_api_key
    amount_cents = _calcola_importo_pagamento(grandezza)
    if not amount_cents:
        messages.error(request, 'Pagamento non disponibile per la grandezza selezionata.')
        return render(request, root, form_context)

    try:
        payment_intent = stripe.PaymentIntent.create(
            amount=amount_cents,
            currency=STRIPE_CURRENCY,
            description=f"Spedizione {grandezza} - {request.user.email}",
            payment_method_types=['card'],
            metadata={
                'cliente': request.user.email,
                'grandezza': grandezza,
                'citta': form_data['citta'],
            },
        )
        
        # Salva i dati nella sessione per dopo la conferma pagamento
        request.session['pending_shipment'] = {
            'payment_intent_id': payment_intent.id,
            **form_data
        }
        
        # Passa il client_secret al template per confermare il pagamento
        form_context['client_secret'] = payment_intent.client_secret
        form_context['stripe_publishable_key'] = os.getenv('STRIPE_PUBLISHABLE_KEY', '')
        form_context['show_payment_form'] = True
        return render(request, root, form_context)
        
    except stripe.error.StripeError as e:
        messages.error(request, f'Pagamento Stripe non riuscito: {str(e)}')
        return render(request, root, form_context)
    except Exception as e:
        messages.error(request, f'Errore imprevisto nel pagamento: {str(e)}')
        return render(request, root, form_context)


def _handle_cash_payment(request, form_context, form_data):
    """Gestisce il pagamento in contanti. Ritorna la response."""
    root = LEDGER_LOGISTIC_CREASPEDIZIONE_URL
    
    try:
        _crea_spedizione_db(
            request, request.user,
            form_data['indirizzo_consegna'],
            form_data['citta'],
            form_data['cap'],
            form_data['provincia'],
            form_data['grandezza'],
            form_data['descrizione'],
            form_data['metodo_pagamento']
        )
        return redirect('dashboard_cliente')
    except Exception as e:
        messages.error(request, f'Errore durante la creazione della spedizione: {str(e)}')
        return render(request, root, form_context)


@ensure_csrf_cookie
@login_required
def crea_spedizione(request):
    """Vista per la creazione di una nuova spedizione"""
    # Verifica permessi
    if request.user.ruolo != 'cliente':
        messages.error(request, 'Solo i clienti possono creare spedizione.')
        return redirect('home')
    
    root =LEDGER_LOGISTIC_CREASPEDIZIONE_URL
    
    # GET request - mostra il form
    if request.method != 'POST':
        return render(request, root, _build_spedizione_form_context(request))
    
    # POST request - estrai i dati
    form_data = {
        'indirizzo_consegna': request.POST.get('indirizzo_consegna', '').strip(),
        'citta': request.POST.get('citta', '').strip(),
        'cap': request.POST.get('cap', '').strip(),
        'provincia': request.POST.get('provincia', '').strip().upper(),
        'grandezza': request.POST.get('grandezza', ''),
        'descrizione': request.POST.get('descrizione', '').strip(),
        'metodo_pagamento': request.POST.get('metodo_pagamento', 'carta').strip()
    }
    
    form_context = _build_spedizione_form_context(request, **form_data)
    
    # Valida i dati
    errors = _validate_spedizione_form(**form_data)
    if errors:
        for error in errors:
            messages.error(request, error)
        return render(request, root, form_context)
    
    # Processa il pagamento in base al metodo selezionato
    if form_data['metodo_pagamento'] == 'carta':
        return _process_stripe_payment(request, form_data['grandezza'], form_context, form_data)
    
    # Pagamento in contanti
    return _handle_cash_payment(request, form_context, form_data)


def _crea_spedizione_db(request, cliente, indirizzo_consegna, citta, cap, provincia, grandezza, descrizione, metodo_pagamento):
    """Helper per creare spedizione nel database"""
    from .models import Spedizione
    
    # Crea il nuovo oggetto spedizione
    spedizione = Spedizione(
        cliente=cliente,
        indirizzo_consegna=indirizzo_consegna,
        citta=citta,
        cap=cap,
        provincia=provincia,
        grandezza=grandezza,
        descrizione=descrizione,
        metodo_pagamento=metodo_pagamento
    )
    
    # Genera il codice tracciamento
    spedizione.codice_tracciamento = spedizione.genera_codice_tracciamento()
    codice_tracciamento = spedizione.codice_tracciamento
    spedizione.gps = random.random() < 0.9
    # Cerca un corriere disponibile e assegna automaticamente
    corriere_disponibile = trova_corriere_disponibile()
    if corriere_disponibile:
        spedizione.corriere = corriere_disponibile
        spedizione.stato = 'in_consegna'
    else:
        spedizione.stato = 'in_attesa'
    
    # Salva la spedizione nel database
    spedizione.save()

    
    messages.success(
        request,
        f'✅ Spedizione creata! Codice: {codice_tracciamento}. '
        f'{"Pagamento alla consegna." if metodo_pagamento == "cash" else "Pagamento completato."}'
    )
    
    return spedizione

def scarica_fattura(request, spedizione_id):
    """Genera e scarica una fattura PDF elegante per la spedizione"""
    from reportlab.lib import colors
    from datetime import datetime
    
    # Recupera la spedizione dal DB
    spedizione = Spedizione.objects.get(id=spedizione_id)
    
    spedizione.fattura_emessa = True
    spedizione.save()

    # Calcola importo in euro
    importo = SPEDIZIONE_IMPORTI_CENT.get(spedizione.grandezza, 0) / 100

    # Crea buffer in memoria
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # Colori personalizzati
    primary_color = colors.HexColor('#1e3a8a')  # Blu scuro
    secondary_color = colors.HexColor('#3b82f6')  # Blu
    text_color = colors.HexColor('#1f2937')  # Grigio scuro
    light_gray = colors.HexColor('#f3f4f6')
    
    # === HEADER CON LOGO E INTESTAZIONE ===
    logo_path = "Ledger_Logistic/ledger-logistic-logo.png"
    pdf.drawImage(logo_path, 50, height - 120, width=80, height=80, mask='auto')
    
    # Info azienda (destra)
    pdf.setFont("Helvetica-Bold", 16)
    pdf.setFillColor(primary_color)
    pdf.drawRightString(width - 50, height - 60, "LEDGER LOGISTIC")
    pdf.setFont("Helvetica", 9)
    pdf.setFillColor(text_color)
    pdf.drawRightString(width - 50, height - 75, "Via del Trasporto, 123")
    pdf.drawRightString(width - 50, height - 88, "20100 Milano (MI)")
    pdf.drawRightString(width - 50, height - 101, "P.IVA: 12345678901")
    
    # Linea separatrice
    pdf.setStrokeColor(secondary_color)
    pdf.setLineWidth(2)
    pdf.line(50, height - 135, width - 50, height - 135)
    
    # === TITOLO FATTURA ===
    pdf.setFont("Helvetica-Bold", 24)
    pdf.setFillColor(primary_color)
    pdf.drawString(50, height - 170, "FATTURA")
    
    # Numero e data fattura
    pdf.setFont("Helvetica", 10)
    pdf.setFillColor(text_color)
    data_oggi = datetime.now().strftime("%d/%m/%Y")
    pdf.drawRightString(width - 50, height - 165, f"Data: {data_oggi}")
    pdf.drawRightString(width - 50, height - 180, f"N. {spedizione.codice_tracciamento}")
    
    # === DATI CLIENTE (BOX) ===
    y_pos = height - 230
    pdf.setFillColor(light_gray)
    pdf.rect(50, y_pos - 70, 250, 65, fill=True, stroke=False)
    
    pdf.setFont("Helvetica-Bold", 11)
    pdf.setFillColor(primary_color)
    pdf.drawString(60, y_pos - 15, "CLIENTE")
    
    pdf.setFont("Helvetica", 10)
    pdf.setFillColor(text_color)
    pdf.drawString(60, y_pos - 32, f"{spedizione.cliente.get_full_name() or spedizione.cliente.username}")
    pdf.drawString(60, y_pos - 47, f"Email: {spedizione.cliente.email}")
    if spedizione.cliente.phone_number:
        pdf.drawString(60, y_pos - 62, f"Tel: {spedizione.cliente.phone_number}")
    
    # === DETTAGLI SPEDIZIONE (BOX) ===
    y_pos = height - 330
    pdf.setFillColor(light_gray)
    pdf.rect(50, y_pos - 130, width - 100, 125, fill=True, stroke=False)
    
    pdf.setFont("Helvetica-Bold", 11)
    pdf.setFillColor(primary_color)
    pdf.drawString(60, y_pos - 15, "DETTAGLI SPEDIZIONE")
    
    # Tabella dettagli
    pdf.setFont("Helvetica", 10)
    pdf.setFillColor(text_color)
    line_height = 20
    y_detail = y_pos - 40
    
    details = [
        ("Codice Tracciamento:", spedizione.codice_tracciamento),
        ("Destinazione:", f"{spedizione.citta} ({spedizione.provincia})"),
        ("Indirizzo:", spedizione.indirizzo_consegna),
        ("CAP:", spedizione.cap),
        ("Dimensione Pacco:", spedizione.get_grandezza_display().upper()),
        ("Metodo Pagamento:", "Carta di Credito" if spedizione.metodo_pagamento == "carta" else "Contanti")
    ]
    
    for label, value in details:
        pdf.setFont("Helvetica-Bold", 9)
        pdf.drawString(60, y_detail, label)
        pdf.setFont("Helvetica", 9)
        pdf.drawString(220, y_detail, str(value))
        y_detail -= line_height
    
    # === TOTALE (BOX EVIDENZIATO) ===
    y_pos = height - 510
    pdf.setFillColor(secondary_color)
    pdf.rect(50, y_pos - 50, width - 100, 45, fill=True, stroke=False)
    
    pdf.setFont("Helvetica-Bold", 14)
    pdf.setFillColor(colors.white)
    pdf.drawString(60, y_pos - 25, "TOTALE FATTURA")
    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawRightString(width - 60, y_pos - 27, f"€ {importo:.2f}")
    
    # === NOTE ===
    y_pos = height - 590
    pdf.setFont("Helvetica-Bold", 10)
    pdf.setFillColor(primary_color)
    pdf.drawString(50, y_pos, "Note:")
    
    pdf.setFont("Helvetica", 9)
    pdf.setFillColor(text_color)
    pdf.drawString(50, y_pos - 18, "• Fattura generata automaticamente dal sistema Ledger Logistic")
    pdf.drawString(50, y_pos - 33, "• Conservare questa fattura per eventuali reclami o contestazioni")
    if spedizione.metodo_pagamento == "carta":
        pdf.drawString(50, y_pos - 48, "• Pagamento già effettuato con carta di credito")
    else:
        pdf.drawString(50, y_pos - 48, "• Pagamento alla consegna")
    
    # === FOOTER ===
    pdf.setStrokeColor(secondary_color)
    pdf.setLineWidth(1)
    pdf.line(50, 80, width - 50, 80)
    
    pdf.setFont("Helvetica-Bold", 10)
    pdf.setFillColor(primary_color)
    pdf.drawCentredString(width / 2, 60, "Grazie per aver scelto Ledger Logistic!")
    
    pdf.setFont("Helvetica", 8)
    pdf.setFillColor(text_color)
    pdf.drawCentredString(width / 2, 45, "Per assistenza: info@ledgerlogistic.it | Tel: +39 02 1234567")
    pdf.drawCentredString(width / 2, 32, "www.ledgerlogistic.it")

    pdf.showPage()
    pdf.save()

    # Riavvolge buffer e restituisce PDF
    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="fattura_{spedizione.codice_tracciamento}.pdf"'
    return response

@require_POST
def conferma_consegna_cliente(request, spedizione_id):
    spedizione = get_object_or_404(Spedizione, id=spedizione_id)
    spedizione.conferma_cliente = True
    spedizione.save()
    return redirect('dashboard_cliente')

@login_required
def conferma_pagamento_stripe(request):
    # Endpoint per confermare il pagamento dopo Stripe
    if request.method != 'POST':
        return JsonResponse({'error': 'Metodo non consentito'}, status=405)
    
    if 'pending_shipment' not in request.session:
        return JsonResponse({
            'success': False,
            'error': 'Nessuna spedizione in attesa',
            'redirect': reverse(pagamento_fallito) # Serve per usare le rotte di django
        }, status=400)
    
    pending = request.session['pending_shipment']
    
    try:
        spedizione = _crea_spedizione_db(
            request,
            request.user,
            pending['indirizzo_consegna'],
            pending['citta'],
            pending['cap'],
            pending['provincia'],
            pending['grandezza'],
            pending['descrizione'],
            pending['metodo_pagamento']
        )
        
        # Salva i dati per la pagina di conferma
        request.session['payment_success'] = {
            'codice_tracciamento': spedizione.codice_tracciamento,
            'citta': spedizione.citta,
            'provincia': spedizione.provincia,
            'indirizzo_consegna': spedizione.indirizzo_consegna,
            'grandezza': spedizione.grandezza,
            'importo': f"{SPEDIZIONE_IMPORTI_CENT[spedizione.grandezza] / 100:.2f}"
        }
        
        # Aggiorna la variabile solo se pagamento con carta (se lo metto qui vuol dire che il pagamento è andato a buon fine)
        if spedizione.metodo_pagamento == 'carta':
            spedizione.conferma_del_gestore_di_pagamento = True
            spedizione.save()
        
        # Genera e scarica la fattura solo dopo che il pagamento è andato a buon fine
        scarica_fattura(request, spedizione.id)  
        
        del request.session['pending_shipment']
        return JsonResponse({
            'success': True, 
            'redirect': reverse(pagamento_confermato)
            })
    
    except Exception as e:
        # Aggiorna la variabile solo se pagamento con carta
        if 'spedizione' in locals() and spedizione.metodo_pagamento == 'carta':
            spedizione.conferma_del_gestore_di_pagamento = False
            spedizione.save()
        
        request.session['payment_error'] = str(e)
        return JsonResponse({
            'success': False,
            'redirect': reverse(pagamento_fallito),
            'error': str(e)
        })


@login_required
def pagamento_confermato(request):
    # Mostra la pagina di pagamento completato con successo
    if 'payment_success' not in request.session:
        messages.warning(request, 'Nessun pagamento da confermare.')
        return redirect('dashboard_cliente')
    
    payment_data = request.session['payment_success']
    del request.session['payment_success']
    
    context = {
        'company_name': COMPANY_NAME,
        'success': True,
        'codice_tracciamento': payment_data['codice_tracciamento'],
        'citta': payment_data['citta'],
        'provincia': payment_data['provincia'],
        'indirizzo_consegna': payment_data['indirizzo_consegna'],
        'grandezza': payment_data['grandezza'],
        'importo': payment_data['importo']
    }
    return render(request, 'Ledger_Logistic/pagamento_conferma.html', context)


@login_required
def pagamento_fallito(request):
    """Mostra la pagina di pagamento fallito"""
    error_message = None
    if 'payment_error' in request.session:
        error_message = request.session['payment_error']
        del request.session['payment_error']
    
    context = {
        'company_name': COMPANY_NAME,
        'success': False,
        'error_message': error_message
    }
    return render(request, 'Ledger_Logistic/pagamento_conferma.html', context)



@login_required
def completa_consegna(request, codice_tracciamento):
    # Vista per completare una consegna e assegnare automaticamente il prossimo spedizione
    # Verifica che l'utente sia un corriere
    if request.user.ruolo != 'corriere':
        messages.error(request, 'Solo i corrieri possono completare consegne.')
        return redirect('home')
    
    # Richiede POST
    if request.method != 'POST':
        messages.error(request, 'Metodo non consentito.')
        return redirect('dashboard_corriere')
    
    from .models import Spedizione
    
    try:
        # Recupera la spedizione da consegnare
        spedizione = Spedizione.objects.get(
            codice_tracciamento=codice_tracciamento,
            corriere=request.user
        )
        
        # Logica a tre stati per traffico e veicolo_disponibile:
        # - Se radio button selezionato 'true' -> True
        # - Se radio button selezionato 'false' -> False  
        # - Se nessun radio button selezionato -> None (NULL)
        
        traffico_value = request.POST.get('traffico', None)
        veicolo_value = request.POST.get('veicolo_disponibile', None)
        meteo_value = request.POST.get('meteo_sfavorevole', None) 
        
        # Converti in Boolean o None
        if traffico_value == 'true':
            spedizione.traffico = True
        elif traffico_value == 'false':
            spedizione.traffico = False
        else:
            spedizione.traffico = None
        
        if veicolo_value == 'true':
            spedizione.veicolo_disponibile = True
        elif veicolo_value == 'false':
            spedizione.veicolo_disponibile = False
        else:
            spedizione.veicolo_disponibile = None
        
        if meteo_value == 'true':
            spedizione.meteo_sfavorevole = True
        elif meteo_value == 'false':
            spedizione.meteo_sfavorevole = False
        else:
            spedizione.meteo_sfavorevole = None

        # Marca come consegnato
        spedizione.stato = 'consegnato'
        spedizione.save()
        
        messages.success(
            request,
            f'✅ Consegna completata per la spedizione {codice_tracciamento}!'
        )
        
        # Cerca e assegna automaticamente un nuovo spedizione
        nuova_spedizione = assegna_spedizione_a_corriere(request.user)
        
        if nuova_spedizione:
            messages.success(
                request,
                f'📦 Nuovo spedizione assegnato: {nuova_spedizione.codice_tracciamento} - Destinazione: {nuova_spedizione.citta}'
            )
        else:
            messages.info(
                request,
                'ℹ️ Nessuna nuova spedizione disponibile al momento.'
            )
        
        return redirect('dashboard_corriere')
        
    except Spedizione.DoesNotExist:
        messages.error(request, 'spedizione non trovata o non autorizzata.')
        return redirect('dashboard_corriere')
    except Exception as e:
        messages.error(request, f'Errore durante il completamento della consegna: {str(e)}')
        return redirect('dashboard_corriere')


@login_required
def accetta_spedizione(request, codice_tracciamento):
    """Vista per accettare una spedizione (gestore)"""
    if request.user.ruolo != 'gestore':
        messages.error(request, 'Solo i gestori possono accettare spedizione.')
        return redirect('home')
    
    from .models import Spedizione
    
    try:
        spedizione = Spedizione.objects.get(codice_tracciamento=codice_tracciamento)
        
        # Cambia stato da in_attesa a in_elaborazione
        if spedizione.stato == 'in_attesa':
            spedizione.stato = 'in_elaborazione'
            spedizione.save()
            messages.success(request, f'✅ Spedizione {codice_tracciamento} accettata!')
        else:
            messages.warning(request, f'La spedizione {codice_tracciamento} non è in stato "In Attesa".')
        
    except Spedizione.DoesNotExist:
        messages.error(request, 'Spedizione non trovata.')
    except Exception as e:
        messages.error(request, f'Errore: {str(e)}')
    
    return redirect('dashboard_gestore')


@login_required
def rifiuta_spedizione(request, codice_tracciamento):
    """Vista per rifiutare una spedizione (gestore)"""
    if request.user.ruolo != 'gestore':
        messages.error(request, 'Solo i gestori possono rifiutare spedizione.')
        return redirect('home')
    
    from .models import Spedizione
    
    try:
        spedizione = Spedizione.objects.get(codice_tracciamento=codice_tracciamento)
        
        # Cambia stato a annullato
        if spedizione.stato in ['in_attesa', 'in_elaborazione']:
            spedizione.stato = 'annullato'
            spedizione.save()
            messages.success(request, f'❌ Spedizione {codice_tracciamento} rifiutata.')
        else:
            messages.warning(request, f'La spedizione {codice_tracciamento} non può essere rifiutata.')
        
    except Spedizione.DoesNotExist:
        messages.error(request, 'Spedizione non trovata.')
    except Exception as e:
        messages.error(request, f'Errore: {str(e)}')
    
    return redirect('dashboard_gestore')

@login_required
def view_gestione_reclami(request):
    context = {
        'reclami': Reclamo.objects.all().order_by('data_creazione'),
        'ReclamiAttivi': Reclamo.objects.filter(risolto=False).count(),
        'ReclamiRisolti': Reclamo.objects.filter(risolto=True).count(),
    }
    return render(request, 'Ledger_Logistic/gestione_reclami.html', context)

@login_required
def invia_reclamo(request, spedizione_id):
    
    #prendo la spedizione associata al reclamo (recuperato dalla dashboard cliente)
    spedizione = get_object_or_404(
        Spedizione,
        id=spedizione_id,
        cliente=request.user
    )

    #quando clicco su invia reclamo nel form per fare il submit
    if request.method == 'POST':
        nome_reclamo = request.POST.get('nomeReclamo') #prendo il valore selezionato nella select
        descrizione = request.POST.get('descrizione') #prendo il valore scritto nella textarea

        if not nome_reclamo or not descrizione:
            return render(request, LEDGER_LOGISTIC_INVIARECLAMO_URL, {
                'spedizione': spedizione,
                'errore': 'Compila tutti i campi'
            })

        # Mappatura  nomeReclamo -> id evento
        mapping_eventi = {
            'Spedizione non effettuata correttamente': 1,
            #'Verifica pagamento': 2, # Rimosso perché non va nel cliente
            'Ritardo di consegna': 3,
        }

        # Recupera l'id evento corrispondente al nomeReclamo selezionato nella select
        evento_id = mapping_eventi.get(nome_reclamo)
        if not evento_id:
            return render(request, LEDGER_LOGISTIC_INVIARECLAMO_URL, {
                'spedizione': spedizione,
                'errore': 'Tipo di reclamo non valido'
            })

        #istanzio oggetto Evento con quell'id
        evento = get_object_or_404(Evento, id=evento_id)

        # Creazione del reclamo nel database con tutti i dati necessari e evento corrispondente
        Reclamo.objects.create(
            nomeReclamo=nome_reclamo,
            evento=evento,
            descrizione=descrizione,
            spedizione=spedizione,
            esito='Non verificato'
        )

        return redirect('dashboard_cliente')

    return render(request, LEDGER_LOGISTIC_INVIARECLAMO_URL, {
        'spedizione': spedizione
    })
    
def gestisci_reclamo(request, id_reclamo):

    context = {
        'reclamo': get_object_or_404(Reclamo, id=id_reclamo)
    }
    return render(request, 'Ledger_Logistic/decisione_reclamo_gestore.html', context)

def gestione_spedizioni(request):
    context = {
        'spedizioni': Spedizione.objects.all().order_by('data_creazione'),
        'spedizioni_in_corso': Spedizione.objects.filter(stato__in=['in_attesa', 'in_elaborazione', 'in_transito', 'in_consegna']).count(),
        'spedizioni_consegnate': Spedizione.objects.filter(stato='consegnato').count(),
    }   
    
    return render(request, 'Ledger_Logistic/gestione_spedizioni_e_pagamenti.html', context)

def dettaglio_spedizione(request, spedizione_id):
    
    context = {
        'spedizione': get_object_or_404(Spedizione, id=spedizione_id)
    }
    return render(request, 'Ledger_Logistic/dettaglio_spedizione.html', context)
    
def verifica_reclamo(id_reclamo):
    from Ledger_Logistic.Blockchain.export_probability import calcola_probabilita
    
    return JsonResponse({
        "esito": calcola_probabilita(id_reclamo),
    })
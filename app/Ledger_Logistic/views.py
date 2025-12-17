from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login as django_login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import TentativiDiLogin, TentativiRecuperoPassword, CodiceOTP,Evento, Prova
from django.utils import timezone
from django.db import IntegrityError
from django.core.mail import send_mail
from django.conf import settings
from .blockchain import get_contract, is_connected, send_transaction
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.http import require_POST
from django.http import JsonResponse, FileResponse
import os
import json

# Ottieni il modello User personalizzato
Utente = get_user_model()

# Costanti
COMPANY_NAME = 'Ledger Logistics'


def home(request):
    # Se l'utente cerca un pacco (logica base)
    tracking_code = request.GET.get('tracking_code')
    context = {
        'company_name': COMPANY_NAME,
        'tracking_code': tracking_code
    }
    return render(request, 'Ledger_Logistic/home.html', context)


def servizi(request):
    """Vista per la pagina servizi"""
    context = {
        'company_name': COMPANY_NAME
    }
    return render(request, 'Ledger_Logistic/servizi.html', context)


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
                subject='Codice OTP - Ledger Logistic',
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
    return redirect('home')


def _handle_incorrect_otp(request, login_attempt):
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
    
    return _handle_incorrect_otp(request, login_attempt)


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
        result = _process_otp_verification(request, email, codice_inserito)
        if result:
            return result
    
    # Calcola tentativi rimanenti e mostra form
    otp_remaining_attempts = 5 - login_attempt.otp_failed_attempts
    
    return render(request, 'Ledger_Logistic/verify_otp.html', {
        'email': email,
        'otp_remaining_attempts': otp_remaining_attempts,
        'otp_failed_attempts': login_attempt.otp_failed_attempts
    })


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

@login_required
def invia_probabilita_blockchain(request, prova_id):
    """
    Recupera le probabilità da una Prova e le invia allo smart contract
    
    Args:
        prova_id: ID della prova da inviare
    """
    # Verifica connessione blockchain
    if not is_connected():
        messages.error(request, '❌ Blockchain non disponibile')
        return redirect('home')
    
    try:
        # Recupera la prova dal database
        prova = Prova.objects.select_related(
            'idEvento1', 'idEvento2', 'idEvento3'
        ).get(id=prova_id)
        
        # Prepara i dati delle probabilità
        probabilita_priori = []
        nomi_eventi = []
        
        # Aggiungi eventi se esistono
        if prova.idEvento1:
            probabilita_priori.append(int(prova.idEvento1.probabilita_priori * 100))
            nomi_eventi.append(prova.idEvento1.nomeEvento)
        
        if prova.idEvento2:
            probabilita_priori.append(int(prova.idEvento2.probabilita_priori * 100))
            nomi_eventi.append(prova.idEvento2.nomeEvento)
        
        if prova.idEvento3:
            probabilita_priori.append(int(prova.idEvento3.probabilita_priori * 100))
            nomi_eventi.append(prova.idEvento3.nomeEvento)
        
        # Probabilità condizionata (moltiplicata per 100 per evitare decimali)
        prob_condizionata = int(prova.probabilita_condizionata * 100)
        
        # Ottieni il contratto
        contract = get_contract()
        
        # Chiama la funzione del contratto (adatta il nome alla tua funzione)
        # Esempio: contract.functions.salvaProbabilita(nomeProva, probabilitaPriori[], probCondizionata)
        success, tx_hash, error = send_transaction(
            contract.functions.salvaProbabilita,
            prova.nomeProva,
            probabilita_priori,
            prob_condizionata
        )
        
        if success:
            messages.success(
                request, 
                f'✅ Probabilità inviate alla blockchain!\n'
                f'TX Hash: {tx_hash}\n'
                f'Prova: {prova.nomeProva}\n'
                f'Eventi: {", ".join(nomi_eventi)}'
            )
        else:
            messages.error(request, f'❌ Errore nell\'invio: {error}')
            
    except Prova.DoesNotExist:
        messages.error(request, '❌ Prova non trovata')
    except Exception as e:
        messages.error(request, f'❌ Errore: {str(e)}')
    
    return redirect('home')


@login_required
def invia_tutte_probabilita_blockchain(request):
    """
    Invia tutte le prove non ancora inviate alla blockchain
    """
    if not is_connected():
        messages.error(request, '❌ Blockchain non disponibile')
        return redirect('home')
    
    try:
        # Recupera tutte le prove
        prove = Prova.objects.select_related(
            'idEvento1', 'idEvento2', 'idEvento3'
        ).all()
        
        successi = 0
        errori = 0
        
        for prova in prove:
            # Prepara i dati
            probabilita_priori = []
            
            if prova.idEvento1:
                probabilita_priori.append(int(prova.idEvento1.probabilita_priori * 100))
            if prova.idEvento2:
                probabilita_priori.append(int(prova.idEvento2.probabilita_priori * 100))
            if prova.idEvento3:
                probabilita_priori.append(int(prova.idEvento3.probabilita_priori * 100))
            
            prob_condizionata = int(prova.probabilita_condizionata * 100)
            
            # Invia al contratto
            contract = get_contract()
            success, _ , error = send_transaction(
                contract.functions.salvaProbabilita,
                prova.nomeProva,
                probabilita_priori,
                prob_condizionata
            )
            
            if success:
                successi += 1
            else:
                errori += 1
                print(f"Errore per prova {prova.nomeProva}: {error}")
        
        messages.success(
            request,
            f'✅ Invio completato!\n'
            f'Successi: {successi}\n'
            f'Errori: {errori}'
        )
        
    except Exception as e:
        messages.error(request, f'❌ Errore: {str(e)}')
    
    return redirect('home')


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
    result, remaining_attempts = _handle_incorrect_reset_otp(request, recovery_attempt)
    if result:
        return result
    
    return render(request, root, {
        'email': email,
        'remaining_attempts': remaining_attempts,
        'otp_failed_attempts': recovery_attempt.otp_failed_attempts
    })


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
    
    if not new_password or not confirm_password:
        messages.error(request, 'Entrambi i campi sono obbligatori.')
        return render(request, root, {'email': email})
    
    if new_password != confirm_password:
        messages.error(request, 'Le password non corrispondono.')
        return render(request, root, {'email': email})
    
    import re
    
    errors = []
    if len(new_password) < 8:
        errors.append('La password deve essere lunga almeno 8 caratteri')
    if not re.search(r'[A-Z]', new_password):
        errors.append('Deve contenere almeno una lettera maiuscola')
    if not re.search(r'[a-z]', new_password):
        errors.append('Deve contenere almeno una lettera minuscola')
    if not re.search(r'\d', new_password):
        errors.append('Deve contenere almeno un numero')
    if not re.search(r'[!@#$%^&*(),.?":{}|<>+]', new_password):
        errors.append('Deve contenere almeno un carattere speciale (!@#$%^&*(),.?":{}|<>+)')
    
    if errors:
        for error in errors:
            messages.error(request, f'❌ {error}')
        return render(request, root, {'email': email})
    
    try:
        user = Utente.objects.get(email=email)
        user.set_password(new_password)
        user.save()
        
        _clear_reset_password_session(request)
        
        messages.success(
            request,
            '✅ Password aggiornata con successo! Ora puoi effettuare il login con la nuova password.'
        )
        return redirect('login')
        
    except Utente.DoesNotExist:
        messages.error(request, 'Errore: utente non trovato.')
        return redirect('reset_password')
    except Exception as e:
        messages.error(request, f'Errore durante l\'aggiornamento della password: {str(e)}')
        return render(request, root, {'email': email})


@staff_member_required
@require_POST
def download_contract(request):
    """Scarica un file contratto"""
    data = json.loads(request.body)
    filepath = data.get('filepath', '')
    
    if os.path.isfile(filepath) and filepath.endswith('.sol'):
        return FileResponse(open(filepath, 'rb'), as_attachment=True)
    return JsonResponse({'error': 'File non trovato'}, status=404)


@staff_member_required
@require_POST
def edit_contract(request):
    """Modifica un file contratto"""
    data = json.loads(request.body)
    filename = data.get('filename', '')
    content = data.get('content', '')
    
    folder_path = os.path.join(settings.BASE_DIR, '..', 'contracts')
    file_path = os.path.join(folder_path, filename)
    
    if filename.endswith('.sol') and os.path.isfile(file_path):
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'File non valido'})


@staff_member_required
@require_POST
def deploy_contract(request):
    """Deploy di un contratto sulla blockchain"""
    from .blockchain import is_connected
    
    data = json.loads(request.body)
    filename = data.get('filename', '')
    params = data.get('params', {})
    
    folder_path = os.path.join(settings.BASE_DIR, '..', 'contracts')
    file_path = os.path.join(folder_path, filename)
    
    if not filename.endswith('.sol') or not os.path.isfile(file_path):
        return JsonResponse({'success': False, 'error': 'File non valido'})
    
    if not is_connected():
        return JsonResponse({'success': False, 'error': 'Blockchain non disponibile'})
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            contract_code = f.read()
        
        contract_name = filename.replace('.sol', '')
        
        success, contract_address, tx_hash, error = deploy_solidity_contract(
            contract_name, 
            contract_code,
            params
        )
        
        if success:
            return JsonResponse({
                'success': True,
                'contract_address': contract_address,
                'tx_hash': tx_hash
            })
        return JsonResponse({'success': False, 'error': error})
            
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


def deploy_solidity_contract(contract_name, contract_code, deploy_params):
    """Funzione helper per il deploy dei contratti"""
    # TODO: Implementare la logica di deploy usando contract_name, contract_code e deploy_params
    # Esempio: compilare con solc, deployare con web3.py
    return (False, None, None, f"Deploy non implementato per {contract_name} - configurare la logica blockchain")
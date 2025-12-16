from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login as django_login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import TentativiDiLogin
from django.utils import timezone
from django.db import IntegrityError

# Ottieni il modello User personalizzato
Utente = get_user_model()


def home(request):
    # Se l'utente cerca un pacco (logica base)
    tracking_code = request.GET.get('tracking_code')
    context = {
        'company_name': 'Ledger Logistic',
        'tracking_code': tracking_code
    }
    return render(request, 'Ledger_Logistic/home.html', context)


def custom_login(request):
    """
    Vista di login personalizzata con contatore di tentativi falliti.
    Blocca l'utente dopo 5 tentativi falliti per 30 minuti.
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
        # Login riuscito - reset del contatore
        login_attempt.reset_attempts()
        django_login(request, user)
        messages.success(request, f'Benvenuto {user.username}!')
        return redirect('home')
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


def custom_logout(request):
    """Vista personalizzata per il logout"""
    logout(request)
    messages.info(request, 'Logout effettuato con successo.')
    return redirect('login')


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
        f'Account creato con successo! Benvenuto {username}, puoi ora effettuare il login con la tua email.'
    )
    return redirect('login')




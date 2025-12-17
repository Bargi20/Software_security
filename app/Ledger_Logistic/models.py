from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.utils import timezone
from datetime import timedelta
import random


# ============= CUSTOM USER MANAGER =============

class UtenteManager(BaseUserManager):
    """Manager personalizzato per il modello Utente"""
    
    def create_user(self, email, username, password=None, **extra_fields):
        """Crea e salva un utente normale"""
        if not email:
            raise ValueError('L\'email è obbligatoria')
        if not username:
            raise ValueError('Lo username è obbligatorio')
        
        email = self.normalize_email(email)
        user = self.model(email=email, username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, username, password=None, **extra_fields):
        """Crea e salva un superuser"""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Il superuser deve avere is_staff=True')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Il superuser deve avere is_superuser=True')
        
        return self.create_user(email, username, password, **extra_fields)


# ============= CUSTOM USER MODEL =============

class Utente(AbstractBaseUser, PermissionsMixin):
    """Modello User personalizzato che usa email per l'autenticazione"""
    
    email = models.EmailField(max_length=254, unique=True, verbose_name='Email')
    username = models.CharField(max_length=150, unique=True, verbose_name='Username')
    first_name = models.CharField(max_length=30, blank=True, verbose_name='Nome')
    last_name = models.CharField(max_length=30, blank=True, verbose_name='Cognome')
    phone_number = models.CharField(max_length=15, blank=True, verbose_name='Telefono')
    address = models.TextField(blank=True, verbose_name='Indirizzo')
    data_nascita = models.DateField(blank=True, null=True, verbose_name='Data di nascita')
    
    is_active = models.BooleanField(default=True, verbose_name='Attivo')
    is_staff = models.BooleanField(default=False, verbose_name='Staff')
    date_joined = models.DateTimeField(default=timezone.now, verbose_name='Data registrazione')
    
    objects = UtenteManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    
    class Meta:
        verbose_name = "Utente"
        verbose_name_plural = "Utenti"
    
    def __str__(self):
        return self.email
    
    def get_full_name(self):
        """Ritorna nome e cognome"""
        return f"{self.first_name} {self.last_name}".strip()
    
    def get_short_name(self):
        """Ritorna il nome"""
        return self.first_name


# ============= LOGIN ATTEMPT MODEL =============

class TentativiDiLogin(models.Model):
    """Modello per tracciare i tentativi di login falliti tramite email"""
    email = models.EmailField(max_length=254, unique=True)
    failed_attempts = models.IntegerField(default=0)
    last_attempt = models.DateTimeField(auto_now=True)
    is_blocked = models.BooleanField(default=False)
    blocked_until = models.DateTimeField(null=True, blank=True)
    
    # Tentativi OTP separati
    otp_failed_attempts = models.IntegerField(default=0)
    otp_is_blocked = models.BooleanField(default=False)
    otp_blocked_until = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Tentativo di Login"
        verbose_name_plural = "Tentativi di Login"
    
    def __str__(self):
        return f"{self.email} - {self.failed_attempts} tentativi"
    
    def increment_failed_attempts(self):
        """Incrementa il contatore dei tentativi falliti"""
        self.failed_attempts += 1
        if self.failed_attempts >= 5:
            self.is_blocked = True
            #Blocco di 30 min
            self.blocked_until = timezone.now() + timedelta(minutes=30)
        self.save()
    
    def increment_otp_failed_attempts(self):
        """Incrementa il contatore dei tentativi OTP falliti"""
        self.otp_failed_attempts += 1
        if self.otp_failed_attempts >= 5:
            self.otp_is_blocked = True
            self.otp_blocked_until = timezone.now() + timedelta(minutes=30)
        self.save()
    
    def reset_attempts(self):
        """Reset del contatore dopo login riuscito"""
        self.failed_attempts = 0
        self.is_blocked = False
        self.blocked_until = None
        self.save()
    
    def reset_otp_attempts(self):
        """Reset del contatore OTP"""
        self.otp_failed_attempts = 0
        self.otp_is_blocked = False
        self.otp_blocked_until = None
        self.save()
    
    def is_account_blocked(self):
        """Controlla se l'account è bloccato (password)"""
        if self.is_blocked:
            if self.blocked_until and timezone.now() > self.blocked_until:
                self.reset_attempts()
                return False
            return True
        return False
    
    def is_otp_blocked(self):
        """Controlla se l'OTP è bloccato"""
        if self.otp_is_blocked:
            if self.otp_blocked_until and timezone.now() > self.otp_blocked_until:
                self.reset_otp_attempts()
                return False
            return True
        return False


# ============= PASSWORD RECOVERY ATTEMPT MODEL =============

class TentativiRecuperoPassword(models.Model):
    """Modello per tracciare i tentativi di recupero password tramite email"""
    email = models.EmailField(max_length=254, unique=True)
    failed_attempts = models.IntegerField(default=0)
    last_attempt = models.DateTimeField(auto_now=True)
    is_blocked = models.BooleanField(default=False)
    blocked_until = models.DateTimeField(null=True, blank=True)
    
    # Tentativi OTP separati
    otp_failed_attempts = models.IntegerField(default=0)
    otp_is_blocked = models.BooleanField(default=False)
    otp_blocked_until = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Tentativo di Recupero Password"
        verbose_name_plural = "Tentativi di Recupero Password"
    
    def __str__(self):
        return f"{self.email} - {self.failed_attempts} tentativi recupero"
    
    def increment_failed_attempts(self):
        """Incrementa il contatore dei tentativi falliti"""
        self.failed_attempts += 1
        if self.failed_attempts >= 5:
            self.is_blocked = True
            self.blocked_until = timezone.now() + timedelta(minutes=30)
        self.save()
    
    def increment_otp_failed_attempts(self):
        """Incrementa il contatore dei tentativi OTP falliti"""
        self.otp_failed_attempts += 1
        if self.otp_failed_attempts >= 5:
            self.otp_is_blocked = True
            self.otp_blocked_until = timezone.now() + timedelta(minutes=30)
        self.save()
    
    def reset_attempts(self):
        """Reset del contatore dopo richiesta riuscita"""
        self.failed_attempts = 0
        self.is_blocked = False
        self.blocked_until = None
        self.save()
    
    def reset_otp_attempts(self):
        """Reset del contatore OTP"""
        self.otp_failed_attempts = 0
        self.otp_is_blocked = False
        self.otp_blocked_until = None
        self.save()
    
    def is_account_blocked(self):
        """Controlla se il recupero password è bloccato"""
        if self.is_blocked:
            if self.blocked_until and timezone.now() > self.blocked_until:
                self.reset_attempts()
                return False
            return True
        return False
    
    def is_otp_blocked(self):
        """Controlla se l'OTP è bloccato"""
        if self.otp_is_blocked:
            if self.otp_blocked_until and timezone.now() > self.otp_blocked_until:
                self.reset_otp_attempts()
                return False
            return True
        return False


# ============= OTP CODE MODEL =============

class CodiceOTP(models.Model):
    """Modello per codici OTP temporanei inviati via email"""
    utente = models.ForeignKey(Utente, on_delete=models.CASCADE, related_name='codici_otp')
    codice = models.CharField(max_length=6)
    creato_il = models.DateTimeField(auto_now_add=True)
    scade_il = models.DateTimeField()
    usato = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = "Codice OTP"
        verbose_name_plural = "Codici OTP"
        ordering = ['-creato_il']
    
    def __str__(self):
        return f"OTP per {self.utente.email} - {self.codice}"
    
    @classmethod
    def genera_codice(cls, utente, durata_minuti=5):
        """Genera un nuovo codice OTP di 6 cifre"""
        codice = ''.join([str(random.randint(0, 9)) for _ in range(6)])
        scadenza = timezone.now() + timedelta(minutes=durata_minuti)
        
        return cls.objects.create(
            utente=utente,
            codice=codice,
            scade_il=scadenza
        )
    
    def is_valido(self):
        """Verifica se il codice è ancora valido"""
        return not self.usato and timezone.now() < self.scade_il
    
    def verifica(self, codice_inserito):
        """Verifica e marca come usato se corretto"""
        if self.is_valido() and self.codice == codice_inserito:
            self.usato = True
            self.save()
            return True
        return False

class Evento(models.Model):
    """Modello per tracciare eventi per l'oracolo bayesiano"""
    nomeEvento = models.CharField(max_length=100)
    probabilita_priori = models.FloatField()  # Rimuovi max_length
    
    class Meta:
        verbose_name = "Evento per oracolo"
        verbose_name_plural = "Eventi per oracolo"
    
    def __str__(self):
        return f"{self.nomeEvento} - {self.probabilita_priori}"
    
class Prova(models.Model):
    """Prova per l'oracolo bayesiano"""
    nomeProva = models.CharField(max_length=100)
    prob1 = models.BooleanField(default=False, null=True, blank=True)
    prob2 = models.BooleanField(default=False, null=True, blank=True)
    prob3 = models.BooleanField(default=False, null=True, blank=True)
    idEvento1 = models.ForeignKey(
        Evento, 
        on_delete=models.CASCADE, 
        related_name='prove_evento1',  # Cambiato
        null=True, 
        blank=True
    )
    idEvento2 = models.ForeignKey(
        Evento, 
        on_delete=models.CASCADE, 
        related_name='prove_evento2',  # Cambiato
        null=True,
        blank=True
    )
    idEvento3 = models.ForeignKey(
        Evento, 
        on_delete=models.CASCADE, 
        related_name='prove_evento3',  # Cambiato
        null=True,
        blank=True
    )
    probabilita_condizionata = models.FloatField()  # Rimuovi max_length
    
    class Meta:
        verbose_name = "Prova per oracolo"
        verbose_name_plural = "Prove per oracolo"
    
    def __str__(self):
        return f"{self.nomeProva} - {self.probabilita_condizionata}"


# ============= MESSAGGIO CONTATTO MODEL =============

class MessaggioContatto(models.Model):
    """Modello per salvare i messaggi inviati tramite il form contatti"""
    nome = models.CharField(max_length=200, verbose_name='Nome e Cognome')
    email = models.EmailField(max_length=254, verbose_name='Email')
    telefono = models.CharField(max_length=20, blank=True, verbose_name='Telefono')
    servizio = models.CharField(max_length=50, blank=True, verbose_name='Servizio di interesse')
    messaggio = models.TextField(verbose_name='Messaggio')
    data_invio = models.DateTimeField(auto_now_add=True, verbose_name='Data invio')
    letto = models.BooleanField(default=False, verbose_name='Letto')
    
    class Meta:
        verbose_name = "Messaggio di Contatto"
        verbose_name_plural = "Messaggi di Contatto"
        ordering = ['-data_invio']
    
    def __str__(self):
        return f"{self.nome} - {self.email} ({self.data_invio.strftime('%d/%m/%Y %H:%M')})"
    
    def mark_as_read(self):
        """Segna il messaggio come letto"""
        self.letto = True
        self.save()

# In models.py, aggiungi:
class FileViewer(models.Model):
    """Modello dummy per visualizzare file nella dashboard admin"""
    
    class Meta:
        verbose_name = "Visualizzatore File"
        verbose_name_plural = "Visualizzatore File"
        managed = False  # Non crea tabella nel database
        app_label = 'Ledger_Logistic'
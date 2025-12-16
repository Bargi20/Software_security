from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.utils import timezone
from datetime import timedelta


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
    
    USERNAME_FIELD = 'email'  # Campo usato per il login
    REQUIRED_FIELDS = ['username']  # Campi obbligatori oltre a email e password
    
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
    email = models.EmailField(max_length=254)
    failed_attempts = models.IntegerField(default=0)
    last_attempt = models.DateTimeField(auto_now=True)
    is_blocked = models.BooleanField(default=False)
    blocked_until = models.DateTimeField(null=True, blank=True)
    
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
            # Blocca per 30 minuti
            self.blocked_until = timezone.now() + timedelta(minutes=30)
        self.save()
    
    def reset_attempts(self):
        """Reset del contatore dopo login riuscito"""
        self.failed_attempts = 0
        self.is_blocked = False
        self.blocked_until = None
        self.save()
    
    def is_account_blocked(self):
        """Controlla se l'account è bloccato"""
        if self.is_blocked:
            if self.blocked_until and timezone.now() > self.blocked_until:
                # Il tempo di blocco è scaduto, sblocca
                self.reset_attempts()
                return False
            return True
        return False

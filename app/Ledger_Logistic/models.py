from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

# Create your models here.

class LoginAttempt(models.Model):
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
    

class UserProfile(models.Model):
    """Estende il modello User per informazioni aggiuntive"""
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone_number = models.CharField(max_length=15, blank=True, null=False)
    address = models.TextField(blank=True, null=False, default='')
    data = models.DateField(blank=True, null=True)
    email = models.EmailField(blank=True, null=False, default='non definita')

    def __str__(self):
        return self.user.username

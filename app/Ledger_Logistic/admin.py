from django_otp.admin import OTPAdminSite
from django.contrib import admin

admin.site.__class__ = OTPAdminSite

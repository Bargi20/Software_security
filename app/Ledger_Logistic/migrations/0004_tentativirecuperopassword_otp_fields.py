# Generated manually for adding OTP fields to TentativiRecuperoPassword model

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Ledger_Logistic', '0003_tentativirecuperopassword'),
    ]

    operations = [
        migrations.AddField(
            model_name='tentativirecuperopassword',
            name='otp_failed_attempts',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='tentativirecuperopassword',
            name='otp_is_blocked',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='tentativirecuperopassword',
            name='otp_blocked_until',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]

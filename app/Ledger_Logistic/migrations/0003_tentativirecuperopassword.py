# Generated manually for adding TentativiRecuperoPassword model

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Ledger_Logistic', '0002_alter_prova_prob1_alter_prova_prob2_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='TentativiRecuperoPassword',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('email', models.EmailField(max_length=254, unique=True)),
                ('failed_attempts', models.IntegerField(default=0)),
                ('last_attempt', models.DateTimeField(auto_now=True)),
                ('is_blocked', models.BooleanField(default=False)),
                ('blocked_until', models.DateTimeField(blank=True, null=True)),
            ],
            options={
                'verbose_name': 'Tentativo di Recupero Password',
                'verbose_name_plural': 'Tentativi di Recupero Password',
            },
        ),
    ]

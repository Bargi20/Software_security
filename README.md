# Azienda di spedizioni - Ledger Logistic 📦

<p align="center">
  <img src="/ledger-logistic-logo.png" width="350">
</p>

Questo progetto ha l'obiettivo di sviluppare un software di gestione per un ipotetica azienda di spedizioni. Esso si basa su alcune tecnologie come le blockchain e gli smart contract per aumentare la sicurezza e la trasparenza del software e del funzionamento dell'azienda.


## Istruzioni per avviare il server

Per far partire **Django**:

1) Da terminale spostarsi nella cartella app e digitare:
        1.1) per Mac/Linux: python3 -m venv venv
        1.2) per Windows: python -m venv venv

2) Attivate lo script activate.ps1 per avviare venv:
        2.1) per Mac/Linux: source venv/bin/activate (Fallo dal terminale, non powershell)
        2.2) per Windows: ./venv/Scripts/activate.ps1

3) Esegui:
        pip install -r requirements.txt

4) Digitare questo per avviare il server:
        python manage.py runserver

5) Creare fie .env (in \app) con dentro:
SUPABASE_DB_URL=postgresql://postgres.hoecofcgyqyknqmcwwtt:sekqyw-texkIm-5gakhe@aws-1-eu-west-1.pooler.supabase.com:6543/postgres
SECRET_KEY= 'django-insecure-=@n2r*1%_7s^8i*2t3i^#^_bou*2v^^a0cy0mmtbcptj@vw^'
EMAIL_HOST='smtp.gmail.com'
EMAIL_PORT=587
EMAIL_HOST_USER='ledgerlogistics1@gmail.com'
EMAIL_HOST_PASSWORD='opdb mtam eddn igvm'
DEFAULT_FROM_EMAIL = 'ledgerlogistics1@gmail.com'
BESU_RPC_URL="http://localhost:8545"
BESU_PRIVATE_KEYS=["0x8f2a55949038a9610f50fb23b5883af3b4ecb3c3bb792cbcefbd1542c692be63","0xc87509a1c067bbde78beb793e6fa76530b6382a4c0241e5e4a9ec0a0f44dc0d3","0xae6ae8e5ccbfb04590405997ee2d52d2b330726137b875053c36d94e974d162f"]
STRIPE_SECRET_KEY=sk_test_51SjdLz2F9wViTbVEAQrOCmCJHjTrIr1wEyAXaFPujAI1g1tgCha2VdqWws67WGjE3o3jQ41MdVNWPqUNg5eRoQq000mn5vhq4J
STRIPE_PUBLISHABLE_KEY=pk_test_51SjdLz2F9wViTbVEvlyEdJrgaK6ejiiOFOhv62gK0JzkLScurQwsifWOn9CcP0J1MBSrMkYefJQlXNexCNqjVDIB00NaF5WUz7

6) Per gestire docker si hanno due opzioni (avviare Docker Desktop prima): 
        - Windows : .\start.cmd (per avviare i container contenenti la blockchain)
                    .\stop.cmd (per spegnere e rimuovere i container contenenti la blockchain)
        - MacOS : ./start.sh (per avviare i container contenenti la blockchain)
                  ./stop.sh (per spegnere e rimuovere i container contenenti la blockchain)


## Autori

- [@SpectreCoded](https://github.com/SpectreCoded)
- [@Barca2002](https://github.com/Barca2002)
- [@Bargi20](https://github.com/Bargi20)
- [@zDarius21](https://github.com/zDarius21)
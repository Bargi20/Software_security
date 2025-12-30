





Per far partire Django:

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

6) Per gestire docker si hanno due opzioni: 
        - Windows : .\start.cmd (per avviare i container contenenti la blockchain)
                    .\stop.cmd (per spegnere e rimuovere i container contenenti la blockchain)
        - MacOS : ./start.sh (per avviare i container contenenti la blockchain)
                  ./stop.sh (per spegnere e rimuovere i container contenenti la blockchain)
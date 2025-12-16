





Per far partire Django:

1) Da terminale spostarsi nella cartella app e digitare:
        python -m venv venv

2.1) per Mac/Linux: python venv\Scripts\activate (Fallo dal terminale, non powershell)
2.2) per Windows: ./venv/Scripts/activate.ps1

3) pip install -r requirements.txt

4) Sempre nella cartella app, digitare questo per avviare il server:
        python manage.py runserver

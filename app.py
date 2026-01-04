import sys
import os

# Aggiungi il percorso corrente a sys.path per importare moduli locali
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import uuid
import threading
from dotenv import dotenv_values
from google_auth_oauthlib.flow import InstalledAppFlow
from flask import Flask, request, jsonify, redirect, render_template
import json
import sql_manager
from apscheduler.schedulers.background import BackgroundScheduler
import classeviva_listener
from functools import wraps
import base64




config = dotenv_values(os.path.dirname(os.path.abspath(__file__)) + "/.env")
SCOPES = ['https://www.googleapis.com/auth/calendar']

db = sql_manager.DatabaseManager()

app = Flask(__name__)

def require_auth(f):
    """Decorator per verificare l'autorizzazione Basic con codice da .env"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_code = config.get('AUTH_CODE')
        auth_header = request.headers.get('Authorization', '')
        
        if not auth_code:
            # Se AUTH_CODE non è configurato, permetti l'accesso
            return f(*args, **kwargs)
        
        if auth_header.startswith('Basic '):
            try:
                credentials = base64.b64decode(auth_header[6:]).decode('utf-8')
                # Accetta sia "codice" che "codice:qualcosa"
                if credentials.split(':')[0] == auth_code or credentials == auth_code:
                    return f(*args, **kwargs)
            except Exception:
                pass
        
        # Ritorna 401 con WWW-Authenticate per mostrare il popup
        response = jsonify({'error': 'Unauthorized'})
        response.status_code = 401
        response.headers['WWW-Authenticate'] = 'Basic realm="Classeviva2GCal"'
        return response
    return decorated_function

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/register')
@require_auth
def register():

    # mostra la form di registrazione
    return render_template('register.html')

@app.route('/register_form', methods=['POST'])
@require_auth
def register_form():
    # gestisce il submit della form HTML
    classeviva_user = request.form.get('classeviva_user')
    classeviva_pwd = request.form.get('classeviva_pwd')
    calendar_id = request.form.get('calendar_id')

    if not all([classeviva_user, classeviva_pwd, calendar_id]):
        return 'Dati mancanti', 400

    user_id = str(uuid.uuid4())
    
    db.cur_execute("INSERT INTO accounts (uuid, c_username, c_password, g_calendarId) VALUES (?, ?, ?, ?) ON DUPLICATE KEY UPDATE uuid = ?, c_username = ?, c_password = ?, g_calendarId = ?;", (user_id, classeviva_user, classeviva_pwd, calendar_id, user_id, classeviva_user, classeviva_pwd, calendar_id))
    try:
        db.commit()
    except Exception as ex:
        return f'Errore nel salvataggio nel database: {ex}', 500
    
    redirect_uri = config.get('URL') + '/oauth2callback'
    print(redirect_uri)
    flow = InstalledAppFlow.from_client_secrets_file(os.path.dirname(os.path.abspath(__file__)) + '/credentials.json', SCOPES, redirect_uri=redirect_uri)
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        state=user_id,
        prompt='consent'  # forza il rilascio/riuso del refresh_token
    )
    return redirect(authorization_url)

@app.route('/oauth2callback')
def oauth2callback():
    # Google will redirect here with code and state (which we used as user_id)
    state = request.args.get('state')
    if not state:
        return 'missing state', 400
    user_id = state
    
    redirect_uri = config.get('URL') + '/oauth2callback'
    flow = InstalledAppFlow.from_client_secrets_file(os.path.dirname(os.path.abspath(__file__)) + '/credentials.json', scopes=SCOPES, state=state, redirect_uri=redirect_uri)
    authorization_response = request.url
    flow.fetch_token(authorization_response=authorization_response)
    creds = flow.credentials

    # Se Google non rimanda il refresh_token (utente aveva già concesso i permessi), riusa quello esistente
    existing_refresh = None
    try:
        db.cur_execute("SELECT g_token FROM accounts WHERE uuid = ?", (user_id,))
        row = db.fetchone()
        if row and row[0]:
            saved = json.loads(row[0])
            existing_refresh = saved.get('refresh_token')
    except Exception:
        existing_refresh = None

    token_json = creds.to_json()
    if existing_refresh and not getattr(creds, 'refresh_token', None):
        merged = json.loads(token_json)
        merged['refresh_token'] = existing_refresh
        token_json = json.dumps(merged)

    db.cur_execute("UPDATE accounts SET g_token = ? WHERE uuid = ?;", (token_json, user_id))

    try:
        db.commit()
        # Avvia la sincronizzazione in background
        threading.Thread(target=classeviva_listener.sincronizza_agenda, daemon=True).start()
        return 'OAuth completato e salvato. Puoi chiudere questa pagina.'
    except Exception as ex:
        return f'Errore nel salvataggio nel database: {ex}', 500

@app.route('/terms')
def terms():
    return render_template('terms.html')

@app.route('/privacy')
def privacy():
    return render_template('privacy.html')

# Avvia lo scheduler in background per sincronizzare a mezzanotte
scheduler = BackgroundScheduler()
scheduler.add_job(
    func=classeviva_listener.sincronizza_agenda,
    trigger="cron",
    hour=int(config.get('TIME_SYNC')..split(':')[0]),
    minute=int(config.get('TIME_SYNC')..split(':')[1]),
    id='sincronizza_agenda_job',
    name='Sincronizza agenda da Classeviva a Google Calendar'
)
scheduler.start()
print("Scheduler avviato. Sincronizzazione programmata ogni mezzanotte.")

if __name__ == '__main__':
    # run flask app (solo in modalità standalone, non con uwsgi)
    app.run(host='0.0.0.0', port=int(config['PORT']), debug=False)

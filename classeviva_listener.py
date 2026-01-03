import os
import sys
# Aggiungi il percorso corrente a sys.path per importare moduli locali
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import classeviva
from classeviva import * # importa tutto da Classeviva.py
from dotenv import dotenv_values
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import datetime
import asyncio
import sql_manager
import time
import json

def _as_date_string(value): # Ritorna una stringa data YYYY-MM-DD da un timestamp ISO, anche con timezone.
    try:
        return datetime.datetime.fromisoformat(value).date().isoformat()
    except Exception:
        return value.split('T')[0] if 'T' in value else value

def sincronizza_agenda(): # Funzione per la sincronizzazione dell'agenda di classeviva con Google Calendar

    
    date = datetime.datetime.now()
    if date.month >= 9 and date.month <= 12:
        inizio_anno = f"{date.year}-09-10"
        fine_anno = f"{date.year + 1}-06-30"
    elif date.month >=1 and date.month <=6:
        inizio_anno = f"{date.year - 1}-09-10"
        fine_anno = f"{date.year}-06-30"
    else:
        print("Mese estivo, nessuna sincronizzazione effettuata.")
        return
        # Qui il daemon deve bloccarsi

    config = dotenv_values(os.path.dirname(os.path.abspath(__file__)) + "/.env")
    db = sql_manager.DatabaseManager()
    db.cur_execute("SELECT * FROM accounts WHERE g_token IS NOT NULL;")

    for row in db.fetchall():

        """
        ##############################
        RECUPERO EVENTI DA CLASSEVIVA
        ##############################
        """

        utente = classeviva.Utente(row[2], row[3])
        i = 1
        while True:
            try:
                print("Connessione in corso...")
                utente()
                if utente.connesso:
                    print("Connesso")
                    break
                else:
                    time.sleep(1)
                    i += 1
                if i == config['MAX_TRIES']:
                    raise Exception('Timeout')
            except Exception as e:
                print(e)
                break

        if utente.connesso is False:
            print("Impossibile connettersi a Classeviva, salto l'utente.")
            continue


        ver_interr = []
        async def recupera_agenda(utente, inizio, fine):
            dati = None
            while dati is None:
                dati = await utente.agenda_da_a(inizio, fine)
            
            print("Filtraggio degli eventi...")

            # Recupero il file delle keywords
            keywords = []
            with open(os.path.dirname(os.path.abspath(__file__)) + '/keywords.json', 'r', encoding='utf-8') as f:
                keywords = json.load(f)["keywords"]

            for data in dati:
                if any(keyword in data['notes'].lower() for keyword in keywords):
                    if "interrogazione" in data['notes'].lower() or "orale" in data['notes'].lower():
                        data['title'] = "Interrogazione"
                    else:
                        data['title'] = "Verifica"
                    ver_interr.append(data)

        asyncio.run(recupera_agenda(utente, inizio_anno, fine_anno))

        print("Sincronizzazione degli eventi al database...")
        for data in ver_interr:
            data_str = _as_date_string(data['evtDatetimeBegin'])
            db.cur_execute("SELECT * FROM agenda WHERE classeviva_id = ?", (str(data['evtId']),))
            if(db.fetchone() is None):
                db.cur_execute("INSERT INTO agenda (classeviva_id, data, autore, titolo, note, gcal_id) VALUES (?, ?, ?, ?, ?, ?)", (data['evtId'], data_str, data['authorName'], data['title'], data['notes'], row[5]))
                db.commit()
                print(f"Evento {data['evtId']} inserito")
        print("Eventi sincronizzati.")

        """
        ##############################
        CARICAMENTO SU GOOGLE CALENDAR
        ##############################
        """

        print("Connessione a Google Calendar...")
        SCOPES = ['https://www.googleapis.com/auth/calendar']

        cred = None

        token_raw = row[4]
        token_info = None
        if token_raw:
            try:
                token_info = json.loads(token_raw)
            except Exception:
                token_info = None

        if token_info is None or 'refresh_token' not in token_info:
            # Token stored ma non valido/assente: lo azzeriamo e passiamo oltre
            db.cur_execute("UPDATE accounts SET g_token = NULL WHERE id = ?;", (row[0],))
            db.commit()
            print("Token non valido o senza refresh_token; eliminato e passo all'utente successivo.")
            continue

        cred = Credentials.from_authorized_user_info(token_info, SCOPES)
        
        if not cred or not cred.valid:
            if cred and cred.expired and cred.refresh_token:
                cred.refresh(Request())
            else:
                print("L'utente non ha un token valido, elimino il token all'utente.")
                db.cur_execute("UPDATE accounts SET g_token = NULL WHERE id = ?;", (row[0],))
                db.commit()
                continue
                
            db.cur_execute("UPDATE accounts SET g_token = ? WHERE id = ?;", (cred.to_json(), row[0]))
            db.commit()
        print("Credenziali ottenute con successo.")
        service = build('calendar', 'v3', credentials=cred)
        
        db.cur_execute("SELECT * FROM agenda WHERE g_inserted = 0 AND gcal_id = ? AND classeviva_id IS NOT NULL AND data >= DATE(?);", (row[5], str(date.year) + "-" + str(date.month) + "-" + str(date.day)))
        for evento in db.fetchall():
            event = {
                'summary': evento[5] + ": " + evento[4],
                'description': evento[6],
                'start': {
                    'date': str(evento[3]),
                    'timeZone': config.get('TIMEZONE'),
                },
                'end': {
                    'date': str(evento[3]),
                    'timeZone': config.get('TIMEZONE'),
                },
                'reminders': {
                    'useDefault': False,
                    'overrides': [
                        {
                            'method': 'popup', 
                            'minutes': 660
                        }
                    ],
                }
            }

            # Verifica che le credenziali abbiano accesso al calendario
            try:
                service.calendars().get(calendarId=evento[7]).execute()
            except HttpError as err:
                status = getattr(err, 'resp', None)
                status_code = None
                if status is not None:
                    status_code = getattr(status, 'status', None)
                
                if status_code in (403, 404):
                    print("Errore: l'account che stai usando non ha accesso a questo calendario (HTTP {}).")
                    continue
                raise err

            try:
                event = service.events().insert(calendarId=evento[7], body=event).execute()
                db.cur_execute("UPDATE agenda SET g_inserted = 1 WHERE id = ?;", (evento[0],))
                db.commit()
                print('Evento creato: %s' % (event.get('htmlLink')))
            except HttpError as error:
                print(f"Errore durante la creazione dell'evento: {error}")
# Classeviva2GCal

Una web application che sincronizza automaticamente gli eventi dall'agenda di Classeviva (piattaforma scolastica per studenti) a Google Calendar.

## 📋 Descrizione

Classeviva2GCal è un'applicazione che permette agli studenti di sincronizzare gli eventi scolastici dalla piattaforma Classeviva direttamente al loro Google Calendar. La sincronizzazione avviene automaticamente ogni giorno a mezzanotte, mantenendo i calendari sempre aggiornati.

### Caratteristiche

- 🔄 Sincronizzazione automatica tra Classeviva e Google Calendar
- 🔐 Autenticazione OAuth2 con Google
- 🛡️ Protezione Basic Auth opzionale
- 📱 Interfaccia web intuitiva per la registrazione
- ⏰ Sincronizzazione programmata giornaliera
- 💾 Database SQLite per la gestione dei dati

## 🚀 Avvio Rapido

### Prerequisiti

- Python 3.8+
- Un account Google con Google Calendar attivo
- Un account Classeviva

### Installazione

1. Clona il repository:
```bash
git clone <repository-url>
cd Classeviva2GCal
```

2. Crea un ambiente virtuale:
```bash
python -m venv .venv
.venv\Scripts\activate
```

3. Installa le dipendenze:
```bash
pip install -r requirements.txt
```

4. Configura le variabili d'ambiente nel file `.env`:
```
# Server configuration
URL= http://localhost
PORT=5000
MAX_TRIES=5
TIMEZONE=Europe/Rome
AUTH_CODE=supersecretcode

DB_MODE=mysql # O sqlite o mysql
DB_DIR=classeviva2gcal.db # Solo se DB_MODE=sqlite

# Solo se DB_MODE=mysql
DB_HOST=localhost
DB_PORT=3306
DB_USER=classeviva2gcal
DB_PASSWORD=evenmoresecretcode
DB_NAME=classeviva2gcal
```

5. Configura le credenziali Google:
   - Scarica il file `credentials.json` da Google Cloud Console
   - Posizionalo nella root del progetto

6. Inizializza il database:
    - Puoi usare MySQL con lo schema `classeviva2gcal-schema.sql` OPPURE
    - Usare il DB sqlite `classeviva2gcal.db`

7. Avvia l'applicazione:
```bash
python app.py
```

L'applicazione sarà disponibile su `http://localhost:5000`

## 📁 Struttura del Progetto

```
├── app.py                      # Applicazione Flask principale
├── classeviva_listener.py      # Logica di sincronizzazione da Classeviva
├── sql_manager.py              # Gestione del database
├── classeviva2gcal-schema.sql  # Schema del database SQLite
├── keywords.json               # Configurazione keywords per gli eventi
├── credentials.json            # Credenziali Google (non committare!)
├── requirements.txt            # Dipendenze Python
├── templates/                  # Template HTML
│   ├── base.html              # Template base
│   ├── home.html              # Pagina principale
│   ├── register.html          # Modulo di registrazione
│   ├── privacy.html           # Informativa privacy
│   └── terms.html             # Termini di servizio
└── static/                    # File statici (CSS, JS, etc.)
```

## 🔄 Flusso di Funzionamento

1. **Registrazione**: L'utente accede alla pagina di registrazione e inserisce:
   - Credenziali Classeviva
   - ID del Google Calendar di destinazione

2. **Autenticazione Google**: L'applicazione reindirizza l'utente per autorizzare l'accesso a Google Calendar via OAuth2

3. **Sincronizzazione**: 
   - Gli dati di registrazione vengono salvati nel database
   - La sincronizzazione avviene automaticamente ogni giorno a mezzanotte
   - Gli eventi di Classeviva vengono sincronizzati a Google Calendar

## 🔑 Variabili d'Ambiente

### Server Configuration
| Variabile | Descrizione | Obbligatorio |
|-----------|-------------|--------------|
| `URL` | URL base dell'applicazione | ✅ |
| `PORT` | Porta su cui ascoltare | ✅ |
| `MAX_TRIES` | Numero massimo di tentativi di sincronizzazione | ❌ |
| `TIMEZONE` | Fuso orario (es. Europe/Rome) | ❌ |
| `AUTH_CODE` | Codice per Basic Auth (opzionale) | ❌ |

### Database Configuration
| Variabile | Descrizione | Obbligatorio |
|-----------|-------------|--------------|
| `DB_MODE` | Tipo di database: `sqlite` o `mysql` | ✅ |
| `DB_DIR` | Percorso del file SQLite (solo se DB_MODE=sqlite) | ⚠️ |

### MySQL Configuration (solo se DB_MODE=mysql)
| Variabile | Descrizione | Obbligatorio |
|-----------|-------------|--------------|
| `DB_HOST` | Indirizzo del server MySQL | ⚠️ |
| `DB_PORT` | Porta del server MySQL | ⚠️ |
| `DB_USER` | Utente MySQL | ⚠️ |
| `DB_PASSWORD` | Password dell'utente MySQL | ⚠️ |
| `DB_NAME` | Nome del database MySQL | ⚠️ |

## 🛡️ Sicurezza

- Le credenziali di Classeviva sono salvate in forma di testo (sono completamente in chiaro, poiché il sistema tenta di accedere automaticamente. Non ho pensato ancora alla cifratura, ma ogni consiglio è utile!)
- I token OAuth2 sono salvati nel database
- È possibile abilitare Basic Auth impostando `AUTH_CODE` nelle variabili d'ambiente
- Le password sono gestite tramite le credenziali OAuth2 di Google

## 📦 Dipendenze Principali

- **Flask**: Framework web
- **Classeviva.py**: Libreria per interagire con l'API Classeviva
- **Google API Python Client**: Integrazione con Google Calendar
- **APScheduler**: Scheduling automatico
- **python-dotenv**: Gestione variabili d'ambiente

Per una lista completa, vedi [requirements.txt](requirements.txt)

## 📄 Licenza

Questo progetto è fornito così com'è. Consulta il file [CREDITS.md](CREDITS.md) per i crediti delle librerie utilizzate.

## 📝 Privacy

Consulta la pagina Privacy nell'applicazione o il file [templates/privacy.html](templates/privacy.html)

## ⚖️ Termini di Servizio

Consulta il file [templates/terms.html](templates/terms.html)

## 🤝 Contributi

I contributi sono benvenuti! Sentiti libero di fare un fork e inviare pull request.

## 📧 Supporto

Per domande o problemi, apri un issue nel repository.

---

## 👨‍💻 Autore

**Ideatore e Creatore**: Matteo Bolliri - taddeo17

---

**Nota**: Assicurati di non committare i file sensibili come `credentials.json` e `.env` nel repository.

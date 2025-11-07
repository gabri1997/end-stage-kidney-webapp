# 📘 Documentazione Tecnica — ESKD WebApp

Data: 7 Novembre 2025  
Branch: deploy

---

## 🔎 Panoramica

ESKD WebApp è una applicazione Django per la gestione pazienti e la predizione del rischio di progressione a End-Stage Kidney Disease (ESKD). Integra:
- gestione anagrafica e clinica (visite, referti MEST-C, upload referti)
- modello ML per classificazione del rischio (BASSO/MEDIO/ALTO)
- stima regressiva degli anni alla ESKD per casi a rischio
- code di background con Dramatiq + Redis
- deploy containerizzato con Gunicorn e Nginx

---

## 🧱 Architettura a Container

Servizi (docker-compose.yml):
- redis (redis:7-alpine)
  - porta 6379 esposta
  - persistenza in volume redis_data
- web (Django + Gunicorn)
  - build da Dockerfile
  - comando: gunicorn eskd_project.wsgi:application --bind 0.0.0.0:8000
  - volumi: sorgente, staticfiles, media
  - env: .env, DJANGO_SETTINGS_MODULE=eskd_project.settings
  - porta 8000 esposta
- dramatiq_worker (worker asincrono)
  - build da Dockerfile
  - comando: python manage.py rundramatiq --processes 2 --threads 4
  - dipende da redis e web
  - condivide media
- nginx (reverse proxy)
  - immagine nginx:latest
  - monta nginx.conf, staticfiles, media
  - espone 80:80 e inoltra a web:8000

Volumi: static_volume, media_volume, redis_data.

Flusso richieste:
Browser → Nginx → Gunicorn → Django → (DB/ML/Redis). Static e media serviti direttamente da Nginx.

---

## 🌐 Web server e proxy

Nginx (nginx.conf):
- resolver 127.0.0.11 (DNS Docker) e upstream django_backend → web:8000
- location /static e /media con alias rispettivi
- proxy_pass verso Gunicorn, header X-Forwarded-* impostati, timeout 60s
- Solo HTTP 80. HTTPS non ancora configurato (vedi Sicurezza)

Gunicorn:
- 3 worker, access/error log su stdout

---

## ⚙️ Django — Configurazione

File: eskd_project/settings.py
- DEBUG: da env (default False)
- SECRET_KEY: da env DJANGO_SECRET_KEY (fallback di sviluppo presente, da cambiare in produzione)
- ALLOWED_HOSTS: da env (default "155.185.49.200,localhost,127.0.0.1")
- CSRF_TRUSTED_ORIGINS: http/https su 155.185.49.200
- SECURE_PROXY_SSL_HEADER impostato
- Header sicurezza non forzati finché non c’è HTTPS (SECURE_SSL_REDIRECT & cookie secure commentati)
- App: prediction, django_dramatiq
- Static: STATICFILES_DIRS=prediction/static, STATIC_ROOT=staticfiles
- Media: MEDIA_ROOT=media
- DB: PostgreSQL esterno (HOST 172.17.0.1, PORT 5432, NAME eskd, USER eskd_user)
- Email: da env (default Gmail SMTP TLS 587)
- Logging: Stream + RotatingFileHandler in logs/django.log (10MB x5), livello INFO in produzione
- Dramatiq/Redis: url da env REDIS_URL (default redis://redis:6379/0)

URL progetto: eskd_project/urls.py include prediction.urls come root.

---

## 🗄️ Database e Modelli

Modelli principali (prediction/models.py):
- Paziente: medico (FK User), medici_condivisi (M2M), anagrafica, data_nascita/eta, sesso, CF unico
- Visita: dati clinici (creatinina, proteinuria, PA), referto file upload (MEDIA_ROOT/referti/paziente_<id>/)
- MESTC: punteggi istologici M,E,S,T,C e data rilevazione
- Predizione: esito (BASSO/MEDIO/ALTO), probabilita_eskd (%), anni_eskd (float opzionale), relazioni a paziente/visita/MESTC
- UserSecurity: domanda di sicurezza e hash della risposta per reset password senza email

Migrazioni presenti in prediction/migrations/.

---

## 🔐 Autenticazione, Reset Password e Sicurezza

- Login/Logout via Django auth.
- Registrazione custom (CustomUserCreationForm) con email obbligatoria e raccolta domanda/risposta di sicurezza.
- Reset password via email: viste Django (PasswordResetView/Confirm/Done/Complete) mappate in prediction/urls.py, template in templates/registration/.
- Reset password senza email: flusso a 2 step con domanda di sicurezza (views password_reset_security_start/verify) e SetPasswordForm.
- Email SMTP configurabile via env; in test usato Gmail App Password.
- Nota: prediction/urls.py contiene duplicazioni per login/logout (due definizioni); consigliata rimozione dei duplicati.

---

## 🧮 Modelli ML e Inferenza

File: prediction/model_loader.py
- Classifier MySimpleBinaryNet (PyTorch) → rischio ESKD
- Regressor MySimpleRegressorNet → anni alla ESKD (clamp 0–10)
- Caricamento scaler Joblib e pesi .pth da prediction/models/classification e regression
- Feature attese (classifier): [Gender, Age, Hypertension, M, E, S, T, C, Proteinuria, Creatinine, Therapy]
- Output: probabilità in %, esito BASSO/MEDIO/ALTO; se non BASSO, calcolo anni_eskd con regressore

Predizione sincrona: views.calcola_eskd costruisce i dati da form/DB e salva Predizione.

Inferenza asincrona: prediction/tasks.py
- prepare_patient_data(paziente) aggrega ultima visita e ultimo MEST-C
- esegui_inference(actor Dramatiq) esegue predict_risk e salva Predizione

---

## 🧰 Form e Template

Form (prediction/forms.py):
- PazienteForm, VisitaForm (con widget e label), MESTCForm
- CalcolaESKDForm per input esplicito in predittore
- CustomUserCreationForm: email + domanda/risposta di sicurezza; valida email univoca e gestione domanda personalizzata
- SecurityQuestionSetupForm, SecurityResetStep1Form/Step2Form

Template:
- Base layout: prediction/templates/base.html — navbar con gradiente viola personalizzato
- Auth: prediction/templates/login.html, prediction/templates/register.html (toggle visibilità password e risposta)
- App: prediction/templates/prediction/* (home, lista_pazienti, dettaglio_paziente, form vari, ecc.)
- Registration/reset: templates/registration/*

Static: prediction/static/, raccolti in staticfiles/ con collectstatic (eseguito in build Dockerfile).

---

## 🧭 Flussi funzionali principali

1) Login/Registrazione
- Registrazione crea utente, associa domanda/risposta di sicurezza, redirect a login.

2) Gestione Pazienti
- CRUD pazienti/visite/MEST-C; upload referti in MEDIA_ROOT.

3) Predizione ESKD
- Dal dettaglio paziente/visita, form "Calcola ESKD" → costruzione dati → predict_risk → salvataggio Predizione.
- Visualizzazione in "dettaglio_paziente". Gli anni sono mostrati in fasce e colori (filtri template personalizzati).

4) Predizione asincrona (opzionale)
- Tramite esegui_inference Dramatiq: invio job → worker calcola e persiste risultato.

5) Reset Password
- Via email (Django) o via domanda di sicurezza (custom 2-step).

---

## 🛡️ Sicurezza

- DEBUG=False in produzione, ALLOWED_HOSTS limitati
- Headers di sicurezza pronti ma HTTPS da attivare prima di abilitarli (SECURE_SSL_REDIRECT, cookie secure, HSTS)
- SECRET_KEY: usare sempre variabile d’ambiente unica in produzione
- Rate limiting login: non presente; valutare django-ratelimit
- Condivisione paziente fra medici tramite medici_condivisi

---

## 📜 Logging e Monitoraggio

- Console + RotatingFileHandler in logs/django.log (10MB x5), formato verbose
- Dramatiq: log su stdout del worker
- Suggeriti: endpoint /health, monitor esterno (UptimeRobot), Prometheus/Grafana

---

## 🚀 Build & Deploy

Dockerfile:
- Python 3.12-slim, build-essential, libpq-dev
- install requirements.txt
- collectstatic in fase build
- CMD gunicorn 3 workers

Avvio tipico:
- docker compose up -d --build
- Migrazioni/utente admin (eseguire nella web):
  - manage.py migrate
  - manage.py createsuperuser

Static/Media:
- staticfiles/ e media/ montati in Nginx, web scrive su volumi condivisi

---

## 🔧 Variabili d’Ambiente (esempio .env)

- DJANGO_SECRET_KEY=<obbligatoria in prod>
- DEBUG=False
- ALLOWED_HOSTS=155.185.49.200,tuo.dominio.it,localhost,127.0.0.1
- REDIS_URL=redis://redis:6379/0
- EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
- EMAIL_HOST=smtp.gmail.com
- EMAIL_PORT=587
- EMAIL_USE_TLS=True
- EMAIL_HOST_USER=<email>
- EMAIL_HOST_PASSWORD=<app_password>
- DEFAULT_FROM_EMAIL=<email>

DB (attuali hardcoded in settings.py):
- NAME=eskd, USER=eskd_user, PASSWORD=PostGrePsw1997!, HOST=172.17.0.1, PORT=5432

Suggerimento: esternalizzare anche i parametri DB in .env.

---

## 🧭 Troubleshooting rapidi

- 504 da Nginx: verifica resolver 127.0.0.11 e upstream web:8000, timeouts; controlla che web sia up
- Redirect loop/errore connessione: non attivare SECURE_SSL_REDIRECT senza HTTPS configurato
- Dramatiq non parte: controlla REDIS_URL e servizio redis
- Modelli ML: File .pth/.pkl mancanti → controlla directory prediction/models/classification|regression
- Static non aggiornati: esegui collectstatic (è in Dockerfile), verifica mount in Nginx

---

## ✅ Migliorie e note aperte

Vedi docs/MIGLIORIE_CONSIGLIATE.md. Priorità:
- HTTPS/SSL su Nginx (porta 443) e abilitare le impostazioni secure
- SECRET_KEY da variabile d’ambiente
- Backup automatici DB
- Rate limiting login e health-check
- Rimuovere duplicati URL login/logout in prediction/urls.py

---

## 📚 Riferimenti

- Django 5.2
- Gunicorn
- Nginx
- Redis + Dramatiq
- PyTorch, scikit-learn, joblib


# 📋 Migliorie Consigliate per ESKD WebApp

## ✅ **Completate Oggi**

### 1. Sicurezza Settings
- ✅ DEBUG impostato su False in produzione
- ✅ ALLOWED_HOSTS limitato agli host validi
- ✅ Security headers aggiunti (HSTS, X-Frame-Options, etc.)
- ✅ CSRF_TRUSTED_ORIGINS configurati
- ✅ Session e CSRF cookies secure quando HTTPS attivo

### 2. Logging
- ✅ Logging configurato con rotazione file
- ✅ Log salvati in `/app/logs/django.log`
- ✅ Formato verbose per debugging
- ✅ Livelli INFO in produzione, DEBUG in sviluppo

### 3. Gunicorn
- ✅ Aumentato numero workers a 3
- ✅ Access e error logs abilitati

---

## 🚨 **URGENTI - Da Fare Subito**

### 1. **HTTPS/SSL** (Priorità MASSIMA!)
**Problema:** Attualmente l'app usa HTTP, non sicuro per dati medici

**Soluzione A - Let's Encrypt (Consigliato):**
```bash
# Installare Certbot
sudo apt-get update
sudo apt-get install certbot python3-certbot-nginx

# Ottenere certificato (serve un dominio!)
sudo certbot --nginx -d tuodominio.it
```

**Soluzione B - Self-Signed (Solo Testing):**
```bash
cd /home/grosati/end-stage-kidney-webapp
mkdir -p ssl
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout ssl/nginx-selfsigned.key \
  -out ssl/nginx-selfsigned.crt \
  -subj "/C=IT/ST=Italy/O=ESKD/CN=155.185.49.200"
```

Poi aggiornare `nginx.conf` per HTTPS (porta 443).

**Impatto:** CRITICO - Dati medici devono essere criptati!

---

### 2. **Backup Automatici Database**
**Problema:** Nessun backup del database PostgreSQL

**Soluzione:**
```bash
# Creare script backup
cat > /home/grosati/backup_db.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/home/grosati/backups"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR
docker exec eskd_db pg_dump -U eskd_user eskd > $BACKUP_DIR/eskd_$DATE.sql
# Mantieni solo ultimi 7 giorni
find $BACKUP_DIR -name "eskd_*.sql" -mtime +7 -delete
EOF

chmod +x /home/grosati/backup_db.sh

# Aggiungere a crontab (backup giornaliero alle 2 AM)
(crontab -l 2>/dev/null; echo "0 2 * * * /home/grosati/backup_db.sh") | crontab -
```

**Impatto:** CRITICO - Perdita dati pazienti = disastro!

---

### 3. **Generare SECRET_KEY Unica**
**Problema:** SECRET_KEY è quella di default di Django

**Soluzione:**
```python
# Generare nuova chiave
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

# Aggiornare in .env
DJANGO_SECRET_KEY=<nuova_chiave_generata>
```

**Impatto:** ALTO - Vulnerabilità sicurezza sessioni

---

## 🎯 **IMPORTANTI - Da Fare Presto**

### 4. **Rate Limiting**
**Problema:** Nessuna protezione contro attacchi brute-force su login

**Soluzione:**
```bash
pip install django-ratelimit
```

```python
# In views.py
from django_ratelimit.decorators import ratelimit

@ratelimit(key='ip', rate='5/m', method='POST')
def login_view(request):
    # ...
```

**Impatto:** ALTO - Prevenzione attacchi

---

### 5. **Monitoring e Health Checks**
**Problema:** Non sai se l'app è down finché qualcuno non si lamenta

**Soluzione A - Health Check Endpoint:**
```python
# In prediction/views.py
from django.http import JsonResponse
from django.db import connection

def health_check(request):
    try:
        # Test DB
        connection.ensure_connection()
        
        # Test Redis
        from redis import Redis
        r = Redis(host='redis', port=6379)
        r.ping()
        
        return JsonResponse({'status': 'healthy'})
    except Exception as e:
        return JsonResponse({'status': 'unhealthy', 'error': str(e)}, status=503)
```

**Soluzione B - Monitoring Esterno:**
- UptimeRobot (gratuito): monitora http://155.185.49.200/health/
- Invia email/SMS se down

**Impatto:** MEDIO - Visibilità problemi

---

### 6. **PostgreSQL nel Docker Compose**
**Problema:** Database esterno, non gestito

**Soluzione:** Aggiungere servizio PostgreSQL in `docker-compose.yml`:
```yaml
services:
  db:
    image: postgres:15-alpine
    container_name: eskd_db
    environment:
      POSTGRES_DB: eskd
      POSTGRES_USER: eskd_user
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

volumes:
  postgres_data:
```

**Impatto:** MEDIO - Gestione semplificata

---

## 💡 **UTILI - Da Considerare**

### 7. **Cache con Redis**
**Problema:** Ogni richiesta colpisce il DB

**Soluzione:**
```python
# In settings.py
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://redis:6379/1',
    }
}

# Usare cache per query pesanti
from django.core.cache import cache

def get_paziente_stats(paziente_id):
    cache_key = f'stats_{paziente_id}'
    stats = cache.get(cache_key)
    if not stats:
        stats = calculate_stats(paziente_id)  # Query pesante
        cache.set(cache_key, stats, 300)  # 5 minuti
    return stats
```

**Impatto:** BASSO - Performance

---

### 8. **API REST (Django REST Framework)**
**Problema:** Solo interfaccia web, nessuna API

**Soluzione:**
```bash
pip install djangorestframework
```

Permetterebbe:
- App mobile in futuro
- Integrazione con altri sistemi
- Export dati automatizzato

**Impatto:** BASSO - Funzionalità future

---

### 9. **Tests Automatizzati**
**Problema:** Nessun test, possibili regressioni

**Soluzione:**
```python
# prediction/tests.py
from django.test import TestCase
from .models import Paziente

class PazienteTestCase(TestCase):
    def test_calcola_eta(self):
        p = Paziente(data_nascita='1980-01-01')
        self.assertGreater(p.calcola_eta(), 40)
```

**Impatto:** BASSO - Qualità codice

---

### 10. **Docker Compose Override per Dev**
**Problema:** Stesso docker-compose per dev e prod

**Soluzione:**
```yaml
# docker-compose.override.yml (gitignored, solo locale)
services:
  web:
    command: python manage.py runserver 0.0.0.0:8000
    volumes:
      - .:/app
    environment:
      - DEBUG=True
```

**Impatto:** BASSO - Developer Experience

---

## 📊 **Riepilogo Priorità**

| Priorità | Miglioria | Effort | Impatto | Deadline |
|----------|-----------|--------|---------|----------|
| 🔴 CRITICA | HTTPS/SSL | 2h | Security | Immediato | fatto bro
| 🔴 CRITICA | Backup DB | 1h | Data Loss | Questa settimana | bho non serve
| 🔴 CRITICA | SECRET_KEY | 5min | Security | Oggi | 
| 🟡 ALTA | Rate Limiting | 1h | Security | 1 settimana | non so cosa si
| 🟡 ALTA | Health Checks | 30min | Reliability | 1 settimana | non so cosa sia 
| 🟢 MEDIA | PostgreSQL in Docker | 2h | Management | 2 settimane | fatto bro 
# Roba inutile 
| 🔵 BASSA | Cache Redis | 3h | Performance | Quando necessario |
| 🔵 BASSA | API REST | 8h | Features | Futuro |
| 🔵 BASSA | Tests | Ongoing | Quality | Ongoing |

---

## 🛠️ **Come Applicare le Modifiche**

### Per HTTPS (dopo aver ottenuto certificati):
1. Aggiornare `nginx.conf` per porta 443
2. Impostare `DEBUG=False` in `.env`
3. Rebuild: `docker compose down && docker compose up -d --build`

### Per Backup:
1. Creare script e crontab come sopra
2. Testare: `/home/grosati/backup_db.sh`
3. Verificare: `ls -lh /home/grosati/backups/`

### Per SECRET_KEY:
1. Generare nuova chiave
2. Aggiornare `.env`
3. Restart: `docker compose restart web`

---

## 📚 **Riferimenti Utili**

- [Django Security Checklist](https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/)
- [Let's Encrypt Setup](https://letsencrypt.org/getting-started/)
- [Nginx HTTPS Config](https://nginx.org/en/docs/http/configuring_https_servers.html)
- [Docker Security Best Practices](https://docs.docker.com/develop/security-best-practices/)

---

**Data creazione:** 7 Novembre 2025  
**Ultima revisione:** 7 Novembre 2025  
**Versione:** 1.0

1. Installo django
2. Creo la struttura del progetto con il core di django che in eskd_project, poi in model ho i pesi, in prediction i templates e le views, e poi ho il manage.py 
3. Verifico che django vada con python manage.py runserver
4. Creo la mia prima app prediction
5. Creo i modelli, dopodichè nella mia pipeline ho database, form,  view e template
6. Ogni volta che modifico il modello Django deve aggiornare la struttura del database creando o cambiando cartelle 
Ora ho
- un sistema di login/logout e autenticazione
- ogni medico (utente) vede solo i suoi pazienti
- puoi aggiungere pazienti, registrare visite e referti MEST-C
- un database coerente e relazioni 1-a-molti perfette
Proseguo con :
- Aggiungere le funzionalità per modificare o cancellare visite e referti direttamente dalle pagine.
  - modificare una visita o un referto MEST-C
  - eliminarli direttamente dalla pagina del paziente
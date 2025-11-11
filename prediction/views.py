from django.shortcuts import render, redirect, get_object_or_404
# Create your views here.
from django.http import HttpResponse
from .models import Paziente, Visita, MESTC
from .forms import PazienteForm
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .forms import PazienteForm, VisitaForm, MESTCForm
from django.utils import timezone
from .model_loader import predict_risk
from .models import Predizione, Visita, MESTC
from .forms import CalcolaESKDForm
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
# In cima al tuo views.py, assicurati di avere questi import:
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.shortcuts import render, redirect
from django.db.models import Q
from django.contrib.auth.models import User

from .forms import CustomUserCreationForm, SecurityQuestionSetupForm, SecurityResetStep1Form, SecurityResetStep2Form
from .models import UserSecurity
from django.contrib.auth.forms import SetPasswordForm

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            # Salva l'utente
            user = form.save()
            username = form.cleaned_data.get('username')
            
            # Messaggio di successo
            messages.success(request, f"✅ Account creato per {username}! Ora puoi effettuare il login.")
            return redirect('login')
        else:
            # Mostra errori specifici
            messages.error(request, "❌ Errore nella registrazione. Controlla i campi e riprova.")
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'register.html', {'form': form})


@login_required
def set_security_question(request):
    existing = getattr(request.user, "security", None)
    if request.method == 'POST':
        form = SecurityQuestionSetupForm(request.POST)
        if form.is_valid():
            form.save_for_user(request.user)
            messages.success(request, "Domanda di sicurezza aggiornata ✅")
            return redirect('home')
    else:
        form = SecurityQuestionSetupForm(initial={
            'question': existing.question if existing else None,
        }) if existing else SecurityQuestionSetupForm()

    return render(request, 'registration/security_setup.html', {'form': form})


from django.views.decorators.http import require_http_methods


@require_http_methods(["GET", "POST"])
def password_reset_security_start(request):
    # Step 1: ask for username; if user+security exists, proceed to step 2 showing the question
    if request.method == 'POST':
        form = SecurityResetStep1Form(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            from django.contrib.auth import get_user_model
            UserModel = get_user_model()
            try:
                user = UserModel.objects.get(username=username)
                if not hasattr(user, 'security'):
                    messages.error(request, "L'account non ha una domanda di sicurezza impostata.")
                else:
                    request.session['pwreset_sec_uid'] = user.id
                    return redirect('password_reset_security_verify')
            except UserModel.DoesNotExist:
                # Messaggio generico per non rivelare esistenza utente
                messages.error(request, "Impossibile procedere con il reset.")
    else:
        form = SecurityResetStep1Form()

    return render(request, 'registration/password_reset_security_start.html', {'form': form})


@require_http_methods(["GET", "POST"])
def password_reset_security_verify(request):
    # Step 2: show question, verify answer, set new password
    from django.contrib.auth import get_user_model
    UserModel = get_user_model()
    uid = request.session.get('pwreset_sec_uid')
    if not uid:
        messages.error(request, "Sessione scaduta. Riprova.")
        return redirect('password_reset_security_start')

    try:
        user = UserModel.objects.get(id=uid)
        sec = user.security
    except (UserModel.DoesNotExist, UserSecurity.DoesNotExist):
        messages.error(request, "Impossibile procedere con il reset.")
        return redirect('password_reset_security_start')

    if request.method == 'POST':
        form = SecurityResetStep2Form(user, request.POST)
        if form.is_valid():
            answer = form.cleaned_data['answer']
            if not sec.check_answer(answer):
                form.add_error('answer', 'Risposta errata')
            else:
                # save new password
                form.save()
                # cleanup session
                request.session.pop('pwreset_sec_uid', None)
                messages.success(request, "Password aggiornata con successo ✅")
                return redirect('login')
    else:
        form = SecurityResetStep2Form(user)

    context = {
        'form': form,
        'question': sec.question,
        'username': user.username,
    }
    return render(request, 'registration/password_reset_security_verify.html', context)

@login_required
def condividi_paziente(request, paziente_id):
    paziente = (
        Paziente.objects.filter(
            Q(id=paziente_id),
            Q(medico=request.user) | Q(medici_condivisi=request.user)
        )
        .distinct()
        .first()
    )

    if not paziente:
        raise Http404("Paziente non trovato")

    if request.method == 'POST':
        username = request.POST.get('username')
        try:
            altro_medico = User.objects.get(username=username)
            paziente.medici_condivisi.add(altro_medico)
            messages.success(request, f"Paziente condiviso con {altro_medico.username} ✅")
        except User.DoesNotExist:
            messages.error(request, "Nessun medico trovato con questo nome utente ❌")

        return redirect('lista_pazienti')

    return render(request, 'prediction/condividi_paziente.html', {'paziente': paziente})

    
    return render(request, 'prediction/condividi_paziente.html', {'paziente': paziente})
@login_required
def home(request):
    # Ottieni alcune statistiche per il dashboard
    num_pazienti = Paziente.objects.filter(
        Q(medico=request.user) | Q(medici_condivisi=request.user)
    ).distinct().count()

    num_visite = Visita.objects.filter(medico=request.user).count()
    ultime_predizioni = Predizione.objects.filter(
        paziente__medico=request.user
    ).order_by('-data_predizione')[:5]
    
    context = {
        'num_pazienti': num_pazienti,
        'num_visite': num_visite,
        'ultime_predizioni': ultime_predizioni,
    }
    return render(request, 'prediction/home.html', context)

from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.shortcuts import render, redirect
from .tasks import esegui_inference

def lancia_inference(request, paziente_id):
    esegui_inference.send(paziente_id)  
    messages.success(request, "Inference avviata in background.")
    return redirect("lista_pazienti")

@login_required
def nuovo_paziente(request):
    if request.method == "POST":
        form = PazienteForm(request.POST)
        if form.is_valid():
            paziente = form.save(commit=False)
            paziente.medico = request.user  # ← assegna il medico loggato
            paziente.save()
            messages.success(request, "✅ Paziente aggiunto con successo.")
            return redirect("lista_pazienti")
    else:
        form = PazienteForm()

    return render(request, "prediction/nuovo_paziente.html", {"form": form})

@login_required
def lista_pazienti(request):
    query = request.GET.get('q', '').strip()
    
    # Filtra pazienti del medico o condivisi con lui
    pazienti = Paziente.objects.filter(
        Q(medico=request.user) | Q(medici_condivisi=request.user)
    ).distinct()
    
    # Applica la ricerca se presente
    if query:
        parole = query.split()
        
        if len(parole) >= 2:
            # Ricerca con nome E cognome
            pazienti = pazienti.filter(
                Q(nome__icontains=parole[0], cognome__icontains=parole[1]) |
                Q(nome__icontains=parole[1], cognome__icontains=parole[0]) |
                Q(nome__icontains=query) |
                Q(cognome__icontains=query)
            )
        else:
            # Ricerca singola parola
            pazienti = pazienti.filter(
                Q(nome__icontains=query) | Q(cognome__icontains=query)
            )
    
    # Ordina i risultati
    pazienti = pazienti.order_by('cognome', 'nome')
    
    context = {"pazienti": pazienti}
    return render(request, "prediction/lista_pazienti.html", context)

@login_required
def dettaglio_paziente(request, paziente_id):
    paziente = (
        Paziente.objects.filter(
            Q(id=paziente_id),
            Q(medico=request.user) | Q(medici_condivisi=request.user)
        )
        .distinct()
        .first()
    )

    if not paziente:
        raise Http404("Paziente non trovato")

    visite = Visita.objects.filter(paziente=paziente).order_by("data_visita")
    mestc_records = MESTC.objects.filter(paziente=paziente).order_by("data_rilevazione")
    predizioni = Predizione.objects.filter(paziente=paziente).order_by("-data_predizione")

    ultima_predizione = predizioni.first()  

    return render(request, "prediction/dettaglio_paziente.html", {
        "paziente": paziente,
        "visite": visite,
        "mestc_records": mestc_records,
        "predizioni": predizioni,
        "ultima_predizione": ultima_predizione,  
    })


@login_required
def nuova_visita(request, paziente_id):
    paziente = get_object_or_404(
    Paziente.objects.filter(Q(medico=request.user) | Q(medici_condivisi=request.user)).distinct(),
    id=paziente_id
)


    if request.method == "POST":
        form = VisitaForm(request.POST, request.FILES)
        if form.is_valid():
            visita = form.save(commit=False)
            visita.paziente = paziente
            visita.medico = request.user  
            visita.save()
            messages.success(request, "✅ Visita aggiunta con successo.")
            return redirect('dettaglio_paziente', paziente_id=paziente.id)

    else:
        form = VisitaForm()

    return render(request, "prediction/nuova_visita.html", {"form": form, "paziente": paziente})

@login_required
def nuovo_mestc(request, paziente_id):
    paziente = get_object_or_404(
    Paziente.objects.filter(Q(medico=request.user) | Q(medici_condivisi=request.user)).distinct(),
    id=paziente_id
)


    if request.method == "POST":
        form = MESTCForm(request.POST)
        if form.is_valid():
            mestc = form.save(commit=False)
            mestc.paziente = paziente
            mestc.save()
            return redirect('dettaglio_paziente', paziente_id=paziente.id)
    else:
        form = MESTCForm()

    return render(request, "prediction/nuovo_mestc.html", {"form": form, "paziente": paziente})


@login_required
def modifica_visita(request, paziente_id, visita_id):
    paziente = (
        Paziente.objects.filter(
            Q(id=paziente_id),
            Q(medico=request.user) | Q(medici_condivisi=request.user)
        )
        .distinct()
        .first()
    )

    if not paziente:
        raise Http404("Paziente non trovato")

    visita = get_object_or_404(Visita, id=visita_id, paziente=paziente)

    if request.method == "POST":
        form = VisitaForm(request.POST, request.FILES, instance=visita)
        if form.is_valid():
            visita = form.save(commit=False)
            visita.medico = request.user 
            visita.save()
            messages.success(request, "✅ Visita modificata con successo.")
            return redirect('dettaglio_paziente', paziente_id=paziente.id)

    else:
        form = VisitaForm(instance=visita)

    return render(request, "prediction/modifica_visita.html", {"form": form, "paziente": paziente, "visita": visita})


@login_required
def elimina_visita(request, paziente_id, visita_id):
    paziente = get_object_or_404(
    Paziente.objects.filter(Q(medico=request.user) | Q(medici_condivisi=request.user)),
    id=paziente_id
)

    visita = get_object_or_404(Visita, id=visita_id, paziente=paziente)

    if request.method == "POST":
        visita.delete()
        return redirect('dettaglio_paziente', paziente_id=paziente.id)

    return render(request, "prediction/conferma_elimina_visita.html", {"paziente": paziente, "visita": visita})

@login_required
def modifica_mestc(request, paziente_id, mestc_id):
    paziente = get_object_or_404(
    Paziente.objects.filter(Q(medico=request.user) | Q(medici_condivisi=request.user)).distinct(),
    id=paziente_id
)

    mestc = get_object_or_404(MESTC, id=mestc_id, paziente=paziente)

    if request.method == "POST":
        form = MESTCForm(request.POST, instance=mestc)
        if form.is_valid():
            form.save()
            return redirect('dettaglio_paziente', paziente_id=paziente.id)
    else:
        form = MESTCForm(instance=mestc)

    return render(request, "prediction/modifica_mestc.html", {"form": form, "paziente": paziente, "mestc": mestc})


@login_required
def elimina_mestc(request, paziente_id, mestc_id):
    paziente = get_object_or_404(
    Paziente.objects.filter(Q(medico=request.user) | Q(medici_condivisi=request.user)).distinct(),
    id=paziente_id
)

    mestc = get_object_or_404(MESTC, id=mestc_id, paziente=paziente)

    if request.method == "POST":
        mestc.delete()
        return redirect('dettaglio_paziente', paziente_id=paziente.id)

    return render(request, "prediction/conferma_elimina_mestc.html", {"paziente": paziente, "mestc": mestc})


@login_required
def calcola_eskd(request, paziente_id, visita_id):
    paziente = get_object_or_404(
    Paziente.objects.filter(Q(medico=request.user) | Q(medici_condivisi=request.user)).distinct(),
    id=paziente_id
)

    visita = get_object_or_404(Visita, id=visita_id)
    mestc = MESTC.objects.filter(paziente=paziente).order_by('-data_rilevazione').first()

    if request.method == "POST":
        form = CalcolaESKDForm(request.POST)
        if form.is_valid():
            form_data = form.cleaned_data

            # --- Recupera i valori dal form, con fallback al DB ---
            sesso = form_data.get("sesso") or getattr(paziente, "sesso", "M") or "M"
            eta = form_data.get("eta") or getattr(paziente, "eta", 50) or 50
            
            iperteso = form_data.get("iperteso")
            if iperteso is None:
                iperteso = int(getattr(paziente, "iperteso", False))
            else:
                iperteso = int(iperteso)

            # --- VALORI MEST-C: usa il form, fallback al DB ---
            M_val = form_data.get("M")
            if M_val is None:
                M_val = getattr(mestc, "M", 0) if mestc else 0
            
            E_val = form_data.get("E")
            if E_val is None:
                E_val = getattr(mestc, "E", 0) if mestc else 0
            
            S_val = form_data.get("S")
            if S_val is None:
                S_val = getattr(mestc, "S", 0) if mestc else 0
            
            T_val = form_data.get("T")
            if T_val is None:
                T_val = getattr(mestc, "T", 0) if mestc else 0
            
            C_val = form_data.get("C")
            if C_val is None:
                C_val = getattr(mestc, "C", 0) if mestc else 0

            # --- VALORI VISITA: usa il form, fallback al DB ---
            proteinuria_val = form_data.get("proteinuria")
            if proteinuria_val is None:
                proteinuria_val = getattr(visita, "proteinuria", 0) or 0
            
            creatinina_val = form_data.get("creatinina")
            if creatinina_val is None:
                creatinina_val = getattr(visita, "creatinina", 0) or 0

            # --- TERAPIE: dal form ---
            anti = form_data.get("Antihypertensive", 0)
            immuno = form_data.get("Immunosuppressants", 0)
            fish = form_data.get("FishOil", 0)
            
            # Converti a int
            anti_int = int(anti) if anti else 0
            immuno_int = int(immuno) if immuno else 0
            fish_int = int(fish) if fish else 0

            # --- Costruzione dizionario dati per il modello ---
            data = {
                "sesso": sesso,
                "eta": float(eta),
                "iperteso": iperteso,

                # Dati MEST-C (dal form o DB)
                "M": int(M_val),
                "E": int(E_val),
                "S": int(S_val),
                "T": int(T_val),
                "C": int(C_val),

                # Dati visita (dal form o DB)
                "proteinuria": float(proteinuria_val),
                "creatinina": float(creatinina_val),

                # Terapie
                "Antihypertensive": anti_int,
                "Immunosuppressants": immuno_int,
                "FishOil": fish_int,
            }

            print("\n" + "="*60)
            print("📋 VERIFICA ORIGINE DATI:")
            print("="*60)
            print(f"M: {M_val} (form: {form_data.get('M')}, DB: {getattr(mestc, 'M', None) if mestc else None})")
            print(f"E: {E_val} (form: {form_data.get('E')}, DB: {getattr(mestc, 'E', None) if mestc else None})")
            print(f"S: {S_val} (form: {form_data.get('S')}, DB: {getattr(mestc, 'S', None) if mestc else None})")
            print(f"T: {T_val} (form: {form_data.get('T')}, DB: {getattr(mestc, 'T', None) if mestc else None})")
            print(f"C: {C_val} (form: {form_data.get('C')}, DB: {getattr(mestc, 'C', None) if mestc else None})")
            print(f"Proteinuria: {proteinuria_val} (form: {form_data.get('proteinuria')}, DB: {getattr(visita, 'proteinuria', None)})")
            print(f"Creatinina: {creatinina_val} (form: {form_data.get('creatinina')}, DB: {getattr(visita, 'creatinina', None)})")
            print("="*60)

            print("\n Dati completi passati al modello:")
            for k, v in data.items():
                print(f"{k:20s} = {v}")
            print("="*60 + "\n")

            # --- Predizione ---
            result = predict_risk(data)
            probabilita = result["probabilita"]
            esito = result["esito"]
            anni_eskd = result.get("anni_eskd", None)

            # --- Salva nel DB ---
            Predizione.objects.create(
                paziente=paziente,
                visita=visita,
                probabilita_eskd=probabilita,
                esito=esito,
                anni_eskd=anni_eskd
            )

            messages.success(request, f"Predizione completata: rischio {esito} ({probabilita:.2f}%)")
            return redirect("dettaglio_paziente", paziente_id=paziente.id)

    else:
        # Precompila form con dati noti
        initial = {
            "sesso": getattr(paziente, "sesso", ""),
            "eta": getattr(paziente, "eta", ""),
            "iperteso": getattr(paziente, "iperteso", False),
            "creatinina": getattr(visita, "creatinina", ""),
            "proteinuria": getattr(visita, "proteinuria", ""),
            "Antihypertensive": False,
            "Immunosuppressants": False,
            "FishOil": False,
        }

        if mestc:
            initial.update({
                "M": mestc.M, 
                "E": mestc.E, 
                "S": mestc.S, 
                "T": mestc.T, 
                "C": mestc.C
            })

        form = CalcolaESKDForm(initial=initial)

    return render(request, "prediction/calcola_eskd.html", {
        "paziente": paziente,
        "visita": visita,
        "form": form
    })


from django.contrib import messages  # aggiungi questo import in alto

@login_required
def modifica_paziente(request, paziente_id):
    paziente = (
        Paziente.objects.filter(
            Q(id=paziente_id),
            Q(medico=request.user) | Q(medici_condivisi=request.user)
        )
        .distinct()
        .first()
    )

    if not paziente:
        raise Http404("Paziente non trovato")


    if request.method == "POST":
        form = PazienteForm(request.POST, instance=paziente)
        if form.is_valid():
            form.save()
            messages.success(request, "✅ Dati del paziente aggiornati con successo.")
            return redirect("dettaglio_paziente", paziente_id=paziente.id)
    else:
        form = PazienteForm(instance=paziente)

    return render(request, "prediction/modifica_paziente.html", {
        "paziente": paziente,
        "form": form
    })


@login_required
def delete_mestc(request, mestc_id):
    mestc = get_object_or_404(MESTC, id=mestc_id)
    paziente_id = mestc.paziente.id

    # Eliminazione diretta
    mestc.delete()

    messages.success(request, "Referto MEST-C eliminato con successo.")
    return redirect("dettaglio_paziente", paziente_id=paziente_id)


@login_required
def delete_predizione(request, predizione_id):
    predizione = get_object_or_404(Predizione, id=predizione_id)
    paziente_id = predizione.paziente.id

    predizione.delete()
    messages.success(request, "Predizione ESKD eliminata con successo.")
    return redirect("dettaglio_paziente", paziente_id=paziente_id)



@login_required
def elimina_paziente(request, paziente_id):
    paziente = (
        Paziente.objects.filter(
            Q(id=paziente_id),
            Q(medico=request.user) | Q(medici_condivisi=request.user)
        )
        .distinct()
        .first()
    )

    if not paziente:
        raise Http404("Paziente non trovato")


    if request.method == "POST":
        nome = f"{paziente.nome} {paziente.cognome}"
        paziente.delete()
        messages.success(request, f"✅ Paziente {nome} eliminato con successo.")
        return redirect("lista_pazienti")

    # Se si accede via GET, mostra la pagina di conferma
    return render(request, "prediction/confirm_delete_paziente.html", {"paziente": paziente})


@login_required
def calcola_eskd_rapido(request):
    """
    View per il calcolo ESKD rapido senza registrare un paziente.
    Permette di inserire i dati clinici e ottenere immediatamente una predizione.
    """
    from .forms import CalcoloESKDRapidoForm
    
    if request.method == "POST":
        form = CalcoloESKDRapidoForm(request.POST)
        if form.is_valid():
            form_data = form.cleaned_data
            
            # Prepara i dati per il modello
            # Converte sesso in formato numerico (M=0, F=1)
            sesso = form_data.get("sesso", "M")
            
            # Gestione dati MEST-C (possono essere vuoti)
            M_val = int(form_data.get("M")) if form_data.get("M") else 0
            E_val = int(form_data.get("E")) if form_data.get("E") else 0
            S_val = int(form_data.get("S")) if form_data.get("S") else 0
            T_val = int(form_data.get("T")) if form_data.get("T") else 0
            C_val = int(form_data.get("C")) if form_data.get("C") else 0
            
            # Calcola creatinina approssimativa da eGFR ed età
            # Formula inversa semplificata: Creatinina ≈ (140 - età) / eGFR
            # (formula molto approssimativa per avere un valore)
            eta = form_data.get("eta", 50)
            egfr = form_data.get("egfr", 60)
            creatinina_stimata = max(0.5, (140 - eta) / (egfr * 1.2))  # stima molto grezza
            
            # Determina ipertensione dai valori pressori
            pressione_sistolica = form_data.get("pressione_sistolica", 120)
            pressione_diastolica = form_data.get("pressione_diastolica", 80)
            iperteso = 1 if (pressione_sistolica >= 140 or pressione_diastolica >= 90) else 0
            
            # Gestione terapie
            antihypertensive = 1 if form_data.get("Antihypertensive", False) else 0
            immunosuppressants = 1 if form_data.get("Immunosuppressants", False) else 0
            fish_oil = 1 if form_data.get("FishOil", False) else 0
            
            # Costruzione dizionario dati per il modello
            data = {
                "sesso": sesso,
                "eta": float(eta),
                "iperteso": iperteso,
                "M": M_val,
                "E": E_val,
                "S": S_val,
                "T": T_val,
                "C": C_val,
                "proteinuria": float(form_data.get("proteinuria", 0)),
                "creatinina": float(creatinina_stimata),
                # Terapie dal form
                "Antihypertensive": antihypertensive,
                "Immunosuppressants": immunosuppressants,
                "FishOil": fish_oil,
            }
            
            # Esegui la predizione
            result = predict_risk(data)
            probabilita = result["probabilita"]
            esito = result["esito"]
            
            # Prepara i dati da mostrare nella pagina dei risultati
            dati_display = {
                "sesso": "Maschio" if sesso == "M" else "Femmina",
                "eta": eta,
                "pressione_sistolica": pressione_sistolica,
                "pressione_diastolica": pressione_diastolica,
                "egfr": egfr,
                "proteinuria": form_data.get("proteinuria"),
                "albumina": form_data.get("albumina"),
                "emoglobina": form_data.get("emoglobina"),
            }
            
            # Aggiungi dati MEST-C solo se presenti
            if M_val or E_val or S_val or T_val or C_val:
                dati_display.update({
                    "M": M_val,
                    "E": E_val,
                    "S": S_val,
                    "T": T_val,
                    "C": C_val,
                })
            
            # Aggiungi terapie ai dati visualizzati
            terapie = []
            if antihypertensive:
                terapie.append("Antipertensiva")
            if immunosuppressants:
                terapie.append("Immunosoppressori")
            if fish_oil:
                terapie.append("Olio di Pesce")
            
            if terapie:
                dati_display["terapie"] = terapie  # Lista invece di stringa
                dati_display["terapie_str"] = ", ".join(terapie)  # Anche la stringa per visualizzazione semplice
            else:
                dati_display["terapie"] = []
                dati_display["terapie_str"] = "Nessuna terapia"
            
            return render(request, "prediction/risultato_eskd_rapido.html", {
                "probabilita": probabilita,
                "esito": esito,
                "dati": dati_display,
            })
    else:
        form = CalcoloESKDRapidoForm()
    
    return render(request, "prediction/calcola_eskd_rapido.html", {
        "form": form,
    })


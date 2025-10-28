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

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
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
        form = UserCreationForm()
    
    return render(request, 'register.html', {'form': form})

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
    query = request.GET.get('q','')
    pazienti = Paziente.objects.filter(
        Q(medico=request.user) | Q(medici_condivisi=request.user)
    ).distinct().order_by('cognome', 'nome')
    if query:
        pazienti = pazienti.filter(
            Q(nome__icontains=query) | Q(cognome__icontains=query)
        )
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
    Paziente.objects.filter(Q(medico=request.user) | Q(medici_condivisi=request.user)),
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
    Paziente.objects.filter(Q(medico=request.user) | Q(medici_condivisi=request.user)),
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
    Paziente.objects.filter(Q(medico=request.user) | Q(medici_condivisi=request.user)),
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
    Paziente.objects.filter(Q(medico=request.user) | Q(medici_condivisi=request.user)),
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
    Paziente.objects.filter(Q(medico=request.user) | Q(medici_condivisi=request.user)),
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

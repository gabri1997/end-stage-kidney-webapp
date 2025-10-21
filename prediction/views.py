from django.shortcuts import render, redirect, get_object_or_404

# Create your views here.
from django.http import HttpResponse
from .models import Paziente, Visita, MESTC
from .forms import PazienteForm
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .forms import PazienteForm, VisitaForm, MESTCForm
from django.utils import timezone
from .model_loader import run_inference_from_data
from .models import Predizione, Visita, MestcRecord
from .forms import CalcolaESKDForm
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages


def home(request):
    return HttpResponse("Ciao, questa è la home di ESKD!")


def nuovo_paziente(request):
    if request.method == "POST":
        form = PazienteForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("lista_pazienti")
    else:
        form = PazienteForm()

    return render(request, "prediction/nuovo_paziente.html", {"form": form})

def lista_pazienti(request):
    pazienti = Paziente.objects.all().order_by("cognome", "nome")
    context = {"pazienti": pazienti}
    return render(request, "prediction/lista_pazienti.html", context)
    from django.shortcuts import get_object_or_404

@login_required
def dettaglio_paziente(request, paziente_id):
    paziente = get_object_or_404(Paziente, id=paziente_id, medico=request.user)
    visite = Visita.objects.filter(paziente=paziente).order_by("data_visita")
    mestc_records = MESTC.objects.filter(paziente=paziente).order_by("data_rilevazione")
    predizioni = Predizione.objects.filter(paziente=paziente).order_by("-data_predizione")

    ultima_predizione = predizioni.first()  # 👈 prendi la più recente

    return render(request, "prediction/dettaglio_paziente.html", {
        "paziente": paziente,
        "visite": visite,
        "mestc_records": mestc_records,
        "predizioni": predizioni,
        "ultima_predizione": ultima_predizione,  # 👈 passala al template
    })


@login_required
def nuova_visita(request, paziente_id):
    paziente = get_object_or_404(Paziente, id=paziente_id, medico=request.user)

    if request.method == "POST":
        form = VisitaForm(request.POST)
        if form.is_valid():
            visita = form.save(commit=False)
            visita.paziente = paziente
            visita.medico = request.user  
            visita.save()
            return redirect('dettaglio_paziente', paziente_id=paziente.id)

    else:
        form = VisitaForm()

    return render(request, "prediction/nuova_visita.html", {"form": form, "paziente": paziente})

@login_required
def nuovo_mestc(request, paziente_id):
    paziente = get_object_or_404(Paziente, id=paziente_id, medico=request.user)

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
    paziente = get_object_or_404(Paziente, id=paziente_id, medico=request.user)
    visita = get_object_or_404(Visita, id=visita_id, paziente=paziente)

    if request.method == "POST":
        form = VisitaForm(request.POST, instance=visita)
        if form.is_valid():
            visita = form.save(commit=False)
            visita.medico = request.user 
            visita.save()
            return redirect('dettaglio_paziente', paziente_id=paziente.id)

    else:
        form = VisitaForm(instance=visita)

    return render(request, "prediction/modifica_visita.html", {"form": form, "paziente": paziente, "visita": visita})


@login_required
def elimina_visita(request, paziente_id, visita_id):
    paziente = get_object_or_404(Paziente, id=paziente_id, medico=request.user)
    visita = get_object_or_404(Visita, id=visita_id, paziente=paziente)

    if request.method == "POST":
        visita.delete()
        return redirect('dettaglio_paziente', paziente_id=paziente.id)

    return render(request, "prediction/conferma_elimina_visita.html", {"paziente": paziente, "visita": visita})

@login_required
def modifica_mestc(request, paziente_id, mestc_id):
    paziente = get_object_or_404(Paziente, id=paziente_id, medico=request.user)
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
    paziente = get_object_or_404(Paziente, id=paziente_id, medico=request.user)
    mestc = get_object_or_404(MESTC, id=mestc_id, paziente=paziente)

    if request.method == "POST":
        mestc.delete()
        return redirect('dettaglio_paziente', paziente_id=paziente.id)

    return render(request, "prediction/conferma_elimina_mestc.html", {"paziente": paziente, "mestc": mestc})


@login_required
def calcola_eskd(request, paziente_id, visita_id):
    paziente = get_object_or_404(Paziente, id=paziente_id)
    visita = get_object_or_404(Visita, id=visita_id)
    mestc = MestcRecord.objects.filter(paziente=paziente).order_by('-data_rilevazione').first()

    if request.method == "POST":
        form = CalcolaESKDForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data

            data["Therapy"] = max(
                int(data.get("Antihypertensive", False)),
                int(data.get("Immunosuppressants", False)),
                int(data.get("FishOil", False)),
            )

            prob = run_inference_from_data(data)
            esito = "Positivo" if prob >= 0.5 else "Negativo"

            Predizione.objects.create(
                paziente=paziente,
                visita=visita,
                medico=request.user,
                probabilita_eskd=prob * 100,
                esito=esito
            )

            return redirect("dettaglio_paziente", paziente_id=paziente.id)
    else:
        initial = {
            "sesso": getattr(paziente, "sesso", ""),
            "eta": getattr(paziente, "eta", ""),
            "creatinina": getattr(visita, "creatinina", ""),
            "pressione_sistolica": getattr(visita, "pressione_sistolica", ""),
            "pressione_diastolica": getattr(visita, "pressione_diastolica", ""),
        }
        if mestc:
            initial.update({
                "M": mestc.M, "E": mestc.E, "S": mestc.S, "T": mestc.T, "C": mestc.C
            })

        form = CalcolaESKDForm(initial=initial)

    return render(request, "prediction/calcola_eskd.html", {
        "paziente": paziente,
        "visita": visita,
        "form": form
    })


@login_required
def modifica_paziente(request, paziente_id):
    paziente = get_object_or_404(Paziente, id=paziente_id)

    if request.method == "POST":
        form = PazienteForm(request.POST, instance=paziente)
        if form.is_valid():
            form.save()
            return redirect("dettaglio_paziente", paziente_id=paziente.id)
    else:
        form = PazienteForm(instance=paziente)

    return render(request, "prediction/modifica_paziente.html", {
        "paziente": paziente,
        "form": form
    })

from django.contrib import messages  # aggiungi questo import in alto

@login_required
def modifica_paziente(request, paziente_id):
    paziente = get_object_or_404(Paziente, id=paziente_id)

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

from django import template
from django.forms.boundfield import BoundField

register = template.Library()

@register.filter(name='addclass')
def addclass(value, arg):
    """Add a class to a form widget"""
    # Verifica che value sia un BoundField (campo di form)
    if isinstance(value, BoundField):
        return value.as_widget(attrs={'class': arg})
    # Se è già una stringa HTML, restituiscila così com'è
    return value


@register.filter(name='anni_eskd_fascia')
def anni_eskd_fascia(anni):
    """
    Converte il numero di anni in una fascia leggibile.
    
    Fasce:
    - < 1 anno
    - 1-3 anni
    - 3-5 anni
    - 5-7 anni
    - 7-10 anni
    - > 10 anni
    """
    if anni is None:
        return "-"
    
    try:
        anni = float(anni)
    except (ValueError, TypeError):
        return "-"
    
    if anni < 1:
        return "< 1 anno"
    elif anni < 3:
        return "1-3 anni"
    elif anni < 5:
        return "3-5 anni"
    elif anni < 7:
        return "5-7 anni"
    elif anni < 10:
        return "7-10 anni"
    else:
        return "> 10 anni"


@register.filter(name='anni_eskd_colore')
def anni_eskd_colore(anni):
    """
    Restituisce la classe CSS Bulma per il colore in base agli anni.
    Più basso è il numero, più urgente (rosso).
    """
    if anni is None:
        return "is-light"
    
    try:
        anni = float(anni)
    except (ValueError, TypeError):
        return "is-light"
    
    if anni < 1:
        return "is-danger"  # Rosso - urgente
    elif anni < 3:
        return "is-warning"  # Giallo/arancione
    elif anni < 5:
        return "is-info"  # Azzurro
    elif anni < 7:
        return "is-link"  # Blu
    elif anni < 10:
        return "is-primary"  # Verde-azzurro
    else:
        return "is-success"  # Verde - meno urgente
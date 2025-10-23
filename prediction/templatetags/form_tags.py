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
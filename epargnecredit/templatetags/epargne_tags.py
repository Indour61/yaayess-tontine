# epargnecredit/templatetags/epargne_tags.py
from django import template

register = template.Library()

@register.filter
def get_item(d, key):
    """
    Accède à d[key] quand d est un dict dans le template.
    Usage: {{ mon_dict|get_item:ma_clef }}
    """
    if isinstance(d, dict):
        return d.get(key)
    return None

# ... garde tes autres tags/filters déjà présents ici ...



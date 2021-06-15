from django import template
from  base.models import Emir
register = template.Library()
@register.simple_tag

def find_user_name(id_user):
    try:
        isim = Emir.objects.filter(id=id_user).filter(durum='Aktif').values_list('is_emri',flat=True).first()
        if isim is not None:
            return isim
        else:
            print(isim)
    except:
        return {}


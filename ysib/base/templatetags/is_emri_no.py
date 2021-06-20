from django import template
from  base.models import Valf,Emir
register = template.Library()
@register.simple_tag

def isemri(id):
    try:
        isemri=Valf.objects.filter(valf_test_id=id).first().is_emri_id
        is_emri = Emir.objects.filter(id=isemri).first().is_emri
        if is_emri is not None:
            return is_emri
        else:
            return "Hata!"
    except:
        return "Hata!"
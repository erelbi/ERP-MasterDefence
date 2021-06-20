from django import template
from  base.models import Valf
register = template.Library()
@register.simple_tag

def valf_no(id):
    try:
        vsn = Valf.objects.filter(valf_test_id=id).first().valf_montaj_id
        if vsn is not None:
            return vsn
        else:
            return "Hata!"
    except:
        return "Hata!"
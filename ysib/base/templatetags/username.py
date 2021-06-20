from django import template
from  base.models import User
register = template.Library()
@register.simple_tag

def user_name(id_user):
    try:
        isim = User.objects.filter(id=id_user).first().username
        if isim is not None:
            return isim
        else:
            return "Hata!"
    except:
        return "Hata!"
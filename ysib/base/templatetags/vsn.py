from django import template
from  base.models import Valf
register = template.Library()
@register.simple_tag

def valf_no(id,type):
    try:
        vsn = Valf.objects.filter(**{find_type_table(type):id}).first().id
        if vsn is not None:
            return vsn
        else:
            return "Hata!"
    except:
        return "Hata!"

def find_type_table(table):
    tableType = dict([
                    ('valfMontaj','valf_montaj_id'),
                    ('valfTest','valf_test_id'),
                    ('valfGovde','valf_govde_id'),
                    ('fm200','fm200_azot_id'),
                    ('havuz','havuz_id'),
                    ('finalMontaj','valf_final_montaj_id')
             ])
    return tableType[table]
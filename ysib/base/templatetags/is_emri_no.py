from django import template
from  base.models import Valf,Emir
register = template.Library()
@register.simple_tag


def isemri(id,type):
    try:
        isemri=Valf.objects.filter(**{find_type_table(type):id}).first().is_emri_id
        is_emri = Emir.objects.filter(id=isemri).first().is_emri
        if is_emri is not None:
            return is_emri
        else:
            return "Hata!"
    except:
        print("isemri : ",id)
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

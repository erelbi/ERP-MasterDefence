# from django import template
# from  base.models import Valf
# register = template.Library()
# @register.simple_tag

# def find_type_count(id_emir,colum):
#     try:
#         null_colum = "{}__isnull=False".format(colum)
#         val= str("'{}'".format(colum))
#         print(id_emir,null_colum,val)
#         return Valf.objects.filter(is_emri_id=57).filter(**null_colum).values_list(**val,flat=True).count()
#     except Exception as err:
#         print(err)
#         return 0
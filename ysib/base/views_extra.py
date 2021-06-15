from base.views import index
from django.http.request import QueryDict
from django.shortcuts import render,redirect
from .forms import UserRegisterForm, IsEmri ,TestForm
from django.contrib import messages
from django.contrib.auth import authenticate, login ,logout
from django.http import HttpResponseRedirect, HttpResponse ,JsonResponse
from django.urls import reverse
from django.db.models import Max, query
from django.contrib.auth.models import User
from .models import Emir , Test, Bildirim, Uretim, Valf,PDF_Rapor
from .models import Valf_montaj,Valf_test,Valf_govde,Valf_fm200,Valf_havuz,Valf_final_montaj
from django.contrib.auth.decorators import login_required
import json, platform, base64, datetime, os
from django.utils import timezone
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import FileSystemStorage
from django.template.loader import render_to_string
from weasyprint import HTML
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from base64 import b64decode
import time
from django.utils import six 
import itertools
from .forms import PDFForm
from datetime import datetime
# Create your views here.





@csrf_exempt
def valf_parti_no_ata(request):
    # ping_signal.send(sender="valf", PING=True)


    emir_valuelist = Emir.objects.filter(is_emri=request.POST.dict()['is_emri']).values_list('id', flat=True)
    print(Valf.objects.filter(is_emri_id=emir_valuelist[0]).values_list('valf_montaj_id',flat=True))

    valf_montaj_idleri= Valf.objects.filter(is_emri_id=emir_valuelist[0]).values_list('valf_montaj_id',flat=True)
  

    kurlenme_parti_noları = []
    for valf_montaj_id in valf_montaj_idleri :
        if  Valf_montaj.objects.filter(id=valf_montaj_id).first().kurlenme_parti_no is None:
            kurlenme_parti_noları.append(0)
        else:
            kurlenme_parti_noları.append(Valf_montaj.objects.filter(id=valf_montaj_id).first().kurlenme_parti_no) 
    print(max(kurlenme_parti_noları))
 
 
    #parti_no__max= valfler.aggregate(Max('kurlenme_parti_no'))['kurlenme_parti_no__max']  









    #valfler= Valf_montaj.objects.filter(is_emri= emir)
    #parti_no__max= valfler.aggregate(Max('kurlenme_parti_no'))['kurlenme_parti_no__max']  
    #if parti_no__max is None: 
    #    parti_no__max=0
    next_parti_no= max(kurlenme_parti_noları) + 1
 
    print("next_parti_no",next_parti_no)



    valfler_id=request.POST.dict()['valfler_id'] 
    print("valfler_id",valfler_id)
    valfler_id_array = json.loads(valfler_id)
    print(valfler_id_array)
    for id in valfler_id_array:
        valf  =  Valf_montaj.objects.get(id=id)
        if valf.kurlenme_parti_no is None:
            valf.kurlenme_parti_no=next_parti_no
            valf.kurlenme_baslangic_tarihi = timezone.now()
            valf.kurlenme_bitis_tarihi =  timezone.now()+timezone.timedelta(minutes=2)
            valf.kurlenme_personel = User.objects.get(id=request.user.id)
            valf.save()
 
    
    return HttpResponse('OK')


@csrf_exempt
def is_emri_valfleri(request):
    
    temp = []
    emir = Emir.objects.get(is_emri=request.POST.dict()['is_emri_id'])
    print("is_emir",emir)
    try:
        is_emir_valfleri =  Valf.objects.filter(is_emri=emir).values_list('valf_montaj',flat=True)
        print("is_emri_valfleri",is_emri_valfleri)
        # //is_emir_valfleri =  Valf_montaj.objects.filter(is_emri=emir)
    except Exception as err:
        is_emir_valfleri =  Valf.objects.filter(is_emri=emir).values_list('valf_montaj',flat=True)
    for is_id in is_emir_valfleri:
        veri={}
        veri['id'] = is_id
        veri['parti_no'] = Valf_montaj.objects.filter(id=is_id).first().kurlenme_parti_no
        temp.append(veri)
        
    # temp = []
    # for valf in is_emir_valfleri.values():
    #     temp.append(valf)
    # veri = list(temp)
    # print("veriiiiiii",list(temp)) 
    return JsonResponse(list(temp),safe=False)

@csrf_exempt
def montajKurlenme(request):
    montaj_list=[]
    try:
        for veri in json.loads(request.POST.dict()['veri']):
            clock = Valf_montaj.objects.filter(id=veri['id']).filter(kurlenme_parti_no=veri['parti_no']).first().kurlenme_bitis_tarihi - timezone.now()
            montaj={}
            montaj['tarih'] = time_calc(clock)
            montaj['partino'] = veri['parti_no']
            montaj['valfno'] = veri['id']
            montaj_list.append(montaj)
        
        
        return JsonResponse(list(montaj_list),safe=False)
       
    except Exception as err:
        print(err)
        return JsonResponse(list(montaj_list),safe=False)

# def duplicate_control_list(liste_montaj):
#     check=[]
#     for item in liste_montaj:
#         if item['partino'] in check:   
#             liste_montaj[check.pop()]['valfno'] = (liste_montaj[check.pop()]['valfno'],item['valfno'])
#             del item['partino']
#         else:
#             check.append(item['partino'])
#     return liste_montaj
        



def time_calc(data):
    if data.days == 0:
        
       return  "{}:{}".format(data.seconds//3600,(data.seconds//60)%60,data.seconds%60)
    else:
        return "Kürlenme Bitmiştir"



@csrf_exempt
def valf_test_kayıt(request):
    data_list = []
    user_id = request.user.id
    new_save = []
    update_save = []
    error_save = []
    for  veri in json.loads(request.POST.dict()['veri']):
        try:
            if (Valf.objects.filter(id=veri['seriNo']).first().valf_test_id):
                ''' Duplike var'''
                valf_id_find = Valf.objects.filter(id=veri['seriNo']).first().valf_test_id
                Valf_test.objects.filter(id=valf_id_find).update(acma=veri['ValfTest_Acma'],kapama=veri['ValfTest_Kapama'],sebep=veri['sebeb'],test_personel_id=user_id,test_tarihi=timezone.now(),uygun=veri['uygunluk'])
                update_save.append(veri['seriNo'])
            else:
                valf_test =Valf_test(acma=veri['ValfTest_Acma'],kapama=veri['ValfTest_Kapama'],sebep=veri['sebeb'],test_personel_id=user_id,test_tarihi=timezone.now(),uygun=veri['uygunluk'])
                valf_id = valf_test.save()
                valf = Valf.objects.get(id=veri['seriNo'])
                valf.valf_test_id = valf_test.id
                valf.save()
                new_save.append(veri['seriNo'])
        except:
            error_save.append(veri['seriNo'])
    return JsonResponse({'status':200,'remark':"Yeni Kayıt:{} Güncellenen Kayıt {}  Hatalı Kayıt {}".format(new_save,update_save,error_save)})



@csrf_exempt
def upload_pdf_rapor(request):
    try:
        if request.method == 'POST':
            if request.FILES and request.POST.dict():
                pdf_response = pdf_save_function(file=request.FILES['file'],filename=request.POST.dict()['pdf_ismi'])
                pdf_remark   = pdf_remark_save(data_pdf=request.POST.dict())
                if pdf_response and pdf_remark:
                    return JsonResponse({'status':200,'message': 'Kayıt Başarılı!'})
                else:
                    return JsonResponse({'status':500,'message': 'Kayıt işlemi baraşız!'})
            else:
                return JsonResponse({'status':400,'message': 'Dosya veya Data Hatası!'})  
    except Exception as err:
        return JsonResponse({'status':400,'message':err }) 


def pdf_save_function(file,filename):
    try:
        fs = FileSystemStorage()
        fs.save(filename,file)
        return True
    except Exception as err:
        print(err)
        return False

def pdf_remark_save(data_pdf):
    try:
        if data_pdf['uygun'] == "true":
            print("istasyon",data_pdf['istasyon'])
            istasyon_id = istasyon_find(data_pdf['istasyon'])
            #model_class = istasyon_model(istasyon_id)
            valf_id=Valf.objects.filter(valf_montaj_id=data_pdf['vsn']).values_list(istasyon_id,flat=True).first()
            # valf_model= hasattr(model_class,objects)## aşağıdaki kodu silicez daha güzelini hazırladık
            #print("istasyon",data_pdf['istasyon'])
            if data_pdf['istasyon'] == 'Valf Test':
                Valf_test.objects.filter(id=valf_id).update(uygun=True)
            
            elif data_pdf['istasyon'] == 'Valf Gövde':
                print("içerde")
                Valf_govde.objects.filter(id=valf_id).update(uygunluk=True)
            
            elif data_pdf['istasyon'] == 'Havuz Test':
                Valf_havuz.objects.filter(id=valf_id).update(uygunluk=True)
        rapor =  PDF_Rapor(istasyon=data_pdf['istasyon'],valf_seri_no=data_pdf['vsn'],pdf_ismi=data_pdf['pdf_ismi'],aciklama=data_pdf['aciklama'])
        rapor.save()
        return True           
    except Exception as err:
        print(err)
        return False

def istasyon_find(istasyon):
    try:
        istasyon_dict={
            'Valf Montaj':'valf_montaj_id',
            'Valf Test':'valf_test_id',
            'Valf Gövde':'valf_govde_id',
            'FM200&Azot':'fm200_azot_id',
            'Havuz Test':'havuz_id',
            'Final Montaj':'valf_final_montaj_id'

        }
        return istasyon_dict[istasyon]
    except Exception as err:
        print(err)
def istasyon_model(Valf_model):
    try:
        istasyon_model_dict={
            'valf_montaj_id':'Valf_montaj',
            'valf_test_id':'Valf_test',
            'valf_govde_id':'Valf_govde',
            'fm200_azot_id':'Valf_fm200',
            'havuz_id':'Valf_havuz',
            'valf_final_montaj_id':'Valf_final_montaj'

        }
        #print(istasyon_model_dict[Valf_model])
        return istasyon_model_dict[Valf_model]
    except Exception as err:
        print(err)



    

# def control_vsn(vsn):
#     try:
#         Valf_test.objects.filter(id)



###############Valf Govde################################

def duplicate_control_govde(id):
    return Valf.objects.filter(valf_montaj_id=id).values_list('valf_govde_id',flat = True).first()

@csrf_exempt
def valf_govde_save(request):   
    print("valf_govde_içerde")
    try:
        valf_govde_veri_list = json.loads(request.POST.dict()['veri'])
        valf_main = Valf.objects.get(id=valf_govde_veri_list[0])
        if  duplicate_control_govde(valf_govde_veri_list[0]) is  None:
            if valf_govde_veri_list[4] == True:
                govde = Valf_govde(tork=valf_govde_veri_list[3],tup_seri_no=valf_govde_veri_list[1] ,sodyum_miktari=valf_govde_veri_list[2],govde_personel_id=request.user.id,uygunluk=True,govde_tarihi=timezone.now())
                print("govde-----True")
            else:
                print("uygundegil")
                govde = Valf_govde(tork=valf_govde_veri_list[3],tup_seri_no=valf_govde_veri_list[1] ,sodyum_miktari=valf_govde_veri_list[2],uygunluk=False,sebep=valf_govde_veri_list[5],govde_personel_id=request.user.id,govde_tarihi=timezone.now())
            govde.save()
            valf_main.valf_govde_id = govde.id
            valf_main.save()
        else:
            print("duplike var")
            Valf_govde.objects.filter(id=valf_main.valf_govde_id).update(tork=valf_govde_veri_list[3],tup_seri_no=valf_govde_veri_list[1] ,sodyum_miktari=valf_govde_veri_list[2],uygunluk=valf_govde_veri_list[4],sebep=valf_govde_veri_list[5],govde_personel_id=request.user.id,govde_tarihi=timezone.now())
           
            return JsonResponse({'status':201,'remark':"Güncelleme İşlemi Başarılı!"})
            
      
        return JsonResponse({'status':200,'remark':"Save"})
    except Exception as err:
        print("valf_govde_hata----->",err)
        



##############Valf Govde Kontrol###############################
@csrf_exempt
def GovdekontrolEt(request):
    if request.method == 'POST':
        try:
            valf_id=Valf.objects.filter(valf_montaj_id=request.POST['veri']).values_list('valf_test_id',flat = True).first()       
            if isinstance(valf_id,int):
                Valf_test.objects.filter(id=valf_id).values_list('uygun',flat = True).first()
                if (Valf_test.objects.filter(id=valf_id).values_list('uygun',flat = True).first()):
                    response = {'status':"OK"}
                else:
                    response = {'status':"NO",'remark':"Bu valfin; valf test adımı başarısız!"}
            else:
                response = {'status':"NO",'remark':"Valf Mevcut Değil!"}
        except:
            response = {'status':"NO",'remark':"Sunucu Fonksiyon Hatası!"}

    return JsonResponse(response)


####################Govde Kurlenme Kontrol##############################

@csrf_exempt
def kurlenme_govde(request):
    list_govde=[]
    is_emri_id = request.POST.dict()['is_emri_id']
    for govde in Valf.objects.filter(is_emri_id=is_emri_id).filter(valf_govde_id__isnull=False).values_list('valf_govde_id',flat=True):
        if uygunluk_kontrol(govde):
            dict_govde = {}
            dict_govde['id'] = Valf.objects.filter(valf_govde_id=govde).values_list('id',flat=True).first()
            dict_govde['parti'] = Valf_govde.objects.filter(id=govde).values_list('govde_kurlenme_parti_no',flat=True).first()
            list_govde.append(dict_govde)
        else:
            print("uygun değil")
            pass
    print(list_govde)
    return JsonResponse(list(list_govde),safe=False)
    


    
    #uygunluk = Valf_govde.objects.filter(id=govde_id).values_list('uygunluk',flat=True)
    #print(uygunluk)


def uygunluk_kontrol(govde):
    try:
       print(type(Valf_govde.objects.filter(id=govde).values_list('uygunluk',flat=True).first()))
       return  Valf_govde.objects.filter(id=govde).values_list('uygunluk',flat=True).first()
    except Exception as err:
        print(err)
        return False


################Govde kurlenme Ata############################
@csrf_exempt
def valf_govde_parti_no_ata(request):
    print(request.POST.dict()['is_emri'])
    print(request.POST.dict()['valfler_id'])
    #valf_govde_idleri = Valf.objects.filter(is_emri_id=request.POST.dict()['is_emri']).values_list('valf_govde_id', flat=True)
    emir_valuelist = Emir.objects.filter(id=request.POST.dict()['is_emri']).values_list('id', flat=True)
    #print(Valf.objects.filter(is_emri_id=emir_valuelist[0]).values_list('valf_govde_id',flat=True))
   
    valf_govde_idleri= Valf.objects.filter(is_emri_id=emir_valuelist[0]).filter(valf_govde_id__isnull=False).values_list('valf_govde_id',flat=True)
    print(valf_govde_idleri)

   
    
    kurlenme_parti_noları = []
    try:
        for valf_id in valf_govde_idleri :
            print("değer",valf_id)
            if  Valf_govde.objects.filter(id=valf_id).first().govde_kurlenme_parti_no is None:
                kurlenme_parti_noları.append(0)
            else:   
               kurlenme_parti_noları.append(Valf_govde.objects.filter(id=valf_id).first().govde_kurlenme_parti_no)
        next_parti_no= max(kurlenme_parti_noları) + 1
    except Exception as err:
        print("error",err)
    print("next_parti_no",next_parti_no)




    valfler_id=request.POST.dict()['valfler_id'] 
    print("valfler_id",valfler_id)
    valfler_id_array = json.loads(valfler_id)
    print(valfler_id_array)
    for id in valfler_id_array:
        valf  =  Valf_govde.objects.get(id=Valf.objects.filter(id=id).values_list('valf_govde_id',flat=True).first())
        if valf.govde_kurlenme_parti_no is None:
            valf.govde_kurlenme_parti_no=next_parti_no
            valf.govde_kurlenme_baslangic_tarihi = timezone.now()
            valf.govde_kurlenme_bitis_tarihi =  timezone.now()+timezone.timedelta(minutes=2)
            valf.govde_kurlenme_personel = User.objects.get(id=request.user.id)
            valf.save()
 
    
    return HttpResponse('OK')



################Govde kurlenme tarih getir##########
@csrf_exempt
def govdemontajKurlenme(request):
    govde_list=[]
    for list_govde in Valf.objects.filter(is_emri_id=request.POST.dict()['is_emri']).values_list('valf_govde_id',flat=True):
         if list_govde != None:
             govde_list.append(list_govde)
    print("--------------Zaman------------------")
    print(govde_list)
    print(request.POST.getlist('parti_no[]'))
    print("---------------Zaman-----------------")
    montaj_list=[]
    try:
        if  len(request.POST.getlist('parti_no[]')[0]) > 0:
            for parti_no,is_emri in zip(request.POST.getlist('parti_no[]'),govde_list):
                print(parti_no,is_emri)
                clock = Valf_govde.objects.filter(id=is_emri).filter(govde_kurlenme_parti_no=parti_no).first().govde_kurlenme_bitis_tarihi - timezone.now()
                print("zaman",timezone.now())
                print(clock)
                print(Valf_govde.objects.filter(govde_kurlenme_parti_no=parti_no).first().govde_kurlenme_bitis_tarihi )
                montaj={}
                montaj['tarih'] = time_calc(clock)
                montaj['partino'] = parti_no
                valf_no_list=[]
                for valf_no in  Valf_govde.objects.filter(govde_kurlenme_parti_no=parti_no).values_list('id',flat=True):  
                    valf_no_list.append(valf_no)
                montaj['valfno'] = Valf.objects.filter(valf_govde_id=valf_no).values_list('id',flat=True).first()
                print("------------------>",valf_no_list)
                montaj_list.append(montaj)
            return JsonResponse(list(montaj_list),safe=False)
        else:
            return JsonResponse(list(montaj_list),safe=False)
    except Exception as err:
        print(err)
        return JsonResponse(list(montaj_list),safe=False)


# def time_calc(data):
#     print("data.days",data.days)
#     if data.days == 0:
        
#        return  "{}:{}".format(data.seconds//3600,(data.seconds//60)%60,data.seconds%60)
#     else:
#         return "Kürleme Bitmiştir"
    

##############FM200Kontrol###############################
@csrf_exempt
def FM200kontrolEt(request):
    if request.method == 'POST':
        try:
            valf_id=Valf.objects.filter(valf_montaj_id=request.POST['veri']).values_list('valf_govde_id',flat = True).first()     
            if isinstance(valf_id,int):
                print("-----------")
                Valf_govde.objects.filter(id=valf_id).values_list('uygunluk',flat = True).first()
                kurlenme_bitis = Valf_govde.objects.filter(id=valf_id).values_list('govde_kurlenme_bitis_tarihi',flat = True).first()
                print("değerler",kurlenme_bitis,Valf_govde.objects.filter(id=valf_id).values_list('uygunluk',flat = True).first())
                print(valf_id,timezone.now())
                if (Valf_govde.objects.filter(id=valf_id).values_list('uygunluk',flat = True).first()) :
                    if kurlenme_bitis < timezone.now():
                        response = {'status':"OK"}
                    else:
                        response = {'status':"NO",'remark':"Bu valfin; kürlenmesi bitmemiş!"}
                else:
                    response = {'status':"NO",'remark':"Bu valfin; valf test adımı başarısız!"}
            else:
                response = {'status':"NO",'remark':"Valf Mevcut Değil!"}
        except:
            response = {'status':"NO",'remark':"Sunucu Fonksiyon Hatası!"}

    return JsonResponse(response)


def duplicate_control_fm200(id):
    return Valf.objects.filter(valf_montaj_id=id).values_list('fm200_azot_id',flat = True).first()

@csrf_exempt
def fm200_save(request):
    print("fm200_içerde")
    try:
        fm200_veri_list = json.loads(request.POST.dict()['veri'])
        valf_main = Valf.objects.get(id=fm200_veri_list[0])
        print(valf_main)
        if  duplicate_control_fm200(fm200_veri_list[0]) is  None:
            fm200 = Valf_fm200(bar=fm200_veri_list[1],fm200=fm200_veri_list[2],fm200_personel_id=request.user.id,bos_agirlik=fm200_veri_list[3],dolu_agirlik=fm200_veri_list[4],kayit_tarihi=timezone.now())
            fm200.save()
            valf_main.fm200_azot_id = fm200.id
            valf_main.save()
        else:
            print("duplike var")
            Valf_fm200.objects.filter(id=valf_main.fm200_azot_id).update(bar=fm200_veri_list[1],fm200=fm200_veri_list[2],fm200_personel_id=request.user.id,bos_agirlik=fm200_veri_list[3],dolu_agirlik=fm200_veri_list[4],kayit_tarihi=timezone.now())
            return JsonResponse({'status':201,'remark':"Güncelleme İşlemi Başarılı!"})
            
      
        return JsonResponse({'status':200,'remark':"Save"})
    except Exception as err:
        print("fm200_hata----->",err)
    


####################FM200 Kurlenme Kontrol##############################

@csrf_exempt
def kurlenme_fm200(request):
    list_fm200=[]
    is_emri_id = request.POST.dict()['is_emri_id']
    for fm200 in Valf.objects.filter(is_emri_id=is_emri_id).filter(fm200_azot_id__isnull=False).values_list('fm200_azot_id',flat=True):
            dict_fm200 = {}
            dict_fm200['id'] = Valf.objects.filter(fm200_azot_id=fm200).values_list('id',flat=True).first()
            dict_fm200['parti'] = Valf_fm200.objects.filter(id=fm200).values_list('fm200_parti_no',flat=True).first()
            list_fm200.append(dict_fm200)
    print(list_fm200)
    return JsonResponse(list(list_fm200),safe=False)

#################FM200 Kurlenme ATA ##################################

@csrf_exempt
def valf_fm200_parti_no_ata(request):
    print(request.POST.dict()['is_emri'])
    print(request.POST.dict()['valfler_id'])
    #valf_govde_idleri = Valf.objects.filter(is_emri_id=request.POST.dict()['is_emri']).values_list('valf_govde_id', flat=True)
    emir_valuelist = Emir.objects.filter(id=request.POST.dict()['is_emri']).values_list('id', flat=True)
    #print(Valf.objects.filter(is_emri_id=emir_valuelist[0]).values_list('valf_govde_id',flat=True))
   
    valf_fm200_idleri= Valf.objects.filter(is_emri_id=emir_valuelist[0]).filter(fm200_azot_id__isnull=False).values_list('fm200_azot_id',flat=True)
    
    kurlenme_parti_noları = []
    try:
        for valf_id in valf_fm200_idleri :
            print("değer",valf_id)
            if  Valf_fm200.objects.filter(id=valf_id).first().fm200_parti_no is None:
                kurlenme_parti_noları.append(0)
            else:   
               kurlenme_parti_noları.append(Valf_fm200.objects.filter(id=valf_id).first().fm200_parti_no)
        next_parti_no= max(kurlenme_parti_noları) + 1
    except Exception as err:
        print("error",err)
    print("next_parti_no",next_parti_no)




    valfler_id=request.POST.dict()['valfler_id'] 
    print("valfler_id",valfler_id)
    valfler_id_array = json.loads(valfler_id)
    print(valfler_id_array)
    for id in valfler_id_array:
        valf  =  Valf_fm200.objects.get(id=Valf.objects.filter(valf_montaj_id=id).values_list('fm200_azot_id',flat=True).first()) 
        if valf.fm200_parti_no is None:
            valf.fm200_parti_no=next_parti_no
            valf.fm200_kurlenme_baslangic_tarihi = timezone.now()
            valf.fm200_kurlenme_bitis_tarihi =  timezone.now()+timezone.timedelta(minutes=2)
            valf.fm200_kurlenme_personel_id = User.objects.get(id=request.user.id)
            valf.save()
 
    
    return HttpResponse('OK')

##########fm2000 kurlenme getir########3
@csrf_exempt
def fm200Kurlenme(request):
    print(request.POST.getlist('parti_no[]'))
    fm200_list=[]
    for fm200 in Valf.objects.filter(is_emri_id=request.POST.dict()['is_emri']).values_list('fm200_azot_id',flat=True):
         if fm200 != None:
             fm200_list.append(fm200)
    montaj_list=[]
    try:
        if  len(request.POST.getlist('parti_no[]')[0]) > 0:
            for parti_no,is_emri in zip(request.POST.getlist('parti_no[]'),fm200_list):
                clock = Valf_fm200.objects.filter(id=is_emri).filter(fm200_parti_no=parti_no).first().fm200_kurlenme_bitis_tarihi - timezone.now()
                montaj={}
                montaj['tarih'] = time_calc(clock)
                montaj['partino'] = parti_no
                valf_no_list=[]
                for valf_no in  Valf_fm200.objects.filter(fm200_parti_no=parti_no).values_list('id',flat=True):  
                    valf_no_list.append(valf_no)
                montaj['valfno'] = Valf.objects.filter(fm200_azot_id=valf_no).values_list('id',flat=True).first()
                montaj_list.append(montaj)
            return JsonResponse(list(montaj_list),safe=False)
        else:
            return JsonResponse(list(montaj_list),safe=False)
    except Exception as err:
        print(err)
        return JsonResponse(list(montaj_list),safe=False)

@csrf_exempt
def fm200deger(request):
    is_emri_id=Valf.objects.filter(valf_montaj_id=request.POST.dict()['valf_seri_no']).values_list('is_emri_id',flat=True).first()
    BosAgirlikMinDeger = Emir.objects.filter(id=is_emri_id).values_list('fm200bosagirlikmindeger',flat=True).first()
    BosAgirlikMaxDeger = Emir.objects.filter(id=is_emri_id).values_list('fm200bosagirlikmaxdeger',flat=True).first()
    FM200DolumMiktariMinDeger = Emir.objects.filter(id=is_emri_id).values_list('fm200dolummiktarimindeger',flat=True).first()
    FM200DolumMiktariMaxDeger = Emir.objects.filter(id=is_emri_id).values_list('fm200dolummiktarimaxdeger',flat=True).first()
    FM200TupGovdeYapısı = Emir.objects.filter(id=is_emri_id).values_list('tup_govde_turu',flat=True).first()
    return JsonResponse({'BosAgirlikMinDeger':BosAgirlikMinDeger,'BosAgirlikMaxDeger':BosAgirlikMaxDeger,'FM200DolumMiktariMinDeger':FM200DolumMiktariMinDeger,'FM200DolumMiktariMaxDeger':FM200DolumMiktariMaxDeger,'FM200TupGovdeYapısı':FM200TupGovdeYapısı} )
# def time_calc(data):
#     print(data.days)
#     if data.days == 0:
        
#        return  "{}:{}".format(data.seconds//3600,(data.seconds//60)%60,data.seconds%60)
#     else:
#         return "Kürleme Bitmiştir"
#################Havuz####################
@csrf_exempt
def havuztestsave(request):
     kayıt=[]
     if len(json.loads(request.POST.dict()['veri'])) > 0 :
        for  veri in json.loads(request.POST.dict()['veri']):
            print(veri)
            try:
                valf_main = Valf.objects.get(id=veri['seriNo'])
                if  duplicate_control_havuztest(veri['seriNo']) is  None:
                    havuz = Valf_havuz(uygunluk=veri['uygunluk'], sebep=veri['sebeb'], kayit_tarihi=timezone.now(), tup_cidar_sicaklik=veri['sicaklik'], tup_basinc=veri['basinc'], havuz_personel=request.user)
                    havuz.save()
                    valf_main.havuz_id = havuz.id
                    valf_main.save()
                    kayıt.append(veri['seriNo'])
                else:
                    print("duplike  var")
                    Valf_havuz.objects.filter(id=Valf.objects.filter(id=veri['seriNo']).values_list('havuz_id',flat=True).first()).update(uygunluk=veri['uygunluk'], sebep=veri['sebeb'], kayit_tarihi=timezone.now(), tup_cidar_sicaklik=veri['sicaklik'], tup_basinc=veri['basinc'], havuz_personel=request.user)
                    
                    kayıt.append(veri['seriNo'])
            except Exception as err:
                print(err)
                return JsonResponse({'code':400,'remark':"Kayıt işleminde Hata tespit edildi"})
        print(kayıt)
        return JsonResponse({'code':200,'vsn':kayıt})
     else:
         return JsonResponse({'code':400,'remark':"Boş Değer Gönderdiniz!"})

def duplicate_control_havuztest(id):
    return Valf.objects.filter(id=id).values_list('havuz_id',flat = True).first()

#################Havuz ID Kontrol##################
@csrf_exempt
def havuztestcontrol(request):
    ### burda nerden kontrol edeceğim&Valf  id den aldım
    try:
        check_id = Valf.objects.filter(id=request.POST.dict()['veri']).values_list('fm200_azot_id',flat=True).first()
        if check_id is None:
            print("None")
            return JsonResponse({'code':400,'remark':'Seri No bulunumadı!'})
        else:
            date_value = Valf_fm200.objects.filter(id=check_id).first().fm200_kurlenme_bitis_tarihi
            print(date_value)
            if date_value<timezone.now():
                print("can not finished")
                return  JsonResponse({'code':200,'remark':'Kürlenmesi tamamlanmış'})
            else:
                print("finished")
                return  JsonResponse({'code':201,'remark':'Kürlenmesi tamamlanmamış'})
    except Exception as err:
        print(err)
        return  JsonResponse({'code':500,'remark':"err"})


###############Final Montaj#####################
@csrf_exempt
def finalmontajcontrol(request):
      try:
        check_id = Valf.objects.filter(id=request.POST.dict()['veri']).values_list('havuz_id',flat=True).first()
        if check_id is None:
            
            return JsonResponse({'code':400,'remark':'Seri No bulunumadı!'})
        else:
            
            if Valf_havuz.objects.filter(id=check_id).first().uygunluk:
                return  JsonResponse({'code':200,'remark':'Uygun'})
            else:
                return  JsonResponse({'code':201,'remark':'Uygun Değil'})
      except Exception as err:
        return  JsonResponse({'code':500,'remark':"err"})

@csrf_exempt
def finalmontajsave(request):
    try:
            print(request.POST.dict())
            vsn = request.POST.dict()['vsn']
            valf_main = Valf.objects.get(id=int(vsn))
            if duplicate_control_finalmontaj(int(vsn)) is None:
                final_montaj=Valf_final_montaj(urun_seri_no=request.POST.dict()['etiket'], funye_seri_omaj=request.POST.dict()['fso'], basinc_anahtari_omaj=request.POST.dict()['bao'], kayit_tarihi=timezone.now(), funye_seri_no=request.POST.dict()['fsn'])
                final_montaj.save()
                valf_main.valf_final_montaj_id = final_montaj.id
                valf_main.save()
                return JsonResponse({'code':200,'remark':"Kayıt Başarılı"})
            else:
                Valf_final_montaj.objects.filter(id=duplicate_control_finalmontaj(vsn)).update(urun_seri_no=request.POST.dict()['etiket'], funye_seri_omaj=request.POST.dict()['fso'], basinc_anahtari_omaj=request.POST.dict()['bao'], kayit_tarihi=timezone.now(), funye_seri_no=request.POST.dict()['fsn'])
                return JsonResponse({'code':201,'remark':"Güncelleme Başarılı!"})
     
    except Exception as err:
         return JsonResponse({'code':500,'remark':"{}".format(err)})

def duplicate_control_finalmontaj(id):
    print(id)
    return Valf.objects.filter(id=id).values_list('valf_final_montaj_id',flat = True).first()


@csrf_exempt
def yazdirtest(request):
    try:
        vsn = request.POST.dict()['veri']
        if Valf.objects.filter(id=vsn).values_list('valf_final_montaj_id',flat=True).count()==1:
            return JsonResponse({'status':'OK'})
        elif Valf.objects.filter(id=vsn).values_list('valf_final_montaj_id',flat=True).count()==0:
            return JsonResponse({'status':'NO'})
        else:
            return JsonResponse({'status':'ERR'})
    except Exception as err:
        return JsonResponse({'status':'ERR'})
@csrf_exempt
def isemridurumdegistir(request):
    durum = request.POST.dict()['durum']
    isemri = request.POST.dict()['isemri']
    try:
        Emir.objects.filter(is_emri=isemri).update(durum=durum)
        return JsonResponse({'status':200,'remark':"Durum Değiştirildi"})
    except Exception as err:
        return JsonResponse({'status':400,'remark':"{}".format(err)})

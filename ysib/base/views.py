from django.shortcuts import render,redirect
from .forms import UserRegisterForm, IsEmri ,TestForm,PDF_Rapor
from django.contrib import messages
from django.contrib.auth import authenticate, login ,logout
from django.http import HttpResponseRedirect, HttpResponse ,JsonResponse
from django.urls import reverse
from django.db.models import Max
from django.contrib.auth.models import User
from .models import Emir , Test, Bildirim, Uretim, Valf
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

# Create your views here.

#mac = platform.machine()[:3] # eğer device ras pi ise 'arm' döner
server = '192.168.1.38:8000'
def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
        print(ip)
    return ip



def bildirim(request):
    bugun = timezone.now()
    birGunOnce = bugun - timezone.timedelta(days=14)
    bildirimq = Bildirim.objects.filter(zaman__range=[birGunOnce,bugun])
    temp = []
    for o in bildirimq.values():
        temp.append(o)
    bildirims = list(temp)
    print(bildirims)
    return JsonResponse(bildirims,safe=False)

@login_required
def index(request):
        #Bildirim.objects.all().delete()
         
        grup = request.user.grup
        birim = request.user.birim
        emirler = Emir.objects.filter(durum="Aktif")
        l = list()
        for e in emirler.values():
           
            data = dict()
            data['is_emri'] = e['is_emri']
            data['valfmontaj'] = Valf.objects.filter(is_emri_id=e['id']).filter(valf_montaj_id__isnull=False).values_list('valf_montaj_id',flat=True).count()or 0
            data['valftest'] = Valf.objects.filter(is_emri_id=e['id']).filter(valf_test_id__isnull=False).values_list('valf_test_id',flat=True).count()or 0
            data['valfgovde'] =Valf.objects.filter(is_emri_id=e['id']).filter(valf_govde_id__isnull=False).values_list('valf_govde_id',flat=True).count()or 0
            data['fm200'] = Valf.objects.filter(is_emri_id=e['id']).filter(fm200_azot_id__isnull=False).values_list('fm200_azot_id',flat=True).count()or 0
            data['havuztest'] = Valf.objects.filter(is_emri_id=e['id']).filter(havuz_id__isnull=False).values_list('havuz_id',flat=True).count()or 0
            data['finalmontaj'] = Valf.objects.filter(is_emri_id=e['id']).filter(valf_final_montaj_id__isnull=False).values_list('valf_final_montaj_id',flat=True).count()or 0
            l.append(data)
        print(l)

        return render(request,'index.html', {  'grup' : grup, "emirler" : emirler, 'birim': birim,'server' : server,'uretims':l})
@login_required
def arama(request):
        mac = request.user_agent.os.family
        q = request.GET.get('q') or request.GET.get('uretim')
        emir = request.GET.get('emir')
        emirs = Emir.objects.all()
        media_url = settings.MEDIA_URL
        aranan = ""
        if q:
                aranan = q
        elif emir:
                aranan = "isemri"
        else:
                print('bos')
        grup = request.user.grup
        birim = request.user.birim
        testler = Test.objects.filter(tur=q)
        # valfmontaj=Valf_montaj.objects.all()
        # valfgovde=Valf_govde.objects.all()
        # finalmontaj=Valf_final_montaj.objects.all()
        # fm200=Valf_fm200.objectsobjects.all()
        print(q)
        # if q == "valfmontaj":
        #     uretims = Uretim.objects.filter(tur="kurlenme")
        # else:
        #     uretims = Uretim.objects.filter(tur=q)
        #     print(uretims)
        if q == "valfmontaj":
             uretims = Valf_montaj.objects.all()
        elif q == "valfgovde":
            uretims = Valf_govde.objects.all()
        elif q == "fm200":
            uretims = Valf_fm200.objects.all()
        elif q == "havuztest":
            uretims = Valf_havuz.objects.all()
        elif q == "finalmontaj":
            uretims = Valf_final_montaj.objects.all()
        else:
             uretims = Uretim.objects.filter(tur=q)
             print(uretims)
        if emir == "tumu":
                emirler = Emir.objects.all()
        else:
                emirler = Emir.objects.filter(is_emri=emir)
        return render(request,'arama.html',{ 'mac' : mac , 'testler' : testler , 'grup': grup,"emirler": emirler, "aranan": aranan, "emirs":emirs, 'birim': birim,'media_url':media_url,"uretims":uretims,'server' : server})
@login_required
@csrf_exempt
def giriskalite(request):
        mac = request.user_agent.os.family
        grup = request.user.grup
        birim = request.user.birim
        #Test.objects.all().delete()  #Test sonuçlarını silmek için
        fullname = request.user.first_name + ' ' + request.user.last_name
        if request.method == 'POST':
                if request.POST.dict()['tur'] == 'basinc':
                        veris = json.loads(request.POST.dict()['veri'])
                        for veri in veris:
                                t = Test(tur='basinc',seri_no = veri[0] , acma = veri[1] , kapatma = veri[2], kabul_durumu = veri[3], testi_yapan = fullname)
                                t.save(force_insert=True)
                elif request.POST.dict()['tur'] == 'manometre':
                        veris = json.loads(request.POST.dict()['veri'])
                        for veri in veris:
                                t = Test(tur='manometre',seri_no = veri[0] , okunan_deger = veri[1], kabul_durumu = veri[2] ,testi_yapan = fullname)
                                t.save(force_insert=True)
                elif request.POST.dict()['tur'] == 'altnipel':
                        print(request.POST)

                        kontrolResult= nipelSeriNoKontrol(request)
                        if kontrolResult == True :
                            if request.FILES:
                                upload_file = request.FILES['file']
                                fs = FileSystemStorage()
                                fs.save(upload_file.name,upload_file)
                            next_lot_no = getNextLotNo( request.POST.dict()['tur'])

                            t = Test(tur='altnipel',lot_no = next_lot_no , pdf_ismi = request.POST.get('pdf_ismi') ,baslangic_seri_no = request.POST.get('baslangic_seri_no'),bitis_seri_no = request.POST.get('bitis_seri_no'), kabul_durumu = request.POST.get('kabulAlt'),testi_yapan = fullname)
                            t.save(force_insert=True)
                            messages.success(request,'Alt nipel testi başarıyla kaydedildi.')
                elif request.POST.dict()['tur'] == 'ustnipel':
                        print(request.POST)

                        kontrolResult= nipelSeriNoKontrol(request)
                        if kontrolResult == True :
                            if request.FILES:
                                upload_file = request.FILES['file']
                                fs = FileSystemStorage()
                                fs.save(upload_file.name,upload_file)
                            next_lot_no = getNextLotNo( request.POST.dict()['tur'])
                            t = Test(tur='ustnipel',lot_no = next_lot_no  , pdf_ismi = request.POST.get('pdf_ismi') ,baslangic_seri_no = request.POST.get('baslangic_seri_no'),bitis_seri_no = request.POST.get('bitis_seri_no'), kabul_durumu = request.POST.get('kabulUst'),testi_yapan = fullname)
                            t.save(force_insert=True)
                            messages.success(request,'Üst nipel testi başarıyla kaydedildi.')
                elif request.POST.dict()['tur'] == 'bakirmembran':
                     
                        print(request.POST)                       
                        
                        next_lot_no = getNextLotNo( request.POST.get('test_tur') )
                        if request.FILES:
                            upload_file = request.FILES['file']
                            fs = FileSystemStorage()
                            fs.save(upload_file.name,upload_file)
                        t = Test(tur=request.POST.get('test_tur'), lot_no =  next_lot_no, pdf_ismi = request.POST.get('pdf_ismi') ,test_basinci = request.POST.get('test_basinci'),
                        patlama_basinci = request.POST.get('patlama_basinci'), kabul_durumu = request.POST.get('kabulBak'),testi_yapan = fullname)
                        t.save(force_insert=True)
                        if(request.POST.get('test_tur') =='bakirmembran'):
                            messages.success(request,'Bakır membran testi başarıyla kaydedildi.')
                        else:
                            messages.success(request,'Emniyet ventili testi başarıyla kaydedildi.')


                        """
                elif request.POST.get('tur') == 'emniyet':
                        print(request.POST)
                        if request.FILES:
                            upload_file = request.FILES['file']
                            fs = FileSystemStorage()
                            fs.save(upload_file.name,upload_file)
                       
                        next_lot_no = getNextLotNo( request.POST.dict()['tur'])
                        t = Test(tur='emniyet',lot_no =next_lot_no, pdf_ismi = request.POST.get('pdf_ismi') ,test_basinci = request.POST.get('test_basinci'), patlama_basinci = request.POST.get('patlama_basinci'),kabul_durumu = request.POST.get('kabulEmn'),testi_yapan = fullname)
                        t.save(force_insert=True)
                        messages.success(request,'Emniyet ventili testi başarıyla kaydedildi.')
                        """
      
        return render(request,'giris-kalite-kontrol.html',{ 'mac' : mac , 'grup': grup, 'birim': birim,'server' : server})


def getNextLotNo(tur):
    test_with_max_lot_no = Test.objects.filter(tur=tur).order_by('-lot_no').first()
    if(test_with_max_lot_no == None):
        max_lot_no=0
    else:
        max_lot_no=test_with_max_lot_no.lot_no
    return max_lot_no + 1 

def nipelSeriNoKontrol(request):
    baslangic_seri_no = request.POST.get('baslangic_seri_no')
    bitis_seri_no = request.POST.get('bitis_seri_no')
    errorFlag=0
    if(int(baslangic_seri_no) > int(bitis_seri_no)):
        errorFlag=1
        messages.warning(request,'Başlangıç seri numarası, bitiş seri numarasından büyük olamaz!')  
        return False                          
    
    testler = Test.objects.filter(tur=request.POST.dict()['tur'] )
    seri_no_aralık_range= range(int(baslangic_seri_no),int(bitis_seri_no)+1)
    seri_no_aralık_list= set(seri_no_aralık_range)
    for test in testler:
        seri_no_aralık_test_range= range(int(test.baslangic_seri_no),int(test.bitis_seri_no)+1)
        intersection_set= seri_no_aralık_list.intersection(seri_no_aralık_test_range)
        if len(intersection_set) !=  0  :
            messages.warning(request,'Seri numarası aralığı mevcut bir seri numarası aralığı ile çakışmaktadır!')
            return False

    return True

@login_required
@csrf_exempt
def uretimkontrol(request):
        mac = request.user_agent.os.family

        ip = get_client_ip(request)
        ip == '192.168.1.36'

        grup = request.user.grup
        birim = request.user.birim

        #Uretim.objects.all().delete()  #Test sonuçlarını silmek için bu yorumu açabilirsiniz
        fullname = request.user.first_name + ' ' + request.user.last_name
        if request.method == 'POST':
                if request.POST.dict()['tur'] == 'valfmontaj':
                        veris = json.loads(request.POST.dict()['veri'])
                        print(veris)
                        t = Uretim(tur='valfmontaj' , okunan_deger = veris[0] ,personel = request.user.get_full_name())
                        t.save(force_insert=True)
                        b = Bildirim(tur="baslangic",kisi = request.user.get_full_name())
                        b.save(force_insert=True)
                elif request.POST.dict()['tur'] == 'kurlenme':
                        veris = json.loads(request.POST.dict()['veri'])
                        '''neval
                        if not Uretim.objects.all():
                            vsn = 1
                        else:
                            a = Uretim.objects.all().order_by('-vsn').values()[0]
                            s = a['vsn']
                            vsn = s + 1
                        v = Valf(vsn=vsn, is_emri=veris[0])
                        v.save(force_insert=True)
                        e = Emir.objects.get(is_emri=veris[0])
                        e.durum = 'Aktif'
                        e.save()
                        t = Uretim(tur='montaj_kurlenme' ,vsn = vsn, is_emri = veris[0] ,personel = request.user.get_full_name(),alt_nipel_no = veris[1],bakir_membran_no = veris[2],ust_nipel_no = veris[3],manometre_no = veris[4],basincanahtari_no = veris[5],montaj_kurlenme_zamani=timezone.now()+timezone.timedelta(minutes=10))
                        t.save(force_insert=True)
                        return HttpResponse(str(vsn))
                        '''
                        print("deneme")
                        #burası  sonradan düzenlenecek Berker
                        # e = Emir.objects.get(is_emri=veris[0])
                        # e.durum = 'Aktif'
                        # e.save()
                        is_emri_adi=veris[0] 
                        emir=Emir.objects.get(is_emri= is_emri_adi)
                        personel_id=request.user.id

                        alt_nipel_no = veris[1]
                        bakir_membran_no = veris[2]
                        ust_nipel_no = veris[3]
                        manometre_no = veris[4]
                        basincanahtari_no = veris[5]
                        sibop =  veris[6]
                        print("deneme2")
                         
                        
                        try:
                            kayit_tarihi=timezone.now()
                            #kurlenme_bitis=timezone.now()+timezone.timedelta(minutes=10)

                            valf_montaj = Valf_montaj(montaj_personel_id= personel_id, alt_nipel_no=alt_nipel_no,bakir_membran_no=bakir_membran_no,ust_nipel_no=ust_nipel_no,manometre_no=manometre_no,basincanahtari_no=basincanahtari_no,montaj_tarihi=kayit_tarihi,sibop=sibop)
                            valf_montaj.save() 
                           

                            valf = Valf(is_emri=emir,valf_montaj=valf_montaj)
                            valf.save()

                            return HttpResponse(str(valf.id))
                        except Exception as err:
                            print(" KAyıt HAstası >  ", err)

                        
                elif request.POST.dict()['tur'] == 'valftest':
                        try:

                            valf_seri_no = json.loads(request.POST.dict()['valf_seri_no'])
                            uygun = json.loads(request.POST.dict()['uygun'])
                           

                            valf = Valf.objects.get(id=valf_seri_no ) 


                            personel_id=User.objects.get(id=request.user.id)
                            test_tarihi=timezone.now()
                            

                            acma = str(uygun)
                            kapama = str(uygun)
                            sebep = str(uygun)
                            if (uygun==True): 
                                sebep=None
                            valf_test= Valf_test(  test_personel=personel_id,test_tarihi=test_tarihi,uygun=uygun)

                            valf_test.save()
                            valf.valf_test=valf_test
                            valf.save()
                        except Exception as err:
                            print(err)
                                 
                                
                elif request.POST.dict()['tur'] == 'valfgovde':
                        
                        veri = json.loads(request.POST.dict()['veri'])
                        
                        '''neval
                        v = Valf.objects.get(vsn=veri[3])
                        is_emri = v.is_emri
                        print('veri[5],sodyum miktarı:: ',veri[5] )
                        t = Uretim.objects.get(vsn=veri[3])
                        t.tur='govde_kurlenme'
                        t.tork_degeri = veri[0]
                        t.uygunluk = veri[1]
                        t.sebep = veri[2]
                        t.tsn = veri[4]
                        t.personel = request.user.get_full_name()
                        t.govde_kurlenme_zamani=timezone.now()+timezone.timedelta(minutes=10)
                        # t = Uretim(tur='valfgovde',tork_degeri = veri[0] ,is_emri=is_emri, uygunluk = veri[1] , sebep = veri[2],
                        #           vsn = veri[3],tsn = veri[4], personel = request.user.get_full_name(),govde_kurlenme_zamani=timezone.now()+timezone.timedelta(minutes=10))
                        t.save()
                        '''
                        valf_seri_no=veri[3]
                        valf = Valf.objects.get(id=valf_seri_no ) 
                        valf.durum='valf_govde'
                        valf.save()

                        
                        personel_id=request.user.id
                        kayit_tarihi=timezone.now()
                        kurlenme_bitis=timezone.now()+timezone.timedelta(minutes=10)
                        tork=veri[0]
                        tup_seri_no=veri[4]
                        sodyum_miktari=veri[5]
                        uygunluk=veri[1]
                        sebep=veri[2]
                        if (uygunluk=='on'): 
                                    sebep=None

                        valf_govde= Valf_govde(valf=valf, personel_id=personel_id,kayit_tarihi=kayit_tarihi,kurlenme_bitis=kurlenme_bitis,tork=tork,tup_seri_no=tup_seri_no,sodyum_miktari=sodyum_miktari,uygunluk=uygunluk,sebep=sebep)
                        valf_govde.save()

                elif request.POST.dict()['tur'] == 'fm200':
                        veri = json.loads(request.POST.dict()['veri'])
                        '''neval
                        v = Valf.objects.get(vsn=veri[4])
                        is_emri = v.is_emri
                        print(veri)
                        t = Uretim.objects.get(vsn=veri[4])
                        t.tur='fm200_kurlenme'
                        t.bos_agirlik = veri[0]
                        t.rekorlu_agirlik = veri[1]
                        t.fm200 = veri[2]
                        t.azot = veri[3]
                        t.personel = request.user.get_full_name()
                        t.fm200_kurlenme_zamani=timezone.now()+timezone.timedelta(minutes=10) 
                        t.save()
                        '''

                        valf_seri_no=veri[4]
                        valf = Valf.objects.get(id=valf_seri_no ) 
                        valf.durum='valf_fm200'
                        valf.save()

                        
                        personel_id=request.user.id
                        kayit_tarihi=timezone.now()
                        kurlenme_bitis=timezone.now()+timezone.timedelta(minutes=10) 
                        bos_agirlik =veri[0]
                        rekorlu_agirlik=veri[1]
                        fm200 = veri[2]
                        azot = veri[3]
                        valf_fm200= Valf_fm200(valf=valf, personel_id=personel_id,kayit_tarihi=kayit_tarihi,kurlenme_bitis=kurlenme_bitis, bos_agirlik =bos_agirlik,rekorlu_agirlik=rekorlu_agirlik, fm200 = fm200,azot = azot)
                        valf_fm200.save()

                elif request.POST.dict()['tur'] == 'havuztest':
                        veri = json.loads(request.POST.dict()['veri'])
                        '''neval
                        print(veri)
                        v = Valf.objects.get(vsn=veri[0])
                        is_emri = v.is_emri
                        t = Uretim(tur='havuztest',vsn = veri[0],tsn = veri[0],is_emri=is_emri , uygunluk = veri[1] , 
                        acma = veri[2], kapatma = veri[3],sebep = veri[4], personel = request.user.get_full_name())
                        t.save(force_insert=True)
                        '''
                        print("veri",veri)

                        valf_seri_no=veri[0]
                        valf = Valf.objects.get(id=valf_seri_no ) 
                        valf.durum='valf_havuz_test'
                        valf.save()

                        
                        personel_id=request.user.id
                        kayit_tarihi=timezone.now()
                        uygunluk= veri[1]
                        tup_cidar_sicaklik =veri[2]
                        tup_basinc = veri[3]
                        sebep=veri[4]
                        if (uygunluk):
                            sebep=None
                        
                        valf_havuz= Valf_havuz(valf=valf, personel_id=personel_id,kayit_tarihi=kayit_tarihi,tup_cidar_sicaklik=tup_cidar_sicaklik, tup_basinc =tup_basinc,uygunluk=uygunluk, sebep = sebep)
                        valf_havuz.save()
 

                elif request.POST.dict()['tur'] == 'finalmontaj':
                        veri = json.loads(request.POST.dict()['veri'])
                        '''neval
                        
                        print(veri)
                        v = Valf.objects.get(vsn=veri[1])
                        is_emri = v.is_emri
                        t = Uretim.objects.get(vsn=veri[1])
                        t.tur='finalmontaj'
                        t.etiket_seri_no = veri[0]
                        t.fsn = veri[2]
                        t.funye_seri_omaj = veri[3]
                        t.basinc_anahtari_omaj = veri[4]
                        t. personel = request.user.get_full_name()
                        #t = Uretim(tur='finalmontaj',etiket_seri_no = veri[0],is_emri=is_emri , vsn = veri[1] , fsn = veri[2],
                        #          funye_seri_omaj = veri[3],basinc_anahtari_omaj = veri[4], personel = request.user.get_full_name())
                        t.save()
                        tup_sayisi_str=Emir.objects.filter(is_emri=is_emri).values()[0]['tup_sayisi']
                        '''

                        valf_seri_no=veri[1]
                        valf = Valf.objects.get(id=valf_seri_no ) 
                        valf.durum='valf_final_montaj'
                        valf.save()

                        
                        personel_id=request.user.id
                        kayit_tarihi=timezone.now()
                        etiket_seri_no = veri[0]
                        funye_seri_no = veri[2]
                        funye_seri_omaj = veri[3]
                        basinc_anahtari_omaj = veri[4]
                        valf_final_montaj= Valf_final_montaj(valf=valf, personel_id=personel_id,kayit_tarihi=kayit_tarihi,etiket_seri_no = etiket_seri_no,funye_seri_no = funye_seri_no ,funye_seri_omaj = funye_seri_omaj,basinc_anahtari_omaj = basinc_anahtari_omaj)
                        valf_final_montaj.save()



                        emir = Emir.objects.get(is_emri=valf.is_emri)
                        emir_tup_sayisi = int(emir.tup_sayisi )
                        emir_biten_valf_sayi =  Valf.objects.filter(is_emri=emir,durum='valf_final_montaj').count()
                        print('emir_biten_valf_sayi',emir_biten_valf_sayi)
                        print('emir_tup_sayisi',emir_tup_sayisi)
                        if(emir_biten_valf_sayi == emir_tup_sayisi):

                            emir.durum = 'Bitmiş'
                            emir.save()

                            b = Bildirim(tur = "bitis" , kisi = request.user.get_full_name())
                            b.save(force_insert=True)

        now = timezone.now()


        #montajkurlenmesi=Valf_montaj.objects.filter(kurlenme_bitis_tarihi__gte=now)
        montajkurlenmesi=Valf_montaj.objects.all()
        # govdekurlenmesi=Valf_govde.objects.filter(kurlenme_bitis__gte=now)
        fm200kurlenmesi=Valf_fm200.objects.filter(fm200_kurlenme_bitis_tarihi__gte=now)
        #acikemirleri= Emir.objects.filter(durum__in=("Aktif","Başlanmamış"))
        acikemirleri=Emir.objects.filter(durum='Aktif').values()
        aktifemirler= Emir.objects.filter(durum="Aktif")
        ####Duplikasyonu önlemek için yaptık ###############
        govde_emir = list(dict.fromkeys(Valf.objects.filter(valf_govde_id__isnull=False).values_list('is_emri_id',flat=True)))
        fm200_emir = list(dict.fromkeys(Valf.objects.filter(fm200_azot_id__isnull=False).values_list('is_emri_id',flat=True)))
        ###################################################
        
        #return render(request,'uretim-kontrol.html',{ 'acikemirleri':acikemirleri,  'grup': grup, 'birim': birim, 'ip': ip,'now':now, 'kurlenmes':montajkurlenmesi,'fm200kurlenmes':fm200kurlenmesi, 'govdekurlenmes': govdekurlenmesi ,'server' : server})
        return render(request,'uretim-kontrol.html',{'grup': grup, 'birim': birim, 'ip': ip,'now':now,'server':server, 'acikemirleri':acikemirleri,'fm200kurlenmes':fm200kurlenmesi,'kurlenmes':montajkurlenmesi,'aktifemirler':aktifemirler,'govde_emir':govde_emir,'fm200_emir':fm200_emir})
@csrf_exempt
def acikisemirleri(request):
    emirler = Emir.objects.filter(durum__in=("Aktif","Başlanmamış"))
    temp = []
    for o in emirler.values():
        temp.append(o['is_emri'])
    veri = list(temp)






@login_required
@csrf_exempt
def isemri(request):
        mac = request.user_agent.os.family
        grup = request.user.grup
        birim = request.user.birim
        #Emir.objects.all().delete()
        fullname = request.user.first_name + ' ' + request.user.last_name
        emirler = Emir.objects.all()
        form = IsEmri(request.POST)
        if request.method == 'POST':
            if 'tur' in request.POST.dict():

                if request.POST.dict()['tur'] == 'oncelik':
                    veri = json.loads(request.POST.dict()['veri'])
                    print(veri)
                    for key in veri:
                        em = Emir.objects.get(is_emri=key)
                        em.oncelik = veri[key]
                        em.save()

                    o = Bildirim(tur="oncelik")
                    o.save()
                    return HttpResponse('onceliktamam')
            else:
                if form.is_valid():
                    if not Emir.objects.all():
                        son_oncelik = 1
                    else:
                        a = Emir.objects.all().order_by('-oncelik').values()[0]
                        s = a['oncelik']
                        son_oncelik = s + 1
                    emir = form.save()
                    emir.refresh_from_db()
                    emir.is_emri = form.cleaned_data.get('is_emri')
                    emir.urun_kodu = form.cleaned_data.get('urun_kodu')
                    emir.baslangic = form.cleaned_data.get('baslangic')
                    emir.bitis = form.cleaned_data.get('bitis')
                    emir.emri_veren = form.cleaned_data.get('emri_veren')
                    emir.tup_govde_turu = form.cleaned_data.get('tup_govde_turu')
                    emir.valf_turu = form.cleaned_data.get('valf_turu')
                    emir.renk = form.cleaned_data.get('renk')
                    emir.emniyet_ventil_turu = form.cleaned_data.get('emniyet_ventil_turu')
                    emir.siparis = form.cleaned_data.get('siparis')
                    emir.fm200bosagirlikmindeger= form.cleaned_data.get('fm200bosagirlikmindeger')
                    emir.fm200bosagirlikmaxdeger = form.cleaned_data.get('fm200bosagirlikmaxdeger')
                    emir.fm200dolummiktarimindeger= form.cleaned_data.get('fm200dolummiktarimindeger')
                    emir.fm200dolummiktarimaxdeger = form.cleaned_data.get('fm200dolummiktarimaxdeger')
                    #if(request.user.grup == "planlama"):
                    t = Bildirim(tur = "is emri",emri_veren_grup = grup, emri_veren = request.user.get_full_name(), is_emri = form.cleaned_data.get('is_emri'))
                    t.save(force_insert=True)
                    emir.oncelik = son_oncelik
                    messages.success(request,'Emir başarıyla eklendi!')
                    emir.save()
                    form.full_clean()
                    return(HttpResponseRedirect(reverse('isemri')))

                else:
                    messages.warning(request,'İş emri eklenemedi.Lütfen tekrar deneyin!Hata: {}'.format(form.errors))
        else:
            form = IsEmri()
            form.fields["emri_veren"].initial = fullname
        return render(request,'is-emri.html', { 'form' : form , 'emirler': emirler , 'mac' : mac , 'fullname' : fullname ,'grup' : grup , 'birim': birim,'server' : server})

#@login_required
def yetkilendirme(request):
        mac = request.user_agent.os.family
        #grup = "yonetici"#request.user.grup
        #birim = request.user.birim
        grup = "Yönetici"
        birim = "IT"
        kullanicilar = User.objects.all()
        if grup == 'Yönetici' and birim == 'IT' or grup == 'Mühendis' and birim == 'IT':
                if request.method == 'POST':
                        form = UserRegisterForm(request.POST)
                        if form.is_valid(): #and profile_form.is_valid():
                                user = form.save()
                                user.refresh_from_db()
                                user.first_name = form.cleaned_data.get('first_name')
                                user.last_name = form.cleaned_data.get('last_name')
                                user.grup = form.cleaned_data.get('grup')
                                user.save()
                                username = form.cleaned_data.get('username')
                                password = form.cleaned_data.get('password1')
                                messages.success(request,'{} isimli kullanıcı {} isimli gruba eklendi!'.format(username,user.grup))
                                return(HttpResponseRedirect(reverse('yetkilendirme')))
                        else:
                                print(form.errors)
                else:
                        form = UserRegisterForm()
                return render(request,'kullanici-yetkilendirme.html',{'form':form,'kullanicilar':kullanicilar , 'mac' : mac , 'grup' : grup, 'birim': birim,'server' : server})
        else:
                return(HttpResponseRedirect(reverse('403')))


@login_required
def performans(request):
        mac = request.user_agent.os.family
        grup = request.user.grup
        birim = request.user.birim
        kullanicilar = User.objects.all()
        return render(request,'performans.html',{ 'mac' : mac , 'grup':grup, 'birim': birim, 'kullanicilar': kullanicilar,'server' : server})


@login_required
@csrf_exempt
def yazdir(request):
    mac = request.user_agent.os.family
    grup = request.user.grup
    birim = request.user.birim
    if True:#grup == 'Yönetici' and birim == 'IT':
        if request.method == 'POST':
            i = Emir.objects.filter(durum=request.POST['durum'])
            temp = []
            for obj in i.values():
                times = obj['emir_zamani'].strftime("%d %B %Y (%H:%M:%S)")
                temp.append(obj['is_emri'] + " " + times)
            veri = list(temp)
            return JsonResponse(veri,safe=False)
        return render(request,'yazdir.html',{ 'mac' : mac , 'grup':grup, 'birim': birim,'server' : server})
    else:
        return(HttpResponseRedirect(reverse('403')))

@login_required
def ulogout(request):
        logout(request)
        return(HttpResponseRedirect(reverse('ulogin')))

@csrf_exempt
def ulogin(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(username=username,password=password)
        if user:
            if user.is_active:
                login(request,user)
                print('{} kullanıcısı tarafından başarılı giriş'.format(username))
                return redirect('arama')
            else:
                messages.warning(request,'Kullanıcı adınızı yada parolanızı yanlış girdiniz.')
        else:
            print("Birisi login olmayı denedi ve başarısız oldu!")
            messages.warning(request,'Kullanıcı adınızı yada parolanızı yanlış girdiniz.')
            return(HttpResponseRedirect(reverse('ulogin')))
    else:
        return render(request,'login.html',{})


def _403(request):
        return render(request,'403.html',{})

def handler404(request,exception):
    return render(request, '403.html', status=404)

@csrf_exempt
def kullanicijson(request):
        username = request.POST.get('username')
        b = User.objects.filter(username=username).values('first_name','last_name','username','grup')
        veri = list(b)
        return JsonResponse(veri,safe=False)
@csrf_exempt
def kullanicisil(request):
        username = request.POST.get('username')
        print(username)
        sildi = User.objects.filter(username=username).delete()
        if sildi:
                return HttpResponse('silindi')
        else:
                return HttpResponse('silinemedi')
@csrf_exempt
def kullaniciduzelt(request):
        veri = request.POST.get('bilgi')
        veri = json.loads(veri)
        a = User.objects.get(username=veri["eskisi"])
        a.username = veri["username"]
        a.first_name = veri["first_name"]
        a.last_name = veri["last_name"]
        a.grup = veri["grup"]
        a.birim = veri["birim"]
        a.save()
        return HttpResponse('duzeltildi')

@csrf_exempt
def passwordreset(request):
        ps = request.POST.get('ps1')
        if request.POST.get('username'):
                u = User.objects.get(username=request.POST.get('username'))
                u.set_password(ps)
                u.save()
                return HttpResponse('parola değiştirildi')
        return HttpResponse('bir hata var')

def get_first_and_lastname(username):
    try:
        first_name=User.objects.filter(username=username).first().first_name
        last_name=User.objects.filter(username=username).first().last_name
        return "{} {}".format(first_name,last_name)
    except:
        return 'isim soyisim'


@csrf_exempt
def pdf(request):
        if request.GET.get('qr'):
            qr = request.GET.get('qr')
            print(qr.split(" ")[0])
            i = qr.split(" ")[0]
        # elif request.GET.get('valfqr'):
        #     qr = request.GET.get('valfqr')
        #     v = Valf.objects.get(vsn=qr)
        #     i = v.is_emri
        print("---------------------")
        valf_no = request.GET.get('vsn')
        Valf_montaj_Data=Valf_montaj.objects.filter(id=Valf.objects.filter(id=valf_no).first().valf_montaj_id).first()
        Valf_fm200_Data=Valf_fm200.objects.filter(id=Valf.objects.filter(id=valf_no).first().fm200_azot_id).first()
        Valf_havuz_Data=Valf_havuz.objects.filter(id=Valf.objects.filter(id=valf_no).first().havuz_id).first()
        Valf_final_Data=Valf_final_montaj.objects.filter(id=Valf.objects.filter(id=valf_no).first().valf_final_montaj_id).first()
        Valf_test_Data=Valf_test.objects.filter(id=Valf.objects.filter(id=valf_no).first().valf_test_id).first()
        Valf_govde_Data=Valf_govde.objects.filter(id=Valf.objects.filter(id=valf_no).first().valf_govde_id).first()
        Emir_Data=Emir.objects.filter(is_emri=i).first()
        valf_final = Valf.objects.filter(id=valf_no).values_list('valf_final_montaj_id',flat=True).first()
        urun_seri_no = Valf_final_montaj.objects.filter(id=valf_final).values_list('urun_seri_no',flat=True).first()
        print("---------------------")   
        try:
            valfmontajPersonel = get_first_and_lastname(User.objects.filter(id=Valf_montaj_Data.montaj_personel_id).first().username)
        except:
            valfmontajPersonel = ''

        try:
            valfmontajTarih = Valf_montaj_Data.montaj_tarihi
        except:
            valfmontajTarih = ''
        try:
            altnipelno = Valf_montaj_Data.alt_nipel_no
        except:
            altnipelno = ''
        try:
            ustnipelno = Valf_montaj_Data.ust_nipel_no
        except:
            ustnipelno = ''
        try:
            switchno = Valf_montaj_Data.basincanahtari_no
        except:
            switchno = ''
        try:
            manometreno = Valf_montaj_Data.manometre_no
        except:
            manometreno = ''

      
        try:
            valftestPersonel = get_first_and_lastname(User.objects.filter(id=Valf_test_Data.test_personel_id).first().username)
        except:
            valftestPersonel = ''
        try:
            valftestTarih = Valf_test_Data.test_tarihi
        except:
            valftestTarih = ''
        try:
            valfTestUygun = 'Uygun' if Valf_test_Data.uygun == True else 'Uygun Değil'
        except:
            valfTestUygun = Valf_test_Data.uygun

       
        try:
            valfgovdePersonel = get_first_and_lastname(User.objects.filter(id=Valf_govde_Data.govde_personel_id).first().username)
        except:
            valfgovdePersonel = ''
        try:
            valfgovdeTarih = Valf_govde_Data.govde_tarihi
        except:
            valfgovdeTarih = ''
        try:
            valfGovdeUygun = 'Uygun' if  Valf_govde_Data.uygunluk == True else 'Uygun Değil'
        except:
            valfGovdeUygun = ''

        try:
            fm200Personel = get_first_and_lastname(User.objects.filter(id=Valf_fm200_Data.fm200_personel_id).first().username)
        except:
            fm200Personel = ''
        try:
            fm200Tarih = Valf_fm200_Data.kayit_tarihi
        except:
            fm200Tarih = ''
        try:
            bosAgirlik = Valf_fm200_Data.bos_agirlik
        except:
            bosAgirlik = ''
        try:
            doluAgirlik = Valf_fm200_Data.dolu_agirlik
        except:
            doluAgirlik = ''
        # try:  Duruma Göre sonradan eklenebilir diye silmiyoruz!
        #     azot = fm200[0]['azot']
        # except:
        #     azot = ''
        try:
            bar = Valf_fm200_Data.bar
        except:
            bar = ''
        
        try:
            havuztestPersonel = get_first_and_lastname(User.objects.filter(id=Valf_havuz_Data.havuz_personel_id).first().username)
        except:
            havuztestPersonel = ''
        try:
            havuztestTarih = Valf_havuz_Data.kayit_tarihi
        except:
            havuztestTarih = ''
        try:
            havuzTestUygun = 'Uygun' if Valf_havuz_Data.uygunluk == True else 'Uygun Değil' 
        except:
            havuzTestUygun = ''

        
        try:
            finalmontajPersonel = get_first_and_lastname(User.objects.filter(id=Valf_final_Data.personel_id).first().username)
        except:
            finalmontajPersonel = ''
        try:
            finalmontajTarih = Valf_final_Data.kayit_tarihi
        except:
            finalmontajTarih = ''

        try:
            membranTipi = Emir_Data.valf_turu
        except:
            membranTipi = ''
        try:
            ventilTipi = Emir_Data.emniyet_ventil_turu
        except:
            ventilTipi = ''
        try:
            tugovdetipi= Emir_Data.tup_govde_turu
        except:
            tugovdetipi= ''
        try:
            siboplotno = Valf_montaj_Data.sibop
        except:
            siboplotno = ''

        print(valftestPersonel,Emir_Data.emniyet_ventil_turu)
        veri = "veri"
        html_string = render_to_string('external/pdf-template.html', {'veri': veri, "qr": urun_seri_no,
            'valfmontajPersonel': valfmontajPersonel, 'valfmontajTarih':valfmontajTarih,'valfgovdePersonel':valfgovdePersonel,
            'valftestPersonel': valftestPersonel, 'valftestTarih': valftestTarih,'valfTestUygun':valfTestUygun,'havuzTestUygun':havuzTestUygun,
            'valfgovdePersonel': valftestPersonel, 'valfgovdeTarih': valfgovdeTarih,'valfGovdeUygun':valfGovdeUygun,'valfMontajUygun':"Uygun*",'fm200Uygun':"Uygun*",'finalMontajUygun':"Uygun*",
            'fm200Personel': fm200Personel, 'fm200Tarih': fm200Tarih,
            'bosAgirlik' : bosAgirlik, 'doluAgirlik' : doluAgirlik,
            'havuztestPersonel': havuztestPersonel, 'havuztestTarih': havuztestTarih,
            'finalmontajPersonel': finalmontajPersonel, 'finalmontajTarih': finalmontajTarih,
            'altnipelno': altnipelno, 'ustnipelno': ustnipelno, 'switchno': switchno,'manometreno': manometreno,
            'is_emri': i,'membranTipi': membranTipi,'ventilTipi': ventilTipi,'urunserino':urun_seri_no,'bar':bar,'tugovdetipi':tugovdetipi,'siboplotno':siboplotno
         }, request=request)

        html = HTML(string=html_string, base_url=request.build_absolute_uri())
        html.write_pdf(target='/tmp/' + qr + '.pdf');

        fs = FileSystemStorage('/tmp/')
        with fs.open(qr + '.pdf') as pdf:
                response = HttpResponse(pdf, content_type='application/pdf')
                response['Content-Disposition'] = 'inline; filename="pdf.pdf"'
                return response

        return response

#Test sonuçları
@csrf_exempt
def dashboard(request):
    bugun = timezone.now()
    print(request.POST.get('gun_sayisi'))
    gun = int(request.POST.get('gun_sayisi'))
    kac_gun = bugun - timezone.timedelta(days=gun)
    veris = Test.objects.filter(test_tarihi__range=[kac_gun,bugun])
    temp = []
    for o in veris.values():
        temp.append(o)
    veri = list(temp)
    print("dashboard", veri)
    return JsonResponse(veri,safe=False)

@csrf_exempt
def uretimdurum(request):
    i = request.POST.get('is_emri')
    print(i)
    veri = list()
    print(Valf.objects.filter(is_emri_id=i).values_list('valf_montaj_id',flat=True).count(),Valf.objects.filter(is_emri_id=i).filter(valf_test_id__isnull=False).values_list('valf_test_id',flat=True).count())
    try:
        veri.append(Valf.objects.filter(is_emri_id=i).filter(valf_montaj_id__isnull=False).values_list('valf_montaj_id',flat=True).count())
        veri.append(Valf.objects.filter(is_emri_id=i).filter(valf_test_id__isnull=False).values_list('valf_test_id',flat=True).count())
        veri.append(Valf.objects.filter(is_emri_id=i).filter(valf_govde_id__isnull=False).values_list('valf_govde_id',flat=True).count())
        veri.append(Valf.objects.filter(is_emri_id=i).filter(fm200_azot_id__isnull=False).values_list('fm200_azot_id',flat=True).count())
        veri.append(Valf.objects.filter(is_emri_id=i).filter(havuz_id__isnull=False).values_list('havuz_id',flat=True).count())
        veri.append(Valf.objects.filter(is_emri_id=i).filter(valf_final_montaj_id__isnull=False).values_list('valf_final_montaj_id',flat=True).count())
        veri.append(Emir.objects.filter(id=i).values()[0]['tup_sayisi'])
    except Exception as err:
        print(err)
        veri = [0,0,0,0,0,0,10]
    print(veri)
    return JsonResponse(veri,safe=False)

@csrf_exempt
def personeldurum(request):
    p = request.POST.get('personel')
    g = request.POST.get('gun_sayisi')
    print(p,g)
    bugun = timezone.now()
    gun = int(request.POST.get('gun_sayisi'))
    kac_gun = bugun - timezone.timedelta(days=gun)
    veris = Test.objects.filter(test_tarihi__range=[kac_gun,bugun])
    veri = list()
    try:
        veri.append(Test.objects.filter(test_tarihi__range=[kac_gun,bugun]).filter(tur="manometre").filter(testi_yapan=p).count())
        veri.append(Test.objects.filter(test_tarihi__range=[kac_gun,bugun]).filter(tur="basinc").filter(testi_yapan=p).count())
        veri.append(Test.objects.filter(test_tarihi__range=[kac_gun,bugun]).filter(tur="altnipel").filter(testi_yapan=p).count())
        veri.append(Test.objects.filter(test_tarihi__range=[kac_gun,bugun]).filter(tur="ustnipel").filter(testi_yapan=p).count())
        veri.append(Test.objects.filter(test_tarihi__range=[kac_gun,bugun]).filter(tur="bakirmembran").filter(testi_yapan=p).count())
        veri.append(Test.objects.filter(test_tarihi__range=[kac_gun,bugun]).filter(tur="emniyet").filter(testi_yapan=p).count())
        veri.append(Uretim.objects.filter(date__range=[kac_gun,bugun]).filter(tur="kurlenme").filter(personel=p).count())
        veri.append(Uretim.objects.filter(date__range=[kac_gun,bugun]).filter(tur="valftest").filter(personel=p).count())
        veri.append(Uretim.objects.filter(date__range=[kac_gun,bugun]).filter(tur="valfgovde").filter(personel=p).count())
        veri.append(Uretim.objects.filter(date__range=[kac_gun,bugun]).filter(tur="fm200").filter(personel=p).count())
        veri.append(Uretim.objects.filter(date__range=[kac_gun,bugun]).filter(tur="havuztest").filter(personel=p).count())
        veri.append(Uretim.objects.filter(date__range=[kac_gun,bugun]).filter(tur="finalmontaj").filter(personel=p).count())
    except:
        veri = [0,0,0,0,0,0,0,0,0,0,0,10]
    print(veri)
    return JsonResponse(veri,safe=False)

@csrf_exempt
def tupTuru(request):
    if request.method == 'POST':
        try:
            u = Emir.objects.filter(is_emri=request.POST.dict()['is_emri']).first()
            bos_agirlik_miktari= u.bos_agirlik_miktari
            fm200_miktari= u.fm200_miktari
            renk= u.renk
            response= bos_agirlik_miktari + ';'+ fm200_miktari +';'+renk
            return HttpResponse(str(response))
        except e :
            print(e)
    return str('tur')


@csrf_exempt
def getEmirNo(request):
    if request.method == 'POST':
        vsn=request.POST.dict()['veri']
        print('getEmirNo',vsn)

        try:
            is_emri = Emir.objects.filter(id=vsn).values_list('is_emri',flat=True).first()
            return HttpResponse(str(is_emri))
        except:
            return HttpResponse(str('NO'))
    return str('is_emri')



@csrf_exempt
def kontrolEt(request):
    if request.method == 'POST':
        tur = request.POST['tur']
        veri = request.POST['veri']
        isemri =  request.POST['isemri']
        t = Test.objects.filter(tur=tur)
        r = "NO"
        if(tur == 'altnipel'):
            t = Test.objects.filter(tur=tur)
            try:
                if(int(veri) in t.values_list('lot_no',flat=True)):
                    r = ('OK')
                else:
                    r = ('NO')
            except:
                r = 'NO'
        if(tur == 'ustnipel'):
            t = Test.objects.filter(tur=tur)
            try:
                if(veri in t.values_list('baslangic_seri_no',flat=True)):
                    r = ('OK')
                else:
                    r = ('NO')
            except:
                r = "NO"
        if(tur == 'manometre'):
            t = Test.objects.filter(tur=tur)
            try:
                if(veri in t.values_list('seri_no',flat=True)):
                    r = ('OK')
                else:
                    r = ('NO')
            except Exception as e:
                print(e)
                r = "NO"
        if(tur == 'basinc'):
            t = Test.objects.filter(tur=tur)
            try:
                if(veri in t.values_list('seri_no',flat=True)):
                    r = ('OK')
                else:
                    r = ('NO')
            except:
                r = "NO"
        if(tur == 'bakirmembran'):
            t = Test.objects.filter(tur=tur)
            try:
                if(int(veri) in t.values_list('lot_no',flat=True)):
                    r = ('OK')
                else:
                    r = ('NO')
            except:
                r = "NO"
        if(tur == 'emniyet'):
            t = Test.objects.filter(tur=tur)
            try:
                if(veri in t.values_list('lot_no',flat=True)):
                    r = ('OK')
                else:
                    r = ('NO')
            except:
                r = "NO"
        if(tur == 'valf_govde'):
            try:
                #Valf.objects.filter(valf_montaj_id=veri).values_list('valf_test_id',flat = True).first()
                #a = isinstance(Valf.objects.filter(valf_montaj_id=veri).values_list('valf_test_id',flat = True).first(),int)
                valf_id=Valf.objects.filter(valf_montaj_id=veri).values_list('valf_test_id',flat = True).first()       
                if isinstance(valf_id,int):
                    Valf_test.objects.filter(id=valf_id).values_list('uygun',flat = True).first()
                    if (Valf_test.objects.filter(id=valf_id).values_list('uygun',flat = True).first()):
                        r = ('OK')
                    else:
                        r = ('NO')
                else:
                    r = ('NO')
            except:
                r = "NO"
        if(tur == 'sibop'):
            print(tur,veri,t.values_list('lot_no',flat=True))
            t = Test.objects.filter(tur=tur)
            try:
                if(int(veri) in t.values_list('lot_no',flat=True)):
                    r = ('OK')
                else:
                    r = ('NO')
            except:
                r = "NO"
        return HttpResponse(r)

@csrf_exempt
def kurlenmeKontrol(request):
    if request.method == 'POST':
        r = "NO"
        tur = request.POST['tur']
        vsn = request.POST['veri']
        print('kurlenmeKontrol',tur,vsn)
        if(tur == 'montaj_kurlenme'):
            try:
                u = Uretim.objects.filter(vsn=vsn)
                print(u,"---------------")
                if(u.values()[0]['montaj_kurlenme_zamani']<timezone.now()):
                    r = 'OK'
                else:
                    r = 'NO'
            except:
                r = 'NO'
        elif (tur=='govde_kurlenme'):

            try:
                u = Uretim.objects.filter(vsn=vsn)
                print('govde_kurlenme_zamani',u.values()[0]['govde_kurlenme_zamani'])
                print('now',timezone.now())
                if(u.values()[0]['govde_kurlenme_zamani']<timezone.now()):
                    r = 'OK'
                else:
                    r = 'NO'
            except:
                r = 'NO'
        elif (tur=='valf_test'):
            print("içerdeyim-----> Valf Test")
            try:
                print(vsn,"----------------------------")
                valf_montaj_id = Valf.objects.filter(id=vsn).first().valf_montaj_id
                print(valf_montaj_id)
                tarih =  Valf_montaj.objects.filter(id=valf_montaj_id).first().kurlenme_bitis_tarihi
                print(tarih)
                print(type(timezone.now()),timezone.now())
                print(type(tarih),tarih)
                if(tarih<timezone.now()):
                    print("büyüktür")
                    r='OK'
                else:
                    print("küçük")
                    r='NO'
            except Exception as err:
            
                print('r',err)
                r='NO'
        elif (tur=='pdfkontrol'):
            print(vsn)
            try:
                if Valf.objects.filter(valf_montaj_id=vsn).count():
                    r='OK'
                else:
                    r='NO'
            except Exception as err:
            
                r='NO'
                print(err)

        return HttpResponse(r)

@csrf_exempt
def newVSN(request):
    if request.method == 'POST':

        vsn = ""
        if not Uretim.objects.all():
            vsn = 1
        else:
            a = Uretim.objects.all().order_by('-vsn').values()[0]
            s = a['vsn']
            print('sssss',s)

            vsn = s + 1
            
            print(vsn)
            r = (str(vsn))
        return HttpResponse(r)
        #return HttpResponse(str(vsn))
        #return JsonResponse({'vsn':vsn})


@csrf_exempt
def hardreset(request):
    print('Hard')

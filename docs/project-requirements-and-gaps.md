# AI Data Cleaner - Gereksinimler ve Eksik Kapatma Planı

Bu dokuman, projeyi juri sunumuna hazirlamak icin gereksinimleri, mevcut durumu,
eksikleri ve aksiyon siralamasini toplar.

## 1. Proje Amaci

AI Data Cleaner, tablo formatindaki ham veri setlerinde veri kalitesi problemlerini
tespit eden, kullaniciya temizlik onerileri sunan, secilen islemleri uygulayan ve
once/sonra kalite raporu ureten bir veri temizleme karar destek sistemidir.

Proje tam otomatik veri degistirme iddiasinda degildir. Temel yaklasim, sistemin
analiz ve oneri uretmesi, son karari kullanicinin vermesidir.

## 2. Fonksiyonel Gereksinimler

### 2.1 Kullanici ve Yetkilendirme

- Kullanici kayit ve giris yapabilmeli.
- Yalnizca kendi veri setlerini, raporlarini ve islem gecmisini gorebilmeli.
- JWT tabanli kimlik dogrulama kullanilmali.
- Sifre sifirlama akisi desteklenmeli.

### 2.2 Veri Yukleme

- CSV ve Excel gibi tablo verileri yuklenebilmeli.
- Dosya tipi, satir sayisi, sutun sayisi ve temel metadata cikarilmali.
- Dosya boyutu siniri kullaniciya net anlatilmali.
- Hatali veya okunamayan dosyalar icin anlasilir hata mesaji verilmeli.

### 2.3 Veri Analizi

- Eksik degerler tespit edilmeli.
- Aykiri degerler tespit edilmeli.
- Format problemleri tespit edilmeli.
- Ozellik muhendisligi onerileri uretilebilmeli.
- Analiz sonucu kullaniciya anlasilir kategorilerle sunulmali.

### 2.4 Temizlik Islemleri

- Kullanici sutun bazinda temizlik yontemi secebilmeli.
- Eksik degerler icin mean, median, mode, KNN, MICE gibi yontemler desteklenmeli.
- Aykiri degerler icin birakma, sinirlama, silme ve model tabanli secenekler olmali.
- Format duzeltmeleri uygulanabilmeli.
- Temizlik islemi ham veriyi dogrudan bozmadan yeni cikti uretmeli.

### 2.5 Raporlama ve Denetim

- Temizlik sonrasi HTML/PDF kalite raporu uretilmeli.
- Raporda once/sonra metrikleri bulunmali.
- Yapilan islemler audit log olarak tutulmali.
- Rapor gecmisi indirilebilir olmali.

### 2.6 Frontend Deneyimi

- Kullanici veri setlerini listeleyebilmeli.
- Veri profili ekrani olmali.
- Temizlik studyosu olmali.
- Once/sonra karsilastirma ekrani olmali.
- Rapor ve loglara kolay erisim saglanmali.
- Mobil ve masaustu gorunumleri tasma yapmadan calismali.

### 2.7 Yardimci Asistan

- Gemini API anahtari tanimliysa yardimci bot calismali.
- API anahtari yoksa ana veri temizleme akisi bozulmamali.
- Botun yardimci ozellik oldugu, cekirdek temizleme motoru olmadigi belirtilmeli.

## 3. Teknik Gereksinimler

- Backend FastAPI ile servis edilmeli.
- Veri islemleri Pandas/NumPy ile yapilmali.
- ML tabanli yontemlerde scikit-learn kullanilmali.
- Veritabani olarak PostgreSQL desteklenmeli.
- Docker Compose ile backend, frontend ve veritabani birlikte calistirilabilmeli.
- Frontend React/Vite ile build alinabilmeli.
- Test paketi temel backend davranislarini dogrulamali.
- Uretim build ve lint temiz gecmeli.

## 4. Juri Karsisinda Kritik Sorular

### Veri Seti Boyutu

Soru: Veri setinin boyutu neden onemli?

Cevap: Proje veriyi Pandas ile bellekte isliyor. MICE, KNN, DBSCAN, LOF ve
Isolation Forest gibi yontemler veri buyudukce daha fazla bellek ve zaman kullanir.
Bu nedenle proje kucuk/orta olcekli tablo verileri icin tasarlanmistir.

Aksiyon:
- Arayuzde ve README'de dosya boyutu siniri net yazilmali.
- Buyuk veri icin gelecek calisma olarak sampling, chunk okuma ve kalici kuyruk
  sistemi belirtilmeli.

### Health Score

Soru: Saglik skoru neye gore hesaplanir?

Cevap: Eksik deger, format problemi ve aykiri deger sayilari agirlikli olarak
toplam hucre sayisina oranlanir. Eksik veri en agir, format problemi orta, aykiri
deger daha hafif cezalandirilir. Cunku aykiri deger her zaman hata olmayabilir.

Aksiyon:
- Frontend'de saglik skoru aciklamasi eklenmeli.
- Rapor ve karsilastirma ekraninda ayni hesap mantigi kullanilmali.

### Aykiri Degerler

Soru: Aykiri degerleri silmek dogru mu?

Cevap: Her zaman degil. Aykiri degerler veri hatasi olabilecegi gibi gercek ve
onemli gozlemler de olabilir. Bu nedenle sistem silmeyi zorlamaz; kullaniciya
birakma, sinirlama veya silme gibi secenekler sunar.

Aksiyon:
- Aykiri deger seceneklerinin yanina kisa risk aciklamalari eklenmeli.

### Eksik Deger Tamamlama

Soru: Doldurulan degerler gercek mi?

Cevap: Hayir, bunlar istatistiksel tahmindir. Bu nedenle sistem farkli yontemler
sunar ve yapilan islemi raporda acikca gosterir.

Aksiyon:
- MICE/KNN gibi yontemler icin "tahmini deger uretir" uyarisi eklenmeli.

### AI Iddiasi

Soru: Projede yapay zeka nerede?

Cevap: Scikit-learn tabanli makine ogrenmesi yontemleri aykiri deger ve eksik
deger analizinde kullanilir. Gemini destekli bot ise yardimci asistan katmanidir.

Aksiyon:
- Sunumda "AI destekli karar destek sistemi" ifadesi kullanilmali.
- "Tam otomatik mucizevi temizleyici" gibi abartili iddialardan kacinilmali.

### Guvenlik ve Gizlilik

Soru: Yuklenen veriler guvende mi?

Cevap: Kullanici bazli yetki kontrolu vardir. Dosyalar proje sunucusunda islenir.
Harici LLM kullanan bot cekirdek temizlik akisi degildir ve hassas veri gonderimi
sinirlandirilmalidir.

Aksiyon:
- Paylasilmis Gemini API anahtari yenilenmeli.
- README'ye gizlilik ve API anahtari uyarisi eklenmeli.

## 5. Mevcut Eksikler ve Oncelik Sirasi

### P0 - Sunum Oncesi Mutlaka

1. Docker ile canli demo akisi dogrulanmali.
2. Kullanici akisi bastan sona test edilmeli:
   kayit, giris, dosya yukleme, analiz, temizlik, rapor indirme.
3. Gemini API anahtari yenilenmeli.
4. README'ye proje kapsami, sinirlari ve calistirma adimlari net eklenmeli.
5. Demo icin 2-3 ornek veri seti hazirlanmali.

### P1 - Juri Sorularini Kapatacak Iyilestirmeler

1. Health score aciklamasi frontend'e eklenmeli.
2. Dosya boyutu ve desteklenen veri tipi bilgisi arayuzde gorunmeli.
3. Rapor ve karsilastirma ekranindaki health score hesaplari tutarlilastirilmali.
4. Temizlik sonrasi analiz cache davranisi netlestirilmeli.
5. Aykiri deger ve MICE/KNN seceneklerine kisa risk aciklamasi eklenmeli.

### P2 - Projeyi Daha Profesyonel Gosterecekler

1. Rapor Gecmisi / Analiz Merkezi ekrani eklenmeli.
2. Proje bazli timeline ekrani daha gorunur hale getirilmeli.
3. Workspace endpoint'i icin basit cache veya ornekleme eklenmeli.
4. Backend main.py router/service katmanlarina ayrilmali.
5. Test kapsaminda frontend kritik akislari icin e2e test dusunulmeli.

### P3 - Gelecek Calisma Olarak Anlatilacaklar

1. Buyuk veri icin chunk processing.
2. Kalici gorev kuyrugu: Celery, RQ veya ARQ.
3. Veri tipi otomatik siniflandirma.
4. Domain bazli aykiri deger politikalari.
5. Model kalitesi icin ground-truth veya kullanici geri bildirimi mekanizmasi.

## 6. Siradaki Uygulama Sirasi

1. README ve arayuzde proje kapsami/dosya limiti aciklamalarini ekle.
2. Health score bilgi kutusunu frontend'e ekle.
3. Health score hesap tutarliligini kontrol edip gerekirse duzelt.
4. Demo veri setlerini hazirla.
5. Docker canli demo kontrolunu yap.
6. Rapor Gecmisi / Analiz Merkezi ekranini tasarla ve ekle.

## 7. Push Politikasi

- Bugunku frontend kalite commit'i GitHub'a pushlandi.
- Bundan sonraki degisiklikler once lokal olarak yapilacak.
- Kullanici kontrol edip onay verdikten sonra yeni commit ve push islemi yapilacak.

FUTBOL AI – ANDROID MANUEL ANALİZ SÜRÜMÜ

Bu paket telefon ekranına uyumlu bir web uygulamasıdır (PWA).
Uygulama yalnızca ANALİZ ET düğmesine basıldığında API isteği yapar.
Arka planda otomatik tarama, sürekli işlem veya günlük bildirim yoktur.

ÖNEMLİ – SÜRÜMÜN SINIRLARI
- Bu ilk çalışan iskelet sürümüdür.
- Şu an tüm API-Football fikstürlerini tarihe göre listeler.
- İlk olasılık motoru genel Poisson başlangıç değerleri kullanır.
- Son 10 maç formu, takım kadro değeri, ilk 11, sakat/cezalı oyuncular henüz olasılık hesabına dahil değildir.
- Bu nedenle sonuçlar bahis tavsiyesi veya garanti değildir. Gerçek model için form ve kadro verisi entegrasyonu sonraki geliştirme adımıdır.
- API-Football planındaki günlük istek kotası geçerlidir.

YAYINA ALMA (Render örneği)
1. ZIP'i çıkar.
2. İçindeki dosyaları bir GitHub deposuna yükle.
3. Render'da New > Web Service ile depoyu bağla.
4. Build: pip install -r requirements.txt
5. Start: gunicorn app:app --bind 0.0.0.0:$PORT
6. Environment Variables bölümüne API_FOOTBALL_KEY ekle. Anahtarı GitHub'a veya sohbete yazma.
7. Deploy bitince verilen HTTPS adresini Android Chrome'da aç.
8. Chrome menüsü > Ana ekrana ekle / Uygulamayı yükle.

PİL VE GİZLİLİK
- Analiz isteği sunucuda yapılır; telefon sürekli işlemci kullanmaz.
- Uygulama kapalıyken veri çekmez.
- API anahtarı yalnızca sunucu ortam değişkeninde tutulmalıdır.

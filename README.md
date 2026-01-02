# Monte_carlo
Monte Carlo Şampiyonlar Ligi Simülasyonu
Amaç: Sezonun kalan maçları üzerinden takımların top8, top24 ve elenme olasılıklarını tahmin etmek.

🔹 Neden Simülasyon?

Sadece puan tablosuna bakmak yanıltıcıdır. Gerçek dünya belirsizliği ve olası skor varyasyonları, stratejik öngörü ve analiz için kritik. Bu nedenle her maç olasılıksal olarak Poisson temelli model ile simüle edildi.

🔹 Proje Mantığı

Veri Çekme: Football-Data.org API’den canlı puan durumu ve kalan fikstür

Simülasyon: Her maç için 100.000 Poisson temelli skor simülasyonu

Olasılık Hesaplama:

Top8’e girme olasılığı

Top24’e girme olasılığı

Elenme olasılığı

🔹 Teknik Detaylar

Dil & Framework: Python + Flask

Veri Kaynağı: Football-Data.org API

Simülasyon Mantığı: Poisson temelli skor tahmini, olasılık modelleme, güç haritası

Simülasyon Sayısı: 100.000

🔹 Örnek Sonuçlar (Temsilcilerimiz)
Takım	Avg Puan	Top8 %	Top24 %	Elenme %
Galatasaray SK	9	1.6	92	8
Qarabağ Ağdam FK	7	0	66	34


.

🔹 Kurulum & Çalıştırma
git clone <repo-url>
cd monte-carlo-cl
pip install -r requirements.txt
python app.py


Sunucu başlatıldıktan sonra: http://127.0.0.1:5000

API Key’inizi API_KEY değişkenine eklemeyi unutmayın.




🔹 Sonuç

Bu proje, analitik düşünce ve belirsizlik yönetimi yeteneğimi gösteren en güçlü portföy örneklerinden biridir. Sadece kod değil, sezonsal stratejik öngörü ve istatistiksel simülasyon kabiliyetimi de ortaya koyar.


# 🚀 AI Data Cleaner (VeriTemiz AI) - Proje Başucu Rehberi

AI Data Cleaner, kaba veri setlerindeki tutarsızlıkları, eksikleri ve aykırılıkları **yapay zeka ve gelişmiş istatistiksel modeller** kullanarak otonom şekilde çözen, son teknoloji bir "Akıllı Veri Temizleme ve Özellik Mühendisliği" (Feature Engineering) platformudur.

Kullanıcıların veri bilimi geçmişi olmasa bile kompleks işlemleri tek tıkla halledebilmesi için hem güçlü bir arka plan (Backend) hem de zarif ve modern bir kullanıcı arayüzüyle (Frontend) tasarlanmıştır. Tüm sistem tamamen kapalı ve bağımsız olarak Docker konteynerleri üzerinde çalışır.

---

## 🛠 Kullanılan Teknolojiler ve Mimari

Proje, güncel sanayi standartlarına uygun bir **Microservices (Mikroservis)** yapısı felsefesiyle tasarlanmıştır. Piyasada yer edinmiş, performanslı teknolojiler tercih edilmiştir:

### ⚙️ Backend (Arka Plan - Veri & Yapay Zeka Merkezi)
*   **Çatı (Framework):** Python tabanlı `FastAPI`. Sunucu asenkron yapısıyla son derece hızlıdır. Tıkanmadan paralel veri analizi yapabilir.
*   **Veri Manipülasyonu:** `Pandas` ve `NumPy`. Büyük CSV/Excel veri setleri üzerinde saniyeler içinde matris işlemleri yürütür.
*   **Makine Öğrenmesi (ML) Modelleri:** `Scikit-learn`
    *   *DBSCAN:* Yoğunluk tabanlı mekansal kümeleme. Çok yönlü (multivariate) bağlamsal aykırıları (Outlier) siler.
    *   *Isolation Forest (İzolasyon Ormanı):* Anormallikleri izole etmek için karar ağaçları topluluğunu kullanır.
    *   *Eksik Veri Tamamlama (Imputation):* K-Nearest Neighbors (KNNImputer) ve MICE yöntemleri entegredir.
*   **Veritabanı ve ORM:** `PostgreSQL` veri saklama merkezi olarak kullanılır. Veritabanı bağlayıcısı olarak `SQLAlchemy` (ORM) görev yapar. İşlem geçmişi, kalite raporları, kullanıcı kayıtları relasyonel bir düzende tablolanır.

### 🎨 Frontend (Ön Yüz - Kullanıcı Arayüzü)
*   **Kütüphane:** Modern, bileşen (component) mimarili `React.js` (JavaScript).
*   **Derleyici:** `Vite`. Eski nesil Webpack'e kıyasla anında canlı sunucu başlangıcı ve mikro saniyelerde derleme (build) imkânı sunar.
*   **Tasarım Mimarisi:** Glassmorphism (Buzlu Cam) efektleri. Sistem CSS Grid ve Flexbox üzerinde, fütüristik renk paletleri ve pürüzsüz animasyonlarla desteklenerek "Premium" bir hissiyat yaratır.
*   **İkonlar ve Deneyim (UX):** `lucide-react` ikon setleri ile temiz ve profesyonel bir tipografi sunulmuştur.
*   **Web Sunucusu:** React kodları derlendikten sonra üretim ortamı (Production) için çok hafif ve uçtan uca hızlı bir HTTP sunucusu olan `Nginx` üzerinden yayınlanır.

### 🐳 Geliştirme Operasyonları (DevOps)
*   **Konteynerizasyon:** Tüm projeyi işletim sisteminizden bağımsız hale getiren `Docker`. Uygulama 3 ana bileşenden oluşur:
    1.  `cleaner-postgres`: PostgreSQL hizmeti.
    2.  `cleaner-backend`: FastAPI ve Python analiz motoru.
    3.  `cleaner-frontend`: Nginx üzerinden sunulan React arayüzü.
*   **Orkestrasyon:** `docker-compose.yml` ile tüm servisler tek satır komut (`docker-compose up -d`) ile birbirleriyle güvenli ağlarda haberleşerek ayağa kalkar.
*   **Kalıcı Depolama (Volumes):** Docker yeniden başlasa bile veri kaybolmasın diye yüklenen CSV'ler, Temizlenmiş CSV'ler (`outputs`) ve Postgres Meta verileri doğrudan sizin sabit diskinizle (Volume map) eşleştirilmiştir.

---

## 🔬 Core Flow — Proje Temel İşleyiş Akışı

1.  **Yükleme Aşaması:** Kullanıcı "Dosya Seçin" alanına dosyasını (ör. `.csv`) sürükleyip bırakır. Arayüz bunu REST API üzerinden `/upload` uç noktasına iletir. UUID şifrelemesi ve metadata çıkarımları (Satır sayısı, Formatı) ile Postgres'e kaydedilir.
2.  **Veri Analizi ve Profil Çıkarma:** Arka planda `report/analyze` tetiklenir.
    *   Boş hücrelerin (%) yüzdesi MICE, Median, Fill yöntemleriyle eşleşir.
    *   Aykırı satırlar IQR ve üç farklı yapay zeka algoritması (DBSCAN, Isolation Forest, Local Outlier Factor) tarafından taranır.
    *   Tarih/İsim formatı tutarsızlıkları bulunur.
    *   Verinin Skewness (Çarpıklık) değerlerine bakılarak Logaritmik veya Z-Score dönüştürücüler planlanır.
3.  **Önerilerin Sunulması:** Ön yüze aktarılan JSON yapısındaki bu dev rapor şık bir "Analiz Önerileri Kutucukları (Checkboxes)" sistemine dönüşür. Kullanıcı her sütun için ne tarz bir işlem uygulayacağını Radio Button'lar arasından seçer.
4.  **Uygulama ve Çıktı Üretimi (Pipeline):** Seçilen düzeltmeler (Selections) topluca `/apply` uç noktasına gider. Pandas üzerinde veri sırayla tüm tıraşlamalardan, dönüşümlerden ve yamalardan geçer.
5.  **Sonuç:** Pırıl pırıl temizlenen algoritma veri seti diske `temizlenmis_veri_[ID].csv` olarak kaydedilir ve indirme linki aktif olur. Yapılan tüm operasyon kalemleri DB üzerine saniye saniye "Audit Log" (İşlem Günlüğü) olarak işlenir.

---

## 🔒 Projenin Güçlü Yönleri (Vurgulanması Gerekenler)
- **Modülerlik:** Her analistin taktikleri ayrı dosyalardadır (`outlier_detector.py`, `feature_engineering.py`). Yeni bir algoritma eklemek kod yapısını bozmaz.
- **Kullanıcı Kararı (Otonomi Kontrolü):** Temizlik katı kurallarla habersiz yapılmaz. Aykırı değer bulunan satırın silineceğine veya yapay zeka ile %5 - %95 bandında sıkıştırılacağına (Winsorize) kullanıcı şeffaf arayüz ile karar verir.
- **Kesinlikle CORS & Bağlantı Problemleri Yoktur:** Hem container yapısındaki güvenlik zırhı (Port atamaları) hem de `localhost` proxy adaptasyonu tam stabil sağlanmıştır. 

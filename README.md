# 🎓 PrepWise — Akıllı Veri Ön İşleme ve Kalite Asistanı

**PrepWise**, ham veri setlerindeki eksiklikler, aykırı değerler ve format tutarsızlıklarını **yapay zeka ve istatistiksel modeller** aracılığıyla tespit eden, temizleme önerileri sunan ve kullanıcı onayıyla temizlenmiş çıktı üreten modern bir veri ön işleme platformudur.

Veri bilimi geçmişi olmayan kullanıcılar bile tek arayüzden karmaşık veri hazırlama adımlarını yönetebilir. Sistem, hem güçlü bir Python/FastAPI arka ucu hem de Glassmorphism estetiğiyle tasarlanmış React tabanlı bir ön yüzden oluşur. Tüm bileşenler Docker konteynerleri üzerinde bağımsız çalışır.

---

## 📌 Kapsam ve Sınırlar

| Konu | Detay |
|---|---|
| **Hedef Veri Tipi** | Küçük–orta ölçekli tablo verisi (CSV / XLSX) |
| **Dosya Boyutu Sınırı** | 20 MB (bellek tüketimini kontrol altında tutmak için) |
| **Kullanıcı Onayı** | Sistem ham veriyi onaysız değiştirmez; önce analiz eder, sonra kullanıcı seçer |
| **Arka Plan İşlemleri** | FastAPI `BackgroundTasks` tabanlı; sunucu kapanırsa yarım kalan görevler `error` durumuna alınır |
| **Büyük Veri Notu** | Chunk processing, kalıcı görev kuyruğu (Celery/ARQ) ve dağıtık işleme gelecek çalışma olarak planlanabilir |

---

## 🛠 Teknoloji Yığını

### ⚙️ Backend

| Teknoloji | Kullanım Amacı |
|---|---|
| **Python / FastAPI** | Ana arka uç çatısı; asenkron, yüksek performanslı REST API |
| **Pandas & NumPy** | CSV/XLSX okuma, profil çıkarma, temizleme pipeline'ı |
| **Scikit-learn** | DBSCAN, Isolation Forest, LOF (aykırı değer tespiti); KNNImputer & MICE (eksik değer doldurma) |
| **SQLAlchemy + PostgreSQL** | Kullanıcı kayıtları, dataset meta verisi, işlem geçmişi |
| **Google Gemini AI** | Gömülü AI chatbot asistanı (`/assistant/chat` endpoint) |
| **SlowAPI** | IP tabanlı rate limiting |
| **JWT (python-jose)** | Kimlik doğrulama ve yetkilendirme |

**Backend modülleri (`backend/modules/`):**

| Modül | Sorumluluk |
|---|---|
| `file_reader.py` | CSV / XLSX okuma ve format tespiti |
| `missing_value.py` | Eksik değer analizi; Median, KNN, MICE stratejileri |
| `outlier_detector.py` | IQR, DBSCAN, Isolation Forest, LOF tabanlı aykırı değer tespiti |
| `format_checker.py` | Tarih, isim, telefon vb. format tutarsızlığı tespiti |
| `feature_engineering.py` | Skewness analizi; Log, Z-Score, Winsorize dönüşümleri |
| `recommendation.py` | Analiz sonuçlarını öneri kartlarına dönüştürme |
| `pipeline.py` | Seçili temizleme adımlarını sıralı uygulama |

---

### 🎨 Frontend

| Teknoloji | Kullanım Amacı |
|---|---|
| **React 18 + Vite** | Bileşen tabanlı, hızlı derleme ve HMR |
| **Vanilla CSS** | Glassmorphism, gradient animasyonlar, CSS Grid & Flexbox |
| **lucide-react** | Tutarlı ikon seti |
| **Nginx** | Üretim ortamında static dosya sunumu ve `/api` reverse proxy |

**Önemli bileşenler (`frontend-new/src/components/`):**

| Bileşen | Açıklama |
|---|---|
| `Hero` | Ana sayfa hero bölümü |
| `FileUpload` | Sürükle-bırak dosya yükleme |
| `AnalysisCards` | Analiz durum kartları |
| `DatasetWorkspace` | Dataset bazlı iş akışı görünümü |
| `UserDashboard` | Kullanıcının proje ve dataset özet paneli |
| `AccountSettings` | Profil, güvenlik ve kullanım istatistikleri sekmeleri |
| `Chatbot` | Gemini tabanlı AI asistan arayüzü |
| `AuthModal` | Giriş / Kayıt / Şifre sıfırlama modal'ı |
| `HowItWorks` | Adım adım nasıl çalışır bölümü |
| `FAQ` | Sık sorulan sorular bölümü |
| `workspace/AnalysisResults` | Analiz önerileri, karşılaştırma ve profil görünümleri |
| `workspace/ComparisonView` | Temizleme öncesi / sonrası karşılaştırma |
| `workspace/ProfileView` | Sütun bazlı veri profili |

---

### 🐳 DevOps

| Servis | Container Adı | Port |
|---|---|---|
| PostgreSQL 15 | `cleaner-postgres` | `127.0.0.1:5432` |
| FastAPI Backend | `cleaner-backend` | `8000` |
| React (Nginx) Frontend | `cleaner-frontend` | `80` |

Tüm servisler `docker-compose.yml` ile tek komutta ayağa kalkar. Upload ve output dosyaları kalıcı volume ile disk üzerinde tutulur.

---

## 🔬 Temel İşleyiş Akışı

```
1. Dosya Yükleme  →  2. Analiz  →  3. Öneri Seçimi  →  4. Pipeline Uygulaması  →  5. Çıktı ve Rapor
```

1. **Yükleme:** Kullanıcı CSV/XLSX dosyasını sürükle-bırak ile yükler. Backend UUID atar, meta veriyi PostgreSQL'e kaydeder.
2. **Analiz:** `report/analyze` tetiklenir — eksik değer yüzdesi, aykırı değerler, format hataları ve skewness değerleri hesaplanır.
3. **Öneri Kartları:** JSON raporu şık checkbox/radio kartlarına dönüştürülür; kullanıcı her sütun için strateji seçer.
4. **Pipeline:** Seçimler `/apply` endpoint'ine gönderilir; veriler tüm temizleme adımlarından geçirilir.
5. **Çıktı:** Temizlenmiş CSV `outputs/` klasörüne kaydedilir; indirme bağlantısı aktif olur. Tüm işlemler audit log olarak veritabanına yazılır.

---

## 🔑 API Endpoint'leri

| Prefix | Router | Açıklama |
|---|---|---|
| `/api/v1/auth/...` | `auth_router` | Kayıt, giriş, token yenileme, şifre sıfırlama |
| `/api/v1/datasets/...` | `dataset_router` | Yükleme, analiz, uygulama, indirme |
| `/api/v1/projects/...` | `project_router` | Proje oluşturma ve listeleme |
| `/api/v1/templates/...` | `template_router` | Temizleme şablonları |
| `/api/v1/assistant/chat` | `assistant_router` | Gemini AI chatbot |

---

## 🚀 Kurulum

### Gereksinimler
- Docker ve Docker Compose yüklü olmalıdır.

### 1. `.env` Dosyasını Oluşturun

```bash
cp .env.example .env
```

`.env` dosyasını açıp en az şu değerleri güncelleyin:

| Değişken | Zorunlu | Açıklama |
|---|---|---|
| `POSTGRES_PASSWORD` | ✅ | Güçlü ve benzersiz bir parola |
| `SECRET_KEY` | ✅ | JWT anahtarı; `openssl rand -hex 32` ile üretin |
| `POSTGRES_USER` | — | Varsayılan: `postgres` |
| `POSTGRES_DB` | — | Varsayılan: `cleaner_db` |
| `GEMINI_API_KEY` | — | AI asistan için Google AI Studio API anahtarı |
| `GEMINI_MODEL` | — | Varsayılan: `gemini-2.5-flash-lite` |

### 2. Servisleri Başlatın

```bash
docker-compose up -d
```

Tüm servisler sağlık kontrollerini geçtikten sonra uygulama `http://localhost` adresinde erişilebilir olur.

### 3. Logları İzleyin (İsteğe Bağlı)

```bash
docker-compose logs -f backend
```

### Servisleri Durdurmak

```bash
docker-compose down
```

> Veritabanı verisini de silmek için: `docker-compose down -v`

---

## 📧 SMTP (E-posta) Yapılandırması

Şifre sıfırlama e-postası için `.env` dosyasına aşağıdaki değişkenleri ekleyin:

| Değişken | Örnek | Açıklama |
|---|---|---|
| `SMTP_HOST` | `smtp.gmail.com` | SMTP sunucu adresi |
| `SMTP_PORT` | `587` | Port; 587 → STARTTLS, 465 → SSL/TLS |
| `SMTP_USER` | `ornek@gmail.com` | Gönderici e-posta adresi |
| `SMTP_PASSWORD` | `xxxx xxxx xxxx xxxx` | Uygulama şifresi |

> **Geliştirici modu (Fallback):** SMTP değişkenleri boş bırakılırsa e-posta gönderilmez; şifre sıfırlama token'ı backend konsol loglarına yazdırılır. Token arayüze girilerek işlem tamamlanabilir.

---

## 🤖 AI Asistan (Gemini)

Kullanıcılar **Chatbot** bileşeni üzerinden Gemini destekli bir asistanla etkileşime girebilir. Asistan yalnızca kimliği doğrulanmış kullanıcılara açıktır.

- API anahtarı yalnızca sunucu tarafında tutulur (`GEMINI_API_KEY`).
- Anahtar tanımlanmazsa `/api/v1/assistant/chat` endpoint'i `503` döner.
- Model varsayılanı: `gemini-2.5-flash-lite` (`.env` ile değiştirilebilir).

---

## 💪 Öne Çıkan Özellikler

- **Kullanıcı Özerkliği:** Hiçbir veri kullanıcı onayı alınmadan değiştirilmez; her adım şeffaf arayüzde sunulur.
- **Modüler Mimari:** Her analiz taktiği ayrı modül dosyasındadır. Yeni algoritma eklemek mevcut yapıyı bozmaz.
- **Proje ve Template Sistemi:** Kullanıcılar çalışmalarını projeler altında gruplar, sık kullanılan konfigürasyonları şablon olarak kaydeder.
- **Veri Karşılaştırma:** `ComparisonView` bileşeni ile temizleme öncesi ve sonrası veri yan yana incelenebilir.
- **Audit Log:** Tüm işlem adımları saniye bazında veritabanına kaydedilir.
- **Rate Limiting:** IP tabanlı istek sınırlama ile API kötüye kullanımı önlenir.
- **SMTP Fallback:** Geliştirme ortamında SMTP yapılandırması gerektirmeden şifre sıfırlama akışı çalışır.

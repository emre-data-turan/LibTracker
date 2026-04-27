# LibTracker

Üniversite kütüphanelerinin ve çalışma alanlarının **anlık doluluk seviyelerini** izleyen, yöneten ve görüntüleyen web uygulaması.

**Ekip:** Rebs Dev &nbsp;|&nbsp; **Hafta:** 9–14 &nbsp;|&nbsp; **Nisan–Haziran 2026**

---

## Özellikler

| # | Özellik | Açıklama |
|---|---------|----------|
| 01 | Gerçek Zamanlı Doluluk | Tüm konumların anlık doluluk yüzdesi |
| 02 | Kullanıcı Geri Bildirimi | Doğrulanmış öğrenciler doluluk güncelleyebilir |
| 03 | Rezervasyon Sistemi | Yoğun dönemlerde koltuk önceden rezerve et |
| 04 | Admin İstatistik Panosu | Günlük zirve saatleri için görsel grafikler |

---

## Hızlı Başlangıç

### Gereksinimler

- Python 3.11+
- pip

### Kurulum

```bash
# Repoyu klonla
git clone https://github.com/emre-data-turan/LibTracker.git
cd LibTracker

# Bağımlılıkları kur
pip install -r backend/requirements.txt

# Ortam değişkenlerini ayarla
cp backend/.env.example backend/.env

# Uygulamayı başlat (seed verisiyle)
cd backend
python app.py
```

Uygulama `http://localhost:5000` adresinde çalışır.
Swagger UI: `http://localhost:5000/apidocs`

### Frontend

```bash
# Tarayıcıda aç
open demo.html   # veya dosyayı direkt tarayıcıya sürükle
```

---

## API Endpoint Listesi

### Libraries

| Method | Endpoint | Açıklama |
|--------|----------|----------|
| GET | `/libraries/` | Tüm kütüphaneler + anlık doluluk |
| GET | `/libraries/<id>/occupancy` | Tek kütüphane doluluk detayı |

### Auth

| Method | Endpoint | Açıklama |
|--------|----------|----------|
| POST | `/auth/register` | Yeni kayıt (üniversite e-postası zorunlu) |
| POST | `/auth/login` | Giriş → JWT token |
| POST | `/auth/logout` | Oturum kapatma (token iptal) |
| GET | `/auth/me` | Mevcut kullanıcı bilgisi |

### Reservations

| Method | Endpoint | Açıklama |
|--------|----------|----------|
| POST | `/reservations/` | Yeni rezervasyon |
| GET | `/reservations/user/<userId>` | Kullanıcının rezervasyonları |
| DELETE | `/reservations/<id>` | Rezervasyon iptali |

### Feedback

| Method | Endpoint | Açıklama |
|--------|----------|----------|
| POST | `/feedback/` | Geri bildirim gönder (rate limit: 30 dk) |
| GET | `/feedback/<libraryId>` | Kütüphane geri bildirimleri |

### Statistics (Admin)

| Method | Endpoint | Açıklama |
|--------|----------|----------|
| GET | `/stats/peak-hours` | Saat bazında zirve doluluk |
| GET | `/stats/daily-usage` | Günlük ortalama kullanım |

---

## Proje Yapısı

```
LibTracker/
├── backend/
│   ├── app.py              # Flask app factory
│   ├── models.py           # SQLAlchemy modelleri
│   ├── database.py         # Singleton SystemDatabase
│   ├── routes/
│   │   ├── auth.py         # JWT auth
│   │   ├── libraries.py    # Doluluk API
│   │   ├── reservations.py # Rezervasyon API
│   │   ├── feedback.py     # Geri bildirim API
│   │   └── stats.py        # Admin istatistik API
│   └── requirements.txt
├── frontend/
│   └── demo.html
├── tests/
│   ├── conftest.py
│   ├── test_auth.py        # 10 auth testi
│   ├── test_reservations.py# 11 rezervasyon testi
│   └── test_feedback.py    # 7 feedback testi
├── .github/
│   └── workflows/
│       └── ci.yml          # GitHub Actions CI
└── README.md
```

---

## Mimari

**Katmanlı Mimari (Layered Architecture)**

```
Frontend (HTML/JS)
      ↓ HTTP
Flask Blueprints (Routes Layer)
      ↓
Business Logic (route handler'lar içinde)
      ↓
SQLAlchemy ORM (Data Access Layer)
      ↓
SQLite / PostgreSQL
```

**Tasarım Deseni:** Singleton — `SystemDatabase` sınıfı tek bir veritabanı bağlantısı yönetir.

---

## Testleri Çalıştırma

```bash
pytest tests/ -v
```

---

## Ekip

| İsim | Rol | Branch |
|------|-----|--------|
| Sirac Ketenoglu | Backend Lead | `feature/backend-core` |
| Emre Turan | Auth & Feedback | `feature/auth-and-feedback` |
| Reis Yıldız | Frontend Lead | `feature/frontend-integration` |
| Barış Küçükkıya | Test & Rezervasyon | `feature/reservation-and-tests` |

---

> **Not:** Gerçek kütüphane sensör verisi olmadığından sistem seed data ve simülasyon kullanır.
> Bu normal ve kabul edilebilir — final raporda "gelecek çalışma" olarak belirtilecek.

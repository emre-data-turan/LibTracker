# LibTracker

A web application that tracks, manages, and displays the **real-time occupancy levels** of university libraries and study areas.

**Team:** Rebs Dev &nbsp;|&nbsp; **Week:** 9–14 &nbsp;|&nbsp; **April–June 2026**

---

## Features

| # | Feature | Description |
|---|---------|----------|
| 01 | Real-Time Occupancy | Live occupancy percentage of all locations |
| 02 | User Feedback | Verified students can update occupancy |
| 03 | Reservation System | Reserve a seat in advance during peak periods |
| 04 | Admin Statistics Dashboard | Visual charts for daily peak hours |

---

## Quick Start

### Requirements

- Python 3.11+
- pip

### Installation

```bash
# Clone the repository
git clone https://github.com/emre-data-turan/LibTracker.git
cd LibTracker

# Install dependencies
pip install -r backend/requirements.txt

# Set up environment variables
cp backend/.env.example backend/.env

# Start the application (with seed data)
cd backend
python app.py
```

The application runs at `http://localhost:5000`.
Swagger UI: `http://localhost:5000/apidocs`

### Frontend

```bash
# Open in browser
open demo.html   # or drag and drop the file directly into the browser
```

---

## API Endpoint List

### Libraries

| Method | Endpoint | Description |
|--------|----------|----------|
| GET | `/libraries/` | All libraries + real-time occupancy |
| GET | `/libraries/<id>/occupancy` | Single library occupancy details |

### Auth

| Method | Endpoint | Description |
|--------|----------|----------|
| POST | `/auth/register` | New registration (university email required) |
| POST | `/auth/login` | Login → JWT token |
| POST | `/auth/logout` | Logout (revoke token) |
| GET | `/auth/me` | Current user info |

### Reservations

| Method | Endpoint | Description |
|--------|----------|----------|
| POST | `/reservations/` | New reservation |
| GET | `/reservations/user/<userId>` | User's reservations |
| DELETE | `/reservations/<id>` | Cancel reservation |

### Feedback

| Method | Endpoint | Description |
|--------|----------|----------|
| POST | `/feedback/` | Submit feedback (rate limit: 30 mins) |
| GET | `/feedback/<libraryId>` | Library feedbacks |

### Statistics (Admin)

| Method | Endpoint | Description |
|--------|----------|----------|
| GET | `/stats/peak-hours` | Peak occupancy by hour |
| GET | `/stats/daily-usage` | Daily average usage |

---

## Project Structure

```
LibTracker/
├── backend/
│   ├── app.py              # Flask app factory
│   ├── models.py           # SQLAlchemy models
│   ├── database.py         # Singleton SystemDatabase
│   ├── routes/
│   │   ├── auth.py         # JWT auth
│   │   ├── libraries.py    # Occupancy API
│   │   ├── reservations.py # Reservation API
│   │   ├── feedback.py     # Feedback API
│   │   └── stats.py        # Admin stats API
│   └── requirements.txt
├── frontend/
│   └── demo.html
├── tests/
│   ├── conftest.py
│   ├── test_auth.py        # 10 auth tests
│   ├── test_reservations.py# 11 reservation tests
│   └── test_feedback.py    # 7 feedback tests
├── .github/
│   └── workflows/
│       └── ci.yml          # GitHub Actions CI
└── README.md
```

---

## Architecture

**Layered Architecture**

```
Frontend (HTML/JS)
      ↓ HTTP
Flask Blueprints (Routes Layer)
      ↓
Business Logic (inside route handlers)
      ↓
SQLAlchemy ORM (Data Access Layer)
      ↓
SQLite / PostgreSQL
```

**Design Pattern:** Singleton — The `SystemDatabase` class manages a single database connection.

---

## Running Tests

```bash
pytest tests/ -v
```

---

## Team

| Name | Role | Branch |
|------|-----|--------|
| Sirac Ketenoglu | Backend Lead | `feature/backend-core` |
| Emre Turan | Auth & Feedback | `feature/auth-and-feedback` |
| Reis Yıldız | Frontend Lead | `feature/frontend-integration` |
| Barış Küçükkıya | Test & Reservation | `feature/reservation-and-tests` |

---

> **Note:** Since there is no real library sensor data, the system uses seed data and simulation.
> This is normal and acceptable — it will be mentioned as "future work" in the final report.


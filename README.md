# BDR — Business Directory Backend

A gated business directory platform. Login required to access anything. Two roles for v1: **admin** and **investor**. One user maps to one listing.

---

## Stack

| Layer | Technology |
|---|---|
| Runtime | Python 3.12 |
| Framework | Django 5.x + Django REST Framework |
| Auth | djangorestframework-simplejwt (15 min access / 7 day refresh) |
| Database | PostgreSQL 16 (FTS + pg_trgm for search) |
| Cache | Redis 7 |
| Email | Gmail SMTP |
| Excel import | openpyxl (sync, max 500 rows) |
| Package manager | uv |
| Admin UI | django-unfold |

---

## Getting Started

### Prerequisites

- Docker + Docker Compose
- uv (`pip install uv` or `brew install uv`)

### 1. Copy environment file

```bash
cp .env.example .env
```

Edit `.env` and fill in your values (database, Redis, Gmail SMTP credentials, secret key).

### 2. Start containers

```bash
docker compose up --build
```

This will:
- Start PostgreSQL 16 with `pg_trgm` extension enabled
- Start Redis 7
- Run `migrate` and start the Django dev server on port 8000

### 3. Create an admin user

```bash
uv run python manage.py createsuperuser
```

### 4. Create a registration key

Use the Django admin UI at `http://localhost:8000/django-admin/` or call:

```
POST /api/admin/registration-keys/create/
```

Share the key value with investors so they can self-register.

---

## Project Layout

```
bdr/
├── docker-compose.yml
├── Dockerfile
├── pyproject.toml          # uv-managed dependencies
├── scripts/
│   └── init_db.sql         # enables pg_trgm on DB init
├── manage.py
├── config/
│   ├── settings/
│   │   ├── base.py
│   │   ├── local.py
│   │   └── production.py
│   ├── urls.py
│   └── wsgi.py
└── apps/
    ├── accounts/           # users, registration keys, JWT auth
    ├── listings/           # listing CRUD, search, email verification
    ├── notifications/      # admin notification inbox
    ├── audit/              # append-only audit log
    └── imports/            # Excel bulk import (preview → confirm)
```

---

## API Reference

All endpoints require a valid JWT `Authorization: Bearer <token>` header unless noted.

### Auth

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/auth/register/` | Self-register with a valid registration key |
| POST | `/api/auth/login/` | Get access + refresh token pair |
| POST | `/api/auth/refresh/` | Exchange refresh token for new access token |
| POST | `/api/auth/logout/` | Blacklist refresh token |
| GET | `/api/auth/me/` | Get own profile |
| PATCH | `/api/auth/me/update/` | Update name / phone number |
| POST | `/api/auth/send-verification/` | Send account email verification |
| POST | `/api/auth/verify-email/` | Confirm account email with token |
| POST | `/api/auth/change-password/` | Change password (authenticated) |
| POST | `/api/auth/forgot-password/` | Request password-reset link |
| POST | `/api/auth/reset-password/` | Confirm password reset with token |

### Listings (investor)

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/listings/mine/` | Get own listing |
| POST | `/api/listings/mine/` | Create own listing |
| PATCH | `/api/listings/mine/` | Edit own listing |
| DELETE | `/api/listings/mine/` | Soft-delete own listing |
| POST | `/api/listings/mine/submit/` | Submit listing for review (→ pending) |
| POST | `/api/listings/mine/send-verification/` | Send contact email verification |
| POST | `/api/listings/mine/verify-email/` | Confirm email verification token |

### Directory

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/search/` | Search published listings |
| GET | `/api/listings/<slug>/` | Public listing detail |

**Search query params:** `q`, `sector`, `country`, `region`, `funding_stage`, `revenue_range`, `headcount`, `company_type`, `sort` (`newest` \| `name`), `page`

### Admin — Listings

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/admin/listings/` | List all listings (`?status=`, `?is_deleted=true`) |
| POST | `/api/admin/listings/` | Create listing manually |
| GET | `/api/admin/listings/<id>/` | Full listing detail |
| PATCH | `/api/admin/listings/<id>/` | Edit any listing |
| PATCH | `/api/admin/listings/<id>/publish/` | Publish or unpublish (`action: "publish"\|"unpublish"`) |
| PATCH | `/api/admin/listings/<id>/archive/` | Archive listing |

### Admin — Users

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/admin/users/` | List users (`?status=`, `?role=`) |
| PATCH | `/api/admin/users/<id>/status/` | Suspend or activate a user |
| GET | `/api/admin/registration-keys/` | List registration keys |
| POST | `/api/admin/registration-keys/create/` | Create new key (deactivates previous) |

### Admin — Notifications & Audit

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/admin/notifications/` | List unread + recent notifications |
| PATCH | `/api/admin/notifications/<id>/read/` | Mark notification as read |
| POST | `/api/admin/notifications/read-all/` | Mark all notifications as read |
| GET | `/api/admin/audit-log/` | Read-only audit log |

### Admin — Import

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/admin/listings/import/sample/` | Download sample Excel template |
| POST | `/api/admin/listings/import/preview/` | Upload Excel file, get validation report |
| POST | `/api/admin/listings/import/confirm/` | Confirm import, write rows as draft listings |

---

## Listing Publish Flow

```
investor creates → DRAFT
investor submits → PENDING  (admin notified)
admin publishes  → PUBLISHED
investor edits   → PENDING  (reverts automatically)
admin unpublishes → DRAFT
admin/investor deletes → ARCHIVED + soft-deleted
```

---

## Excel Import Format

File must be `.xlsx`. Required columns: `company_name`, `primary_email`, `hq_country`.

Products: semicolon-separated rows of `name|description|category`
Key people: semicolon-separated rows of `name|title|linkedin`

Maximum 500 rows per import. Duplicate detection by `(company_name, hq_country)` within the file.

---

## Environment Variables

| Variable | Description |
|---|---|
| `SECRET_KEY` | Django secret key |
| `DEBUG` | `True` in local, `False` in production |
| `ALLOWED_HOSTS` | Comma-separated allowed hosts |
| `DATABASE_URL` | PostgreSQL connection string |
| `REDIS_URL` | Redis connection string |
| `EMAIL_HOST_USER` | Gmail address |
| `EMAIL_HOST_PASSWORD` | Gmail app password |
| `DJANGO_SETTINGS_MODULE` | e.g. `config.settings.local` |

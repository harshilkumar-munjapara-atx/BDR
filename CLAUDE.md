# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## Commands

All Django management commands must be run with `uv run` — never activate the venv manually.

```bash
# Start all services
docker compose up --build

# Run migrations
uv run python manage.py migrate

# Create a migration
uv run python manage.py makemigrations <app> --name <description>

# Open Django shell
uv run python manage.py shell

# Create superuser (admin role)
uv run python manage.py createsuperuser
```

Settings module is selected via `DJANGO_SETTINGS_MODULE` in `.env`. Default for local is `config.settings.local`.

There are no automated tests. Testing is done manually via Postman.

---

## Architecture

### App layout

```
apps/
├── accounts/     # Custom user model, registration keys, JWT auth
├── listings/     # BusinessListing + 7 related models, search, email verification
├── notifications/# Admin inbox (in-app only, no email)
├── audit/        # Append-only AuditLog, never raises
└── imports/      # Excel bulk import: preview → confirm (2-step)
```

### Auth model

- `AUTH_USER_MODEL = "accounts.User"` — email-based, UUID PK
- Two roles only: `admin` and `investor`
- Users have a `status` of `active` or `suspended`; suspended users are rejected at login
- Self-registration requires a valid `RegistrationKey` (only one key is active at a time — `RegistrationKey.save()` auto-deactivates all others)
- JWT: 15-min access, 7-day refresh. Refresh tokens are rotated and blacklisted on use.
- Custom token serializer (`CustomTokenObtainPairSerializer`) embeds `role` and `name` into the JWT payload

### Permissions pattern

Two custom permission classes in `apps/accounts/permissions.py`:
- `IsAdmin` — checks `request.user.role == "admin"`
- `IsActiveUser` — checks `request.user.status == "active"`

Most investor views use `[IsAuthenticated, IsActiveUser]`. Admin views use `[IsAuthenticated, IsAdmin]`.

### Listing data model

`BusinessListing` is the root. All other listing data hangs off it:
- **OneToOne** (single per listing): `ListingIdentity`, `ListingContact`, `ListingCommercial`
- **FK many**: `ListingOffice`, `ListingProduct`, `ListingKeyPerson`
- Each user can own at most one listing — enforced at DB level via `owner = OneToOneField(User)` and a HTTP 409 guard in `MyListingView.post()`

Status flow: `DRAFT → PENDING → PUBLISHED`. Editing a `PUBLISHED` listing auto-reverts it to `PENDING`. Delete sets `status=ARCHIVED`, `is_deleted=True`, `deleted_at=now()` (soft delete — data is never removed from DB).

`ListingWriteSerializer._save_nested()` handles all related sub-models in one call. Offices, products, and key people are **deleted and re-created** on every update (not diffed). OneToOne sub-models use `update_or_create`.

Slug generation is in `apps/listings/slug_utils.py`. Slugs are derived from `company_name` with a numeric suffix appended if the base slug is taken.

### Search

`SearchView` (`GET /api/search/`) is in `apps/listings/search_views.py`:
- Only queries `status=PUBLISHED, is_deleted=False`
- Full-text search via `SearchVector` with weights (A: company_name/tagline, B: description/product name, C: product description) + `TrigramSimilarity` fallback on `company_name`
- Results are cached in Redis under `search:<md5(params)>` with a 5-minute TTL (`SEARCH_CACHE_TTL`)
- Cache is invalidated with `cache.delete_pattern("search:*")` on publish, unpublish, edit, and delete

### Notification signal

`apps/listings/signals.py` — a `post_save` signal on `BusinessListing` creates an in-app `Notification` for every active admin when a listing transitions to `PENDING`. Registered in `apps/listings/apps.py`.

### Audit log

`apps/audit/services.log_action()` — call this after any meaningful state change. It wraps `AuditLog.objects.create()` in `try/except` and logs on failure; it never raises. The `AuditLog` admin is fully read-only (all `has_*_permission` methods return `False`).

### Excel import

Two-step flow in `apps/imports/`:
1. `POST /api/admin/import/preview/` — parses the file, returns a validation report, writes nothing
2. `POST /api/admin/import/confirm/` — writes valid rows as `status=DRAFT, source=EXCEL_IMPORT, owner=None`

Parser (`apps/imports/parser.py`) enforces max 500 rows. Deduplication is done within the file by `(company_name, hq_country)`. Products and key people are encoded as semicolon-separated `field|field|field` strings in the Excel columns.

### Caching

Redis is the only cache backend. Search results are cached; nothing else is. Key pattern: `"search:<md5>"`. Invalidate with `cache.delete_pattern("search:*")` whenever published listing data changes.

### Environment variables

All settings are loaded via `python-decouple`. Required vars: `DJANGO_SECRET_KEY`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `REDIS_URL`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `DJANGO_SETTINGS_MODULE`. See `config/settings/base.py` for the full list and defaults.

### Infrastructure

Three Docker services (`docker-compose.yml`):
- `db` — postgres:16, `pg_trgm` enabled via `scripts/init_db.sql` (mounted at container init)
- `redis` — redis:7-alpine
- `api` — Django app; depends on both db and redis healthchecks before starting

Media files are stored on the local filesystem at `MEDIA_ROOT`. No object storage.

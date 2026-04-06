# Listings API

Base prefix: `/api/` for investor-facing endpoints, `/api/admin/` for admin endpoints.

---

## Status Flow

```
DRAFT → PENDING → PUBLISHED
                      ↓
                  ARCHIVED
```

- Investor creates a listing → starts as `draft`
- Investor submits → `draft` → `pending`
- Admin publishes → `pending` → `published`
- Admin unpublishes → `published` → `draft`
- Admin or investor deletes → `archived`
- Editing a `published` listing auto-reverts it to `pending`

---

## Investor Endpoints

> All investor endpoints require `Bearer <token>` and an `active` account status.

---

### 1. Get My Listing

Route: `/api/listings/mine/`  
Method: `GET`  
Authentication: `Bearer <token>`

#### Response (Success - 200)
```json
{
    "id": "a1b2c3d4-...",
    "status": "draft",
    "source": "manual",
    "published_at": null,
    "contact_email_verified": false,
    "created_at": "2025-10-09T11:00:00Z",
    "updated_at": "2025-10-09T11:00:00Z",
    "identity": {
        "company_name": "Acme Corp",
        "slug": "acme-corp",
        "tagline": "Building the future",
        "description": "A description of the company.",
        "company_type": "startup",
        "sector_tags": ["FinTech", "SaaS"],
        "founded_year": 2018,
        "headcount_range": "11-50",
        "website_url": "https://acme.com",
        "linkedin_url": "https://linkedin.com/company/acme",
        "logo_url": "",
        "other_social": {}
    },
    "contact": {
        "primary_email": "hello@acme.com",
        "primary_phone": "+2347012345678",
        "hq_country": "Nigeria",
        "hq_city": "Lagos",
        "regions_served": ["West Africa"],
        "timezone": "Africa/Lagos"
    },
    "commercial": {
        "revenue_range": "$1M-$5M",
        "funding_stage": "Series A",
        "business_type_tags": ["B2B", "SaaS"]
    },
    "offices": [
        { "country": "Nigeria", "city": "Lagos", "is_hq": true }
    ],
    "products": [
        {
            "id": "e5f6...",
            "name": "Core Platform",
            "short_description": "Our flagship product.",
            "category_tag": "SaaS"
        }
    ],
    "key_people": [
        {
            "id": "f7g8...",
            "full_name": "Ada Okafor",
            "job_title": "CEO",
            "linkedin_url": "https://linkedin.com/in/ada-okafor",
            "display_order": 0
        }
    ]
}
```

#### Response (Error - 404)
```json
{ "detail": "No listing found." }
```

---

### 2. Create My Listing

Route: `/api/listings/mine/`  
Method: `POST`  
Authentication: `Bearer <token>`

> One listing per user. Returns `409` if a listing already exists.  
> `offices`, `products`, and `key_people` are **replaced entirely** on every update — not merged.

#### Request Body
```json
{
    "identity": {
        "company_name": "Acme Corp",
        "tagline": "Building the future",
        "description": "A description of the company.",
        "company_type": "startup",
        "sector_tags": ["FinTech", "SaaS"],
        "founded_year": 2018,
        "headcount_range": "11-50",
        "website_url": "https://acme.com",
        "linkedin_url": "https://linkedin.com/company/acme"
    },
    "contact": {
        "primary_email": "hello@acme.com",
        "primary_phone": "+2347012345678",
        "hq_country": "Nigeria",
        "hq_city": "Lagos",
        "regions_served": ["West Africa"],
        "timezone": "Africa/Lagos"
    },
    "commercial": {
        "revenue_range": "$1M-$5M",
        "funding_stage": "Series A",
        "business_type_tags": ["B2B", "SaaS"]
    },
    "offices": [
        { "country": "Nigeria", "city": "Lagos", "is_hq": true }
    ],
    "products": [
        {
            "name": "Core Platform",
            "short_description": "Our flagship product.",
            "category_tag": "SaaS"
        }
    ],
    "key_people": [
        {
            "full_name": "Ada Okafor",
            "job_title": "CEO",
            "linkedin_url": "https://linkedin.com/in/ada-okafor",
            "display_order": 0
        }
    ]
}
```

**Required fields:** `identity.company_name`, `contact.primary_email`  
**Optional:** everything else

**`company_type` values:** `startup`, `sme`, `enterprise`, `ngo`, `other`

#### Response (Success - 201)
Full listing object (same shape as GET `/listings/mine/`).

#### Response (Error - 409)
```json
{ "detail": "You already have a listing. Edit your existing listing instead." }
```

---

### 3. Update My Listing

Route: `/api/listings/mine/`  
Method: `PATCH`  
Authentication: `Bearer <token>`

> All fields are optional — send only what you want to change.  
> If the listing is `published`, it is automatically reverted to `pending` on update.  
> `offices`, `products`, and `key_people` arrays are **fully replaced** if provided.

#### Request Body
Same schema as POST. Include only the sections you want to update.

#### Response (Success - 200)
Full listing object.

#### Response (Error - 403)
```json
{ "detail": "Archived listings cannot be edited." }
```

#### Response (Error - 404)
```json
{ "detail": "No listing found." }
```

---

### 4. Delete My Listing

Route: `/api/listings/mine/`  
Method: `DELETE`  
Authentication: `Bearer <token>`

> Soft delete. Sets `status=archived`, `is_deleted=true`, `deleted_at=<timestamp>`. Data is not removed from the database.

#### Response (Success - 204)
```
No content
```

#### Response (Error - 404)
```json
{ "detail": "No listing found." }
```

---

### 5. Submit Listing for Review

Route: `/api/listings/mine/submit/`  
Method: `POST`  
Authentication: `Bearer <token>`

> Transitions the listing from `draft` to `pending`. No request body needed.  
> Requires the listing to have both identity and contact information filled in.

#### Request Body
```json
{}
```

#### Response (Success - 200)
Full listing object with `status: "pending"`.

#### Response (Error - 400)
```json
{ "detail": "Only draft listings can be submitted." }
```
```json
{ "detail": "Listing must have identity information before submitting." }
```
```json
{ "detail": "Listing must have contact information before submitting." }
```

#### Response (Error - 404)
```json
{ "detail": "No listing found." }
```

---

### 6. Send Contact Email Verification

Route: `/api/listings/mine/send-verification/`  
Method: `POST`  
Authentication: `Bearer <token>`

> Sends a verification token to the listing's `primary_email`. Any previous unverified token is deleted.  
> Token expires after 24 hours.

#### Request Body
```json
{}
```

#### Response (Success - 200)
```json
{ "detail": "Verification email sent to hello@acme.com." }
```

#### Response (Error - 400)
```json
{ "detail": "Listing has no contact information." }
```

#### Response (Error - 404)
```json
{ "detail": "No listing found." }
```

---

### 7. Confirm Contact Email Verification

Route: `/api/listings/mine/verify-email/`  
Method: `POST`  
Authentication: `Bearer <token>`

> Verifies the token received by email. One-time use — the token cannot be reused once verified.

#### Request Body
```json
{
    "token": "<token_from_email>"
}
```

#### Response (Success - 200)
```json
{ "detail": "Contact email verified successfully." }
```

#### Response (Error - 400)
```json
{ "detail": "Token is required." }
```
```json
{ "detail": "Invalid or already used token." }
```
```json
{ "detail": "Token has expired. Request a new one." }
```

#### Response (Error - 403)
```json
{ "detail": "Token does not belong to your listing." }
```

---

### 8. Get Published Listing (Public Detail)

Route: `/api/listings/<slug>/`  
Method: `GET`  
Authentication: `Bearer <token>`

> Returns only `published` listings. Returns `404` for drafts, pending, or archived listings.

#### Response (Success - 200)
Full listing object (same shape as GET `/listings/mine/`).

#### Response (Error - 404)
```json
{ "detail": "Not found." }
```

---

### 9. Search Listings

Route: `/api/search/`  
Method: `GET`  
Authentication: `Bearer <token>`

> Full-text search across published listings. Results are cached in Redis for 5 minutes.  
> Search ranking: company name & tagline (highest) → description & product name → product description (lowest).  
> Falls back to trigram similarity on company name when full-text rank is low.

#### Query Parameters (all optional)

| Parameter       | Description                                        |
|-----------------|----------------------------------------------------|
| `q`             | Full-text search query                             |
| `sort`          | `newest` (default, by publish date) or `name`     |
| `sector`        | Filter by sector tag (e.g. `FinTech`)              |
| `country`       | Filter by HQ country                               |
| `region`        | Filter by region served (e.g. `West Africa`)       |
| `funding_stage` | Filter by funding stage (e.g. `Series A`)          |
| `revenue_range` | Filter by revenue range (e.g. `$1M-$5M`)          |
| `headcount`     | Filter by headcount range (e.g. `11-50`)           |
| `company_type`  | Filter by company type (e.g. `startup`)            |
| `page`          | Page number (default: 1)                           |

#### Response (Success - 200)
```json
{
    "count": 2,
    "page": 1,
    "page_size": 20,
    "match_type": "exact",
    "results": [
        {
            "id": "0e87817f-b31d-4097-8655-5ffecf5dc153",
            "slug": "lattice-cloud",
            "company_name": "Lattice Cloud",
            "tagline": "Connecting ideas to outcomes",
            "logo_url": "",
            "sector_tags": [
                "Logistics",
                "Supply Chain"
            ],
            "hq_country": "Senegal",
            "hq_city": "Dakar",
            "funding_stage": "Series A",
            "products": [
                {
                    "id": "5cc9e24e-0ca0-42fc-8163-b7ed445f4f14",
                    "name": "InsightHub",
                    "short_description": "A powerful insighthub for modern teams.",
                    "category_tag": "SaaS"
                },
                {
                    "id": "a5f8a61e-fd1b-4ec9-bc64-e04411e0985b",
                    "name": "ReportBuilder",
                    "short_description": "A powerful reportbuilder for modern teams.",
                    "category_tag": "API"
                }
            ],
            "key_people": [
                {
                    "id": "6c9a1525-a4a6-487f-89f2-f5d91d87ac15",
                    "full_name": "Ngozi Banda",
                    "job_title": "CEO",
                    "linkedin_url": "https://linkedin.com/in/ngozi-banda",
                    "display_order": 0
                },
                {
                    "id": "000229ed-114f-4909-802c-504d42b70906",
                    "full_name": "Yemi Mwangi",
                    "job_title": "Founder",
                    "linkedin_url": "https://linkedin.com/in/yemi-mwangi",
                    "display_order": 1
                }
            ],
            "status": "published",
            "source": "manual",
            "published_at": null,
            "created_at": "2026-04-04T07:29:21.752277Z",
            "updated_at": "2026-04-04T07:29:21.752279Z"
        },
        {
            "id": "6c1c7205-9ad7-4d4e-b63e-103cae0847ca",
            "slug": "nexacloud",
            "company_name": "NexaCloud",
            "tagline": "Your growth, our mission",
            "logo_url": "",
            "sector_tags": [
                "FinTech",
                "SaaS"
            ],
            "hq_country": "South Africa",
            "hq_city": "Johannesburg",
            "funding_stage": "Bootstrapped",
            "products": [
                {
                    "id": "995e585f-7449-4e2f-87bc-a2f4f3170e28",
                    "name": "SecureVault",
                    "short_description": "A powerful securevault for modern teams.",
                    "category_tag": "Mobile App"
                }
            ],
            "key_people": [
                {
                    "id": "4e258bc2-2ed3-4e11-bcc4-9d17ae961135",
                    "full_name": "Yemi Okafor",
                    "job_title": "MD",
                    "linkedin_url": "https://linkedin.com/in/yemi-okafor",
                    "display_order": 0
                }
            ],
            "status": "published",
            "source": "manual",
            "published_at": null,
            "created_at": "2026-04-04T07:29:21.628594Z",
            "updated_at": "2026-04-04T16:14:05.325383Z"
        }
    ]
}
```

---

## Admin Endpoints

> All admin endpoints require `Bearer <token>` and `role: admin`.

---

### 10. List All Listings

Route: `/api/admin/listings/`  
Method: `GET`  
Authentication: `Bearer <token>` (Admin only)

#### Query Parameters (all optional)

| Parameter    | Description                                     | Values                                    |
|--------------|-------------------------------------------------|-------------------------------------------|
| `status`     | Filter by listing status                        | `draft`, `pending`, `published`, `archived` |
| `is_deleted` | Include soft-deleted listings                   | `true`                                    |

#### Response (Success - 200)
```json
{
    "count": 120,
    "next": "http://api/admin/listings/?page=2",
    "previous": null,
    "results": [
        {
            "id": "a1b2c3d4-...",
            "company_name": "Acme Corp",
            "slug": "acme-corp",
            "owner_email": "owner@acme.com",
            "status": "pending",
            "source": "manual",
            "created_at": "2025-10-09T11:00:00Z",
            "updated_at": "2025-10-09T11:00:00Z"
        }
    ]
}
```

#### Response (Error - 403)
```json
{ "detail": "You do not have permission to perform this action." }
```

---

### 11. Admin Create Listing

Route: `/api/admin/listings/`  
Method: `POST`  
Authentication: `Bearer <token>` (Admin only)

> Creates a listing owned by the admin user. Same schema as investor create.

#### Request Body
Same as investor [Create My Listing](#2-create-my-listing).

#### Response (Success - 201)
```json
{
    "id": "a1b2c3d4-...",
    "company_name": "Acme Corp",
    "slug": "acme-corp",
    "owner_email": "admin@example.com",
    "status": "draft",
    "source": "manual",
    "created_at": "2025-10-09T11:00:00Z",
    "updated_at": "2025-10-09T11:00:00Z"
}
```

---

### 12. Get Listing Detail (Admin)

Route: `/api/admin/listings/<uuid>/`  
Method: `GET`  
Authentication: `Bearer <token>` (Admin only)

#### Response (Success - 200)
Full listing object (same shape as GET `/listings/mine/`).

#### Response (Error - 404)
```json
{ "detail": "Not found." }
```

---

### 13. Update Listing (Admin)

Route: `/api/admin/listings/<uuid>/`  
Method: `PATCH`  
Authentication: `Bearer <token>` (Admin only)

> Same update logic as investor PATCH. If the listing is `published`, it is reverted to `pending`.  
> `offices`, `products`, and `key_people` are fully replaced if provided.

#### Request Body
Same as investor [Update My Listing](#3-update-my-listing).

#### Response (Success - 200)
Full listing object.

#### Response (Error - 404)
```json
{ "detail": "Not found." }
```

---

### 14. Publish / Unpublish Listing

Route: `/api/admin/listings/<uuid>/publish/`  
Method: `PATCH`  
Authentication: `Bearer <token>` (Admin only)

#### Request Body
```json
{ "action": "publish" }
```
```json
{ "action": "unpublish" }
```

> `publish` → sets `status=published`, records `published_at`  
> `unpublish` → sets `status=draft`, clears `published_at`

#### Response (Success - 200)
```json
{
    "id": "a1b2c3d4-...",
    "company_name": "Acme Corp",
    "slug": "acme-corp",
    "owner_email": "owner@acme.com",
    "status": "published",
    "source": "manual",
    "created_at": "2025-10-09T11:00:00Z",
    "updated_at": "2025-10-09T11:00:00Z"
}
```

#### Response (Error - 400)
```json
{ "detail": "action must be 'publish' or 'unpublish'." }
```

#### Response (Error - 404)
```json
{ "detail": "Not found." }
```

---

### 15. Archive Listing (Admin)

Route: `/api/admin/listings/<uuid>/archive/`  
Method: `PATCH`  
Authentication: `Bearer <token>` (Admin only)

> Sets `status=archived`. Unlike an investor delete, this does **not** set `is_deleted=true`.

#### Request Body
```json
{}
```

#### Response (Success - 204)
```
No content
```

#### Response (Error - 404)
```json
{ "detail": "Not found." }
```

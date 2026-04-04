# Excel Import API

All routes are admin-only (`IsAdmin` permission required).

The import flow is two-step: **preview first** (validates, writes nothing), then **confirm** (writes valid rows as draft listings).

---

### 1. Download Sample File

Route: `/api/admin/listings/import/sample/`  
Method: `GET`  
Authentication: Admin only

#### Response (Success - 200)
Returns the sample `.xlsx` file as a download (`listings_import_sample.xlsx`).

> Use this to get a correctly formatted template before preparing your import file.

---

### 2. Preview Import

Route: `/api/admin/listings/import/preview/`  
Method: `POST`  
Authentication: Admin only  
Content-Type: `multipart/form-data`

#### Request Body:
| Field | Type | Description |
|-------|------|-------------|
| `file` | `file` | Excel file (`.xlsx` or `.xls`). Maximum 500 data rows. |

#### Response (Success - 200)
```json
{
    "total_rows": 10,
    "valid_rows": 8,
    "error_rows": [
        {
            "row": 4,
            "company_name": "Acme Corp",
            "errors": ["primary_email is required."]
        },
        {
            "row": 7,
            "company_name": "Globex",
            "errors": ["founded_year '20xx' is not a valid year.", "Duplicate entry: Globex / Nigeria."]
        }
    ],
    "global_errors": [],
    "can_import": true
}
```

> `can_import` is `true` only when there are no `global_errors` and at least one valid row. Use this flag to decide whether to proceed to the confirm step. Nothing is written to the database.

#### Response (Error - 400, No File)
```json
{
    "detail": "No file provided."
}
```

#### Response (Error - 400, Wrong Format)
```json
{
    "detail": "Only .xlsx / .xls files are accepted."
}
```

---

### 2. Confirm Import

Route: `/api/admin/listings/import/confirm/`  
Method: `POST`  
Authentication: Admin only  
Content-Type: `multipart/form-data`

#### Request Body:
| Field | Type | Description |
|-------|------|-------------|
| `file` | `file` | Same Excel file uploaded in the preview step (`.xlsx` or `.xls`). |

#### Response (Success - 201)
```json
{
    "created": 8,
    "skipped": 2,
    "message": "Import complete. 8 listings created as draft."
}
```

> All valid rows are created as `status=DRAFT`, `source=EXCEL_IMPORT`, with no owner assigned. Invalid rows within an otherwise valid file are silently skipped and counted in `skipped`. Each created listing is recorded in the audit log.

#### Response (Error - 400, File-level Errors)
```json
{
    "detail": "File has errors.",
    "global_errors": [
        "File has 612 rows; maximum allowed is 500."
    ]
}
```

#### Response (Error - 400, No Valid Rows)
```json
{
    "detail": "No valid rows to import."
}
```

---

### Excel File Format

The first row must be a header row. Column names are **case-insensitive** and whitespace-trimmed.

#### Required Columns:
| Column | Description |
|--------|-------------|
| `company_name` | Name of the business |
| `primary_email` | Primary contact email |
| `hq_country` | Headquarters country |

#### Optional Columns:
| Column | Description |
|--------|-------------|
| `tagline` | Short tagline |
| `description` | Full business description |
| `company_type` | Type of company |
| `sector` | Comma-separated sector tags (e.g. `Fintech, SaaS`) |
| `founded_year` | Year founded (integer) |
| `headcount_range` | Headcount range string |
| `website` | Website URL |
| `linkedin` | LinkedIn URL |
| `primary_phone` | Primary contact phone |
| `hq_city` | Headquarters city |
| `regions_served` | Comma-separated regions (e.g. `Africa, MENA`) |
| `revenue_range` | Revenue range string |
| `funding_stage` | Funding stage string |
| `business_type_tags` | Comma-separated business type tags |
| `products` | Semicolon-separated products, each pipe-delimited: `name\|description\|category` |
| `key_people` | Semicolon-separated people, each pipe-delimited: `full_name\|job_title\|linkedin_url` |

#### Multi-value Column Examples:
```
products:   "Analytics Dashboard|BI tool for SMEs|SaaS; Mobile App|iOS app|Mobile"
key_people: "Jane Doe|CEO|https://linkedin.com/in/jane; John Smith|CTO|"
```

#### Validation Rules:
- Maximum **500 rows** per file.
- Rows missing `company_name`, `primary_email`, or `hq_country` are invalid.
- `founded_year` must be a valid integer if provided.
- Duplicate `(company_name, hq_country)` pairs within the same file are flagged as errors.

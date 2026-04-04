# Audit Log API

All routes are admin-only (`IsAdmin` permission required). The audit log is append-only and read-only — entries are never modified or deleted.

---

### 1. List Audit Logs

Route: `/api/admin/audit-log/`  
Method: `GET`  
Authentication: Admin only

#### Query Parameters:
| Parameter | Type | Description |
|-----------|------|-------------|
| `target_type` | `string` | Filter by the type of the target object (case-insensitive, e.g. `businesslisting`) |
| `target_id` | `string` | Filter by the ID of the target object |
| `action` | `string` | Filter by action type. One of: `created`, `updated`, `deleted`, `published`, `archived`, `key_changed` |

#### Response (Success - 200)
```json
[
    {
        "id": "b3f6a1c2-...",
        "actor_email": "admin@example.com",
        "action": "published",
        "target_type": "BusinessListing",
        "target_id": "a1b2c3d4-...",
        "changed_fields": {
            "status": ["pending", "published"]
        },
        "timestamp": "2025-10-09T11:14:06.183646+05:30"
    }
]
```

> Results are ordered by newest first. `actor_email` is `null` if the actor's account has been deleted. `changed_fields` is a JSON object containing the fields that were changed — structure varies by action type and may be empty (`{}`).

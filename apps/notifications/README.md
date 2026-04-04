# Notifications API

All routes are admin-only (`IsAdmin` permission required).

---

### 1. List Notifications

Route: `/api/notifications/`  
Method: `GET`  
Authentication: Admin only

#### Query Parameters:
| Parameter | Type | Description |
|-----------|------|-------------|
| `unread` | `string` | Pass `true` to return only unread notifications |

#### Response (Success - 200)
```json
{
    "unread_count": 3,
    "results": [
        {
            "id": "b3f6a1c2-...",
            "type": "new_listing_submitted",
            "reference_id": "a1b2c3d4-...",
            "message": "A new listing has been submitted for review.",
            "is_read": false,
            "created_at": "2025-10-09T11:14:06.183646+05:30"
        }
    ]
}
```

> Returns up to 50 notifications, ordered by newest first. `unread_count` always reflects the total unread count regardless of the `unread` filter. `type` is one of: `new_listing_submitted`, `new_user_registered`, `listing_flagged`. `reference_id` points to the related object (e.g. listing UUID) and may be `null`.

---

### 2. Mark Notification as Read

Route: `/api/notifications/{id}/read/`  
Method: `PATCH`  
Authentication: Admin only

#### Path Parameters:
| Parameter | Type | Description |
|-----------|------|-------------|
| `id` | `uuid` | The notification UUID |

#### Response (Success - 200)
```json
{
    "id": "b3f6a1c2-...",
    "type": "new_listing_submitted",
    "reference_id": "a1b2c3d4-...",
    "message": "A new listing has been submitted for review.",
    "is_read": true,
    "created_at": "2025-10-09T11:14:06.183646+05:30"
}
```

#### Response (Error - 404)
```json
{
    "detail": "Not found."
}
```

> Only marks the calling admin's own notification as read. A notification belonging to another admin returns 404.

---

### 3. Mark All Notifications as Read

Route: `/api/notifications/read-all/`  
Method: `POST`  
Authentication: Admin only

#### Request Body:
None

#### Response (Success - 204)
No content.

> Marks all unread notifications for the calling admin as read in a single bulk update.

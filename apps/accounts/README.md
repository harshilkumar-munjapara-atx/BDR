# Accounts API

Base prefix: `/api/auth/` for user-facing endpoints, `/api/admin/` for admin endpoints.

---

## Auth Endpoints

### 1. Register

Route: `/api/auth/register/`  
Method: `POST`  
Authentication: None

#### Request Body:
```json
{
    "email": "user@example.com",
    "name": "John Doe",
    "phone_number": "+1234567890",
    "password": "securepassword",
    "registration_key": "YOUR_REGISTRATION_KEY"
}
```

> `phone_number` is optional. `registration_key` must match an active key in the system.

#### Response (Success - 201)
```json
{
    "id": "b3f6a1c2-...",
    "email": "user@example.com",
    "name": "John Doe",
    "phone_number": "+1234567890",
    "role": "investor",
    "status": "active",
    "email_verified": false,
    "created_at": "2025-10-09T11:14:06.183646+05:30"
}
```

#### Response (Error - 400)
```json
{
    "registration_key": ["Invalid or expired registration key."]
}
```
```json
{
    "email": ["An account with this email already exists."]
}
```

---

### 2. Login

Route: `/api/auth/login/`  
Method: `POST`  
Authentication: None

#### Request Body:
```json
{
    "email": "user@example.com",
    "password": "securepassword"
}
```

#### Response (Success - 200)
```json
{
    "access": "<access_token>",
    "refresh": "<refresh_token>",
    "role": "investor",
    "name": "John Doe"
}
```

#### Response (Error - 401)
```json
{
    "detail": "No active account found with the given credentials"
}
```

#### Response (Error - 400, Suspended Account)
```json
{
    "non_field_errors": ["Your account has been suspended."]
}
```

---

### 3. Refresh Token

Route: `/api/auth/refresh/`  
Method: `POST`  
Authentication: None

#### Request Body:
```json
{
    "refresh": "<refresh_token>"
}
```

#### Response (Success - 200)
```json
{
    "access": "<new_access_token>"
}
```

#### Response (Error - 401)
```json
{
    "detail": "Token is invalid or expired",
    "code": "token_not_valid"
}
```

---

### 4. Logout

Route: `/api/auth/logout/`  
Method: `POST`  
Authentication: `Bearer <token>`

#### Request Body:
```json
{
    "refresh": "<refresh_token>"
}
```

#### Response (Success - 204)
```
No content
```

#### Response (Error - 400)
```json
{
    "detail": "Invalid token."
}
```

---

### 5. Get Current User

Route: `/api/auth/me/`  
Method: `GET`  
Authentication: `Bearer <token>`

#### Response (Success - 200)
```json
{
    "id": "b3f6a1c2-...",
    "email": "user@example.com",
    "name": "John Doe",
    "phone_number": "+1234567890",
    "role": "investor",
    "status": "active",
    "email_verified": false,
    "created_at": "2025-10-09T11:14:06.183646+05:30"
}
```

#### Response (Error - 401)
```json
{
    "detail": "Authentication credentials were not provided."
}
```

---

### 6. Update Current User

Route: `/api/auth/me/update/`  
Method: `PATCH`  
Authentication: `Bearer <token>`

#### Request Body (all fields optional):
```json
{
    "name": "Jane Doe",
    "phone_number": "+9876543210"
}
```

#### Response (Success - 200)
```json
{
    "name": "Jane Doe",
    "phone_number": "+9876543210"
}
```

#### Response (Error - 401)
```json
{
    "detail": "Authentication credentials were not provided."
}
```

---

## Admin Endpoints

> All admin endpoints require `role: admin`.

### 7. List Users

Route: `/api/admin/users/`  
Method: `GET`  
Authentication: `Bearer <token>` (Admin only)

#### Query Parameters (optional):
| Parameter | Description | Values |
|-----------|-------------|--------|
| `status`  | Filter by account status | `active`, `suspended` |
| `role`    | Filter by role | `admin`, `investor` |

#### Response (Success - 200)
```json
[
    {
        "id": "b3f6a1c2-...",
        "email": "user@example.com",
        "name": "John Doe",
        "role": "investor",
        "status": "active",
        "created_at": "2025-10-09T11:14:06.183646+05:30"
    }
]
```

#### Response (Error - 403)
```json
{
    "detail": "You do not have permission to perform this action."
}
```

---

### 8. Update User Status

Route: `/api/admin/users/<uuid>/status/`  
Method: `PATCH`  
Authentication: `Bearer <token>` (Admin only)

#### Request Body:
```json
{
    "status": "suspended"
}
```

> Accepted values: `active`, `suspended`

#### Response (Success - 200)
```json
{
    "status": "suspended"
}
```

#### Response (Error - 400)
```json
{
    "status": ["Invalid status."]
}
```

#### Response (Error - 403)
```json
{
    "detail": "You do not have permission to perform this action."
}
```

#### Response (Not Found - 404)
```json
{
    "detail": "No User matches the given query."
}
```

---

### 9. List Registration Keys

Route: `/api/admin/registration-keys/`  
Method: `GET`  
Authentication: `Bearer <token>` (Admin only)

#### Response (Success - 200)
```json
[
    {
        "id": "c4e7b2d1-...",
        "key_value": "INVITE-ABC123",
        "is_active": true,
        "notes": "For Q4 onboarding batch",
        "created_by_name": "Admin User",
        "created_at": "2025-10-01T09:00:00.000000+05:30"
    }
]
```

> Only one key can be active at a time. Creating a new active key automatically deactivates the previous one.

#### Response (Error - 403)
```json
{
    "detail": "You do not have permission to perform this action."
}
```

---

### 10. Create Registration Key

Route: `/api/admin/registration-keys/create/`  
Method: `POST`  
Authentication: `Bearer <token>` (Admin only)

#### Request Body:
```json
{
    "key_value": "INVITE-XYZ789",
    "notes": "For new investor batch"
}
```

> `notes` is optional. The new key is automatically set as active; the previously active key is deactivated.

#### Response (Success - 201)
```json
{
    "key_value": "INVITE-XYZ789",
    "notes": "For new investor batch"
}
```

#### Response (Error - 400)
```json
{
    "key_value": ["This key value already exists."]
}
```

#### Response (Error - 403)
```json
{
    "detail": "You do not have permission to perform this action."
}
```

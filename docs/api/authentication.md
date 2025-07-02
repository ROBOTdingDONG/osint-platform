# API Authentication

## Overview

The OSINT Platform API uses JWT (JSON Web Tokens) for secure authentication and authorization. This guide covers all authentication methods, security best practices, and implementation examples.

## Authentication Flow

### 1. User Registration

```http
POST /api/v1/auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "SecurePassword123!",
  "full_name": "John Doe",
  "organization": "ACME Corp"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "user_id": "user_123456",
    "email": "user@example.com",
    "verification_required": true
  },
  "message": "Registration successful. Please verify your email."
}
```

### 2. Email Verification

```http
POST /api/v1/auth/verify-email
Content-Type: application/json

{
  "token": "email_verification_token_here"
}
```

### 3. User Login

```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "SecurePassword123!"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "expires_in": 3600,
    "user": {
      "id": "user_123456",
      "email": "user@example.com",
      "full_name": "John Doe",
      "role": "user",
      "permissions": ["read:data", "write:reports"]
    }
  }
}
```

## Token Types

### Access Token
- **Purpose**: Authenticate API requests
- **Lifetime**: 1 hour (configurable)
- **Usage**: Include in Authorization header
- **Claims**: User ID, email, role, permissions, expiration

### Refresh Token
- **Purpose**: Obtain new access tokens
- **Lifetime**: 30 days (configurable)
- **Usage**: Refresh access tokens when expired
- **Security**: Stored securely, single-use

## Making Authenticated Requests

### Authorization Header

```http
GET /api/v1/user/profile
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json
```

### cURL Example

```bash
curl -X GET "https://api.osintplatform.com/api/v1/user/profile" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json"
```

### Python Example

```python
import requests

headers = {
    "Authorization": "Bearer YOUR_ACCESS_TOKEN",
    "Content-Type": "application/json"
}

response = requests.get(
    "https://api.osintplatform.com/api/v1/user/profile",
    headers=headers
)

user_data = response.json()
```

### JavaScript Example

```javascript
const token = localStorage.getItem('access_token');

const response = await fetch('/api/v1/user/profile', {
  method: 'GET',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  }
});

const userData = await response.json();
```

## Token Refresh

When an access token expires, use the refresh token to obtain a new one:

```http
POST /api/v1/auth/refresh
Content-Type: application/json

{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "expires_in": 3600
  }
}
```

## API Keys (Server-to-Server)

For server-to-server authentication, use API keys:

### Generate API Key

```http
POST /api/v1/auth/api-keys
Authorization: Bearer YOUR_ACCESS_TOKEN
Content-Type: application/json

{
  "name": "Production API Key",
  "permissions": ["read:data", "write:reports"],
  "expires_at": "2025-12-31T23:59:59Z"
}
```

### Use API Key

```http
GET /api/v1/data/sources
X-API-Key: your-api-key-here
Content-Type: application/json
```

## Role-Based Access Control (RBAC)

### User Roles

| Role | Description | Default Permissions |
|------|-------------|--------------------|
| `admin` | Full system access | All permissions |
| `manager` | Team management | Read/write data, manage users |
| `analyst` | Data analysis | Read data, create reports |
| `viewer` | Read-only access | Read data, view reports |
| `api_user` | API access only | Configurable per key |

### Permission System

Permissions follow the format: `action:resource`

#### Available Permissions

**Data Management:**
- `read:data` - View collected data
- `write:data` - Modify data entries
- `delete:data` - Remove data entries

**Collection Management:**
- `read:collectors` - View data collectors
- `write:collectors` - Create/modify collectors
- `execute:collectors` - Run collection jobs

**Report Management:**
- `read:reports` - View reports
- `write:reports` - Create/modify reports
- `share:reports` - Share reports externally

**User Management:**
- `read:users` - View user profiles
- `write:users` - Manage user accounts
- `admin:users` - Full user administration

**Organization Management:**
- `read:organization` - View org settings
- `write:organization` - Modify org settings
- `admin:organization` - Full org administration

## Security Best Practices

### Client-Side Security

1. **Token Storage**
   ```javascript
   // Secure token storage
   const tokenStorage = {
     setToken: (token) => {
       sessionStorage.setItem('access_token', token);
     },
     getToken: () => {
       return sessionStorage.getItem('access_token');
     },
     removeToken: () => {
       sessionStorage.removeItem('access_token');
       sessionStorage.removeItem('refresh_token');
     }
   };
   ```

2. **Automatic Token Refresh**
   ```javascript
   class APIClient {
     async request(url, options = {}) {
       let token = tokenStorage.getToken();
       
       // Try request with current token
       let response = await fetch(url, {
         ...options,
         headers: {
           'Authorization': `Bearer ${token}`,
           ...options.headers
         }
       });
       
       // If token expired, refresh and retry
       if (response.status === 401) {
         token = await this.refreshToken();
         response = await fetch(url, {
           ...options,
           headers: {
             'Authorization': `Bearer ${token}`,
             ...options.headers
           }
         });
       }
       
       return response;
     }
   }
   ```

### Server-Side Security

1. **API Key Rotation**
   - Rotate API keys regularly
   - Monitor API key usage
   - Revoke compromised keys immediately

2. **Rate Limiting by Authentication**
   ```python
   # Higher limits for authenticated users
   rate_limits = {
       'anonymous': '100/hour',
       'authenticated': '1000/hour',
       'premium': '10000/hour'
   }
   ```

## Multi-Factor Authentication (MFA)

### Enable MFA

```http
POST /api/v1/auth/mfa/enable
Authorization: Bearer YOUR_ACCESS_TOKEN
Content-Type: application/json

{
  "method": "totp"
}
```

### MFA Login Flow

1. **Initial Login** (Username/Password)
2. **MFA Challenge** (TOTP code required)
3. **Complete Authentication** (Full access granted)

```http
POST /api/v1/auth/mfa/verify
Content-Type: application/json

{
  "mfa_token": "temp_token_from_initial_login",
  "code": "123456"
}
```

## Logout and Token Revocation

### Logout

```http
POST /api/v1/auth/logout
Authorization: Bearer YOUR_ACCESS_TOKEN
Content-Type: application/json

{
  "revoke_all_tokens": false
}
```

### Revoke All Sessions

```http
POST /api/v1/auth/revoke-all
Authorization: Bearer YOUR_ACCESS_TOKEN
```

## Error Handling

### Authentication Errors

| Error Code | HTTP Status | Description |
|------------|-------------|-------------|
| `AUTH_REQUIRED` | 401 | No authentication provided |
| `TOKEN_EXPIRED` | 401 | Access token has expired |
| `TOKEN_INVALID` | 401 | Token is malformed or invalid |
| `INSUFFICIENT_PERMISSIONS` | 403 | User lacks required permissions |
| `ACCOUNT_DISABLED` | 403 | User account is disabled |
| `EMAIL_NOT_VERIFIED` | 403 | Email verification required |
| `MFA_REQUIRED` | 403 | Multi-factor authentication required |

### Example Error Response

```json
{
  "success": false,
  "error": {
    "code": "TOKEN_EXPIRED",
    "message": "Access token has expired",
    "details": {
      "expired_at": "2025-07-02T10:30:00Z",
      "refresh_endpoint": "/api/v1/auth/refresh"
    }
  },
  "timestamp": "2025-07-02T11:30:00Z"
}
```

## Testing Authentication

### Postman Collection

Import our [Postman collection](../testing/postman-collection.json) for easy API testing.

### Test Credentials

```
# Development Environment
Email: test@osintplatform.com
Password: TestPassword123!
API Key: dev_api_key_123456789
```

---

**Security Notice**: Never expose authentication tokens or API keys in client-side code, logs, or version control. Always use environment variables for sensitive configuration.
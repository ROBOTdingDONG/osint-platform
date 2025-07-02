# API Overview

## Introduction

The OSINT Platform API is a RESTful service built with FastAPI that provides comprehensive endpoints for data collection, analysis, and reporting. The API follows OpenAPI 3.0 specifications and includes automatic documentation generation.

## API Base URL

- **Production**: `https://api.osintplatform.com`
- **Staging**: `https://staging-api.osintplatform.com`
- **Development**: `http://localhost:8000`

## API Versioning

The API uses URL path versioning:
- Current version: `v1`
- Base path: `/api/v1`
- Full endpoint example: `https://api.osintplatform.com/api/v1/health`

## Content Types

- **Request**: `application/json`
- **Response**: `application/json`
- **File uploads**: `multipart/form-data`

## Response Format

All API responses follow a consistent format:

```json
{
  "success": true,
  "data": {},
  "message": "Success",
  "timestamp": "2025-07-02T10:30:00Z",
  "request_id": "req_123456789"
}
```

### Error Response Format

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid request parameters",
    "details": {
      "field": "email",
      "issue": "Invalid email format"
    }
  },
  "timestamp": "2025-07-02T10:30:00Z",
  "request_id": "req_123456789"
}
```

## HTTP Status Codes

| Code | Description | Usage |
|------|-------------|-------|
| 200 | OK | Successful GET, PUT, PATCH |
| 201 | Created | Successful POST |
| 204 | No Content | Successful DELETE |
| 400 | Bad Request | Invalid request syntax |
| 401 | Unauthorized | Authentication required |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource not found |
| 422 | Unprocessable Entity | Validation errors |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server error |

## Authentication

The API uses JWT (JSON Web Tokens) for authentication. See [Authentication Guide](./authentication.md) for detailed information.

## Rate Limiting

API requests are rate-limited to ensure fair usage:

- **Free tier**: 100 requests/hour
- **Pro tier**: 1,000 requests/hour
- **Enterprise tier**: 10,000 requests/hour

See [Rate Limiting Guide](./rate-limiting.md) for more details.

## API Endpoints Categories

### Core Endpoints
- **Authentication**: User registration, login, token refresh
- **Users**: User management and profiles
- **Organizations**: Multi-tenant organization management

### Data Collection
- **Sources**: Manage data sources and connections
- **Collectors**: Control data collection jobs
- **Scrapers**: Web scraping configurations

### Analysis & Processing
- **Analytics**: Data analysis and insights
- **Reports**: Generate and manage reports
- **Alerts**: Configure monitoring and notifications

### System
- **Health**: System health and status
- **Metrics**: Performance and usage metrics
- **Webhooks**: External integrations

## SDK and Libraries

### Official SDKs
- **Python**: `pip install osint-platform-sdk`
- **JavaScript/Node.js**: `npm install @osint-platform/sdk`
- **Go**: `go get github.com/osint-platform/go-sdk`

### Quick SDK Example (Python)

```python
from osint_platform import OSINTClient

# Initialize client
client = OSINTClient(
    api_key="your-api-key",
    base_url="https://api.osintplatform.com"
)

# Get user profile
user = client.users.get_profile()
print(f"Welcome, {user.name}!")

# Start data collection
job = client.collectors.start_job(
    source_type="social_media",
    target="@company_handle",
    schedule="daily"
)
```

## Interactive Documentation

- **Swagger UI**: Available at `/docs` endpoint
- **ReDoc**: Available at `/redoc` endpoint
- **OpenAPI Schema**: Available at `/openapi.json`

## Support

For API support:
- 📧 API Support: api-support@osintplatform.com
- 💬 Discord: [#api-support channel](https://discord.gg/osint-platform)
- 📖 Documentation: This guide and endpoint reference

---

**Next Steps:**
- [Authentication Guide](./authentication.md)
- [Endpoints Reference](./endpoints.md)
- [Request Examples](./examples.md)
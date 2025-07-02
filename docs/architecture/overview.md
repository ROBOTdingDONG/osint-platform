# System Architecture Overview

## Introduction

The OSINT Platform is designed as a modern, cloud-native application with a microservices architecture that ensures scalability, maintainability, and security. This document provides a comprehensive overview of the system architecture, components, and their interactions.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                 USERS                                           │
├─────────────────────────────────────────────────────────────────────────────────┤
│                     Web App    │    Mobile App    │    API Clients             │
└─────────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              LOAD BALANCER                                     │
│                             (Nginx/Cloudflare)                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              API GATEWAY                                       │
│                            (FastAPI Application)                               │
├─────────────────────────────────────────────────────────────────────────────────┤
│  Authentication │  Rate Limiting  │  Request Routing  │  Response Caching     │
└─────────────────────────────────────────────────────────────────────────────────┘
                                      │
                    ┌─────────────────┼─────────────────┐
                    ▼                 ▼                 ▼
┌──────────────────────┐  ┌──────────────────────┐  ┌──────────────────────┐
│   CORE SERVICES      │  │   DATA PIPELINE      │  │   ANALYSIS ENGINE    │
├──────────────────────┤  ├──────────────────────┤  ├──────────────────────┤
│ • User Management    │  │ • Apache Airflow     │  │ • ML Models          │
│ • Organization Mgmt  │  │ • Data Collectors    │  │ • Sentiment Analysis │
│ • Report Generation  │  │ • Web Scrapers       │  │ • Trend Detection    │
│ • Alert System      │  │ • API Integrations   │  │ • Entity Recognition │
│ • Webhook Manager    │  │ • Data Validation    │  │ • Competitive Intel  │
└──────────────────────┘  └──────────────────────┘  └──────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              DATA LAYER                                        │
├─────────────────────────────────────────────────────────────────────────────────┤
│  MongoDB Cluster  │  Redis Cache  │  InfluxDB  │  Object Storage (S3/GCS)     │
│  (Primary Data)   │  (Sessions)   │ (Metrics)  │  (Files/Media)               │
└─────────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                            EXTERNAL SERVICES                                   │
├─────────────────────────────────────────────────────────────────────────────────┤
│  Social Media APIs │  News APIs  │  Email Service │  Monitoring │  Analytics   │
│  Twitter, LinkedIn │  NewsAPI    │  SendGrid      │  DataDog    │  Mixpanel    │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. Frontend Layer

#### Web Application
- **Technology**: React 18 + TypeScript
- **UI Framework**: Tailwind CSS + Tremor Charts
- **State Management**: Zustand
- **Build Tool**: Vite
- **Features**:
  - Responsive dashboard
  - Real-time data visualization
  - Advanced filtering and search
  - Report builder interface
  - User management console

#### Mobile Application (Planned)
- **Technology**: React Native
- **Platforms**: iOS, Android
- **Features**:
  - Dashboard overview
  - Push notifications
  - Offline data viewing
  - Alert management

### 2. API Gateway & Backend

#### FastAPI Application
- **Language**: Python 3.11+
- **Framework**: FastAPI
- **ASGI Server**: Uvicorn
- **Features**:
  - Automatic OpenAPI documentation
  - Request/response validation
  - Dependency injection
  - Background tasks
  - WebSocket support

#### Core Services

**Authentication Service**
```python
# JWT-based authentication
# OAuth2 integration
# Role-based access control (RBAC)
# Multi-factor authentication (MFA)
```

**User Management Service**
```python
# User registration and profiles
# Organization management
# Permission management
# Audit logging
```

**Data Collection Service**
```python
# Source configuration
# Collection job management
# Data validation and enrichment
# Error handling and retry logic
```

**Analytics Service**
```python
# Data processing pipelines
# ML model execution
# Report generation
# Real-time analysis
```

### 3. Data Pipeline

#### Apache Airflow
- **Purpose**: Workflow orchestration
- **Configuration**: Docker-based deployment
- **Features**:
  - Scheduled data collection
  - Dependency management
  - Error handling and retries
  - Pipeline monitoring

#### Data Collectors

**Social Media Collectors**
```python
# Twitter API integration
# LinkedIn data collection
# Reddit monitoring
# Instagram insights
# YouTube analytics
```

**News & Content Collectors**
```python
# RSS feed monitoring
# News API integration
# Web scraping (Scrapy/Playwright)
# PDF document processing
# Image and video analysis
```

**Business Intelligence Collectors**
```python
# Company data APIs
# Financial information
# Patent databases
# Government records
# Market research data
```

### 4. Analysis Engine

#### Machine Learning Pipeline
```python
# Preprocessing
class DataPreprocessor:
    def clean_text(self, text: str) -> str
    def extract_entities(self, text: str) -> List[Entity]
    def normalize_data(self, data: Dict) -> Dict

# Analysis Models
class SentimentAnalyzer:
    def analyze_sentiment(self, text: str) -> SentimentScore
    
class TrendDetector:
    def detect_trends(self, data: TimeSeries) -> List[Trend]
    
class CompetitiveAnalyzer:
    def analyze_competitors(self, data: List[CompanyData]) -> CompetitiveIntelligence
```

#### AI Integration
- **OpenAI API**: Advanced text analysis
- **Custom Models**: Domain-specific analysis
- **Vector Databases**: Semantic search
- **Real-time Processing**: Stream processing

### 5. Data Layer

#### Primary Database (MongoDB)
```javascript
// Data Models
Collections: {
  users: UserDocument,
  organizations: OrganizationDocument,
  data_sources: DataSourceDocument,
  collected_data: CollectedDataDocument,
  reports: ReportDocument,
  alerts: AlertDocument,
  audit_logs: AuditLogDocument
}

// Indexes for performance
Indexes: {
  users: ['email', 'organization_id'],
  collected_data: ['source_id', 'created_at', 'processed_at'],
  reports: ['user_id', 'created_at'],
  alerts: ['user_id', 'active', 'triggered_at']
}
```

#### Cache Layer (Redis)
```python
# Caching Strategy
CachePatterns = {
    'user_sessions': 'session:{user_id}',
    'api_responses': 'api:{endpoint}:{params_hash}',
    'analysis_results': 'analysis:{data_id}',
    'rate_limits': 'rate_limit:{user_id}:{endpoint}'
}

# TTL Configuration
TTL = {
    'sessions': 86400,  # 24 hours
    'api_responses': 3600,  # 1 hour
    'analysis_results': 604800,  # 7 days
    'rate_limits': 3600  # 1 hour
}
```

#### Time Series Database (InfluxDB)
```sql
-- Metrics and Performance Data
MEASUREMENTS:
  api_requests,
  collection_jobs,
  analysis_performance,
  user_activity,
  system_metrics

-- Retention Policies
RETENTION POLICIES:
  realtime: 24h,
  daily: 30d,
  weekly: 1y,
  monthly: 5y
```

## Security Architecture

### Authentication & Authorization

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   User Login    │───▶│   JWT Token     │───▶│   API Access    │
│                 │    │   Generation    │    │   with RBAC     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │   Token Store   │
                       │   (Redis)       │
                       └─────────────────┘
```

### Data Protection

1. **Encryption**
   - TLS 1.3 for data in transit
   - AES-256 for data at rest
   - Field-level encryption for sensitive data

2. **Access Control**
   - Role-based permissions
   - Resource-level authorization
   - API rate limiting
   - IP whitelisting

3. **Audit & Compliance**
   - Comprehensive audit logging
   - GDPR compliance features
   - SOC 2 ready architecture
   - Data retention policies

## Scalability & Performance

### Horizontal Scaling

```yaml
# Kubernetes Deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: osint-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: osint-api
  template:
    spec:
      containers:
      - name: api
        image: osint-platform/api:latest
        resources:
          requests:
            cpu: 100m
            memory: 256Mi
          limits:
            cpu: 500m
            memory: 512Mi
```

### Database Scaling

```javascript
// MongoDB Sharding Strategy
ShardingKey: {
  collected_data: { organization_id: 1, created_at: 1 },
  reports: { organization_id: 1 },
  users: { organization_id: 1 }
}

// Read Replicas
ReadPreference: {
  analytics: 'secondary',
  reports: 'secondaryPreferred',
  real_time: 'primary'
}
```

### Caching Strategy

```python
# Multi-level Caching
CacheLevels = {
    'L1': 'Application Cache (In-Memory)',
    'L2': 'Redis Cache (Distributed)',
    'L3': 'CDN Cache (Global)'
}

# Cache Invalidation
InvalidationStrategies = {
    'time_based': 'TTL expiration',
    'event_based': 'Cache tags and events',
    'dependency_based': 'Cache dependencies'
}
```

## Monitoring & Observability

### Application Monitoring

```python
# Metrics Collection
Metrics = {
    'api_requests': Counter('api_requests_total'),
    'response_time': Histogram('api_response_time_seconds'),
    'active_users': Gauge('active_users_total'),
    'collection_jobs': Gauge('collection_jobs_running')
}

# Health Checks
HealthChecks = {
    'database': check_database_connection,
    'cache': check_redis_connection,
    'external_apis': check_external_services,
    'disk_space': check_disk_usage
}
```

### Logging Architecture

```json
{
  "timestamp": "2025-07-02T10:30:00Z",
  "level": "INFO",
  "service": "api",
  "request_id": "req_123456",
  "user_id": "user_789",
  "endpoint": "/api/v1/data/collect",
  "method": "POST",
  "status_code": 200,
  "response_time": 0.125,
  "message": "Data collection job started"
}
```

## Deployment Architecture

### Production Environment

```yaml
# Docker Compose Overview
services:
  api:
    image: osint-platform/api:latest
    replicas: 3
    
  frontend:
    image: osint-platform/frontend:latest
    replicas: 2
    
  data-pipeline:
    image: osint-platform/pipeline:latest
    
  mongodb:
    image: mongo:6.0
    replicas: 3
    
  redis:
    image: redis:7.0
    replicas: 3
    
  nginx:
    image: nginx:alpine
    replicas: 2
```

### Kubernetes Deployment

```yaml
# Production Kubernetes Configuration
apiVersion: v1
kind: Namespace
metadata:
  name: osint-platform
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: osint-api
  namespace: osint-platform
spec:
  replicas: 5
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 2
      maxUnavailable: 1
```

## Data Flow

### Collection Pipeline

```
1. Data Sources → 2. Collectors → 3. Validation → 4. Storage → 5. Analysis → 6. Reports
     │               │              │              │             │            │
     ▼               ▼              ▼              ▼             ▼            ▼
 Social Media    Scrapy/API     Schema Check    MongoDB     ML Models    Dashboard
 News APIs       Workers        Data Clean      Redis       AI Analysis   Alerts
 Web Content     Airflow DAGs   Duplicate Det   InfluxDB    Trends        Exports
```

### Request Processing

```
User Request → Load Balancer → API Gateway → Authentication → Rate Limiting → 
Business Logic → Database Query → Cache Check → Response Formation → 
Cache Update → Response Delivery
```

## Technology Stack Summary

| Layer | Technology | Purpose |
|-------|------------|----------|
| **Frontend** | React 18, TypeScript, Tailwind CSS | User interface |
| **API** | FastAPI, Python 3.11 | Backend services |
| **Database** | MongoDB, Redis, InfluxDB | Data storage |
| **Pipeline** | Apache Airflow, Celery | Data processing |
| **ML/AI** | scikit-learn, spaCy, OpenAI | Data analysis |
| **Infrastructure** | Docker, Kubernetes, Nginx | Deployment |
| **Monitoring** | Prometheus, Grafana, ELK | Observability |
| **Security** | JWT, OAuth2, TLS 1.3 | Authentication |

---

**Next Sections:**
- [API Architecture](./api.md)
- [Data Pipeline](./data-pipeline.md)
- [Frontend Architecture](./frontend.md)
- [Infrastructure](./infrastructure.md)
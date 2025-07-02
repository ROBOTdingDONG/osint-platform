# OSINT Platform Deployment Guide

This guide covers deploying the OSINT Platform to production environments using Docker, Kubernetes, and cloud platforms.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Environment Setup](#environment-setup)
- [Docker Deployment](#docker-deployment)
- [Kubernetes Deployment](#kubernetes-deployment)
- [Cloud Platform Deployment](#cloud-platform-deployment)
- [Monitoring Setup](#monitoring-setup)
- [Security Configuration](#security-configuration)
- [Backup and Recovery](#backup-and-recovery)
- [Troubleshooting](#troubleshooting)

## Prerequisites

### System Requirements

**Minimum Requirements:**
- CPU: 4 cores
- RAM: 8GB
- Storage: 50GB SSD
- Network: 100Mbps

**Recommended for Production:**
- CPU: 8+ cores
- RAM: 16GB+
- Storage: 200GB+ SSD
- Network: 1Gbps

### Software Dependencies

- Docker 20.10+
- Docker Compose 2.0+
- Kubernetes 1.24+ (for K8s deployment)
- kubectl configured
- Helm 3.0+ (optional)

## Environment Setup

### 1. Clone Repository

```bash
git clone https://github.com/yourusername/osint-platform.git
cd osint-platform
```

### 2. Configure Environment Variables

```bash
# Copy environment template
cp .env.example .env

# Edit configuration
vim .env
```

**Critical Environment Variables:**

```bash
# Application
ENVIRONMENT=production
DEBUG=false
API_URL=https://api.yourdomain.com
FRONTEND_URL=https://yourdomain.com

# Security
JWT_SECRET=your-super-secure-jwt-secret-key
ENCRYPTION_KEY=your-32-character-encryption-key

# Database
MONGODB_URL=mongodb://username:password@mongodb:27017/osint_platform
REDIS_URL=redis://redis:6379/0

# API Keys
OPENAI_API_KEY=your-openai-api-key
TWITTER_API_KEY=your-twitter-api-key
NEWS_API_KEY=your-news-api-key

# Email
SMTP_HOST=smtp.yourdomain.com
SMTP_USERNAME=noreply@yourdomain.com
SMTP_PASSWORD=your-smtp-password
```

## Docker Deployment

### Production Docker Compose

```bash
# Create production override
cp docker-compose.yml docker-compose.prod.yml
```

**docker-compose.prod.yml:**

```yaml
version: '3.8'

services:
  # Use production builds
  api:
    build:
      context: ./backend
      target: production
    restart: unless-stopped
    environment:
      - ENVIRONMENT=production
    deploy:
      replicas: 3
      resources:
        limits:
          memory: 512M
          cpus: '0.5'

  frontend:
    build:
      context: ./frontend
      target: production
    restart: unless-stopped
    deploy:
      replicas: 2
      resources:
        limits:
          memory: 128M
          cpus: '0.2'

  # Production database with persistence
  mongodb:
    image: mongo:6.0
    restart: unless-stopped
    environment:
      MONGO_INITDB_ROOT_USERNAME: ${MONGODB_USERNAME}
      MONGO_INITDB_ROOT_PASSWORD: ${MONGODB_PASSWORD}
    volumes:
      - mongodb_data:/data/db
      - ./backups:/backups
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '1.0'

  # Redis with persistence
  redis:
    image: redis:7.0-alpine
    restart: unless-stopped
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data

  # Nginx reverse proxy
  nginx:
    image: nginx:alpine
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./infrastructure/nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./infrastructure/nginx/ssl:/etc/nginx/ssl
    depends_on:
      - frontend
      - api

volumes:
  mongodb_data:
  redis_data:
```

### Deploy with Docker

```bash
# Build and start services
docker-compose -f docker-compose.prod.yml up -d

# View logs
docker-compose -f docker-compose.prod.yml logs -f

# Scale services
docker-compose -f docker-compose.prod.yml up -d --scale api=3 --scale frontend=2
```

## Kubernetes Deployment

### 1. Create Namespace

```bash
kubectl apply -f infrastructure/kubernetes/namespace.yaml
```

### 2. Create Secrets

```bash
# Create MongoDB secret
kubectl create secret generic mongodb-secret \
  --from-literal=username=admin \
  --from-literal=password=your-secure-password \
  -n osint-platform

# Create application secrets
kubectl create secret generic app-secrets \
  --from-literal=mongodb-url="mongodb://admin:password@mongodb-service:27017/osint_platform" \
  --from-literal=redis-url="redis://redis-service:6379/0" \
  --from-literal=jwt-secret="your-jwt-secret" \
  --from-literal=openai-api-key="your-openai-key" \
  -n osint-platform
```

### 3. Deploy Infrastructure

```bash
# Deploy MongoDB
kubectl apply -f infrastructure/kubernetes/mongodb-deployment.yaml

# Deploy Redis
kubectl apply -f infrastructure/kubernetes/redis-deployment.yaml

# Wait for databases to be ready
kubectl wait --for=condition=ready pod -l app=mongodb -n osint-platform --timeout=300s
kubectl wait --for=condition=ready pod -l app=redis -n osint-platform --timeout=300s
```

### 4. Deploy Applications

```bash
# Build and push images
docker build -t your-registry/osint-backend:latest ./backend
docker build -t your-registry/osint-frontend:latest ./frontend
docker push your-registry/osint-backend:latest
docker push your-registry/osint-frontend:latest

# Update image references in deployment files
sed -i 's|osint-platform/backend:latest|your-registry/osint-backend:latest|' infrastructure/kubernetes/backend-deployment.yaml
sed -i 's|osint-platform/frontend:latest|your-registry/osint-frontend:latest|' infrastructure/kubernetes/frontend-deployment.yaml

# Deploy applications
kubectl apply -f infrastructure/kubernetes/backend-deployment.yaml
kubectl apply -f infrastructure/kubernetes/frontend-deployment.yaml

# Deploy ingress
kubectl apply -f infrastructure/kubernetes/ingress.yaml
```

### 5. Verify Deployment

```bash
# Check pod status
kubectl get pods -n osint-platform

# Check services
kubectl get services -n osint-platform

# Check ingress
kubectl get ingress -n osint-platform

# View logs
kubectl logs -f deployment/backend -n osint-platform
```

## Cloud Platform Deployment

### AWS EKS

```bash
# Create EKS cluster
eksctl create cluster --name osint-platform --region us-west-2 --nodes 3

# Configure kubectl
aws eks update-kubeconfig --region us-west-2 --name osint-platform

# Install AWS Load Balancer Controller
kubectl apply -f https://github.com/kubernetes-sigs/aws-load-balancer-controller/releases/download/v2.4.4/aws-load-balancer-controller.yaml
```

### Google GKE

```bash
# Create GKE cluster
gcloud container clusters create osint-platform \
  --zone us-central1-a \
  --num-nodes 3 \
  --enable-autoscaling \
  --min-nodes 1 \
  --max-nodes 10

# Get credentials
gcloud container clusters get-credentials osint-platform --zone us-central1-a
```

### Azure AKS

```bash
# Create resource group
az group create --name osint-platform --location eastus

# Create AKS cluster
az aks create \
  --resource-group osint-platform \
  --name osint-platform \
  --node-count 3 \
  --enable-addons monitoring \
  --generate-ssh-keys

# Get credentials
az aks get-credentials --resource-group osint-platform --name osint-platform
```

## Monitoring Setup

### Prometheus and Grafana

```bash
# Install Prometheus Operator
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm install prometheus prometheus-community/kube-prometheus-stack -n monitoring --create-namespace

# Apply custom configuration
kubectl apply -f infrastructure/monitoring/prometheus-config.yaml

# Access Grafana
kubectl port-forward svc/prometheus-grafana 3000:80 -n monitoring
```

### Application Metrics

Add to your backend application:

```python
from prometheus_client import Counter, Histogram, generate_latest

# Metrics
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
REQUEST_DURATION = Histogram('http_request_duration_seconds', 'HTTP request duration')

@app.middleware("http")
async def metrics_middleware(request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()
    
    REQUEST_DURATION.observe(duration)
    return response

@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type="text/plain")
```

## Security Configuration

### SSL/TLS Setup

```bash
# Install cert-manager
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.10.0/cert-manager.yaml

# Create ClusterIssuer
kubectl apply -f - <<EOF
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: admin@yourdomain.com
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
    - http01:
        ingress:
          class: nginx
EOF
```

### Network Policies

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: osint-platform-netpol
  namespace: osint-platform
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: osint-platform
  egress:
  - to: []
    ports:
    - protocol: TCP
      port: 53
    - protocol: UDP
      port: 53
  - to:
    - namespaceSelector:
        matchLabels:
          name: osint-platform
```

## Backup and Recovery

### Database Backup

```bash
# Create backup script
cat > backup.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups"
MONGO_HOST="mongodb-service"
MONGO_DB="osint_platform"

# Create backup
mongodump --host $MONGO_HOST --db $MONGO_DB --out $BACKUP_DIR/mongo_$DATE

# Compress backup
tar -czf $BACKUP_DIR/mongo_$DATE.tar.gz -C $BACKUP_DIR mongo_$DATE
rm -rf $BACKUP_DIR/mongo_$DATE

# Keep only last 7 days
find $BACKUP_DIR -name "mongo_*.tar.gz" -mtime +7 -delete
EOF

chmod +x backup.sh
```

### Automated Backups with CronJob

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: mongodb-backup
  namespace: osint-platform
spec:
  schedule: "0 2 * * *"  # Daily at 2 AM
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: mongodb-backup
            image: mongo:6.0
            command:
            - /bin/bash
            - -c
            - |
              DATE=$(date +%Y%m%d_%H%M%S)
              mongodump --host mongodb-service --db osint_platform --out /backup/mongo_$DATE
              tar -czf /backup/mongo_$DATE.tar.gz -C /backup mongo_$DATE
              rm -rf /backup/mongo_$DATE
            volumeMounts:
            - name: backup-storage
              mountPath: /backup
          volumes:
          - name: backup-storage
            persistentVolumeClaim:
              claimName: backup-pvc
          restartPolicy: OnFailure
```

## Troubleshooting

### Common Issues

**1. Database Connection Issues**

```bash
# Check MongoDB status
kubectl logs deployment/mongodb -n osint-platform

# Test connection
kubectl run -it --rm debug --image=mongo:6.0 --restart=Never -- mongo mongodb-service:27017
```

**2. Application Not Starting**

```bash
# Check pod status
kubectl describe pod <pod-name> -n osint-platform

# Check logs
kubectl logs <pod-name> -n osint-platform

# Check events
kubectl get events -n osint-platform --sort-by='.metadata.creationTimestamp'
```

**3. SSL Certificate Issues**

```bash
# Check certificate status
kubectl describe certificate osint-platform-tls -n osint-platform

# Check cert-manager logs
kubectl logs -n cert-manager deployment/cert-manager
```

### Performance Tuning

**Backend Scaling:**

```bash
# Scale backend pods
kubectl scale deployment backend --replicas=5 -n osint-platform

# Enable horizontal pod autoscaler
kubectl autoscale deployment backend --cpu-percent=70 --min=3 --max=10 -n osint-platform
```

**Database Optimization:**

```javascript
// MongoDB indexes for better performance
db.collected_data.createIndex({ "collection_timestamp": -1 })
db.collected_data.createIndex({ "metadata.source": 1, "collection_timestamp": -1 })
db.collected_data.createIndex({ "content_hash": 1 }, { unique: true })
```

### Health Checks

```bash
# API health check
curl https://api.yourdomain.com/health

# Database health check
kubectl exec -it deployment/mongodb -n osint-platform -- mongo --eval "db.adminCommand('ping')"

# Redis health check
kubectl exec -it deployment/redis -n osint-platform -- redis-cli ping
```

## Support

For deployment support:
- Email: ops@osintplatform.com
- Documentation: https://docs.osintplatform.com
- Issues: https://github.com/yourusername/osint-platform/issues

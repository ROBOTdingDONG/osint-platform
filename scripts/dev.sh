#!/bin/bash

# ===============================================================================
# OSINT Platform Development Script
# Starts all development services locally
# ===============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if port is in use
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null ; then
        return 0
    else
        return 1
    fi
}

# Function to wait for service
wait_for_service() {
    local service_name=$1
    local port=$2
    local max_attempts=30
    local attempt=1
    
    log_info "Waiting for $service_name to be ready..."
    
    while [ $attempt -le $max_attempts ]; do
        if check_port $port; then
            log_success "$service_name is ready on port $port"
            return 0
        fi
        
        echo -n "."
        sleep 2
        attempt=$((attempt + 1))
    done
    
    echo
    log_error "$service_name failed to start on port $port after $max_attempts attempts"
    return 1
}

# Function to start MongoDB
start_mongodb() {
    log_info "Starting MongoDB..."
    
    if check_port 27017; then
        log_info "MongoDB is already running on port 27017"
    else
        # Try to start MongoDB with Docker
        if command -v docker >/dev/null 2>&1; then
            docker run -d \
                --name osint-mongodb-dev \
                -p 27017:27017 \
                -e MONGO_INITDB_ROOT_USERNAME=admin \
                -e MONGO_INITDB_ROOT_PASSWORD=password \
                -e MONGO_INITDB_DATABASE=osint_platform \
                mongo:6.0 >/dev/null 2>&1 || true
            
            wait_for_service "MongoDB" 27017
        else
            log_error "MongoDB not running and Docker not available. Please start MongoDB manually."
            return 1
        fi
    fi
}

# Function to start Redis
start_redis() {
    log_info "Starting Redis..."
    
    if check_port 6379; then
        log_info "Redis is already running on port 6379"
    else
        # Try to start Redis with Docker
        if command -v docker >/dev/null 2>&1; then
            docker run -d \
                --name osint-redis-dev \
                -p 6379:6379 \
                redis:7.0-alpine >/dev/null 2>&1 || true
            
            wait_for_service "Redis" 6379
        else
            log_error "Redis not running and Docker not available. Please start Redis manually."
            return 1
        fi
    fi
}

# Function to start backend
start_backend() {
    log_info "Starting backend server..."
    
    cd backend
    
    # Activate virtual environment
    if [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
    else
        log_error "Virtual environment not found. Run ./scripts/setup.sh first."
        return 1
    fi
    
    # Start the backend server in background
    uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
    BACKEND_PID=$!
    
    cd ..
    
    # Wait for backend to be ready
    wait_for_service "Backend API" 8000
    
    echo $BACKEND_PID > .backend.pid
}

# Function to start frontend
start_frontend() {
    log_info "Starting frontend development server..."
    
    cd frontend
    
    # Check if node_modules exists
    if [ ! -d "node_modules" ]; then
        log_error "Node modules not found. Run ./scripts/setup.sh first."
        return 1
    fi
    
    # Start the frontend server in background
    npm start &
    FRONTEND_PID=$!
    
    cd ..
    
    # Wait for frontend to be ready
    wait_for_service "Frontend" 3000
    
    echo $FRONTEND_PID > .frontend.pid
}

# Function to cleanup on exit
cleanup() {
    log_info "Shutting down development servers..."
    
    # Kill backend
    if [ -f ".backend.pid" ]; then
        BACKEND_PID=$(cat .backend.pid)
        kill $BACKEND_PID 2>/dev/null || true
        rm .backend.pid
    fi
    
    # Kill frontend
    if [ -f ".frontend.pid" ]; then
        FRONTEND_PID=$(cat .frontend.pid)
        kill $FRONTEND_PID 2>/dev/null || true
        rm .frontend.pid
    fi
    
    log_success "Development servers stopped"
}

# Function to show status
show_status() {
    echo
    log_success "OSINT Platform Development Environment"
    echo "========================================"
    echo
    echo "Services:"
    
    if check_port 27017; then
        echo "  ✅ MongoDB      : http://localhost:27017"
    else
        echo "  ❌ MongoDB      : Not running"
    fi
    
    if check_port 6379; then
        echo "  ✅ Redis        : http://localhost:6379"
    else
        echo "  ❌ Redis        : Not running"
    fi
    
    if check_port 8000; then
        echo "  ✅ Backend API  : http://localhost:8000"
        echo "  📚 API Docs     : http://localhost:8000/docs"
    else
        echo "  ❌ Backend API  : Not running"
    fi
    
    if check_port 3000; then
        echo "  ✅ Frontend     : http://localhost:3000"
    else
        echo "  ❌ Frontend     : Not running"
    fi
    
    echo
    echo "Controls:"
    echo "  Ctrl+C to stop all services"
    echo "  View logs in separate terminals:"
    echo "    Backend : tail -f backend/logs/osint_platform.log"
    echo "    Frontend: Check the terminal where this script was run"
    echo
}

# Main function
main() {
    log_info "Starting OSINT Platform development environment..."
    
    # Set up cleanup trap
    trap cleanup EXIT INT TERM
    
    # Start services
    start_mongodb
    start_redis
    start_backend
    start_frontend
    
    # Show status
    show_status
    
    # Wait for user to stop
    log_info "All services started successfully!"
    log_info "Press Ctrl+C to stop all services"
    
    # Keep script running
    while true; do
        sleep 1
    done
}

# Check arguments
case "${1:-}" in
    "status")
        show_status
        exit 0
        ;;
    "stop")
        cleanup
        exit 0
        ;;
    "help")
        echo "Usage: $0 [status|stop|help]"
        echo "  status : Show service status"
        echo "  stop   : Stop all services"
        echo "  help   : Show this help"
        exit 0
        ;;
esac

# Run main function
main "$@"

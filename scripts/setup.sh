#!/bin/bash

# ===============================================================================
# OSINT Platform Setup Script
# Initializes the development environment and dependencies
# ===============================================================================

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
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

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check Python version
check_python_version() {
    if command_exists python3; then
        PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
        REQUIRED_VERSION="3.11"
        
        if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" = "$REQUIRED_VERSION" ]; then
            log_success "Python $PYTHON_VERSION found"
            return 0
        else
            log_error "Python $REQUIRED_VERSION or higher required, found $PYTHON_VERSION"
            return 1
        fi
    else
        log_error "Python 3 not found"
        return 1
    fi
}

# Function to check Node.js version
check_node_version() {
    if command_exists node; then
        NODE_VERSION=$(node -v | sed 's/v//')
        REQUIRED_VERSION="18.0.0"
        
        if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$NODE_VERSION" | sort -V | head -n1)" = "$REQUIRED_VERSION" ]; then
            log_success "Node.js $NODE_VERSION found"
            return 0
        else
            log_error "Node.js $REQUIRED_VERSION or higher required, found $NODE_VERSION"
            return 1
        fi
    else
        log_error "Node.js not found"
        return 1
    fi
}

# Function to setup backend
setup_backend() {
    log_info "Setting up backend..."
    
    cd backend
    
    # Create virtual environment
    if [ ! -d "venv" ]; then
        log_info "Creating Python virtual environment..."
        python3 -m venv venv
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Upgrade pip
    log_info "Upgrading pip..."
    pip install --upgrade pip
    
    # Install dependencies
    log_info "Installing backend dependencies..."
    pip install -r requirements.txt
    
    # Install development dependencies
    if [ -f "requirements-dev.txt" ]; then
        log_info "Installing development dependencies..."
        pip install -r requirements-dev.txt
    fi
    
    # Create logs directory
    mkdir -p logs
    
    cd ..
    log_success "Backend setup completed"
}

# Function to setup frontend
setup_frontend() {
    log_info "Setting up frontend..."
    
    cd frontend
    
    # Install dependencies
    log_info "Installing frontend dependencies..."
    npm install
    
    cd ..
    log_success "Frontend setup completed"
}

# Function to setup data pipeline
setup_data_pipeline() {
    log_info "Setting up data pipeline..."
    
    cd data-pipeline
    
    # Create virtual environment
    if [ ! -d "venv" ]; then
        log_info "Creating Python virtual environment for data pipeline..."
        python3 -m venv venv
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Install dependencies
    if [ -f "requirements.txt" ]; then
        log_info "Installing data pipeline dependencies..."
        pip install -r requirements.txt
    fi
    
    cd ..
    log_success "Data pipeline setup completed"
}

# Function to setup environment files
setup_environment() {
    log_info "Setting up environment files..."
    
    # Copy environment template if .env doesn't exist
    if [ ! -f ".env" ]; then
        if [ -f ".env.example" ]; then
            cp .env.example .env
            log_success "Created .env file from template"
            log_warning "Please update .env file with your actual configuration values"
        else
            log_warning ".env.example not found"
        fi
    else
        log_info ".env file already exists"
    fi
    
    # Setup backend environment
    if [ ! -f "backend/.env" ]; then
        if [ -f "backend/.env.example" ]; then
            cp backend/.env.example backend/.env
            log_success "Created backend/.env file from template"
        fi
    fi
    
    # Setup frontend environment
    if [ ! -f "frontend/.env" ]; then
        if [ -f "frontend/.env.example" ]; then
            cp frontend/.env.example frontend/.env
            log_success "Created frontend/.env file from template"
        fi
    fi
}

# Function to check Docker
check_docker() {
    if command_exists docker; then
        log_success "Docker found"
        if command_exists docker-compose; then
            log_success "Docker Compose found"
        else
            log_warning "Docker Compose not found. Install it for easy development setup."
        fi
    else
        log_warning "Docker not found. Install Docker for containerized development."
    fi
}

# Function to create necessary directories
setup_directories() {
    log_info "Creating necessary directories..."
    
    # Create main directories
    mkdir -p backend/{app/{api/{v1/{endpoints,deps}},core,db/{models,repositories},services,utils},tests,logs,scripts}
    mkdir -p frontend/{src/{components,pages,hooks,utils,services,contexts},public,tests}
    mkdir -p data-pipeline/{collectors/{social_media,news,companies},processors,schedulers/dags,tests}
    mkdir -p infrastructure/{kubernetes,terraform,docker,monitoring}
    mkdir -p docs/{api,deployment,development}
    mkdir -p scripts
    
    log_success "Directory structure created"
}

# Function to setup Git hooks
setup_git_hooks() {
    if [ -d ".git" ]; then
        log_info "Setting up Git hooks..."
        
        # Create pre-commit hook
        cat > .git/hooks/pre-commit << 'EOF'
#!/bin/bash
# Run linting and tests before commit

echo "Running pre-commit checks..."

# Check if we're in the backend directory and run Python checks
if [ -f "backend/requirements.txt" ]; then
    echo "Running backend checks..."
    cd backend
    source venv/bin/activate 2>/dev/null || true
    
    # Run flake8 if available
    if command -v flake8 >/dev/null 2>&1; then
        echo "Running flake8..."
        flake8 app --max-line-length=100 --exclude=venv
    fi
    
    cd ..
fi

# Check if we're in the frontend directory and run Node checks
if [ -f "frontend/package.json" ]; then
    echo "Running frontend checks..."
    cd frontend
    
    # Run ESLint if available
    if [ -f "node_modules/.bin/eslint" ]; then
        echo "Running ESLint..."
        npm run lint
    fi
    
    cd ..
fi

echo "Pre-commit checks completed!"
EOF
        
        chmod +x .git/hooks/pre-commit
        log_success "Git pre-commit hook installed"
    else
        log_info "Not a Git repository, skipping Git hooks setup"
    fi
}

# Main setup function
main() {
    log_info "Starting OSINT Platform setup..."
    echo
    
    # Check prerequisites
    log_info "Checking prerequisites..."
    
    if ! check_python_version; then
        log_error "Python 3.11+ is required. Please install it and try again."
        exit 1
    fi
    
    if ! check_node_version; then
        log_error "Node.js 18+ is required. Please install it and try again."
        exit 1
    fi
    
    check_docker
    echo
    
    # Setup components
    setup_directories
    setup_environment
    setup_backend
    setup_frontend
    setup_data_pipeline
    setup_git_hooks
    
    echo
    log_success "OSINT Platform setup completed successfully!"
    echo
    log_info "Next steps:"
    echo "  1. Update .env files with your configuration"
    echo "  2. Start the development environment:"
    echo "     docker-compose up -d    # Or"
    echo "     ./scripts/dev.sh        # For local development"
    echo "  3. Access the application:"
    echo "     Frontend: http://localhost:3000"
    echo "     Backend API: http://localhost:8000"
    echo "     API Docs: http://localhost:8000/docs"
    echo
}

# Run main function
main "$@"

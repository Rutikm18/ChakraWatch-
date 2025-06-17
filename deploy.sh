#!/bin/bash
# ChakraWatch Docker Setup and Git Push Script
# Only creates missing Docker files and pushes to repository

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_header() {
    echo -e "${PURPLE}🛡️  $1${NC}"
}

print_header "ChakraWatch Docker Setup & Git Push Script"
echo "============================================="

# Check if we're in the right directory
if [[ ! -f "app.py" ]] || [[ ! -f "requirements.txt" ]]; then
    print_error "This doesn't appear to be a ChakraWatch directory!"
    print_info "Expected files: app.py, requirements.txt"
    print_info "Current directory: $(pwd)"
    exit 1
fi

print_status "Found existing ChakraWatch files"

# Ask for git repository (optional)
echo
read -p "Enter Git repository URL (optional, press Enter to skip): " GIT_REMOTE
if [[ -n "$GIT_REMOTE" ]]; then
    read -p "Enter branch name (default: main): " input_branch
    GIT_BRANCH=${input_branch:-main}
fi

print_info "Checking existing files..."

# Check what files already exist
EXISTING_FILES=()
if [[ -f "app.py" ]]; then EXISTING_FILES+=("app.py"); fi
if [[ -f "requirements.txt" ]]; then EXISTING_FILES+=("requirements.txt"); fi
if [[ -f "deploy.sh" ]]; then EXISTING_FILES+=("deploy.sh"); fi
if [[ -f "README.md" ]]; then EXISTING_FILES+=("README.md"); fi
if [[ -f "frontend/index.html" ]]; then EXISTING_FILES+=("frontend/index.html"); fi
if [[ -f "frontend/style.css" ]]; then EXISTING_FILES+=("frontend/style.css"); fi
if [[ -f "frontend/script.js" ]]; then EXISTING_FILES+=("frontend/script.js"); fi

print_info "Existing files (will be preserved):"
for file in "${EXISTING_FILES[@]}"; do
    echo "   ✅ $file"
done

# Create only missing Docker files
echo
print_info "Creating missing Docker configuration files..."

# Create .dockerignore if missing
if [[ ! -f ".dockerignore" ]]; then
    print_info "Creating .dockerignore..."
    cat > .dockerignore << 'EOF'
# Git
.git
.gitignore
.gitattributes

# Documentation
LICENSE
*.md

# Python
__pycache__
*.pyc
*.pyo
*.pyd
.Python
build
*.egg-info
.pytest_cache
.coverage

# Virtual environments
venv/
env/
.venv/
.env/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Local data (will be mounted as volumes)
data/
logs/
*.db
*.sqlite
*.sqlite3

# Development files
debug.py
run.py
test_*.py
tests/

# Screenshots and media
screenshots/
*.png
*.jpg
*.gif
*.mp4

# Temporary files
*.tmp
*.log
.cache/
EOF
    print_status ".dockerignore created"
else
    print_warning ".dockerignore already exists (preserved)"
fi

# Create Dockerfile if missing
if [[ ! -f "Dockerfile" ]]; then
    print_info "Creating Dockerfile..."
    cat > Dockerfile << 'EOF'
# ChakraWatch Docker Image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        curl \
        gcc \
    && rm -rf /var/lib/apt/lists/*

# Create directories
RUN mkdir -p /app/data /app/logs /app/frontend

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY app.py .
COPY frontend/ ./frontend/

# Create non-root user for security
RUN adduser --disabled-password --gecos '' --uid 1000 appuser \
    && chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start command
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
EOF
    print_status "Dockerfile created"
else
    print_warning "Dockerfile already exists (preserved)"
fi

# Create docker-compose.yml if missing
if [[ ! -f "docker-compose.yml" ]]; then
    print_info "Creating docker-compose.yml..."
    cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  chakrawatch:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: chakrawatch-app
    ports:
      - "8000:8000"
    volumes:
      # Persist database and logs
      - ./data:/app/data
      - ./logs:/app/logs
      # Optional: Mount frontend for development
      - ./frontend:/app/frontend:ro
    environment:
      - DATABASE_URL=sqlite:///./data/chakrawatch.db
      - DEBUG=false
      - MAX_ARTICLES_PER_SOURCE=20
      - REQUEST_TIMEOUT=30
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 30s
    networks:
      - chakrawatch-network

  # Optional: Add PostgreSQL for production
  # postgres:
  #   image: postgres:15-alpine
  #   container_name: chakrawatch-db
  #   environment:
  #     POSTGRES_DB: chakrawatch
  #     POSTGRES_USER: chakrawatch
  #     POSTGRES_PASSWORD: your_secure_password
  #   volumes:
  #     - postgres_data:/var/lib/postgresql/data
  #   networks:
  #     - chakrawatch-network

  # Optional: Add Redis for caching
  # redis:
  #   image: redis:7-alpine
  #   container_name: chakrawatch-cache
  #   networks:
  #     - chakrawatch-network

volumes:
  # Uncomment if using PostgreSQL
  # postgres_data:

networks:
  chakrawatch-network:
    driver: bridge
EOF
    print_status "docker-compose.yml created"
else
    print_warning "docker-compose.yml already exists (preserved)"
fi

# Create .env.example if missing
if [[ ! -f ".env.example" ]]; then
    print_info "Creating .env.example..."
    cat > .env.example << 'EOF'
# ChakraWatch Environment Configuration

# Database
DATABASE_URL=sqlite:///./data/chakrawatch.db
# DATABASE_URL=postgresql://user:password@postgres:5432/chakrawatch

# Application Settings
DEBUG=false
MAX_ARTICLES_PER_SOURCE=20
REQUEST_TIMEOUT=30

# Server Configuration
HOST=0.0.0.0
PORT=8000

# Security (generate your own secret key)
SECRET_KEY=your-super-secret-key-here

# Optional: Redis Cache
# REDIS_URL=redis://redis:6379/0

# Optional: External API Keys
# VIRUSTOTAL_API_KEY=your_api_key
# SHODAN_API_KEY=your_api_key
EOF
    print_status ".env.example created"
else
    print_warning ".env.example already exists (preserved)"
fi

# Create .gitignore if missing
if [[ ! -f ".gitignore" ]]; then
    print_info "Creating .gitignore..."
    cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
share/python-wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# Virtual environments
.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/

# ChakraWatch specific
data/
logs/
*.db
*.sqlite
*.sqlite3

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Logs
*.log

# Docker
docker-compose.override.yml

# Secrets
.env
*.pem
*.key
EOF
    print_status ".gitignore created"
else
    print_warning ".gitignore already exists (preserved)"
fi

# Update README.md with Docker information if it exists
if [[ -f "README.md" ]]; then
    print_info "README.md exists - would you like to update it with Docker deployment info?"
    read -p "Update README.md? (y/n): " update_readme
    
    if [[ "$update_readme" =~ ^[Yy]$ ]]; then
        # Backup existing README
        cp README.md README.md.backup
        print_info "Backed up existing README.md to README.md.backup"
        
        # Update README with Docker section
        cat >> README.md << 'EOF'

## 🐳 Docker Deployment

### Prerequisites
- Docker installed
- Docker Compose installed

### Quick Deploy
```bash
# Make deployment script executable (if not already)
chmod +x deploy.sh

# Start ChakraWatch
./deploy.sh

# View logs
./deploy.sh logs

# Check status  
./deploy.sh status

# Stop
./deploy.sh stop
```

### Docker Commands
```bash
# Build and start
docker-compose up -d

# View logs
docker-compose logs -f chakrawatch

# Stop and remove
docker-compose down

# Rebuild image
docker-compose build --no-cache
```

### Environment Variables
Create a `.env` file based on `.env.example`:
```bash
cp .env.example .env
# Edit .env with your settings
```

### Production Deployment
For production, edit `docker-compose.yml` to:
- Uncomment PostgreSQL service
- Set strong passwords
- Configure SSL/TLS
- Set DEBUG=false
EOF
        print_status "README.md updated with Docker deployment information"
    else
        print_info "README.md preserved unchanged"
    fi
fi

# Make deploy.sh executable if it exists
if [[ -f "deploy.sh" ]]; then
    chmod +x deploy.sh
    print_status "deploy.sh made executable"
fi

# Check if git is initialized
print_info "Checking Git repository status..."

if [[ ! -d ".git" ]]; then
    print_info "Initializing Git repository..."
    git init
    print_status "Git repository initialized"
else
    print_status "Git repository already exists"
fi

# Add all files to git
print_info "Adding files to Git..."
git add .

# Check if there are changes to commit
if git diff --staged --quiet; then
    print_warning "No changes to commit"
else
    # Commit changes
    print_info "Committing changes..."
    git commit -m "Add Docker deployment configuration for ChakraWatch

- Add Dockerfile for containerized deployment
- Add docker-compose.yml for service orchestration
- Add .dockerignore for optimized builds
- Add .env.example for configuration template
- Add .gitignore for version control
- Update documentation with Docker deployment instructions

ChakraWatch is now ready for Docker deployment with:
- Professional cybersecurity threat intelligence platform
- Real-time monitoring from multiple sources
- AI-powered threat analysis and IOC extraction
- Professional UI with royal blue theme
- Production-ready Docker configuration"

    print_status "Changes committed to Git"
fi

# Push to remote repository if provided
if [[ -n "$GIT_REMOTE" ]]; then
    print_info "Setting up remote repository..."
    
    # Check if remote already exists
    if git remote | grep -q "origin"; then
        git remote set-url origin "$GIT_REMOTE"
        print_info "Updated existing remote origin"
    else
        git remote add origin "$GIT_REMOTE"
        print_info "Added remote origin: $GIT_REMOTE"
    fi
    
    # Push to remote
    print_info "Pushing to remote repository..."
    if git push -u origin "$GIT_BRANCH" 2>/dev/null; then
        print_status "Successfully pushed to $GIT_REMOTE (branch: $GIT_BRANCH)"
    else
        print_warning "Failed to push to remote. Trying force push..."
        if git push -u origin "$GIT_BRANCH" --force; then
            print_status "Force push successful"
        else
            print_error "Failed to push to remote repository"
            print_info "You may need to manually push: git push -u origin $GIT_BRANCH"
        fi
    fi
fi

# Show final status
echo
print_header "Setup Complete!"
echo "================"

print_info "Files created/updated:"
if [[ ! -f ".dockerignore.bak" ]]; then echo "   ✅ .dockerignore"; fi
if [[ ! -f "Dockerfile.bak" ]]; then echo "   ✅ Dockerfile"; fi
if [[ ! -f "docker-compose.yml.bak" ]]; then echo "   ✅ docker-compose.yml"; fi
if [[ ! -f ".env.example.bak" ]]; then echo "   ✅ .env.example"; fi
if [[ ! -f ".gitignore.bak" ]]; then echo "   ✅ .gitignore"; fi

print_info "Preserved existing files:"
for file in "${EXISTING_FILES[@]}"; do
    echo "   ✅ $file"
done

echo
print_info "Next steps:"
echo "   1. Test Docker deployment:"
echo "      ./deploy.sh"
echo ""
echo "   2. Access ChakraWatch:"
echo "      http://localhost:8000"
echo ""
echo "   3. View logs:"
echo "      ./deploy.sh logs"
echo ""
echo "   4. Check API documentation:"
echo "      http://localhost:8000/docs"

if [[ -n "$GIT_REMOTE" ]]; then
    echo ""
    print_status "Repository: $GIT_REMOTE"
    print_status "Branch: $GIT_BRANCH"
fi

echo ""
print_header "ChakraWatch is ready for Docker deployment! 🛡️"
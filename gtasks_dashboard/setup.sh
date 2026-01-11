#!/bin/bash

# GTasks Dashboard - Automated Setup Script
# This script will set up the GTasks Dashboard with all dependencies

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="gtasks-dashboard"
PYTHON_ENV_NAME="gtasks-dashboard"
MIN_NODE_VERSION="16"
MIN_PYTHON_VERSION="3.8"

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check version
check_version() {
    local cmd=$1
    local version_arg=$2
    local min_version=$3
    
    if command_exists $cmd; then
        local current_version=$(eval $cmd $version_arg 2>/dev/null | head -n1 | grep -o '[0-9]\+\.[0-9]\+\.[0-9]\+' | head -n1)
        if [[ $(printf '%s\n' "$min_version" "$current_version" | sort -V | head -n1) == "$min_version" ]]; then
            print_success "$cmd version $current_version is compatible"
            return 0
        else
            print_error "$cmd version $current_version is too old. Minimum required: $min_version"
            return 1
        fi
    else
        print_error "$cmd is not installed"
        return 1
    fi
}

# Function to install Node.js via nvm (if needed)
install_nodejs() {
    if ! command_exists node; then
        print_status "Installing Node.js..."
        
        # Install nvm if not present
        if [[ ! -f "$HOME/.nvm/nvm.sh" ]]; then
            curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
        fi
        
        # Load nvm and install Node.js
        export NVM_DIR="$HOME/.nvm"
        [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
        nvm install node
        nvm use node
        nvm alias default node
        
        print_success "Node.js installed successfully"
    fi
}

# Function to install Python and virtual environment
install_python() {
    if ! command_exists python3; then
        print_status "Python 3 is required but not installed"
        print_warning "Please install Python 3.8+ manually and run this script again"
        exit 1
    fi
    
    print_status "Setting up Python virtual environment..."
    
    # Create virtual environment
    python3 -m venv $PYTHON_ENV_NAME
    
    # Activate virtual environment
    source $PYTHON_ENV_NAME/bin/activate
    
    # Upgrade pip
    pip install --upgrade pip
    
    # Install Python dependencies
    if [[ -f "requirements.txt" ]]; then
        pip install -r requirements.txt
        print_success "Python dependencies installed"
    else
        print_warning "requirements.txt not found, skipping Python dependencies"
    fi
}

# Function to install Node.js dependencies
install_nodejs_deps() {
    print_status "Installing Node.js dependencies..."
    
    # Install root dependencies
    npm install
    
    # Install server dependencies
    cd server && npm install && cd ..
    
    print_success "Node.js dependencies installed"
}

# Function to set up environment files
setup_environment() {
    print_status "Setting up environment files..."
    
    # Create .env file if it doesn't exist
    if [[ ! -f ".env" ]]; then
        cat > .env << EOF
# GTasks Dashboard Environment Configuration
NODE_ENV=development
PORT=8080
CLIENT_URL=http://localhost:3000

# GTasks CLI Integration
GTASKS_CLI_PATH=../gtasks_cli

# Database Configuration
DATABASE_PATH=./data/dashboard.db

# JWT Configuration
JWT_SECRET=your-super-secret-jwt-key-change-this-in-production

# Rate Limiting
RATE_LIMIT_WINDOW_MS=900000
RATE_LIMIT_MAX_REQUESTS=100

# Sync Configuration
SYNC_INTERVAL=30000
AUTO_SYNC=true

# MCP Configuration
MCP_ENABLED=true
MCP_PORT=3001

# Notification Settings
NOTIFICATIONS_ENABLED=true
DESKTOP_NOTIFICATIONS=true

# Logging
LOG_LEVEL=info
LOG_FILE=./logs/app.log
EOF
        print_success "Created .env file with default configuration"
    else
        print_warning ".env file already exists, skipping creation"
    fi
    
    # Create necessary directories
    mkdir -p data logs
    
    print_success "Environment setup complete"
}

# Function to build the project
build_project() {
    print_status "Building the project..."
    
    # Build client
    npm run build:client
    
    # Build server
    cd server && npm run build && cd ..
    
    print_success "Project built successfully"
}

# Function to run tests
run_tests() {
    print_status "Running tests..."
    
    # Run client tests
    if npm run test --silent 2>/dev/null; then
        print_success "Client tests passed"
    else
        print_warning "No client tests configured or tests failed"
    fi
    
    # Run server tests
    cd server
    if npm run test --silent 2>/dev/null; then
        print_success "Server tests passed"
    else
        print_warning "No server tests configured or tests failed"
    fi
    cd ..
}

# Function to create startup scripts
create_startup_scripts() {
    print_status "Creating startup scripts..."
    
    # Development startup script
    cat > start-dev.sh << 'EOF'
#!/bin/bash
echo "Starting GTasks Dashboard in development mode..."
npm run dev
EOF
    
    # Production startup script
    cat > start-prod.sh << 'EOF'
#!/bin/bash
echo "Starting GTasks Dashboard in production mode..."
npm run build
npm run start
EOF
    
    # Make scripts executable
    chmod +x start-dev.sh start-prod.sh
    
    print_success "Startup scripts created"
}

# Function to display final instructions
show_final_instructions() {
    print_success "GTasks Dashboard setup complete!"
    echo ""
    echo -e "${GREEN}Quick Start:${NC}"
    echo "  Development: ./start-dev.sh"
    echo "  Production:  ./start-prod.sh"
    echo ""
    echo -e "${BLUE}Manual Commands:${NC}"
    echo "  npm run dev     - Start in development mode"
    echo "  npm run build   - Build the project"
    echo "  npm run start   - Start in production mode"
    echo ""
    echo -e "${BLUE}Server Commands:${NC}"
    echo "  cd server && npm run dev  - Start server in development"
    echo "  cd server && npm run start - Start server in production"
    echo ""
    echo -e "${BLUE}Access the Dashboard:${NC}"
    echo "  Frontend: http://localhost:3000"
    echo "  Backend API: http://localhost:8080"
    echo "  WebSocket: ws://localhost:8080"
    echo ""
    echo -e "${BLUE}Docker Deployment:${NC}"
    echo "  docker build -t gtasks-dashboard ."
    echo "  docker run -p 3000:3000 -p 8080:8080 gtasks-dashboard"
    echo ""
    echo -e "${YELLOW}Don't forget to:${NC}"
    echo "  1. Configure your .env file with proper settings"
    echo "  2. Set up your GTasks CLI credentials"
    echo "  3. Configure MCP integration if needed"
    echo ""
}

# Main setup process
main() {
    echo -e "${BLUE}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                   GTasks Dashboard Setup                    ║"
    echo "║                Advanced Task Management                     ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    
    print_status "Starting setup process..."
    
    # Check prerequisites
    print_status "Checking prerequisites..."
    
    # Check Node.js
    if ! check_version node "--version" "$MIN_NODE_VERSION"; then
        install_nodejs
    fi
    
    # Check Python
    if ! check_version python3 "--version" "$MIN_PYTHON_VERSION"; then
        print_error "Python $MIN_PYTHON_VERSION+ is required"
        exit 1
    fi
    
    # Install Python environment
    install_python
    
    # Install Node.js dependencies
    install_nodejs_deps
    
    # Set up environment
    setup_environment
    
    # Create startup scripts
    create_startup_scripts
    
    # Build project
    build_project
    
    # Run tests
    run_tests
    
    # Show final instructions
    show_final_instructions
}

# Run main function
main "$@"
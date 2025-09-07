#!/bin/bash

# MongoDB QA Portfolio Setup Script
# Author: QA Engineer
# Description: Setup script for MongoDB QA testing environment

set -e  # Exit on any error

echo "🚀 MongoDB QA Portfolio Setup"
echo "=============================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

# Check if running on macOS
if [[ "$OSTYPE" == "darwin"* ]]; then
    print_info "Detected macOS"
    PLATFORM="macos"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    print_info "Detected Linux"
    PLATFORM="linux"
else
    print_warning "Unsupported OS: $OSTYPE. Manual setup may be required."
    PLATFORM="unknown"
fi

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check Python installation
check_python() {
    if command_exists python3; then
        python_version=$(python3 --version | cut -d' ' -f2)
        print_status "Python 3 found (version: $python_version)"
        return 0
    else
        print_error "Python 3 not found. Please install Python 3.8+ manually."
        return 1
    fi
}

# Check pip installation
check_pip() {
    if command_exists pip3; then
        pip_version=$(pip3 --version | cut -d' ' -f2)
        print_status "pip found (version: $pip_version)"
        return 0
    elif command_exists pip; then
        pip_version=$(pip --version | cut -d' ' -f2)
        print_status "pip found (version: $pip_version)"
        return 0
    else
        print_error "pip not found. Please install pip manually."
        return 1
    fi
}

# Check MongoDB installation
check_mongodb() {
    if command_exists mongod; then
        mongodb_version=$(mongod --version | grep "db version" | cut -d' ' -f3 || echo "unknown")
        print_status "MongoDB found (version: $mongodb_version)"
        return 0
    else
        print_warning "MongoDB not found. Please install MongoDB manually."
        print_info "Visit: https://docs.mongodb.com/manual/installation/"
        return 1
    fi
}

# Setup Python virtual environment
setup_virtual_env() {
    print_info "Setting up Python virtual environment..."
    
    if [ ! -d "venv" ]; then
        python3 -m venv venv
        print_status "Virtual environment created"
    else
        print_status "Virtual environment already exists"
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    print_status "Virtual environment activated"
    
    # Upgrade pip
    pip install --upgrade pip
    print_status "pip upgraded"
}

# Install Python dependencies
install_python_dependencies() {
    print_info "Installing Python dependencies..."
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Install dependencies from requirements.txt
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt
        print_status "Python dependencies installed"
    else
        print_warning "requirements.txt not found, installing basic dependencies..."
        pip install pymongo pytest faker cryptography
        print_status "Basic dependencies installed"
    fi
}

# Test MongoDB connection
test_mongodb_connection() {
    print_info "Testing MongoDB connection..."
    
    # Check if mongosh is available, otherwise try mongo
    if command_exists mongosh; then
        MONGO_CLIENT="mongosh"
    elif command_exists mongo; then
        MONGO_CLIENT="mongo"
    else
        print_warning "No MongoDB client found. Please install mongosh or mongo shell."
        return 1
    fi
    
    # Test connection
    if $MONGO_CLIENT --eval "db.runCommand({ping: 1})" --quiet > /dev/null 2>&1; then
        print_status "MongoDB is running and accessible"
        return 0
    else
        print_warning "MongoDB is not running or not accessible."
        print_info "Please start MongoDB manually:"
        if [[ "$PLATFORM" == "macos" ]]; then
            print_info "  brew services start mongodb/brew/mongodb-community"
        elif [[ "$PLATFORM" == "linux" ]]; then
            print_info "  sudo systemctl start mongod"
        else
            print_info "  mongod --config mongod-test.conf"
        fi
        return 1
    fi
}

# Setup directories
setup_directories() {
    print_info "Setting up directories..."
    
    # Create necessary directories
    mkdir -p reports
    mkdir -p data/test-db
    mkdir -p logs
    
    print_status "Directories created"
}

# Create sample configuration
create_sample_config() {
    print_info "Creating sample configuration files..."
    
    # Create basic MongoDB config if it doesn't exist
    if [ ! -f "mongod-test.conf" ]; then
        cat > mongod-test.conf << EOF
# Basic MongoDB configuration for testing
storage:
  dbPath: ./data/test-db
systemLog:
  destination: file
  path: ./logs/mongod-test.log
net:
  port: 27017
  bindIp: 127.0.0.1
EOF
        print_status "MongoDB test configuration created"
    fi
}

# Display completion message
display_completion_message() {
    echo ""
    echo "🎉 MongoDB QA Portfolio Setup Status"
    echo "===================================="
    echo ""
    
    if check_python && check_pip; then
        echo "✅ Python environment: Ready"
    else
        echo "❌ Python environment: Requires manual setup"
    fi
    
    if check_mongodb; then
        echo "✅ MongoDB: Installed"
        if test_mongodb_connection; then
            echo "✅ MongoDB connection: Working"
        else
            echo "⚠️  MongoDB connection: Please start MongoDB"
        fi
    else
        echo "❌ MongoDB: Requires manual installation"
    fi
    
    echo ""
    echo "🚀 Next steps:"
    echo "  1. Activate virtual environment: source venv/bin/activate"
    echo "  2. Start MongoDB (if not running)"
    echo "  3. Run tests: python run_tests.py"
    echo ""
    echo "📚 Available commands:"
    echo "  • python run_tests.py --help                    # Show all options"
    echo "  • python run_tests.py --suite functional        # Run functional tests"
    echo "  • python run_tests.py --suite performance       # Run performance tests"
    echo ""
    print_status "Setup completed! Happy testing! 🧪"
}

# Main setup function
main() {
    echo "Starting MongoDB QA Portfolio setup..."
    echo ""
    
    # Check prerequisites
    if ! check_python || ! check_pip; then
        print_error "Prerequisites not met. Please install Python 3.8+ and pip manually."
        exit 1
    fi
    
    # Run setup steps
    setup_virtual_env
    install_python_dependencies
    setup_directories
    create_sample_config
    
    # Display completion message
    display_completion_message
}

# Run main function
main

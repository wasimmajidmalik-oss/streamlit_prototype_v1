#!/bin/bash

# AI Voice Chatbot - Docker Deployment Script
# This script helps you deploy the voice chatbot using Docker

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
APP_NAME="voice-chatbot"
PORT="8501"
COMPOSE_FILE="docker-compose.yml"

# Print colored output
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

# Check if Docker is installed
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    if ! docker info &> /dev/null; then
        print_error "Docker is not running. Please start Docker first."
        exit 1
    fi
    
    print_success "Docker is installed and running"
}

# Check if Docker Compose is available
check_docker_compose() {
    if command -v docker-compose &> /dev/null; then
        COMPOSE_CMD="docker-compose"
    elif docker compose version &> /dev/null; then
        COMPOSE_CMD="docker compose"
    else
        print_error "Docker Compose is not available. Please install Docker Compose."
        exit 1
    fi
    
    print_success "Docker Compose is available"
}

# Check if .env file exists and has API key
check_env_file() {
    if [ ! -f ".env" ]; then
        print_warning ".env file not found. Creating from example..."
        if [ -f ".env.example" ]; then
            cp .env.example .env
            print_warning "Please edit .env file and add your OpenAI API key"
            print_warning "You can get your API key from: https://platform.openai.com/api-keys"
            read -p "Press Enter after you've updated the .env file with your API key..."
        else
            print_error ".env.example file not found. Creating basic .env file..."
            echo "OPENAI_API_KEY=your_openai_api_key_here" > .env
            print_warning "Please edit .env file and add your OpenAI API key"
            read -p "Press Enter after you've updated the .env file with your API key..."
        fi
    fi
    
    # Check if API key is set
    if grep -q "your_openai_api_key_here" .env; then
        print_warning "Please update your OpenAI API key in the .env file"
        print_warning "Current .env file still contains placeholder"
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
    
    print_success ".env file is configured"
}

# Build the Docker image
build_image() {
    print_status "Building Docker image..."
    if $COMPOSE_CMD build; then
        print_success "Docker image built successfully"
    else
        print_error "Failed to build Docker image"
        exit 1
    fi
}

# Start the application
start_app() {
    print_status "Starting the voice chatbot application..."
    if $COMPOSE_CMD up -d; then
        print_success "Application started successfully"
        print_success "Voice Chatbot is now running at: http://localhost:$PORT"
        print_status "To view logs: $COMPOSE_CMD logs -f"
        print_status "To stop: $COMPOSE_CMD down"
    else
        print_error "Failed to start application"
        exit 1
    fi
}

# Stop the application
stop_app() {
    print_status "Stopping the voice chatbot application..."
    if $COMPOSE_CMD down; then
        print_success "Application stopped successfully"
    else
        print_error "Failed to stop application"
        exit 1
    fi
}

# Show application status
show_status() {
    print_status "Application status:"
    $COMPOSE_CMD ps
    
    echo
    print_status "Application logs (last 20 lines):"
    $COMPOSE_CMD logs --tail=20
}

# Show application logs
show_logs() {
    print_status "Following application logs (Ctrl+C to exit):"
    $COMPOSE_CMD logs -f
}

# Update application
update_app() {
    print_status "Updating application..."
    
    # Pull latest changes if in git repo
    if [ -d ".git" ]; then
        print_status "Pulling latest changes from git..."
        git pull
    fi
    
    # Rebuild and restart
    print_status "Rebuilding and restarting application..."
    $COMPOSE_CMD down
    $COMPOSE_CMD build --no-cache
    $COMPOSE_CMD up -d
    
    print_success "Application updated successfully"
}

# Show help
show_help() {
    echo "AI Voice Chatbot - Docker Deployment Script"
    echo
    echo "Usage: $0 [command]"
    echo
    echo "Commands:"
    echo "  start     - Build and start the application (default)"
    echo "  stop      - Stop the application"
    echo "  restart   - Restart the application"
    echo "  status    - Show application status and recent logs"
    echo "  logs      - Follow application logs"
    echo "  update    - Update and restart the application"
    echo "  build     - Build the Docker image only"
    echo "  help      - Show this help message"
    echo
    echo "Examples:"
    echo "  $0              # Start the application"
    echo "  $0 start        # Start the application"
    echo "  $0 logs         # View live logs"
    echo "  $0 stop         # Stop the application"
}

# Main function
main() {
    echo "=== AI Voice Chatbot - Docker Deployment ==="
    echo
    
    # Get command (default to start)
    COMMAND=${1:-start}
    
    case $COMMAND in
        "start")
            check_docker
            check_docker_compose
            check_env_file
            build_image
            start_app
            ;;
        "stop")
            check_docker_compose
            stop_app
            ;;
        "restart")
            check_docker_compose
            stop_app
            start_app
            ;;
        "status")
            check_docker_compose
            show_status
            ;;
        "logs")
            check_docker_compose
            show_logs
            ;;
        "update")
            check_docker
            check_docker_compose
            update_app
            ;;
        "build")
            check_docker
            check_docker_compose
            build_image
            ;;
        "help")
            show_help
            ;;
        *)
            print_error "Unknown command: $COMMAND"
            echo
            show_help
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"
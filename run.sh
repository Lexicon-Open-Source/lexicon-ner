#!/bin/bash

# Script to manage the Lexicon NER Docker container

# Function to show help information
show_help() {
    echo "Lexicon Named Entity Recognition Service"
    echo ""
    echo "Usage: ./run.sh [command]"
    echo ""
    echo "Commands:"
    echo "  start       - Start the service"
    echo "  stop        - Stop the service"
    echo "  restart     - Restart the service"
    echo "  logs        - Show logs"
    echo "  rebuild     - Rebuild and restart the service"
    echo "  status      - Check service status"
    echo "  test        - Run test script"
    echo "  help        - Show this help"
    echo ""
    echo "Examples:"
    echo "  ./run.sh start     # Start the service"
    echo "  ./run.sh logs      # Show logs"
}

# Function to check if docker compose is installed
check_docker() {
    if ! command -v docker &> /dev/null; then
        echo "Error: Docker is not installed. Please install Docker first."
        exit 1
    fi
}

# Start the service
start_service() {
    echo "Starting Lexicon NER service..."
    docker compose up -d
    echo "Service started. Access the API at http://localhost:8000"
    echo "For API documentation, visit http://localhost:8000/docs"
}

# Stop the service
stop_service() {
    echo "Stopping Lexicon NER service..."
    docker compose down
    echo "Service stopped."
}

# Show logs
show_logs() {
    echo "Showing logs (press Ctrl+C to exit)..."
    docker logs -f lexicon-ner
}

# Check service status
check_status() {
    echo "Checking service status..."
    if docker ps | grep -q lexicon-ner; then
        echo "Lexicon NER service is running."
        echo "Container ID: $(docker ps | grep lexicon-ner | awk '{print $1}')"
        echo "Status: $(docker ps | grep lexicon-ner | awk '{print $NF}')"
    else
        echo "Lexicon NER service is not running."
    fi
}

# Rebuild and restart the service
rebuild_service() {
    echo "Rebuilding and restarting Lexicon NER service..."
    docker compose down
    docker compose build --no-cache
    docker compose up -d
    echo "Service rebuilt and started."
}

# Run the test script
run_tests() {
    echo "Running test script..."
    python test_ner.py
}

# Main script logic
check_docker

# Process commands
case "$1" in
    start)
        start_service
        ;;
    stop)
        stop_service
        ;;
    restart)
        stop_service
        start_service
        ;;
    logs)
        show_logs
        ;;
    status)
        check_status
        ;;
    rebuild)
        rebuild_service
        ;;
    test)
        run_tests
        ;;
    help|*)
        show_help
        ;;
esac
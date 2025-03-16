#!/bin/bash

# Script to manage the Lexicon NER Docker container

# Default API key
DEFAULT_API_KEY="lexicon-ner-default-key"

# Load environment variables from .env file if it exists
if [ -f ".env" ]; then
    echo "Loading environment variables from .env file..."
    export $(grep -v '^#' .env | xargs)
else
    echo "No .env file found, using default values."
    # Create .env file from sample if it doesn't exist
    if [ -f ".env.sample" ]; then
        echo "Creating .env file from .env.sample..."
        cp .env.sample .env
        echo ".env file created. You may want to edit it with your own values."
    fi
fi

# Function to show help information
show_help() {
    echo "Lexicon Named Entity Recognition Service"
    echo ""
    echo "Usage: ./run.sh [command] [options]"
    echo ""
    echo "Commands:"
    echo "  start       - Start the service"
    echo "  stop        - Stop the service"
    echo "  restart     - Restart the service"
    echo "  logs        - Show logs"
    echo "  rebuild     - Rebuild and restart the service"
    echo "  status      - Check service status"
    echo "  test        - Run test script (NER)"
    echo "  test-legal  - Run legal entity recognition test script"
    echo "  config      - Edit the configuration (.env file)"
    echo "  help        - Show this help"
    echo ""
    echo "Options:"
    echo "  --api-key=KEY       - Set the API key (for start, restart, and rebuild commands)"
    echo "  --openai-key=KEY    - Set the OpenAI API key (for start, restart, and rebuild commands)"
    echo "  --no-auth           - Disable API key authentication (for start, restart, and rebuild commands)"
    echo ""
    echo "Examples:"
    echo "  ./run.sh start                                            # Start with default API key"
    echo "  ./run.sh start --api-key=my-secret-key                    # Start with custom API key"
    echo "  ./run.sh start --openai-key=sk-...                        # Start with custom OpenAI API key"
    echo "  ./run.sh start --api-key=my-key --openai-key=sk-...       # Start with both keys custom"
    echo "  ./run.sh start --no-auth                                  # Start with API authentication disabled"
    echo "  ./run.sh config                                           # Edit the configuration file"
    echo "  ./run.sh test                                             # Run NER tests"
    echo "  ./run.sh test-legal                                       # Run legal entity recognition tests"
    echo "  ./run.sh logs                                             # Show logs"
}

# Function to check if docker compose is installed
check_docker() {
    if ! command -v docker &> /dev/null; then
        echo "Error: Docker is not installed. Please install Docker first."
        exit 1
    fi
}

# Function to edit the .env file
edit_config() {
    echo "Editing configuration (.env file)..."

    # Create .env file from sample if it doesn't exist
    if [ ! -f ".env" ] && [ -f ".env.sample" ]; then
        echo "Creating .env file from .env.sample..."
        cp .env.sample .env
    elif [ ! -f ".env" ]; then
        echo "No .env or .env.sample file found. Creating empty .env file..."
        touch .env
    fi

    # Open the .env file with the default text editor
    if [ ! -z "$EDITOR" ]; then
        $EDITOR .env
    elif command -v nano &> /dev/null; then
        nano .env
    elif command -v vim &> /dev/null; then
        vim .env
    elif command -v vi &> /dev/null; then
        vi .env
    else
        echo "No suitable text editor found. Please edit the .env file manually."
    fi

    echo "Configuration updated. Restart the service to apply changes."
}

# Start the service
start_service() {
    echo "Starting Lexicon NER service..."

    # Apply API key settings if provided via command line (overrides .env)
    if [ ! -z "$CUSTOM_API_KEY" ]; then
        export API_KEY=$CUSTOM_API_KEY
        echo "Using custom API key from command line."
    elif [ ! -z "$API_KEY" ]; then
        echo "Using API key from .env file."
    else
        export API_KEY=$DEFAULT_API_KEY
        echo "Using default API key. Override with --api-key option or in .env file."
    fi

    # Apply OpenAI API key if provided
    if [ ! -z "$CUSTOM_OPENAI_KEY" ]; then
        export OPENAI_API_KEY=$CUSTOM_OPENAI_KEY
        echo "Using custom OpenAI API key from command line."
    elif [ ! -z "$OPENAI_API_KEY" ]; then
        echo "Using OpenAI API key from .env file."
    else
        echo "No OpenAI API key configured. Legal entity recognition will not work."
    fi

    if [ "$NO_AUTH" = true ]; then
        export REQUIRE_API_KEY=0
        echo "API key authentication disabled via command line."
    elif [ "$REQUIRE_API_KEY" = "0" ]; then
        echo "API key authentication disabled in .env file."
    else
        export REQUIRE_API_KEY=1
        echo "API key authentication enabled."
    fi

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

        # Check OpenAI API key status
        if [ ! -z "$OPENAI_API_KEY" ]; then
            echo "OpenAI API key is configured."
        else
            echo "OpenAI API key is not configured. Legal entity recognition will not work."
        fi
    else
        echo "Lexicon NER service is not running."
    fi
}

# Rebuild and restart the service
rebuild_service() {
    echo "Rebuilding and restarting Lexicon NER service..."

    # Apply API key settings if provided via command line (overrides .env)
    if [ ! -z "$CUSTOM_API_KEY" ]; then
        export API_KEY=$CUSTOM_API_KEY
        echo "Using custom API key from command line."
    elif [ ! -z "$API_KEY" ]; then
        echo "Using API key from .env file."
    else
        export API_KEY=$DEFAULT_API_KEY
        echo "Using default API key. Override with --api-key option or in .env file."
    fi

    # Apply OpenAI API key if provided
    if [ ! -z "$CUSTOM_OPENAI_KEY" ]; then
        export OPENAI_API_KEY=$CUSTOM_OPENAI_KEY
        echo "Using custom OpenAI API key from command line."
    elif [ ! -z "$OPENAI_API_KEY" ]; then
        echo "Using OpenAI API key from .env file."
    else
        echo "No OpenAI API key configured. Legal entity recognition will not work."
    fi

    if [ "$NO_AUTH" = true ]; then
        export REQUIRE_API_KEY=0
        echo "API key authentication disabled via command line."
    elif [ "$REQUIRE_API_KEY" = "0" ]; then
        echo "API key authentication disabled in .env file."
    else
        export REQUIRE_API_KEY=1
        echo "API key authentication enabled."
    fi

    docker compose down
    docker compose build --no-cache
    docker compose up -d
    echo "Service rebuilt and started."
}

# Run the NER test script
run_tests() {
    echo "Running NER test script..."
    # Pass the current API key to the test script
    export API_KEY=${API_KEY:-$DEFAULT_API_KEY}
    python test_ner.py
}

# Run the legal entity recognition test script
run_legal_tests() {
    echo "Running legal entity recognition test script..."
    # Pass the current API key to the test script
    export API_KEY=${API_KEY:-$DEFAULT_API_KEY}

    # Check if OpenAI API key is configured
    if [ -z "$OPENAI_API_KEY" ]; then
        echo "Warning: OpenAI API key is not configured. Legal entity recognition will not work."
        echo "Please set the OPENAI_API_KEY in your .env file or use --openai-key option."
    fi

    python test_legal.py
}

# Parse command line options
parse_options() {
    for arg in "$@"; do
        case $arg in
            --api-key=*)
                CUSTOM_API_KEY="${arg#*=}"
                shift
                ;;
            --openai-key=*)
                CUSTOM_OPENAI_KEY="${arg#*=}"
                shift
                ;;
            --no-auth)
                NO_AUTH=true
                shift
                ;;
            *)
                # Unknown option
                ;;
        esac
    done
}

# Main script logic
check_docker
parse_options "$@"

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
    test-legal)
        run_legal_tests
        ;;
    config)
        edit_config
        ;;
    help|*)
        show_help
        ;;
esac
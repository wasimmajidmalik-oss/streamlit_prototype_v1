#!/bin/bash

# Health check script for the voice chatbot Docker container
# This script checks if the Streamlit application is running and responding

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configuration
HEALTH_URL="http://localhost:8501/_stcore/health"
TIMEOUT=10

# Function to check if Streamlit is responding
check_streamlit_health() {
    if command -v curl >/dev/null 2>&1; then
        # Use curl if available
        if curl -f -s --max-time $TIMEOUT "$HEALTH_URL" >/dev/null 2>&1; then
            return 0
        else
            return 1
        fi
    elif command -v wget >/dev/null 2>&1; then
        # Use wget as fallback
        if wget -q --timeout=$TIMEOUT --tries=1 --spider "$HEALTH_URL" >/dev/null 2>&1; then
            return 0
        else
            return 1
        fi
    else
        # No HTTP client available, check if port is listening
        if command -v nc >/dev/null 2>&1; then
            if nc -z localhost 8501 >/dev/null 2>&1; then
                return 0
            else
                return 1
            fi
        else
            # Last resort: check if Python process is running
            if pgrep -f "streamlit" >/dev/null 2>&1; then
                return 0
            else
                return 1
            fi
        fi
    fi
}

# Main health check
if check_streamlit_health; then
    echo -e "${GREEN}✓ Health check passed - Streamlit is responding${NC}"
    exit 0
else
    echo -e "${RED}✗ Health check failed - Streamlit is not responding${NC}"
    exit 1
fi
#!/bin/bash

# Test script for Docker deployment
# This script tests the voice chatbot deployment

echo "🧪 Testing AI Voice Chatbot Docker Deployment"
echo "=============================================="

# Check if Docker is running
echo "📋 Checking Docker..."
if docker info >/dev/null 2>&1; then
    echo "✅ Docker is running"
else
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Check if .env file exists and has API key
echo "📋 Checking environment configuration..."
if [ -f ".env" ]; then
    if grep -q "your_openai_api_key_here" .env; then
        echo "⚠️  Warning: Please update your OpenAI API key in .env file"
    else
        echo "✅ Environment file configured"
    fi
else
    echo "❌ .env file not found. Please create it with your OpenAI API key."
    exit 1
fi

# Build the Docker image
echo "📋 Building Docker image..."
if docker-compose build; then
    echo "✅ Docker image built successfully"
else
    echo "❌ Failed to build Docker image"
    exit 1
fi

# Start the application
echo "📋 Starting application..."
if docker-compose up -d; then
    echo "✅ Application started successfully"
    
    # Wait for application to be ready
    echo "📋 Waiting for application to be ready..."
    sleep 10
    
    # Check if application is responding
    if curl -f -s http://localhost:8501/_stcore/health >/dev/null 2>&1; then
        echo "✅ Application is responding"
        echo ""
        echo "🎉 SUCCESS! Voice Chatbot is running at:"
        echo "   👉 http://localhost:8501"
        echo ""
        echo "📱 To use the voice features:"
        echo "   1. Open the URL in your browser"
        echo "   2. Grant microphone permissions when prompted"
        echo "   3. Use the voice recorder to speak with the AI"
        echo ""
        echo "📋 Management commands:"
        echo "   • View logs: docker-compose logs -f"
        echo "   • Stop app: docker-compose down"
        echo "   • Restart: docker-compose restart"
    else
        echo "⚠️  Application started but may not be fully ready yet"
        echo "   Please wait a moment and check http://localhost:8501"
    fi
    
else
    echo "❌ Failed to start application"
    exit 1
fi

echo ""
echo "🧪 Test completed successfully!"
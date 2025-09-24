# 🐳 Docker Deployment Guide

This guide explains how to deploy the AI Voice Chatbot using Docker.

## 📋 Prerequisites

- Docker installed on your system
- Docker Compose (usually included with Docker Desktop)
- OpenAI API key
- Microphone and speakers access (for voice features)

## 🚀 Quick Start

### 1. Clone or Download the Project

```bash
git clone <your-repo-url>
cd gitpush_folder
```

### 2. Set Up Environment Variables

Copy the example environment file and add your OpenAI API key:

```bash
# Copy example file
cp .env.example .env

# Edit .env file and add your OpenAI API key
# Replace 'your_openai_api_key_here' with your actual API key
```

Your `.env` file should look like:
```
OPENAI_API_KEY=sk-proj-your-actual-api-key-here
```

### 3. Build and Run with Docker Compose

```bash
# Build and start the application
docker-compose up --build

# Or run in detached mode (background)
docker-compose up -d --build
```

### 4. Access the Application

Open your web browser and navigate to:
- **Local**: http://localhost:8501
- **Network**: http://your-server-ip:8501

## 🛠️ Manual Docker Commands

If you prefer not to use Docker Compose:

### Build the Image

```bash
docker build -t voice-chatbot .
```

### Run the Container

```bash
# Basic run
docker run -p 8501:8501 --env-file .env voice-chatbot

# Run with environment variable directly
docker run -p 8501:8501 -e OPENAI_API_KEY=your_api_key_here voice-chatbot

# Run in background with restart policy
docker run -d --name voice-chatbot --restart unless-stopped -p 8501:8501 --env-file .env voice-chatbot
```

## 🔧 Configuration Options

### Environment Variables

You can configure the application using these environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_API_KEY` | Required | Your OpenAI API key |
| `STREAMLIT_SERVER_PORT` | 8501 | Port for the web interface |
| `STREAMLIT_SERVER_ADDRESS` | 0.0.0.0 | Server bind address |

### Custom Port

To run on a different port (e.g., 8080):

```bash
# Docker Compose: Edit docker-compose.yml
ports:
  - "8080:8501"

# Docker run:
docker run -p 8080:8501 --env-file .env voice-chatbot
```

## 🖥️ Production Deployment

### With Reverse Proxy (Nginx)

Example Nginx configuration:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Cloud Deployment

#### Docker Hub
1. Build and tag your image:
   ```bash
   docker build -t your-username/voice-chatbot .
   docker push your-username/voice-chatbot
   ```

#### Google Cloud Run
```bash
# Build for Cloud Run
gcloud builds submit --tag gcr.io/your-project/voice-chatbot

# Deploy
gcloud run deploy voice-chatbot \
  --image gcr.io/your-project/voice-chatbot \
  --platform managed \
  --port 8501 \
  --set-env-vars OPENAI_API_KEY=your_api_key
```

#### AWS ECS/Fargate
Use the provided docker-compose.yml as a template for ECS task definitions.

## 🔍 Troubleshooting

### Common Issues

1. **Permission Denied**
   ```bash
   # Fix ownership issues
   sudo chown -R $USER:$USER .
   ```

2. **Port Already in Use**
   ```bash
   # Check what's using port 8501
   sudo lsof -i :8501
   
   # Use different port
   docker run -p 8502:8501 --env-file .env voice-chatbot
   ```

3. **🎉 FULL AUDIO SUPPORT IN DOCKER!**
   
   **✅ Complete voice chatbot functionality is available in Docker:**
   - **🎤 Voice Input**: Browser-based microphone recording works perfectly
   - **🔊 Voice Output**: AI responses play automatically through browser
   - **🌐 Cross-Platform**: Works on Windows, Mac, Linux Docker hosts
   - **🛡️ No Special Setup**: No system audio device configuration needed
   
   **Browser Requirements:**
   - Modern browser (Chrome, Firefox, Safari, Edge)
   - Grant microphone permissions when prompted
   - Use HTTPS in production for microphone access
   
   **Available Features:**
   - Real-time voice conversation with OpenAI models
   - Speech-to-text using Whisper API
   - Natural text-to-speech responses
   - Fallback text input/output mode

4. **OpenAI API Errors**
   - Verify your API key is correct
   - Check your OpenAI account has credits
   - Ensure stable internet connection

### Logs and Debugging

```bash
# View container logs
docker logs voice-chatbot

# Follow logs in real-time
docker logs -f voice-chatbot

# Access container shell
docker exec -it voice-chatbot /bin/bash
```

### Health Checks

The container includes health checks. Check status:

```bash
# Docker Compose
docker-compose ps

# Docker run
docker ps
```

## 🔒 Security Considerations

### API Key Security
- Never commit `.env` files to version control
- Use Docker secrets in production:
  ```bash
  echo "your_api_key" | docker secret create openai_api_key -
  ```

### Network Security
- Run behind a reverse proxy in production
- Use HTTPS for microphone access
- Consider rate limiting

### Container Security
- Container runs as non-root user
- Minimal base image used
- No unnecessary packages installed

## 📊 Monitoring

### Resource Usage
```bash
# Monitor container resources
docker stats voice-chatbot

# Container resource limits
docker run --memory=1g --cpus=1 -p 8501:8501 --env-file .env voice-chatbot
```

### Application Metrics
- Access Streamlit's built-in metrics at `/_stcore/health`
- Monitor OpenAI API usage in your OpenAI dashboard

## 🔄 Updates and Maintenance

### Updating the Application
```bash
# Pull latest code
git pull

# Rebuild and restart
docker-compose down
docker-compose up --build -d
```

### Backup and Data
The application is stateless, but you may want to backup:
- Configuration files (`.env`, `docker-compose.yml`)
- Any custom modifications to the application

## 📞 Support

If you encounter issues:

1. Check the troubleshooting section above
2. Review container logs
3. Verify your OpenAI API key and credits
4. Test with a minimal Docker setup
5. Check Docker and system requirements

## 🏷️ Version Information

- **Docker Image**: Based on Python 3.9.13 slim
- **Architecture**: Supports AMD64 and ARM64
- **Dependencies**: See requirements.txt for Python packages
- **System**: Debian-based with audio libraries
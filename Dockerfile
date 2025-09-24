# Use Python 3.9.13 slim image as base
FROM python:3.9.13-slim

# Set working directory
WORKDIR /app

# Install system dependencies for audio processing and health checks
RUN apt-get update && apt-get install -y \
    build-essential \
    portaudio19-dev \
    libasound2-dev \
    libsndfile1 \
    pulseaudio \
    pulseaudio-utils \
    alsa-utils \
    alsa-base \
    libasound2-plugins \
    curl \
    netcat-traditional \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user for security and add to audio group
RUN useradd --create-home --shell /bin/bash --groups audio app && chown -R app:app /app

# Switch to non-root user
USER app

# Set up audio environment variables
ENV PULSE_RUNTIME_PATH=/tmp/pulse-socket
ENV ALSA_CARD=0
ENV PYGAME_HIDE_SUPPORT_PROMPT=1

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0

# Copy requirements first for better caching
COPY --chown=app:app requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --user -r requirements.txt

# Copy application files
COPY --chown=app:app Major_working_code_v3_browser_audio.py .
COPY --chown=app:app Major_working_code_v3.py .
COPY --chown=app:app healthcheck.sh .

# Make health check script executable
RUN chmod +x healthcheck.sh

# Create a default .env file template (users will need to add their API key)
RUN echo "OPENAI_API_KEY=your_openai_api_key_here" > .env.template

# Expose the Streamlit port
EXPOSE 8501

# Add health check using our custom script
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD ./healthcheck.sh

# Create streamlit config directory and add configuration
RUN mkdir -p /home/app/.streamlit
RUN echo '[server]' > /home/app/.streamlit/config.toml && \
    echo 'port = 8501' >> /home/app/.streamlit/config.toml && \
    echo 'address = "0.0.0.0"' >> /home/app/.streamlit/config.toml && \
    echo 'headless = true' >> /home/app/.streamlit/config.toml && \
    echo 'enableCORS = false' >> /home/app/.streamlit/config.toml && \
    echo 'enableXsrfProtection = false' >> /home/app/.streamlit/config.toml

# Command to run the browser-based audio application (Docker-optimized)
CMD ["python", "-m", "streamlit", "run", "Major_working_code_v3_browser_audio.py", "--server.address", "0.0.0.0", "--server.port", "8501"]
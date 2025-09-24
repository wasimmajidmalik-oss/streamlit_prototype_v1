# Use Python 3.9.13 slim image as base
FROM python:3.9.13-slim

# Set working directory
WORKDIR /app

# Install system dependencies - minimal for web app
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user for security
RUN useradd --create-home --shell /bin/bash app && chown -R app:app /app

# Switch to non-root user
USER app

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0

# Copy requirements first for better caching
COPY --chown=app:app requirements-docker.txt .

# Install Python dependencies (Docker-optimized)
RUN pip install --no-cache-dir --user -r requirements-docker.txt

# Copy application files
COPY --chown=app:app Major_working_code_v3_docker.py .
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

# Command to run the Docker-optimized application
CMD ["python", "-m", "streamlit", "run", "Major_working_code_v3_docker.py", "--server.address", "0.0.0.0", "--server.port", "8501"]
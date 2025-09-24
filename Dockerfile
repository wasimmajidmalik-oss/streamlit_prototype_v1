FROM python:3.9.13-slim

# Install EVERYTHING your original code needs + virtual audio magic
RUN apt-get update && apt-get install -y \
    portaudio19-dev \
    libportaudio2 \
    libasound2-dev \
    python3-pyaudio \
    alsa-utils \
    pulseaudio \
    pulseaudio-utils \
    ffmpeg \
    xvfb \
    curl \
    sudo \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy and install your exact requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy your original code (no modifications needed)
COPY . .

# Make the startup script executable  
RUN chmod +x start_with_audio.sh

# Create user with audio permissions
RUN useradd -m -u 1000 appuser && \
    usermod -a -G audio,pulse-access appuser && \
    echo "appuser ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers && \
    chown -R appuser:appuser /app

USER appuser

EXPOSE 8501

# This runs your ORIGINAL code with virtual audio
CMD ["./start_with_audio.sh"]
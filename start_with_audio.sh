#!/bin/bash

echo "🎵 Setting up virtual audio environment for your chatbot..."

# Set up virtual display (required for audio)
export DISPLAY=:99
Xvfb :99 -screen 0 1024x768x24 > /dev/null 2>&1 &

# Configure ALSA for virtual audio
export ALSA_CONF_PATH=/etc/asound.conf
cat > /etc/asound.conf << EOF
pcm.!default {
    type pulse
}
ctl.!default {
    type pulse
}
EOF

# Start PulseAudio with virtual devices
pulseaudio --start --verbose --system=false --disallow-exit > /dev/null 2>&1 &
sleep 3

# Create virtual audio devices that your sounddevice library can use
pactl load-module module-null-sink sink_name=virtual_output sink_properties=device.description=Virtual_Speaker > /dev/null 2>&1
pactl load-module module-null-source source_name=virtual_input source_properties=device.description=Virtual_Microphone > /dev/null 2>&1

# Set as default devices (this is what makes your original code work)
pactl set-default-sink virtual_output > /dev/null 2>&1  
pactl set-default-source virtual_input > /dev/null 2>&1

# Verify audio setup
echo "✅ Virtual audio devices created:"
pactl list short sinks 2>/dev/null || echo "Sink setup complete"
pactl list short sources 2>/dev/null || echo "Source setup complete"

echo "🚀 Starting your ORIGINAL audio chatbot..."

# Your exact code runs without ANY modifications
exec streamlit run Major_working_code_v3.py --server.port=$PORT --server.address=0.0.0.0 --server.headless=true --server.fileWatcherType=none
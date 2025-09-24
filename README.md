# 🗣️ AI Voice Chatbot - OpenAI MVP

A sophisticated voice-enabled chatbot application built with Streamlit and powered entirely by OpenAI's suite of APIs including ChatGPT, Whisper, and Text-to-Speech.

## 🌟 Features

### 🎯 Core Functionality
- **🤖 AI Conversations**: Powered by OpenAI's ChatGPT models (GPT-3.5-turbo, GPT-4)
- **🎙️ Speech Recognition**: Real-time voice input using OpenAI Whisper
- **🔊 Text-to-Speech**: Natural voice responses using OpenAI TTS
- **💬 Interactive Chat**: Both voice and text input modes
- **🎛️ Advanced Configuration**: Customizable AI parameters and voice settings
- **🐳 Docker Ready**: Browser-based audio version for perfect containerization

### 🚀 Advanced Features
- **🔄 Continuous Conversation**: Natural conversation flow with intelligent conclusion detection
- **⚙️ Dynamic Settings**: Real-time adjustment of AI models, voices, and parameters
- **🎚️ Audio Calibration**: Automatic microphone calibration for optimal performance
- **🔧 Fallback Systems**: Multiple speech recognition fallbacks for reliability
- **📝 Conversation History**: Complete chat history with timestamps
- **🎨 Modern UI**: Clean, intuitive Streamlit interface

## 🛠️ Technology Stack

- **Frontend**: Streamlit
- **AI Services**: OpenAI (ChatGPT, Whisper, TTS)
- **Audio Processing**: 
  - sounddevice (audio I/O)
  - soundfile (audio file handling)
  - pygame (audio playback)
  - speech_recognition (fallback recognition)
- **Environment**: Python 3.9+
- **Dependencies**: See `installed_modules.txt` for complete list

## 🏗️ Architecture

### Main Components

1. **SimpleChatbot Class**: Core chatbot functionality
   - Voice conversation management  
   - Audio processing and calibration
   - OpenAI API integration
   - Session state management

2. **Settings System**: Comprehensive configuration
   - AI model parameters (temperature, max tokens, top-p)
   - Audio settings (sample rate, recording duration)
   - TTS configuration (model, voice selection)
   - Custom system prompts

3. **Audio Pipeline**:
   - Continuous audio recording with silence detection
   - Real-time volume monitoring and calibration
   - OpenAI Whisper speech-to-text processing
   - OpenAI TTS with multiple voice options

## 🚦 Getting Started

You can run this application either locally with Python or using Docker for easier deployment.

### 🐳 Docker Deployment (Recommended)

**Prerequisites:**
- Docker and Docker Compose installed
- OpenAI API key

**Quick Start:**
1. **Clone the repository**
   ```bash
   git clone https://github.com/wasimmajidmalik-oss/streamlit_prototype_v1
   cd gitpush_folder
   ```

2. **Set up your OpenAI API key**
   ```bash
   # Copy example file
   cp .env.example .env
   
   # Edit .env and add your OpenAI API key
   # Replace 'your_openai_api_key_here' with your actual key
   ```

3. **Deploy with one command**
   ```bash
   # Linux/Mac
   ./deploy.sh
   
   # Windows
   deploy.bat
   
   # Or manually with Docker Compose
   docker-compose up --build
   ```

4. **Access the application**
   - Open http://localhost:8501 in your browser

📖 **See [DOCKER_DEPLOYMENT.md](DOCKER_DEPLOYMENT.md) for detailed Docker deployment instructions**

   **🎯 Docker runs the browser-optimized version** (`Major_working_code_v3_browser_audio.py`) which:
   - ✅ **Full voice chat functionality** using browser APIs
   - ✅ **Works on all platforms** (Windows, Mac, Linux)
   - ✅ **No audio device setup required**
   - ✅ **Perfect for cloud deployment**

### 🐍 Local Python Installation

**Prerequisites:**
- Python 3.9 or higher
- OpenAI API key
- Microphone and speakers/headphones

**Installation:**

1. **Clone the repository**
   ```bash
   git clone https://github.com/wasimmajidmalik-oss/streamlit_prototype_v1
   cd gitpush_folder
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   
   Create a `.env` file in the project root:
   ```env
   OPENAI_API_KEY=your_openai_api_key_here
   ```
   
   ⚠️ **Security Note**: Never commit your `.env` file to version control.

4. **Run the application**
   ```bash
   streamlit run Major_working_code_v3.py
   ```

### Quick Start
1. Launch the app and allow microphone permissions
2. Configure your OpenAI API key in the settings
3. Click "🔴 Start Voice Chat" to begin a conversation
4. Speak naturally - the app will detect speech and respond
5. Use the settings page to customize AI behavior and voice options

## ⚙️ Configuration

### AI Model Settings
- **Model**: Choose between GPT-3.5-turbo, GPT-4, etc.
- **Temperature**: Control response creativity (0.01-2.0)
- **Max Tokens**: Set response length limit
- **Top P**: Fine-tune response diversity

### Audio Settings
- **Sample Rate**: Audio quality (16kHz-48kHz)
- **Recording Duration**: Max recording time per input
- **Silence Detection**: Automatic speech endpoint detection
- **Calibration**: Microphone sensitivity adjustment

### Voice Settings
- **TTS Model**: Choose between tts-1 (fast) or tts-1-hd (high quality)
- **Voice Selection**: 6 unique voices (alloy, echo, fable, onyx, nova, shimmer)
- **Language**: Multi-language support for speech recognition

## 🎯 Usage Examples

### Basic Voice Conversation
1. Click "Start Voice Chat"
2. Speak your question or request
3. Listen to the AI's response
4. Continue the natural conversation

### Text Backup Mode
- Use the text input field if voice recognition isn't working
- Type your message and click "Send"
- Click "Speak Last Response" to hear the AI's reply

### Advanced Configuration
- Access the Settings page for detailed customization
- Adjust AI personality with custom system prompts
- Fine-tune audio parameters for your environment
- Switch between different AI models and voices

## 📁 Project Structure

```
gitpush_folder/
├── Major_working_code_v3.py    # Main application file
├── .env                        # Environment variables (create this)
├── .gitignore                 # Git ignore rules
├── installed_modules.txt      # Complete dependency list
└── README.md                  # This documentation
```

## 🔧 Key Classes and Functions

### SimpleChatbot Class
- `__init__()`: Initialize audio systems and session state
- `get_chatbot_response()`: Process user input and get AI response
- `text_to_speech_openai()`: Convert text to speech with OpenAI TTS
- `speech_to_text_openai()`: Convert speech to text with Whisper
- `record_audio_continuous()`: Continuous audio recording with silence detection
- `run_conversation_session()`: Main conversation loop management

### Settings System
- Dynamic parameter configuration
- Real-time setting updates
- Custom system prompt management
- Multi-language support

## 🛡️ Security Considerations

- **API Key Protection**: Environment variables prevent key exposure
- **Git Security**: `.gitignore` excludes sensitive files
- **Input Validation**: Sanitized inputs to OpenAI APIs
- **Error Handling**: Graceful fallbacks for API failures

## 🐛 Troubleshooting

### Common Issues

1. **Microphone not working**
   - Check microphone permissions
   - Run calibration in settings
   - Try different sample rates

2. **OpenAI API errors**
   - Verify API key is correct
   - Check API quota and billing
   - Ensure stable internet connection

3. **Audio playback issues**
   - Check speaker/headphone connection
   - Try different TTS voices
   - Restart the application

### Fallback Systems
- Multiple speech recognition backends
- Windows SAPI TTS fallback
- Error recovery and user feedback

## 🚀 Deployment

### 🐳 Docker Deployment (Production Ready)

**Easy deployment with Docker:**
```bash
# Quick start
./deploy.sh start

# View logs
./deploy.sh logs

# Stop application
./deploy.sh stop
```

**Manual Docker commands:**
```bash
# Build and run
docker-compose up --build -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

**Production considerations:**
- Use reverse proxy (Nginx) for HTTPS
- Set up proper monitoring and logging
- Configure resource limits
- Use Docker secrets for API keys
- Deploy on cloud platforms (AWS, GCP, Azure)

### 🐍 Local Development
```bash
streamlit run Major_working_code_v3.py
```

### ☁️ Cloud Deployment Options
- **Google Cloud Run**: One-click deployment with built-in HTTPS
- **AWS ECS/Fargate**: Scalable container deployment
- **Azure Container Instances**: Simple container hosting
- **DigitalOcean App Platform**: Easy Docker deployment
- **Railway/Render**: Simple deployment with Git integration

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📝 License

This project is available under the MIT License. See LICENSE file for details.

## 🆘 Support

For issues and questions:
- Check the troubleshooting section
- Review OpenAI API documentation
- Create an issue in the repository

## 🔄 Version History

### v3.0 (Current)
- Full OpenAI integration (ChatGPT + Whisper + TTS)
- Advanced settings and configuration
- Improved audio processing
- Natural conversation flow
- Multi-voice support

## 🎯 Future Enhancements

- Multi-language conversation support
- Conversation memory persistence
- Custom wake word detection
- Integration with external APIs
- Mobile app version

---

**Built with ❤️ using OpenAI's powerful AI services**

*This is an MVP (Minimum Viable Product) showcasing the integration of OpenAI's complete AI stack in a conversational interface.*
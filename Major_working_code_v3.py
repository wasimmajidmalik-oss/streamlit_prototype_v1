import streamlit as st
import sounddevice as sd
import soundfile as sf
import threading
import time
import json
import tempfile
import os
from dotenv import load_dotenv
from datetime import datetime
import queue
import numpy as np
import pygame
import speech_recognition as sr

# Import OpenAI for ChatGPT integration
import openai
from openai import OpenAI

# Load environment variables from .env file
load_dotenv()

# Initialize OpenAI client
API_KEY = os.getenv("OPENAI_API_KEY")
if not API_KEY:
    st.error("OpenAI API key not found! Please check your .env file.")
    st.stop()

client = OpenAI(api_key=API_KEY)

def get_response(prompt):
    """
    Given a prompt string it will get model inference using OpenAI ChatGPT
    params: prompt, str
    returns: response object with same structure as original Gemini response
    """
    try:
        # Use dynamic parameters from session state
        temperature = st.session_state.get('ai_temperature', 0.01)
        max_tokens = st.session_state.get('ai_max_tokens', 2048)
        top_p = st.session_state.get('ai_top_p', 0.6)
        model = st.session_state.get('ai_model', 'gpt-3.5-turbo')
        
        # Call OpenAI ChatGPT API
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a helpful and friendly AI assistant. "
                "Always respond in the exact JSON format requested by the user."},
                {"role": "user", "content": prompt}
            ],
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p
        )
        
        # Extract the response content
        response_content = response.choices[0].message.content.strip()
        
        # Try to parse as JSON first, if it fails, wrap it in the expected format
        try:
            # Check if the response is already in JSON format
            json.loads(response_content)
            prediction_json = response_content
        except json.JSONDecodeError:
            # If not JSON, wrap the response in the expected format
            prediction_json = json.dumps({"response": response_content})
            
        # Create a mock response object that matches the original Gemini structure
        class MockResponse:
            def __init__(self, prediction_content):
                self.status_code = 200
                self.text = json.dumps({"prediction": prediction_content})
                
        return MockResponse(prediction_json)
        
    except Exception as e:
        # Return error response in same format as original
        class MockErrorResponse:
            def __init__(self, error_msg):
                self.status_code = 500
                self.text = json.dumps({"error": str(error_msg)})
                
        return MockErrorResponse(f"OpenAI API error: {e}")

def show_settings_page():
    """Display the settings configuration page"""
    st.title("⚙️ Voice Chatbot Settings")
    st.write("Configure all parameters for your AI chatbot experience")
    
    # Create tabs for different setting categories
    tab1, tab2, tab3, tab4 = st.tabs(["🤖 AI Settings", "🎤 Audio Settings", "🔊 Voice Settings", "📝 Customization"])
    
    with tab1:
        st.header("AI Model Configuration")
        
        col1, col2 = st.columns(2)
        with col1:
            st.session_state.ai_model = st.selectbox(
                "Model",
                options=["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo"],
                index=["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo"].index(st.session_state.get('ai_model', 'gpt-3.5-turbo')),
                help="Choose the AI model for conversation"
            )
            
            st.session_state.ai_temperature = st.slider(
                "Temperature",
                min_value=0.0, max_value=2.0, 
                value=st.session_state.get('ai_temperature', 0.01),
                step=0.01,
                help="Controls randomness (0.0 = focused, 2.0 = creative)"
            )
            
        with col2:
            st.session_state.ai_max_tokens = st.number_input(
                "Max Tokens",
                min_value=100, max_value=4096,
                value=st.session_state.get('ai_max_tokens', 2048),
                step=100,
                help="Maximum response length"
            )
            
            st.session_state.ai_top_p = st.slider(
                "Top P",
                min_value=0.0, max_value=1.0,
                value=st.session_state.get('ai_top_p', 0.6),
                step=0.01,
                help="Controls diversity (0.1 = focused, 1.0 = diverse)"
            )
    
    with tab2:
        st.header("Audio Recording Configuration")
        
        col1, col2 = st.columns(2)
        with col1:
            st.session_state.audio_sample_rate = st.selectbox(
                "Sample Rate (Hz)",
                options=[16000, 22050, 44100, 48000],
                index=[16000, 22050, 44100, 48000].index(st.session_state.get('audio_sample_rate', 48000)),
                help="Audio quality (higher = better quality, more processing)"
            )
            
            st.session_state.silence_duration_to_stop = st.slider(
                "Silence Duration to Stop (seconds)",
                min_value=0.5, max_value=10.0,
                value=st.session_state.get('silence_duration_to_stop', 2.5),
                step=0.1,
                help="How long to wait in silence before stopping recording"
            )
            
            st.session_state.calibration_duration = st.slider(
                "Calibration Duration (seconds)",
                min_value=1.0, max_value=10.0,
                value=st.session_state.get('calibration_duration', 3.0),
                step=0.5,
                help="Time to calibrate ambient noise levels"
            )
            
        with col2:
            st.session_state.max_recording_time = st.slider(
                "Max Recording Time (seconds)",
                min_value=10.0, max_value=120.0,
                value=st.session_state.get('max_recording_time', 30.0),
                step=1.0,
                help="Maximum time to record before auto-stopping"
            )
            
            st.session_state.min_recording_time = st.slider(
                "Min Recording Time (seconds)",
                min_value=0.1, max_value=5.0,
                value=st.session_state.get('min_recording_time', 1.0),
                step=0.1,
                help="Minimum recording time before allowing stop"
            )
            
            st.session_state.chunk_duration = st.slider(
                "Chunk Duration (seconds)",
                min_value=0.1, max_value=1.0,
                value=st.session_state.get('chunk_duration', 0.2),
                step=0.05,
                help="Audio processing chunk size"
            )
    
    with tab3:
        st.header("Text-to-Speech & Speech Recognition")
        
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Text-to-Speech (TTS)")
            st.session_state.tts_model = st.selectbox(
                "TTS Model",
                options=["tts-1", "tts-1-hd"],
                index=["tts-1", "tts-1-hd"].index(st.session_state.get('tts_model', 'tts-1')),
                help="TTS quality (tts-1 = faster, tts-1-hd = higher quality)"
            )
            
            st.session_state.tts_voice = st.selectbox(
                "Voice",
                options=["alloy", "echo", "fable", "onyx", "nova", "shimmer"],
                index=["alloy", "echo", "fable", "onyx", "nova", "shimmer"].index(st.session_state.get('tts_voice', 'alloy')),
                help="Choose the AI voice personality"
            )
            
            st.session_state.tts_speed = st.slider(
                "Speech Speed",
                min_value=0.25, max_value=4.0,
                value=st.session_state.get('tts_speed', 1.0),
                step=0.05,
                help="Speech speed: 0.25 = very slow, 1.0 = normal, 4.0 = very fast"
            )
            
        with col2:
            st.subheader("Speech Recognition")
            st.session_state.whisper_model = st.selectbox(
                "Whisper Model",
                options=["whisper-1"],
                index=0,
                help="Speech recognition model"
            )
            
            st.session_state.whisper_language = st.selectbox(
                "Language",
                options=["en", "es", "fr", "de", "it", "pt", "ru", "ja", "ko", "zh"],
                index=["en", "es", "fr", "de", "it", "pt", "ru", "ja", "ko", "zh"].index(st.session_state.get('whisper_language', 'en')),
                help="Primary language for speech recognition"
            )
    
    with tab4:
        st.header("Custom System Prompt")
        st.write("Customize how your AI assistant behaves and responds")
        
        st.session_state.custom_system_prompt = st.text_area(
            "System Prompt",
            value=st.session_state.get('custom_system_prompt', ''),
            height=300,
            help="Define the AI's personality, behavior, and conversation ending logic"
        )
        
        if st.button("🔄 Reset to Default Prompt"):
            st.session_state.custom_system_prompt = """You are a helpful and friendly AI assistant.
You provide clear, concise, and helpful responses to user questions and requests.
Keep your responses conversational and engaging.

IMPORTANT: You must analyze the conversation flow and determine if this is a natural ending point. 
Consider ending the conversation when:
- User says goodbye, farewell, or dismissal phrases
- User expresses gratitude and seems satisfied with help received
- The conversation has reached a natural conclusion
- User indicates they are done or have no more questions
- The task or question has been fully completed and user seems content"""
            st.rerun()
            
        st.markdown("---")
        
        st.header("Custom Welcome Message")
        st.write("Customize the greeting message that starts each conversation")
        
        st.session_state.custom_welcome_message = st.text_area(
            "Welcome Message",
            value=st.session_state.get('custom_welcome_message', 'Hello! I\'m your AI assistant powered by OpenAI. How can I help you today?'),
            height=100,
            help="This message will be spoken and displayed when starting a new conversation"
        )
        
        if st.button("🔄 Reset to Default Welcome Message"):
            st.session_state.custom_welcome_message = "Hello! I'm your AI assistant powered by OpenAI. How can I help you today?"
            st.rerun()
    
    # Settings actions
    st.header("Settings Management")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("💾 Save Settings", type="primary"):
            st.success("✅ Settings saved successfully!")
            
    with col2:
        if st.button("🔄 Reset All Settings"):
            # Reset all settings to default
            settings_keys = [
                'ai_temperature', 'ai_max_tokens', 'ai_top_p', 'ai_model',
                'audio_sample_rate', 'silence_duration_to_stop', 'max_recording_time',
                'min_recording_time', 'calibration_duration', 'chunk_duration',
                'tts_model', 'tts_voice', 'tts_speed', 'whisper_model', 'whisper_language', 
                'custom_system_prompt', 'custom_welcome_message'
            ]
            for key in settings_keys:
                if key in st.session_state:
                    del st.session_state[key]
            
            # Reinitialize with defaults
            chatbot = SimpleChatbot()
            st.success("✅ All settings reset to defaults!")
            st.rerun()
            
    with col3:
        if st.button("🏠 Back to Chat"):
            st.session_state.current_page = "chat"
            st.rerun()
    
    # Display current settings summary
    with st.expander("📊 Current Settings Summary"):
        col1, col2 = st.columns(2)
        with col1:
            st.write("**AI Settings:**")
            st.write(f"- Model: {st.session_state.get('ai_model', 'gpt-3.5-turbo')}")
            st.write(f"- Temperature: {st.session_state.get('ai_temperature', 0.01)}")
            st.write(f"- Max Tokens: {st.session_state.get('ai_max_tokens', 2048)}")
            st.write(f"- Top P: {st.session_state.get('ai_top_p', 0.6)}")
            
            st.write("**Audio Settings:**")
            st.write(f"- Sample Rate: {st.session_state.get('audio_sample_rate', 48000)} Hz")
            st.write(f"- Silence Duration: {st.session_state.get('silence_duration_to_stop', 2.5)}s")
            st.write(f"- Max Recording: {st.session_state.get('max_recording_time', 30.0)}s")
            
        with col2:
            st.write("**Voice Settings:**")
            st.write(f"- TTS Model: {st.session_state.get('tts_model', 'tts-1')}")
            st.write(f"- Voice: {st.session_state.get('tts_voice', 'alloy')}")
            st.write(f"- Speech Speed: {st.session_state.get('tts_speed', 1.0)}x")
            st.write(f"- Language: {st.session_state.get('whisper_language', 'en')}")
            
            st.write("**Other Settings:**")
            st.write(f"- Min Recording: {st.session_state.get('min_recording_time', 1.0)}s")
            st.write(f"- Calibration: {st.session_state.get('calibration_duration', 3.0)}s")
            st.write(f"- Chunk Duration: {st.session_state.get('chunk_duration', 0.2)}s")
            
            welcome_preview = st.session_state.get('custom_welcome_message', 'Hello! I\'m your AI assistant...')[:50]
            if len(st.session_state.get('custom_welcome_message', '')) > 50:
                welcome_preview += "..."
            st.write(f"- Welcome Message: {welcome_preview}")

class SimpleChatbot:
    def __init__(self):
        self.is_recording = False
        self.is_playing = False
        self.interrupt_detected = False
        self.audio_queue = queue.Queue()
        self.interrupt_flag = threading.Event()
        self.conversation_active = threading.Event()
        self.recognizer = sr.Recognizer()
        self.say_process = None  # For macOS 'say' command process
        
        # Audio settings for sounddevice - Use dynamic sample rate
        self.SAMPLE_RATE = st.session_state.get('audio_sample_rate', 48000)
        self.CHANNELS = 1
        self.DTYPE = np.int16
        
        # Initialize pygame for audio playback with error handling for Docker
        self.pygame_available = False
        try:
            pygame.mixer.pre_init(frequency=22050, size=-16, channels=2, buffer=512)
            pygame.mixer.init()
            self.pygame_available = True
        except pygame.error as e:
            if "No such file or directory" in str(e) or "ALSA" in str(e):
                # Running in Docker or headless environment - audio playback disabled
                st.warning("🔇 Audio playback disabled (running in headless/Docker environment)")
                st.info("💡 TTS audio will be generated but not played. Use browser's built-in audio controls if needed.")
            else:
                st.error(f"Audio initialization failed: {e}")
        except Exception as e:
            st.warning(f"Audio system not available: {e}")
        
        # Initialize session state if not already done
        self._init_session_state()

    def _init_session_state(self):
        """Initialize session state variables safely"""
        if 'chat_history' not in st.session_state:
            st.session_state.chat_history = []
        if 'is_listening' not in st.session_state:
            st.session_state.is_listening = False
        if 'conversation_context' not in st.session_state:
            st.session_state.conversation_context = []
        if 'conversation_concluded' not in st.session_state:
            st.session_state.conversation_concluded = False
        if 'microphone_calibrated' not in st.session_state:
            st.session_state.microphone_calibrated = False
        if 'silence_threshold' not in st.session_state:
            st.session_state.silence_threshold = 0.01
        
        # Initialize configurable parameters with default values
        self._init_parameters()

    def _init_parameters(self):
        """Initialize configurable parameters in session state"""
        # AI Model Parameters
        if 'ai_temperature' not in st.session_state:
            st.session_state.ai_temperature = 0.01
        if 'ai_max_tokens' not in st.session_state:
            st.session_state.ai_max_tokens = 2048
        if 'ai_top_p' not in st.session_state:
            st.session_state.ai_top_p = 0.6
        if 'ai_model' not in st.session_state:
            st.session_state.ai_model = "gpt-3.5-turbo"
        
        # Audio Parameters
        if 'audio_sample_rate' not in st.session_state:
            st.session_state.audio_sample_rate = 48000
        if 'silence_duration_to_stop' not in st.session_state:
            st.session_state.silence_duration_to_stop = 2.5
        if 'max_recording_time' not in st.session_state:
            st.session_state.max_recording_time = 30.0
        if 'min_recording_time' not in st.session_state:
            st.session_state.min_recording_time = 1.0
        if 'calibration_duration' not in st.session_state:
            st.session_state.calibration_duration = 3.0
        if 'chunk_duration' not in st.session_state:
            st.session_state.chunk_duration = 0.2
        
        # TTS Parameters
        if 'tts_model' not in st.session_state:
            st.session_state.tts_model = "tts-1"
        if 'tts_voice' not in st.session_state:
            st.session_state.tts_voice = "alloy"
        if 'tts_speed' not in st.session_state:
            st.session_state.tts_speed = 1.0
        
        # Whisper Parameters
        if 'whisper_model' not in st.session_state:
            st.session_state.whisper_model = "whisper-1"
        if 'whisper_language' not in st.session_state:
            st.session_state.whisper_language = "en"
        
        # Custom System Prompt
        if 'custom_system_prompt' not in st.session_state:
            st.session_state.custom_system_prompt = """You are a helpful and friendly AI assistant.
You provide clear, concise, and helpful responses to user questions and requests.
Keep your responses conversational and engaging.

IMPORTANT: You must analyze the conversation flow and determine if this is a natural ending point. 
Consider ending the conversation when:
- User says goodbye, farewell, or dismissal phrases
- User expresses gratitude and seems satisfied with help received
- The conversation has reached a natural conclusion
- User indicates they are done or have no more questions
- The task or question has been fully completed and user seems content"""
        
        # Custom Welcome Message
        if 'custom_welcome_message' not in st.session_state:
            st.session_state.custom_welcome_message = "Hello! I'm your AI assistant powered by OpenAI. How can I help you today?"
            
        if 'microphone_calibrated' not in st.session_state:
            st.session_state.microphone_calibrated = False
        if 'silence_threshold' not in st.session_state:
            st.session_state.silence_threshold = None

    def get_chatbot_response(self, user_input):
        """Get response from LLM with simple chatbot persona"""
        
        # Build conversation context (last 6 exchanges for better performance)
        context = "\n".join([f"{msg['role']}: {msg['content']}" for msg 
                            in st.session_state.conversation_context[-6:]])
        
        # Use custom system prompt from settings
        system_prompt = st.session_state.get('custom_system_prompt', '')
        
        chatbot_prompt = f"""{system_prompt}

Previous conversation context:
{context}

Current user input: {user_input}

Respond naturally and helpfully. You MUST respond in this exact JSON format:
{{
    "response": "your helpful response here",
    "end_conversation": false
}}

Set "end_conversation" to true ONLY when you determine this is a natural ending point for the conversation.
If ending the conversation, make your response a warm, appropriate farewell.
"""
        
        try:
            response = get_response(chatbot_prompt)
            
            if response.status_code == 200:
                response_data = json.loads(response.text)
                
                if 'prediction' in response_data:
                    # The prediction contains the JSON string from OpenAI
                    prediction_str = response_data['prediction']
                    
                    try:
                        # Parse the JSON response from OpenAI
                        prediction_data = json.loads(prediction_str)
                        
                        # Extract the response and end_conversation flag
                        if isinstance(prediction_data, dict):
                            ai_response = prediction_data.get('response', '').strip()
                            end_conversation = prediction_data.get('end_conversation', False)
                            
                            # Set the conversation concluded flag if LLM decided to end
                            if end_conversation:
                                st.session_state.conversation_concluded = True
                            
                            return ai_response if ai_response else "I'm here to help. What can I assist you with?"
                        elif isinstance(prediction_data, str):
                            return prediction_data.strip()
                        else:
                            # If it's not in expected format, return the raw content
                            return str(prediction_data).strip()
                            
                    except json.JSONDecodeError:
                        # If prediction is not valid JSON, return it as is
                        return prediction_str.strip() if isinstance(prediction_str, str) else str(prediction_str)
                        
                else:
                    return "I'm experiencing some technical difficulties. Please try again."
            else:
                return "I'm here to help. What can I assist you with?"
            
        except json.JSONDecodeError as e:
            try:
                # Try to get raw response text
                raw_text = response.text.strip() if hasattr(response, 'text') else str(response)
                if raw_text and len(raw_text) > 10:
                    return raw_text
                else:
                    return "I'm experiencing some technical difficulties, but I'm here to help."
            except:
                return "I'm here to help. Please try again."
        except Exception as e:
            st.error(f"Response error: {e}")
            return "I'm experiencing some technical difficulties, but I'm here to help you."

    def text_to_speech_openai(self, text):
        """Text-to-speech using OpenAI TTS API with interruption capability"""
        try:
            # Reset interrupt flag
            self.interrupt_flag.clear()
            
            # Clean text for speech (remove special characters that might cause issues)
            clean_text = text.replace('"', '').replace("'", "").replace('\n', ' ')
            
            # Call OpenAI TTS API with dynamic parameters
            tts_model = st.session_state.get('tts_model', 'tts-1')
            tts_voice = st.session_state.get('tts_voice', 'alloy')
            tts_speed = st.session_state.get('tts_speed', 1.0)
            
            response = client.audio.speech.create(
                model=tts_model,  # Dynamic model
                voice=tts_voice,  # Dynamic voice
                input=clean_text,
                speed=tts_speed  # Dynamic speech speed
            )
            
            # Save audio to temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as tmp_file:
                tmp_file_path = tmp_file.name
                
            # Write audio content to file
            response.stream_to_file(tmp_file_path)
            
            try:
                if self.pygame_available:
                    # Load and play audio using pygame
                    pygame.mixer.music.load(tmp_file_path)
                    pygame.mixer.music.play()
                    
                    # Monitor for interruptions during playback
                    while pygame.mixer.music.get_busy():
                        if self.interrupt_flag.is_set():
                            pygame.mixer.music.stop()
                            st.info("🟡 Interrupted - I'm listening...")
                            break
                        time.sleep(0.05)  # Check every 50ms
                else:
                    # Docker/headless mode - provide audio file download option
                    st.success("🔊 TTS audio generated successfully")
                    with open(tmp_file_path, "rb") as audio_file:
                        audio_bytes = audio_file.read()
                        st.audio(audio_bytes, format="audio/mp3")
                    st.info("🎵 Use the audio player above to hear the response")
                    
            finally:
                # Clean up temporary file
                try:
                    os.unlink(tmp_file_path)
                except:
                    pass
                
        except Exception as e:
            # OpenAI TTS failed - show error and continue without voice output
            st.error(f"⚠️ Text-to-speech failed: {e}")
            st.info("� Response will be shown as text only. Please check your OpenAI API key and connection.")

    def speech_to_text_openai(self, audio_file_path):
        """Speech recognition using OpenAI Whisper API"""
        try:
            # Use dynamic Whisper parameters
            whisper_model = st.session_state.get('whisper_model', 'whisper-1')
            whisper_language = st.session_state.get('whisper_language', 'en')
            
            with open(audio_file_path, "rb") as audio_file:
                transcript = client.audio.transcriptions.create(
                    model=whisper_model,
                    file=audio_file,
                    language=whisper_language  # Dynamic language setting
                )
            return transcript.text.strip() if transcript.text else None
            
        except Exception as e:
            st.warning(f"OpenAI Whisper failed: {e}. Trying speech_recognition fallback...")
            
            # Fallback to speech_recognition library
            try:
                with sr.AudioFile(audio_file_path) as source:
                    self.recognizer.adjust_for_ambient_noise(source, duration=0.2)
                    audio = self.recognizer.record(source)
                    
                # Try offline Sphinx as last resort
                try:
                    text = self.recognizer.recognize_sphinx(audio)
                    st.success(f"🟢 Speech recognized via Sphinx fallback: '{text}'")
                    return text
                except sr.UnknownValueError:
                    st.error("Could not understand audio with any method")
                    return None
                except sr.RequestError as e:
                    st.error(f"Sphinx error: {e}")
                    return None
                    
            except Exception as fallback_error:
                st.error(f"All speech recognition methods failed: {fallback_error}")
                return None

    def calibrate_silence_threshold(self):
        """Calibrate the silence threshold based on ambient noise"""
        try:
            # Check if we're in a Docker/headless environment
            try:
                # Test if audio input is available
                test_chunk = sd.rec(
                    int(0.1 * self.SAMPLE_RATE),
                    samplerate=self.SAMPLE_RATE,
                    channels=self.CHANNELS,
                    dtype=np.float32
                )
                sd.wait()
            except Exception as audio_error:
                st.warning("🔇 Audio input not available (Docker/headless environment)")
                st.info("📝 Using default threshold for text-only mode")
                return 50  # Default threshold for Docker environment
            
            st.info("🔧 Calibrating microphone... Please stay quiet for 3 seconds")
            
            # Use dynamic calibration parameters
            calibration_duration = st.session_state.get('calibration_duration', 3.0)
            chunk_duration = st.session_state.get('chunk_duration', 0.2)
            chunk_size = int(chunk_duration * self.SAMPLE_RATE)
            chunks_needed = int(calibration_duration / chunk_duration)
            
            ambient_levels = []
            
            for i in range(chunks_needed):
                chunk = sd.rec(
                    chunk_size,
                    samplerate=self.SAMPLE_RATE,
                    channels=self.CHANNELS,
                    dtype=np.float32
                )
                sd.wait()
                
                volume = np.sqrt(np.mean(chunk**2)) * 10000
                ambient_levels.append(volume)
                
            ambient_levels_sorted = sorted(ambient_levels)
            filtered_levels = ambient_levels_sorted[len(ambient_levels)//5:-len(ambient_levels)//5] or ambient_levels
            
            avg_ambient = np.mean(filtered_levels)
            max_ambient = np.max(filtered_levels)
            
            threshold = max(avg_ambient * 4.0, max_ambient * 2.5, 20)
            threshold = min(threshold, 200)
            
            st.success(f"🟢 Calibration complete! Threshold set to {threshold:.0f}")
            return threshold
            
        except Exception as e:
            st.warning(f"Calibration failed: {e}. Using conservative threshold of 50.")
            return 50

    def record_audio_continuous(self):
        """Record audio continuously without buffering issues"""
        try:
            # Calibrate the microphone only once per session
            if not st.session_state.microphone_calibrated:
                st.session_state.silence_threshold = self.calibrate_silence_threshold()
                st.session_state.microphone_calibrated = True
                
            silence_threshold = st.session_state.silence_threshold
            
            st.info("🔴 Recording started – Speak naturally!")
            
            # Audio recording parameters - use dynamic values
            silence_duration_to_stop = st.session_state.get('silence_duration_to_stop', 2.5)
            max_recording_time = st.session_state.get('max_recording_time', 30.0)
            min_recording_time = st.session_state.get('min_recording_time', 1.0)
            
            # Create progress indicators
            status_text = st.empty()
            volume_bar = st.progress(0)
            
            # Initialize recording variables with smoothing
            all_audio_data = []
            recording = True
            speech_detected = False
            silence_start_time = None
            start_time = time.time()
            volume_history = []
            
            # Start continuous recording stream
            def audio_callback(indata, frames, time_info, status):
                if status:
                    print(f"Audio callback status: {status}")
                all_audio_data.append(indata.copy())
                
            # Start the audio stream
            with sd.InputStream(
                callback=audio_callback,
                channels=self.CHANNELS,
                samplerate=self.SAMPLE_RATE,
                dtype=np.float32,
                blocksize=2048,
                latency='low'
            ):
                
                while recording:
                    current_time = time.time()
                    elapsed_time = current_time - start_time
                    
                    # Check if we have audio data to analyze
                    if len(all_audio_data) > 0:
                        recent_chunks = all_audio_data[-10] if len(all_audio_data) >= 10 else all_audio_data
                        recent_audio = np.concatenate(recent_chunks)
                        
                        current_volume = float(np.sqrt(np.mean(recent_audio**2)) * 10000)
                        volume_history.append(current_volume)
                        if len(volume_history) > 5:
                            volume_history.pop(0)
                            
                        volume = float(np.mean(volume_history))
                        volume_normalized = float(min(volume / 200, 1.0))
                        
                        if len(volume_history) % 3 == 0:
                            volume_bar.progress(volume_normalized)
                        
                        # Check if this is speech or silence
                        speech_threshold = silence_threshold
                        silence_threshold_lower = silence_threshold * 0.7
                        
                        if volume > speech_threshold and not speech_detected:
                            speech_detected = True
                            silence_start_time = None
                            status_text.text(f"🔴 Recording... (elapsed_time:.1f)s - SPEECH DETECTED!")
                        elif volume < silence_threshold_lower and speech_detected:
                            if silence_start_time is None:
                                silence_start_time = current_time
                                
                            silence_duration = current_time - silence_start_time
                            status_text.text(f"🟡 Silence detected... {silence_duration:.1f}s / {silence_duration_to_stop:.1f}s")
                            
                            if silence_duration >= silence_duration_to_stop and elapsed_time >= min_recording_time:
                                status_text.text(f"🟢 Finished speaking detected!")
                                recording = False
                                break
                        elif speech_detected and volume >= silence_threshold_lower:
                            silence_start_time = None
                            status_text.text(f"🔴 Recording... (elapsed_time:.1f)s - Speaking...")
                        else:
                            status_text.text(f"🔴 Waiting for speech... (elapsed_time:.1f)s")
                        
                    if elapsed_time >= max_recording_time:
                        st.warning(f"🔴 Maximum recording time reached")
                        recording = False
                        break
                        
                    time.sleep(0.1)
                    
            # Clear progress indicators
            status_text.empty()
            volume_bar.empty()
            
            if not speech_detected:
                st.error(f"🔴 No speech detected. Please speak louder or check your microphone.")
                return None
                
            if len(all_audio_data) == 0:
                st.error("No audio data captured")
                return None
            
            # Combine all audio chunks into final audio
            final_audio = np.concatenate(all_audio_data)
            final_audio_int16 = (final_audio * 32767).astype(np.int16)
            
            st.success(f"🟢 Recording complete! Captured {len(final_audio)/self.SAMPLE_RATE:.1f} seconds")
            return final_audio_int16
            
        except Exception as e:
            st.error(f"Recording error: {e}")
            return None

    def listen_for_speech_sounddevice(self):
        """Speech recognition using continuous recording with OpenAI Whisper"""
        try:
            audio_data = self.record_audio_continuous()
            
            if audio_data is None:
                return None
                
            st.info("🟢 Processing speech with OpenAI Whisper...")
            
            # Create temporary WAV file
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
                target_sample_rate = 16000
                downsample_factor = self.SAMPLE_RATE // target_sample_rate
                
                if downsample_factor > 1:
                    downsampled_audio = audio_data[::downsample_factor]
                    effective_sample_rate = target_sample_rate
                else:
                    downsampled_audio = audio_data
                    effective_sample_rate = self.SAMPLE_RATE
                    
                sf.write(
                    tmp_file.name,
                    downsampled_audio,
                    effective_sample_rate,
                    subtype='PCM_16'
                )
                
            try:
                # Use OpenAI Whisper for speech recognition
                text = self.speech_to_text_openai(tmp_file.name)
                
                # Clean up temporary file
                os.unlink(tmp_file.name)
                
                if text and len(text.strip()) > 0:
                    st.success(f"🟢 Speech recognized: '{text}'")
                    return text.strip()
                else:
                    st.warning("No text was extracted from the audio")
                    return None
                    
            except Exception as recognition_error:
                st.error(f"Recognition processing error: {recognition_error}")
                try:
                    os.unlink(tmp_file.name)
                except:
                    pass
                return None
                return None
                
        except Exception as e:
            st.error(f"Listening error: {e}")
            return None

    def run_conversation_session(self):
        """Run the conversation session"""
        # Welcome message - use custom welcome message from settings
        welcome_msg = st.session_state.get('custom_welcome_message', "Hello! I'm your AI assistant powered by OpenAI. How can I help you today?")
        st.session_state.chat_history.append({
            "role": "assistant",
            "content": welcome_msg,
            "timestamp": datetime.now()
        })
        st.session_state.conversation_context.append({"role": "assistant", "content": welcome_msg})
        
        # Play welcome message
        self.text_to_speech_openai(welcome_msg)
    
        
        # Main conversation loop
        silence_count = 0
        
        while st.session_state.is_listening:
            st.info("🟢 Ready to listen – Please speak now...")
            
            # Listen for user input
            user_input = self.listen_for_speech_sounddevice()
            
            if user_input:
                silence_count = 0
            
            # Add user input to chat history
            st.session_state.chat_history.append({
                "role": "user",
                "content": user_input,
                "timestamp": datetime.now()
            })
            st.session_state.conversation_context.append({"role": "user", "content": user_input})
            
            st.success(f"You said: {user_input}")
            
            # Get chatbot response (includes automatic conclusion detection)
            with st.spinner("Thinking..."):
                response = self.get_chatbot_response(user_input)
                
            # Add response to chat history
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": response,
                "timestamp": datetime.now()
            })
            st.session_state.conversation_context.append({"role": "assistant", "content": response})
            
            st.info(f"Assistant: {response}")
            
            # Speak the response
            self.text_to_speech_openai(response)
            
            # Check if conversation was concluded by the AI's analysis
            if st.session_state.conversation_concluded:
                st.session_state.is_listening = False
                st.success("🎉 Conversation concluded naturally. Thank you for chatting!")
                break
            
        else:
            silence_count += 1
            if silence_count >= 2:
                prompt_msg = "I'm still here. Feel free to speak when you're ready."
                st.info(prompt_msg)
                self.text_to_speech_openai(prompt_msg)
                silence_count = 0
            elif silence_count == 1:
                st.warning("I didn't catch that. Please try speaking again.")
                
    st.success("Voice conversation session completed.")

    def start_conversation_loop(self):
        """Start voice conversation controls"""
        
        # Don't show voice controls if conversation is concluded
        if st.session_state.get('conversation_concluded', False):
            return
            
        col1, col2 = st.columns(2)
        
        with col1:
            # Adjust button text based on environment
            button_text = "🔴 Start Voice Chat" if self.pygame_available else "🔴 Try Voice Chat (Limited)"
            button_help = None if self.pygame_available else "Voice features may be limited in Docker/headless environment"
            
            if st.button(button_text, type="primary", use_container_width=True, help=button_help):
                if not self.pygame_available:
                    st.warning("⚠️ Running in Docker/headless mode - voice features may be limited")
                    st.info("💡 Consider using text input below for full functionality")
                
                st.session_state.is_listening = True
                st.success("🟢 Voice conversation started!")
                
                try:
                    self.run_conversation_session()
                except Exception as e:
                    st.error(f"Conversation error: {e}")
                    if "audio" in str(e).lower() or "alsa" in str(e).lower():
                        st.info("💡 This appears to be an audio-related error. Try using text input instead.")
                    st.session_state.is_listening = False
                    
        with col2:
            if st.button("🛑 Stop Chat", use_container_width=True):
                st.session_state.is_listening = False
                self.interrupt_flag.set()
                st.success("Conversation stopped")

def main():
    st.set_page_config(
        page_title="Simple Voice Chatbot - Full OpenAI",
        page_icon="🗣",
        layout="centered"
    )
    
    # Initialize page state
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "chat"
    
    # Page navigation
    if st.session_state.current_page == "settings":
        show_settings_page()
        return
    
    # Simple CSS
    st.markdown("""
    <style>
    .user-message {
        background-color: #e3f2fd;
        padding: 10px;
        border-radius: 10px;
        margin: 5px 0;
        border-left: 4px solid #2196f3;
    }
    .assistant-message {
        background-color: #f3e5f5;
        padding: 10px;
        border-radius: 10px;
        margin: 5px 0;
        border-left: 4px solid #9c27b0;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Header with settings button
    col1, col2 = st.columns([3, 1])
    with col1:
        st.title("🗣 Simple Voice Chatbot - Full OpenAI")
        st.write("🎧 A clean, simple voice-enabled chatbot interface powered "
                 "entirely by OpenAI (ChatGPT + Whisper + TTS)!")
    with col2:
        st.write("")  # Spacer
        if st.button("⚙️ Settings", use_container_width=True):
            st.session_state.current_page = "settings"
            st.rerun()
    
    # Display the services being used with current settings
    model = st.session_state.get('ai_model', 'gpt-3.5-turbo')
    tts_model = st.session_state.get('tts_model', 'tts-1')
    tts_voice = st.session_state.get('tts_voice', 'alloy')
    tts_speed = st.session_state.get('tts_speed', 1.0)
    whisper_model = st.session_state.get('whisper_model', 'whisper-1')
    
    st.info(f"🔧 **Current Configuration:**\n"
            f"- **Chat:** {model}\n"
            f"- **Speech Recognition:** {whisper_model}\n" 
            f"- **Text-to-Speech:** {tts_model} ({tts_voice} voice, {tts_speed}x speed)")
    
    # Initialize chatbot
    chatbot = SimpleChatbot()
    
    # Show Docker/headless environment notice if applicable
    if not chatbot.pygame_available:
        st.info("🐳 **Docker/Headless Mode Detected**\n"
                "- Voice input may not be available\n"
                "- TTS audio will be provided via built-in browser player\n"
                "- Use text input below for full functionality")
    
    # Status indicator with conversation conclusion check
    if st.session_state.get('conversation_concluded', False):
        st.success("✅ Conversation completed naturally")
        # Add restart option
        if st.button("🔄 Start New Conversation", type="primary", use_container_width=True):
            st.session_state.conversation_concluded = False
            st.session_state.chat_history = []
            st.session_state.conversation_context = []
            st.rerun()
    elif st.session_state.is_listening:
        st.success("🟢 Voice chat active")
    else:
        st.info("🔴 Voice chat ready")
        
    # Voice conversation controls
    chatbot.start_conversation_loop()
    
    # Clear button
    if st.button("🗑 Clear Chat", use_container_width=True):
        st.session_state.chat_history = []
        st.session_state.conversation_context = []
        st.session_state.conversation_concluded = False
        st.rerun()
        st.session_state.is_listening = False
        st.success("Chat history cleared")
        st.rerun()
        
    st.markdown("---")
    
    # Chat history display
    st.subheader("📝 Conversation")
    
    if st.session_state.chat_history:
        for message in st.session_state.chat_history[-10:]:  # Show last 10 messages
            if message["role"] == "user":
                st.markdown(f"""
                <div class="user-message">
                <strong>You:</strong> {message["content"]}<br>
                <small>🕐 {message["timestamp"].strftime("%H:%M:%S")}</small>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="assistant-message">
                <strong>Assistant:</strong> {message["content"]}<br>
                <small>🕐 {message["timestamp"].strftime("%H:%M:%S")}</small>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.info("🟡 Start a voice conversation or type a message below to begin!")
        
    st.markdown("---")
    
    # Text input as backup
    st.subheader("📝 Text Input")
    user_text = st.text_input("Type your message:",
                             placeholder="Type here if voice isn't working...")
                             
    col_send, col_speak = st.columns(2)
    
    with col_send:
        if st.button("📤 Send", use_container_width=True) and user_text:
            # Process text input
            st.session_state.chat_history.append({
                "role": "user",
                "content": user_text,
                "timestamp": datetime.now()
            })
            st.session_state.conversation_context.append({"role": "user", "content": user_text})
            
            # Get chatbot response
            response = chatbot.get_chatbot_response(user_text)
            
            # Add response to history
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": response,
                "timestamp": datetime.now()
            })
            st.session_state.conversation_context.append({"role": "assistant", "content": response})
            
            st.rerun()
            
    with col_speak:
        if st.button("🔊 Speak Last Response", use_container_width=True) and st.session_state.chat_history:
            last_response = st.session_state.chat_history[-1]
            if last_response["role"] == "assistant":
                chatbot.text_to_speech_openai(last_response["content"])

if __name__ == "__main__":
    main()

import streamlit as st
import threading
import time
import json
import tempfile
import os
from dotenv import load_dotenv
from datetime import datetime
import queue
import numpy as np

# Import OpenAI for ChatGPT integration
import openai
from openai import OpenAI

# Audio libraries - with Docker compatibility
try:
    import sounddevice as sd
    import soundfile as sf
    import pygame
    import speech_recognition as sr
    AUDIO_AVAILABLE = True
except ImportError:
    # Running in Docker or audio libraries not available
    AUDIO_AVAILABLE = False
    st.warning("🐳 Running in Docker mode - Audio libraries not available. Using text-only mode.")

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
    
    if not AUDIO_AVAILABLE:
        st.warning("🐳 **Docker Mode**: Audio libraries not available. Only text-based chat is supported.")
    
    # Create tabs for different setting categories
    tab1, tab2 = st.tabs(["🤖 AI Settings", "📝 Customization"])
    
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
            help="This message will be displayed when starting a new conversation"
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

class SimpleChatbot:
    def __init__(self):
        self.is_recording = False
        self.is_playing = False
        self.interrupt_detected = False
        self.audio_queue = queue.Queue()
        self.interrupt_flag = threading.Event()
        self.conversation_active = threading.Event()
        
        if AUDIO_AVAILABLE:
            self.recognizer = sr.Recognizer()
            # Audio settings for sounddevice
            self.SAMPLE_RATE = 48000
            self.CHANNELS = 1
            self.DTYPE = np.int16
            
            try:
                # Initialize pygame for audio playback
                pygame.mixer.pre_init(frequency=22050, size=-16, channels=2, buffer=512)
                pygame.mixer.init()
            except:
                st.warning("Audio playback initialization failed - text-only mode")
        
        # Initialize session state if not already done
        self._init_session_state()

    def _init_session_state(self):
        """Initialize session state variables safely"""
        if 'chat_history' not in st.session_state:
            st.session_state.chat_history = []
        if 'conversation_context' not in st.session_state:
            st.session_state.conversation_context = []
        if 'conversation_concluded' not in st.session_state:
            st.session_state.conversation_concluded = False
        
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
        """Text-to-speech using OpenAI TTS API - Docker compatible"""
        if not AUDIO_AVAILABLE:
            st.info("🔊 **Audio Response**: " + text)
            return
            
        try:
            # Clean text for speech
            clean_text = text.replace('"', '').replace("'", "").replace('\n', ' ')
            
            # Call OpenAI TTS API
            response = client.audio.speech.create(
                model="tts-1",
                voice="alloy",
                input=clean_text,
                speed=1.0
            )
            
            # Save audio to temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as tmp_file:
                tmp_file_path = tmp_file.name
                
            # Write audio content to file
            response.stream_to_file(tmp_file_path)
            
            try:
                # Load and play audio using pygame
                pygame.mixer.music.load(tmp_file_path)
                pygame.mixer.music.play()
                
                # Wait for playback to finish
                while pygame.mixer.music.get_busy():
                    time.sleep(0.05)
                    
            finally:
                # Clean up temporary file
                try:
                    os.unlink(tmp_file_path)
                except:
                    pass
                
        except Exception as e:
            st.info("🔊 **Audio Response**: " + text)
            st.warning(f"Text-to-speech not available: {e}")

def main():
    st.set_page_config(
        page_title="AI Voice Chatbot - Docker Ready",
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
        st.title("🗣 AI Voice Chatbot - Docker Ready")
        if AUDIO_AVAILABLE:
            st.write("🎧 Full voice-enabled chatbot with OpenAI integration!")
        else:
            st.write("💬 Text-based chatbot powered by OpenAI - Perfect for Docker deployment!")
    with col2:
        st.write("")  # Spacer
        if st.button("⚙️ Settings", use_container_width=True):
            st.session_state.current_page = "settings"
            st.rerun()
    
    # Display current mode
    if AUDIO_AVAILABLE:
        st.info("🔧 **Full Mode**: Voice input/output + Text chat available")
    else:
        st.info("🐳 **Docker Mode**: Text-only chat (Audio libraries not available in container)")
    
    # Initialize chatbot
    chatbot = SimpleChatbot()
    
    # Status indicator
    if st.session_state.get('conversation_concluded', False):
        st.success("✅ Conversation completed naturally")
        if st.button("🔄 Start New Conversation", type="primary", use_container_width=True):
            st.session_state.conversation_concluded = False
            st.session_state.chat_history = []
            st.session_state.conversation_context = []
            st.rerun()
    
    # Voice controls (only show if audio is available)
    if AUDIO_AVAILABLE and not st.session_state.get('conversation_concluded', False):
        st.subheader("🎤 Voice Controls")
        st.warning("⚠️ Voice features require microphone access and may not work in Docker containers")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔴 Start Voice Chat", type="primary", use_container_width=True):
                st.info("Voice chat functionality requires local deployment")
        with col2:
            if st.button("🛑 Stop Chat", use_container_width=True):
                st.info("Voice chat stopped")
    
    # Clear button
    if st.button("🗑 Clear Chat", use_container_width=True):
        st.session_state.chat_history = []
        st.session_state.conversation_context = []
        st.session_state.conversation_concluded = False
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
        welcome_msg = st.session_state.get('custom_welcome_message', "Hello! I'm your AI assistant powered by OpenAI. How can I help you today?")
        st.info(f"🤖 {welcome_msg}")
        
    st.markdown("---")
    
    # Text input
    st.subheader("💬 Text Chat")
    user_text = st.text_input("Type your message:", placeholder="Ask me anything...")
                             
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
            with st.spinner("Thinking..."):
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
        if st.button("🔊 Speak Response", use_container_width=True) and st.session_state.chat_history:
            last_response = st.session_state.chat_history[-1]
            if last_response["role"] == "assistant":
                chatbot.text_to_speech_openai(last_response["content"])

if __name__ == "__main__":
    main()
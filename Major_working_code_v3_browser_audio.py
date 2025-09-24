# Browser-Based Audio Voice Chatbot
# This version uses browser APIs for audio instead of system audio
# Perfect for Docker deployment on any platform

import streamlit as st
import tempfile
import time
import json
import os
from dotenv import load_dotenv
from datetime import datetime
import numpy as np
from io import BytesIO
import base64

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

# Browser-based audio recording component
def audio_recorder_component():
    """Create a browser-based audio recorder using Streamlit's audio_input"""
    st.write("🎤 **Voice Input**")
    
    # Use Streamlit's built-in audio input
    audio_bytes = st.audio_input("Record your voice message")
    
    if audio_bytes:
        # Save the audio bytes to a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_file:
            tmp_file.write(audio_bytes.getvalue())
            return tmp_file.name
    
    return None

def speech_to_text_openai(audio_file_path):
    """Speech recognition using OpenAI Whisper API"""
    try:
        with open(audio_file_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language="en"
            )
        return transcript.text.strip() if transcript.text else None
    except Exception as e:
        st.error(f"Speech recognition failed: {e}")
        return None

def text_to_speech_openai(text):
    """Text-to-speech using OpenAI TTS API with browser playback"""
    try:
        response = client.audio.speech.create(
            model="tts-1",
            voice="alloy",
            input=text,
            speed=1.0
        )
        
        # Create audio data for browser playback
        audio_data = response.content
        
        # Convert to base64 for browser playback
        audio_base64 = base64.b64encode(audio_data).decode()
        
        # Create HTML audio player that auto-plays
        audio_html = f"""
        <audio autoplay>
            <source src="data:audio/mp3;base64,{audio_base64}" type="audio/mp3">
            Your browser does not support the audio element.
        </audio>
        """
        
        # Display the audio player
        st.markdown("🔊 **AI Response Audio:**")
        st.markdown(audio_html, unsafe_allow_html=True)
        
    except Exception as e:
        st.error(f"Text-to-speech failed: {e}")

def get_chatbot_response(user_input, conversation_history):
    """Get response from OpenAI ChatGPT"""
    try:
        # Build conversation context
        messages = [
            {"role": "system", "content": "You are a helpful and friendly AI assistant. Keep responses conversational and concise."}
        ]
        
        # Add conversation history (last 6 exchanges)
        for msg in conversation_history[-6:]:
            messages.append({"role": msg["role"], "content": msg["content"]})
        
        # Add current user input
        messages.append({"role": "user", "content": user_input})
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            temperature=0.7,
            max_tokens=500
        )
        
        return response.choices[0].message.content.strip()
        
    except Exception as e:
        st.error(f"ChatGPT API error: {e}")
        return "I'm sorry, I encountered an error. Please try again."

def main():
    st.set_page_config(
        page_title="Browser-Based Voice Chatbot",
        page_icon="🎙️",
        layout="centered"
    )
    
    st.title("🎙️ Browser-Based Voice Chatbot")
    st.write("🌐 **Docker-Compatible Voice Chat with Browser Audio**")
    
    st.info("💡 This version uses your browser's built-in audio capabilities, making it perfect for Docker deployment!")
    
    # Initialize session state
    if 'conversation_history' not in st.session_state:
        st.session_state.conversation_history = []
    
    # Two columns for input methods
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🎤 Voice Input")
        
        # Browser-based audio recording
        audio_file = audio_recorder_component()
        
        if audio_file and st.button("🎯 Process Voice", type="primary"):
            with st.spinner("🔄 Converting speech to text..."):
                user_text = speech_to_text_openai(audio_file)
                
            if user_text:
                st.success(f"📝 You said: **{user_text}**")
                
                # Add to conversation history
                st.session_state.conversation_history.append({
                    "role": "user",
                    "content": user_text,
                    "timestamp": datetime.now(),
                    "type": "voice"
                })
                
                # Get AI response
                with st.spinner("🤖 Generating response..."):
                    ai_response = get_chatbot_response(user_text, st.session_state.conversation_history)
                
                # Add AI response to history
                st.session_state.conversation_history.append({
                    "role": "assistant",
                    "content": ai_response,
                    "timestamp": datetime.now(),
                    "type": "text"
                })
                
                st.success(f"🤖 AI: **{ai_response}**")
                
                # Generate and play audio response
                text_to_speech_openai(ai_response)
                
                # Clean up temporary file
                try:
                    os.unlink(audio_file)
                except:
                    pass
                
                st.rerun()
    
    with col2:
        st.subheader("⌨️ Text Input")
        
        # Text input as alternative
        user_text_input = st.text_area(
            "Type your message:",
            placeholder="Type here if voice input isn't working...",
            height=100
        )
        
        if st.button("📤 Send Text", type="primary") and user_text_input:
            # Add to conversation history
            st.session_state.conversation_history.append({
                "role": "user",
                "content": user_text_input,
                "timestamp": datetime.now(),
                "type": "text"
            })
            
            # Get AI response
            with st.spinner("🤖 Generating response..."):
                ai_response = get_chatbot_response(user_text_input, st.session_state.conversation_history)
            
            # Add AI response to history
            st.session_state.conversation_history.append({
                "role": "assistant",
                "content": ai_response,
                "timestamp": datetime.now(),
                "type": "text"
            })
            
            st.success(f"🤖 AI: **{ai_response}**")
            
            # Generate and play audio response
            text_to_speech_openai(ai_response)
            
            st.rerun()
    
    # Clear conversation button
    st.markdown("---")
    if st.button("🗑️ Clear Conversation"):
        st.session_state.conversation_history = []
        st.rerun()
    
    # Display conversation history
    st.markdown("---")
    st.subheader("💬 Conversation History")
    
    if st.session_state.conversation_history:
        for i, msg in enumerate(st.session_state.conversation_history[-10:]):  # Show last 10 messages
            timestamp = msg["timestamp"].strftime("%H:%M:%S")
            msg_type = "🎤" if msg.get("type") == "voice" else "⌨️"
            
            if msg["role"] == "user":
                st.markdown(f"""
                <div style="background-color: #e3f2fd; padding: 10px; border-radius: 10px; margin: 5px 0; border-left: 4px solid #2196f3;">
                <strong>{msg_type} You ({timestamp}):</strong><br>{msg["content"]}
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style="background-color: #f3e5f5; padding: 10px; border-radius: 10px; margin: 5px 0; border-left: 4px solid #9c27b0;">
                <strong>🤖 Assistant ({timestamp}):</strong><br>{msg["content"]}
                </div>
                """, unsafe_allow_html=True)
    else:
        st.info("🔄 Start a conversation by using voice input or typing a message!")
    
    # Docker deployment info
    st.markdown("---")
    st.markdown("### 🐳 Docker Deployment Ready!")
    st.info("""
    ✅ **This version is optimized for Docker deployment:**
    - Uses browser-based audio recording (no system audio devices needed)
    - Browser handles audio playback automatically  
    - Works on Windows, Mac, and Linux Docker hosts
    - No special audio device configuration required
    """)

if __name__ == "__main__":
    main()
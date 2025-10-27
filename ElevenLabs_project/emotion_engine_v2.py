import pygame
import io
import time  # For controlling playback flow
import os
from dotenv import load_dotenv 
from elevenlabs.client import ElevenLabs 
from elevenlabs import Voice 

# -------------------------------------------------------------
# 2. CONFIGURATION (The Architect's Parameters)

# Load variables from the .env file (Requires: pip3 install python-dotenv)
# Ensure you have a file named '.env' in your project folder with:
# ELEVENLABS_API_KEY=YOUR_ACTUAL_API_KEY_HERE
#load_dotenv() 
#API_KEY = os.getenv("ELEVENLABS_API_KEY") 

#if not API_KEY:
#    raise ValueError("ELEVENLABS_API_KEY not found in .env file.")
API_KEY = "sk_0cdf46dd659d5f29a25d816745c8565a06b9540ef6698dd5" # TEST LINE
VOICE_ID = "JBKXQq8eu7bjrKXhy7MD" # Example voice ID
MODEL_ID = "eleven_multilingual_v2" # Recommended high-quality model

# NEW: Map emotional scores to music files (The Mythic Layer)
# !!! You MUST create and place these three .mp3 files in the project folder !!!
MUSIC_ASSETS = {
    "Heroic Climax": "heroic_climax.mp3",
    "Tense Stealth": "tense_stealth.mp3",
    "Somber Sacrifice": "somber_sacrifice.mp3",
}

# Initialize the ElevenLabs client
client = ElevenLabs(api_key=API_KEY) 

# -------------------------------------------------------------

def initialize_audio_engine():
    """Initializes Pygame and its mixer for audio playback."""
    try:
        pygame.init()
        # Initialize the mixer with standard high-quality audio parameters
        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
        print("✅ Pygame Audio Mixer Initialized.")
        return True
    except pygame.error as e:
        print(f"❌ Error initializing Pygame mixer. Check system audio or drivers: {e}")
        return False

def generate_and_play_scene(dialogue_text, emotional_score):
    """Generates audio via the corrected SDK method and plays it using Pygame,
    concurrently with the background music score."""
    
    # 1. Start the Background Music
    music_file = MUSIC_ASSETS.get(emotional_score)
    if music_file:
        try:
            # Use mixer.music.load() for long background tracks
            pygame.mixer.music.load(music_file)
            # Play the music once (loops=0)
            pygame.mixer.music.play(loops=0) 
            print(f"🎵 Playing background score: '{emotional_score}'...")
        except pygame.error as e:
            print(f"⚠️ Warning: Could not load music file '{music_file}'. Ensure file exists: {e}")
            
    print(f"🎙️ Generating dialogue for '{emotional_score}'...")
    
    # 2. ELEVENLABS GENERATION (The Corrected SDK Call)
    try:
        # THE SYNTAX ERROR IS FIXED HERE: The final ')' is present.
        # The correct method for the current SDK version returns a generator (stream)
        audio_data_generator = client.text_to_speech.convert(
            text=dialogue_text,
            voice_id=VOICE_ID,
            model_id=MODEL_ID,
            output_format="mp3_44100_128", 
        ) # <--- The closing parenthesis is here!
        print("✅ Audio data successfully received.")
    
    except Exception as e:
        print(f"❌ Error during ElevenLabs generation. Check API Key/Network/Rate Limits: {e}")
        return

    # 3. PYGAME PLAYBACK (The Final Stream Fix)
    
    # FIX: Assemble all byte chunks from the generator and join into single bytes object
    try:
        # This line was corrected to include the full generator name and the closing parenthesis.
        audio_bytes = b"".join(audio_data_generator) 
    except TypeError as e:
        print(f"❌ Failed to assemble audio bytes. Generator issue: {e}")
        return

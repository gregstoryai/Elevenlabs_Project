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
load_dotenv() 
API_KEY = os.getenv("ELEVENLABS_API_KEY") 

if not API_KEY:
    raise ValueError("ELEVENLABS_API_KEY not found in .env file.")

VOICE_ID = "JBKXQq8eu7bjrKXhy7MD" # Example voice ID
MODEL_ID = "eleven_multilingual_v2" # Recommended high-quality model

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
    """Generates audio via the corrected SDK method and plays it using Pygame."""
    
    print(f"🎙️ Generating dialogue for '{emotional_score}'...")
    
    # 3. ELEVENLABS GENERATION (The Corrected SDK Call)
    try:
        # The correct method for the current SDK version returns a generator (stream)
        audio_data_generator = client.text_to_speech.convert(
            text=dialogue_text,
            voice_id=VOICE_ID,
            model_id=MODEL_ID,
            output_format="mp3_44100_128", # High quality output format
        )
        print("✅ Audio data successfully received.")
    
    except Exception as e:
        print(f"❌ Error during ElevenLabs generation. Check API Key/Network/Rate Limits: {e}")
        return

    # 4. PYGAME PLAYBACK (The Final Stream Fix)
    
    # --- FIX: Collect all chunks from the generator and join into single bytes object ---
    try:
        # Assemble all byte chunks from the generator into one complete object
        audio_bytes = b"".join(audio_data_generator) 
    except TypeError as e:
        print(f"❌ Failed to assemble audio bytes. Generator issue: {e}")
        return

    # Use io.BytesIO on the assembled bytes
    audio_buffer = io.BytesIO(audio_bytes)

    try:
        sound = pygame.mixer.Sound(audio_buffer)
        
        print(f"▶️ Playing scene: '{emotional_score}'...")
        channel = sound.play()
        
        # Wait until the audio finishes playing
        while channel.get_busy():
            time.sleep(0.1)
        
        print("⏹️ Playback complete.")
        
    except pygame.error as e:
        print(f"❌ Pygame Playback Error. Audio format may be incompatible: {e}")


# -------------------------------------------------------------
# 5. THE MAIN ENGINE LOOP (The Mission Execution)

if __name__ == "__main__":
    if not initialize_audio_engine():
        exit()
        
    print("\n--- Welcome to the Emotion-Scoring Engine ---")
    
    while True:
        dialogue = input("\nPlease enter a line of dialogue for the scene (or 'quit' to exit):\n> ")
        
        if dialogue.lower() == 'quit':
            break

        # Simple logic for emotional choice
        print("\nNow, choose the emotional score for the scene:")
        print("1. Heroic Climax (Triumphant, inspiring music for a final battle)")
        print("2. Tense Stealth (Low, anxious strings for a stealth mission)")
        print("3. Somber Sacrifice (A sad, slow piano for a moment of loss)")
        choice = input("Enter your choice (1, 2, or 3): ")

        if choice == '1':
            score = "Heroic Climax"
        elif choice == '2':
            score = "Tense Stealth"
        elif choice == '3':
            score = "Somber Sacrifice"
        else:
            print("Invalid choice. Try again.")
            continue
        
        # Execute the scene
        print(f"\n🎬 Staging scene: '{score}'...")
        generate_and_play_scene(dialogue, score)

    # Clean up Pygame resources and systems
    pygame.quit()
    print("Engine shut down. Mission complete.")

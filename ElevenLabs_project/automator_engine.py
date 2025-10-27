import pygame
import io
import time
import os
from dotenv import load_dotenv 
from elevenlabs.client import ElevenLabs 
from elevenlabs import Voice 
# Import the data structures
from audio_db import VOICE_ACTORS, MOOD_PRESETS, SOUND_EFFECTS 

# -------------------------------------------------------------
# 2. CONFIGURATION & INITIALIZATION

load_dotenv() 
API_KEY = os.getenv("ELEVENLABS_API_KEY") 

if not API_KEY:
    # Use a hardcoded test key if the env file fails, allowing the demo to run locally
    print("⚠️ API_KEY not loaded from .env. Using fallback test mode.")
    # You MUST replace this with your actual key if the .env file is not working!
    API_KEY = "YOUR_ACTUAL_ELEVENLABS_API_KEY_HERE" 

VOICE_ID = "JBFqnCBsd6RMkjVDRZzb" # Default voice ID
MODEL_ID = "eleven_multilingual_v2" 

# Initialize the ElevenLabs client
client = ElevenLabs(api_key=API_KEY) 

def initialize_audio_engine():
    """Initializes Pygame and its mixer for audio playback."""
    try:
        pygame.init()
        # Set number of channels high enough to play dialogue and SFX concurrently (Source 2.4)
        pygame.mixer.set_num_channels(8) 
        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
        print("✅ Pygame Audio Mixer Initialized.")
        return True
    except pygame.error as e:
        print(f"❌ Error initializing Pygame mixer. Check system audio or drivers: {e}")
        return False

# -------------------------------------------------------------
# 3. THE CONNECTOR (XML Construction Logic)

def apply_mood_xml(phrase, mood_key):
    """
    Constructs the final SSML string using the selected mood template.
    """
    mood_key = mood_key if mood_key in MOOD_PRESETS else "NONE"
    
    # Get the template and replace the placeholder
    xml_template = MOOD_PRESETS[mood_key]['xml_template']
    final_text = xml_template.format(PHRASE=phrase)
    
    # Wrap in <speak> tags if SSML tags were used
    if mood_key != "NONE":
        # Note: ElevenLabs often accepts simple tags, but SSML requires <speak> wrappers
        final_text = f"<speak>{final_text}</speak>"
        
    return final_text

def get_user_selections():
    """Prompts the user for dialogue, voice actor, mood, and sound effect."""
    
    dialogue = input("\n[1/4] Enter the line of dialogue (or 'quit'):\n> ").strip()
    if dialogue.lower() == 'quit':
        return None, None, None, None
    
    # --- Voice Actor Selection ---
    print("\n[2/4] Choose a Voice Actor:")
    voice_keys = list(VOICE_ACTORS.keys())
    for i, name in enumerate(voice_keys):
        desc = VOICE_ACTORS[name]['description']
        print(f"{i + 1}. {name} ({desc})")
    
    try:
        voice_choice = int(input("Enter choice (number): "))
        voice_key = voice_keys[voice_choice - 1]
    except (ValueError, IndexError):
        print("Invalid choice. Defaulting to 'The Architect'.")
        voice_key = "The Architect"

    # --- Mood Selection ---
    print("\n[3/4] Choose an Emotional Mood:")
    mood_keys = list(MOOD_PRESETS.keys())
    for i, mood in enumerate(mood_keys):
        desc = MOOD_PRESETS[mood]['description']
        print(f"{i + 1}. {mood} ({desc})")
    
    try:
        mood_choice = int(input("Enter choice (number): "))
        mood_key = mood_keys[mood_choice - 1]
    except (ValueError, IndexError):
        print("Invalid choice. Defaulting to NONE.")
        mood_key = "NONE"
        
    # --- Sound Effect Selection ---
    print("\n[4/4] Choose a Sound Effect:")
    sfx_keys = list(SOUND_EFFECTS.keys())
    for i, sfx in enumerate(sfx_keys):
        desc = SOUND_EFFECTS[sfx]['type']
        print(f"{i + 1}. {sfx} ({desc})")

    try:
        sfx_choice = int(input("Enter choice (number): "))
        sfx_key = sfx_keys[sfx_choice - 1]
    except (ValueError, IndexError):
        print("Invalid choice. Defaulting to NONE.")
        sfx_key = "NONE"

    return dialogue, voice_key, mood_key, sfx_key

# -------------------------------------------------------------
# 4. THE EXECUTIONER (API Call & Pygame)

def generate_and_play_scene(final_text, voice_id, sfx_key):
    """Generates speech and plays it concurrently with a sound effect."""
    
    sfx_path = SOUND_EFFECTS[sfx_key]['file_path']
    sfx_channel = None

    # 1. Start the Sound Effect (Concurrent Playback)
    if sfx_path:
        try:
            # Load SFX as a Pygame Sound object (different from mixer.music)
            sfx_sound = pygame.mixer.Sound(sfx_path)
            # Play the SFX, Pygame handles which channel to use (Source 2.4)
            sfx_channel = sfx_sound.play() 
            print(f"🔊 Playing SFX: {sfx_key}...")
        except pygame.error as e:
            print(f"⚠️ Warning: Could not load SFX file '{sfx_path}'. Ensure file exists in /assets: {e}")
            
    print(f"🎙️ Generating dialogue...")
    
    # 2. ELEVENLABS GENERATION
    try:
        audio_data_generator = client.text_to_speech.convert(
            text=final_text,
            voice_id=voice_id,
            model_id=MODEL_ID,
            output_format="mp3_44100_128", 
        )
        audio_bytes = b"".join(audio_data_generator) 
        print("✅ Audio data successfully received.")
    
    except Exception as e:
        print(f"❌ Error during ElevenLabs generation. Check API Key/Network/Rate Limits: {e}")
        return

    # 3. DIALOGUE PLAYBACK
    audio_buffer = io.BytesIO(audio_bytes)

    try:
        dialogue_sound = pygame.mixer.Sound(audio_buffer)
        
        print(f"▶️ Playing Dialogue...")
        dialogue_channel = dialogue_sound.play()
        
        # Wait until the dialogue finishes playing
        while dialogue_channel.get_busy():
            time.sleep(0.1)
        
        print("⏹️ Dialogue playback complete.")
        
    except pygame.error as e:
        print(f"❌ Pygame Playback Error. Audio format may be incompatible: {e}")
        
    # 4. Stop the SFX if it's still running
    if sfx_channel and sfx_channel.get_busy():
        sfx_channel.stop()
        print("⏹️ SFX stopped.")


# -------------------------------------------------------------
# 5. THE MAIN ENGINE LOOP (The Mission Execution)

if __name__ == "__main__":
    if not initialize_audio_engine():
        exit()
        
    print("\n--- Welcome to the Mythic Audio Automator ---")
    
    while True:
        # Get all inputs
        dialogue, voice_key, mood_key, sfx_key = get_user_selections()
        
        if dialogue is None:
            break

        # Construct final text
        final_text = apply_mood_xml(dialogue, mood_key)
        
        # Get final voice ID
        voice_id = VOICE_ACTORS[voice_key]['voice_id']

        # Execute the scene
        print(f"\n🎬 Staging scene: Voice='{voice_key}', Mood='{mood_key}', SFX='{sfx_key}'...")
        generate_and_play_scene(final_text, voice_id, sfx_key)

    # Clean up Pygame resources and systems
    pygame.quit()
    print("Engine shut down. Mission complete.")

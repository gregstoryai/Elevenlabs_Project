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
    # Fallback/Test Key for local development
    print("⚠️ API_KEY not loaded from .env. Using hardcoded test mode.")
    API_KEY = "YOUR_ACTUAL_ELEVENLABS_API_KEY_HERE" 

MODEL_ID = "eleven_multilingual_v2" 
FINAL_OUTPUT_FILE = "final_scene_audio.mp3" 

# Initialize the ElevenLabs client
client = ElevenLabs(api_key=API_KEY) 

def initialize_audio_engine():
    """Initializes Pygame and its mixer for audio playback."""
    try:
        pygame.init()
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
    # NOTE: This function is only called if a voice is selected.
    mood_key = mood_key if mood_key in MOOD_PRESETS else "NONE"
    
    xml_template = MOOD_PRESETS[mood_key]['xml_template']
    final_text = xml_template.format(PHRASE=phrase)
    
    if mood_key != "NONE":
        final_text = f"<speak>{final_text}</speak>"
        
    return final_text

def get_user_selections():
    """Prompts the user for dialogue, voice actor, mood, and sound effect."""
    
    dialogue = input("\n[1/3-4] Enter dialogue or action (or 'DONE'):\n> ").strip()
    if dialogue.upper() == 'DONE':
        return None, None, None, None
    
    # --- Voice Actor Selection (Includes NONE option) ---
    print("\n[2/3-4] Choose a Voice Actor (or NONE for SFX only):")
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
    
    # --- Mood Selection (BYPASS if NONE voice is selected) ---
    mood_key = "NONE" # Default to NONE
    if voice_key != "NONE (SFX Only)":
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
        
    # --- Sound Effect Selection (Always presented) ---
    print(f"\n[{3 if voice_key == 'NONE (SFX Only)' else 4}/4] Choose a Sound Effect:")
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
# 4. THE EXECUTIONER (Scene Generation and Playback)

def process_scene_turn(final_text, voice_key, sfx_key):
    """
    Handles SFX playback and dialogue generation, bypassing dialogue
    if the voice actor is NONE.
    """
    
    sfx_path = SOUND_EFFECTS[sfx_key]['file_path']
    sfx_channel = None
    dialogue_bytes = b""
    
    # 1. Start the Sound Effect
    if sfx_path:
        try:
            sfx_sound = pygame.mixer.Sound(sfx_path)
            sfx_channel = sfx_sound.play() 
            print(f"🔊 Playing SFX: {sfx_key}...")
            # Wait a short time for SFX to start before processing dialogue
            time.sleep(0.5) 
        except pygame.error as e:
            print(f"⚠️ Warning: Could not load SFX file '{sfx_path}'. Ensure file exists: {e}")
    
    # 2. DIALOGUE GENERATION (BYPASS LOGIC)
    if voice_key != "NONE (SFX Only)":
        voice_id = VOICE_ACTORS[voice_key]['voice_id']
        print(f"🎙️ Generating dialogue for {voice_key}...")
        try:
            audio_data_generator = client.text_to_speech.convert(
                text=final_text,
                voice_id=voice_id,
                model_id=MODEL_ID,
                output_format="mp3_44100_128", 
            )
            dialogue_bytes = b"".join(audio_data_generator) 
            print("✅ Dialogue audio generated.")
            
        except Exception as e:
            print(f"❌ Error during ElevenLabs generation: {e}")
            
        # 3. Play dialogue while SFX might still be running
        if dialogue_bytes:
            audio_buffer = io.BytesIO(dialogue_bytes)
            try:
                dialogue_sound = pygame.mixer.Sound(audio_buffer)
                print("▶️ Playing Dialogue...")
                dialogue_channel = dialogue_sound.play()
                
                # Wait until the dialogue finishes playing
                while dialogue_channel.get_busy():
                    time.sleep(0.1)
            except pygame.error as e:
                print(f"❌ Pygame Playback Error: {e}")
    
    else:
        # If NONE is selected, just wait for the SFX to finish before compiling
        if sfx_channel:
            sfx_duration = sfx_channel.get_sound().get_length()
            print(f"💤 Waiting {sfx_duration:.2f}s for SFX to complete...")
            time.sleep(sfx_duration)
            sfx_channel.stop() # Ensure it stops cleanly
            
        # Add a short silent segment to the dialogue stream for spacing
        print("✅ Generated 1-second silence placeholder.")
        return b'\x00' * 44100 # Add 1 second of silence (approx. 44100 samples)
        

    # 4. Stop the SFX if it's still running (after dialogue)
    if sfx_channel and sfx_channel.get_busy():
        sfx_channel.stop()
        print("⏹️ SFX stopped.")
    
    return dialogue_bytes

# -------------------------------------------------------------
# 5. THE MAIN ENGINE LOOP (Dialogue Construction Loop)

if __name__ == "__main__":
    if not initialize_audio_engine():
        exit()
        
    print("\n--- Mythic Audio Automator v3: Custom Dialogue Engine ---")
    
    all_scene_audio = []
    turn_counter = 1
    
    while True:
        print(f"\n--- TURN {turn_counter} ---")
        
        # Get all required input
        dialogue, voice_key, mood_key, sfx_key = get_user_selections()
        
        if dialogue is None:
            break

        # 1. Construct final text (only needed if voice is active)
        if voice_key != "NONE (SFX Only)":
            final_text = apply_mood_xml(dialogue, mood_key)
        else:
            final_text = dialogue # Keep original text for logging/context

        # 2. Execute the scene turn
        print(f"🎬 Staging turn: Voice='{voice_key}', Mood='{mood_key}', SFX='{sfx_key}'...")
        # Note: final_text is XML-enhanced dialogue OR context for SFX
        turn_audio = process_scene_turn(final_text, voice_key, sfx_key)
        
        # 3. Save audio segment and advance turn
        if turn_audio:
            all_scene_audio.append(turn_audio)
        
        turn_counter += 1

    # --- Final Audio Compilation and Playback (remains the same) ---
    if all_scene_audio:
        print("\n\n*** COMPILING FINAL SCENE ***")
        
        # 1. Concatenate all audio segments
        final_bytes = b"".join(all_scene_audio)
        
        # 2. Save the final file to disk
        with open(FINAL_OUTPUT_FILE, "wb") as f:
            f.write(final_bytes)
        print(f"✅ Scene saved to: {FINAL_OUTPUT_FILE}")
        
        # 3. Play the complete scene back for review
        # (Playback logic is removed from final compilation for simplicity of this long script)

    # Clean up Pygame resources
    pygame.quit()
    print("Engine shut down. Mission complete.")

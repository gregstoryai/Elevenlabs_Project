import pygame
import io
import time
import os
from dotenv import load_dotenv 
from elevenlabs.client import ElevenLabs 
from elevenlabs import Voice 
from pydub import AudioSegment # Crucial for timing and compilation
# Import the data structures (Requires: audio_db.py file)
from audio_db import VOICE_ACTORS, MOOD_PRESETS, SOUND_EFFECTS 

# -------------------------------------------------------------
# 2. CONFIGURATION & INITIALIZATION

load_dotenv() 
API_KEY = os.getenv("ELEVENLABS_API_KEY") 

if not API_KEY:
    # Fallback/Test Key for local development (MUST BE REPLACED WITH YOUR KEY)
    print("⚠️ API_KEY not loaded from .env. Using hardcoded test mode.")
    API_KEY = "YOUR_ACTUAL_ELEVENLABS_API_KEY_HERE" 

MODEL_ID = "eleven_multilingual_v2" 
FINAL_OUTPUT_FILE = "final_scene_audio.mp3" 
NONE_VOICE_KEY = "NONE (SFX Only)" # Constant for the bypass key
SILENCE_VOICE_KEY = "SILENCE_MAKER" # Constant for utility voice

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
# 3. THE CONNECTOR (XML Construction Logic and User Input)

def apply_mood_xml(phrase, mood_key):
    """
    Constructs the final SSML string using the selected mood template.
    """
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
    if voice_key != NONE_VOICE_KEY:
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
    # Adjust prompt count based on whether the Mood step was presented
    prompt_num = 3 if voice_key == NONE_VOICE_KEY else 4
    print(f"\n[{prompt_num}/4] Choose a Sound Effect:")
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

def process_scene_turn(final_text, voice_key, sfx_key, turn_number):
    """
    Generates dialogue/silence, mixes the SFX into the audio segment, 
    and saves the combined result to a temp file.
    Returns the path to the saved temporary file.
    """
    
    sfx_path = SOUND_EFFECTS[sfx_key]['file_path']
    temp_file_path = f"temp_turn_{turn_number}.mp3"
    current_audio = None
    
    # --- Generation of Dialogue/Silence Segment ---
    if voice_key == NONE_VOICE_KEY:
        # SILENCE GENERATION (Utility Voice)
        voice_id = VOICE_ACTORS[SILENCE_VOICE_KEY]['voice_id'] 
        print("🎙️ Generating 1-second silence via API...")
        api_text = "<speak><break time=\"1000ms\"/></speak>" 
    else:
        # DIALOGUE GENERATION (Chosen Actor)
        voice_id = VOICE_ACTORS[voice_key]['voice_id']
        print(f"🎙️ Generating dialogue for {voice_key}...")
        api_text = final_text 

    try:
        # 1. ElevenLabs API Call
        audio_data_generator = client.text_to_speech.convert(
            text=api_text,
            voice_id=voice_id,
            model_id=MODEL_ID,
            output_format="mp3_44100_128", 
        )
        
        # 2. Convert raw bytes to AudioSegment for mixing
        audio_bytes = b"".join(audio_data_generator)
        current_audio = AudioSegment.from_file(io.BytesIO(audio_bytes), format="mp3")
        print("✅ Audio segment generated.")
        
    except Exception as e:
        print(f"❌ Error during ElevenLabs generation: {e}")
        return None 

    # --- 3. SFX Mixing (Overlaying SFX onto the Dialogue/Silence Segment) ---
    if sfx_path and os.path.exists(sfx_path):
        try:
            sfx_audio = AudioSegment.from_file(sfx_path)
            
            # Adjust dialogue/silence volume slightly for SFX to be prominent
            dialogue_volume_adjusted = current_audio - 3.0 
            
            # Overlay the SFX onto the segment (SFX starts at position 0ms)
            mixed_audio = dialogue_volume_adjusted.overlay(sfx_audio, position=0)
            current_audio = mixed_audio
            print(f"🔊 SFX '{sfx_key}' mixed into segment.")
            
        except Exception as e:
            print(f"⚠️ Warning: Failed to mix SFX '{sfx_key}'. Check file format: {e}")
            
    # --- 4. Save and Playback (FIXED DURATION CHECK) ---
    
    # Save the final mixed/silent segment to a temporary file
    current_audio.export(temp_file_path, format="mp3")
    print(f"✅ Segment saved to {temp_file_path}.")

    # Play the mixed segment immediately for review
    if os.path.exists(temp_file_path):
        # 1. Load the generated audio segment again to measure its length
        playback_segment = AudioSegment.from_mp3(temp_file_path)
        playback_duration_seconds = playback_segment.duration_seconds
        
        # 2. Pygame loads the sound
        review_sound = pygame.mixer.Sound(temp_file_path)
        print(f"▶️ Playing Segment ({playback_duration_seconds:.1f}s)...")
        review_channel = review_sound.play()
        
        # 3. Wait for the PRECISE DURATION plus a small buffer (The FIX)
        time.sleep(playback_duration_seconds + 0.5) 
        
        # 4. Ensure playback stops before proceeding
        review_channel.stop()

    return temp_file_path

# -------------------------------------------------------------
# 5. THE MAIN ENGINE LOOP (Dialogue Construction Loop)

if __name__ == "__main__":
    
    if not initialize_audio_engine():
        exit()
        
    print("\n--- Mythic Audio Automator v3: Custom Dialogue Engine ---")
    
    all_temp_files = [] # List to hold paths to temp files
    turn_counter = 1
    
    while True:
        print(f"\n--- TURN {turn_counter} ---")
        
        # Get all required input
        dialogue, voice_key, mood_key, sfx_key = get_user_selections()
        
        if dialogue is None:
            break

        # 1. Construct final text 
        if voice_key != NONE_VOICE_KEY:
            final_text = apply_mood_xml(dialogue, mood_key)
        else:
            final_text = dialogue # Keep original text for logging/context

        # 2. Execute the scene turn
        print(f"🎬 Staging turn: Voice='{voice_key}', Mood='{mood_key}', SFX='{sfx_key}'...")
        turn_file_path = process_scene_turn(final_text, voice_key, sfx_key, turn_counter)
        
        # 3. Save file path and advance turn
        if turn_file_path and os.path.exists(turn_file_path):
            all_temp_files.append(turn_file_path)
        
        turn_counter += 1

    # --- Final Audio Compilation and Playback ---
    if all_temp_files:
        print("\n\n*** COMPILING FINAL SCENE with pydub ***")
        
        try:
            # 1. Load the first segment
            final_audio = AudioSegment.from_mp3(all_temp_files[0])
            
            # 2. Concatenate the remaining segments using pydub
            for path in all_temp_files[1:]:
                segment = AudioSegment.from_mp3(path)
                final_audio += segment
            
            # 3. Export the final file
            final_audio.export(FINAL_OUTPUT_FILE, format="mp3")
            print(f"✅ Full scene compiled and saved to: {FINAL_OUTPUT_FILE}")
            
        except Exception as e:
            print(f"❌ Failed to compile final audio using pydub. Error: {e}")
            print("Note: Ensure all temp files are valid MP3s and FFmpeg is installed.")
            
        # 4. Clean up temporary files (Crucial for a clean system)
        for path in all_temp_files:
            try:
                os.remove(path)
            except OSError as e:
                print(f"Could not remove temp file {path}: {e}")

    # Clean up Pygame resources
    pygame.quit()
    print("Engine shut down. Mission complete.")

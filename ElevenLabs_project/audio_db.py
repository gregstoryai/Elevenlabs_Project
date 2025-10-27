# audio_db.py

# 1. VOICE ACTOR DATABASE
VOICE_ACTORS = {
     "SILENCE_MAKER": { 
    	"voice_id": "fUjY9K2nAIwlALOwSiwc", # Use a standard voice ID
    	"description": "Used to generate a silent MP3 segment.",
	"tags": ["utility"],
     },
     "NONE (SFX Only)": {  # Renamed for clarity in the menu
        "voice_id": "NO_VOICE",  # Placeholder ID
        "description": "Scene focusing purely on sound effects.",
        "tags": ["ambient", "action"],
    },
    "Interviewer": {
        "voice_id": "7cOBG34AiHrAzs842Rdi",  # Example ID
        "description": "Strategic, thoughtful, measured tone.",
        "tags": ["calm", "instructional"],
    },
    "Greg": {
        "voice_id": "JBKXQq8eu7bjrKXhy7MD",  # Example ID
        "description": "Emotional, immediate, high-intensity.",
        "tags": ["tense", "dramatic"],
    }
}

# 2. MOOD / XML PRESETS (The SSML Enhancement)
# Placeholder: {PHRASE} will be replaced by the user's text.
MOOD_PRESETS = {
    "TENSE": {
        "description": "High anxiety, whispered tone.",
        # Using SSML <emotion> tag for advanced control (ElevenLabs supported)
        "xml_template": "<emotion category='anxiety' intensity='high'>{PHRASE}</emotion>",
    },
    "HEROIC": {
        "description": "Triumphant, powerful, loud tone.",
        "xml_template": "<emotion category='determination' intensity='medium'>{PHRASE}</emotion>",
    },
    "SOMBER": {
        "description": "Sad, low, slow, reflecting tone.",
        "xml_template": "<emotion category='sadness' intensity='low'>{PHRASE}</emotion>",
    },
}

# 3. SOUND EFFECT DATABASE (Requires actual audio files in an 'assets' folder)
SOUND_EFFECTS = {
    "NONE": {
	"file_path": None, 
	"type": "None", 
	"tags": []
    },
    "FOOTSTEPS": {
        "file_path": "assets/footsteps.mp3",
        "type": "ambient",
        "tags": ["tense", "stealth"],
    },
    "DOOR_CLOSE": {
        "file_path": "assets/door_close.mp3",
        "type": "impact",
        "tags": ["dramatic"],
    }

}

import os
import json
import pyttsx3
import pyaudio
import difflib
from vosk import Model, KaldiRecognizer
import time

# Enhanced TTS engine initialization
engine = pyttsx3.init()
engine.setProperty('rate', 150)  # Slower speech rate for clarity
engine.setProperty('volume', 1.0)  # Maximum volume

# Try to use the best available voice
voices = engine.getProperty('voices')
if len(voices) > 1:
    # Prefer female voices (often clearer) if available
    for voice in voices:
        if 'female' in voice.name.lower():
            engine.setProperty('voice', voice.id)
            break
    else:
        engine.setProperty('voice', voices[0].id)  # Fallback to first voice

# Load Vosk model with better error handling
try:
    model_path = r"C:\Users\Mohamed Jefri\voice assistant\model\vosk-model-en-us-0.22"
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model not found at {model_path}")
    
    model = Model(model_path)
    recognizer = KaldiRecognizer(model, 16000)
    print("✅ Speech recognition model loaded successfully")
except Exception as e:
    print(f"❌ Model error: {str(e)}")
    exit(1)

# Audio setup with error handling
try:
    mic = pyaudio.PyAudio()
    print("✅ Audio system initialized")
except Exception as e:
    print(f"❌ Audio error: {str(e)}")
    exit(1)

# Enhanced app commands with clearer responses
APPS = {
    "YouTube": {
        "triggers": ["youtube", "video", "watch", "videos"],
        "action": lambda: os.system("start chrome https://youtube.com"),
        "response": "Opening YouTube for you"
    },
    "Chrome": {
        "triggers": ["chrome", "browser", "search", "google", "web"],
        "action": lambda query=None: os.system(f"start chrome https://google.com/search?q={query.replace(' ', '+')}" if query else "start chrome"),
        "response": lambda query: f"Searching Google for {query}" if query else "Opening Chrome browser"
    },
    "Camera": {
        "triggers": ["camera", "webcam", "photo", "picture"],
        "action": lambda: os.system("start microsoft.windows.camera:"),
        "response": "Opening the camera application"
    },
    "Notepad": {
        "triggers": ["notepad", "notes", "text", "write"],
        "action": lambda: os.system("notepad"),
        "response": "Opening Notepad for you"
    }
}

def speak(text, wait=False):
    """Improved speech output with clear pronunciation"""
    print(f"🤖: {text}")
    
    # Split long sentences for better pacing
    if len(text.split()) > 15:
        parts = text.split(',')
        if len(parts) > 1:
            for part in parts:
                engine.say(part.strip())
                engine.runAndWait()
                time.sleep(0.3)  # Pause between sentences
            return
    
    engine.say(text)
    engine.runAndWait()
    if wait:
        time.sleep(0.5)  # Pause after important messages

def listen():
    """Enhanced listening with better feedback"""
    stream = mic.open(
        format=pyaudio.paInt16,
        channels=1,
        rate=16000,
        input=True,
        frames_per_buffer=8192,
        input_device_index=None  # Use default microphone
    )
    
    print("🔊 Listening... (Speak now)")
    speak("I'm listening", wait=True)
    
    while True:
        try:
            data = stream.read(4096, exception_on_overflow=False)
            if recognizer.AcceptWaveform(data):
                result = json.loads(recognizer.Result())
                text = result.get("text", "").strip().lower()
                if text:
                    print(f"👤 You said: {text}")
                    return text
        except Exception as e:
            print(f"⚠️ Listening error: {str(e)}")
            speak("I'm having trouble hearing you. Please try again.")
            return ""

def get_closest_app(command):
    """Improved command matching"""
    command_words = command.split()
    best_match = None
    best_score = 0
    
    for app, config in APPS.items():
        for trigger in config["triggers"]:
            # Get best match for each trigger
            matches = difflib.get_close_matches(trigger, command_words, n=1, cutoff=0.6)
            if matches:
                score = difflib.SequenceMatcher(None, trigger, matches[0]).ratio()
                if score > best_score:
                    best_score = score
                    best_match = (app, config)
    
    return best_match if best_score > 0.65 else (None, None)

def process_command(command):
    """Enhanced command processing with clearer responses"""
    if not command:
        speak("I didn't hear anything. Please try speaking again.")
        return False

    # Exit command
    if any(exit_word in command for exit_word in ["stop", "exit", "quit", "bye"]):
        speak("Goodbye! Have a wonderful day.")
        exit()

    # Greetings
    if any(greet in command for greet in ["hi", "hello", "hey", "greetings"]):
        speak("Hello there! I can help you open applications. Say 'help' to learn what I can do.")
        return True

    # Help command
    if "help" in command or "what can you do" in command or "options" in command:
        speak("I can open these applications for you: " + 
             ", ".join([app for app in APPS.keys()]) + 
             ". Just say 'open' followed by the application name.")
        return True

    # Match app
    app, config = get_closest_app(command)
    if app and config:
        if app == "Chrome" and ("search" in command or "google" in command):
            query = " ".join([w for w in command.split() if w not in config["triggers"]])
            if query:
                config["action"](query)
                response = config["response"](query) if callable(config["response"]) else config["response"]
                speak(response)
                return True

        config["action"]()
        response = config["response"]() if callable(config["response"]) else config["response"]
        speak(response)
        return True

    speak("I didn't quite understand that. Try saying something like 'open YouTube' or 'search for cats on Google'.")
    return False

# Main program with better initialization
def main():
    speak("Voice assistant activated. How can I help you today?")
    
    while True:
        try:
            command = listen()
            if command:
                process_command(command)
        except KeyboardInterrupt:
            speak("Shutting down the voice assistant. Goodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")
            speak("Sorry, I encountered an error. Let me try again.")
            time.sleep(1)

if __name__ == "__main__":
    main()
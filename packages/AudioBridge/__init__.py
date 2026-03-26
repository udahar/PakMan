"""
AudioBridge
Speech-to-text and text-to-speech pipeline for AI agents.

Quick start:
    from AudioBridge import AudioBridge

    ab = AudioBridge()

    # Transcribe a file
    result = ab.transcribe("meeting.wav")
    if result.ok:
        print(result.text)

    # Live mic → text (requires pyaudio + SpeechRecognition)
    result = ab.listen(duration=5)

    # Text → speech file
    ab.speak("Task complete.", output="done.mp3")

    # Force specific backends
    ab = AudioBridge(stt_backend="faster_whisper", tts_backend="pyttsx3")

STT backends (auto-detected):
    openai (OPENAI_API_KEY), faster-whisper, SpeechRecognition

TTS backends (auto-detected):
    openai (OPENAI_API_KEY), pyttsx3 (offline), gTTS (Google, online)
"""
from .bridge import AudioBridge, AudioResult

__version__ = "0.1.0"
__all__ = ["AudioBridge", "AudioResult"]

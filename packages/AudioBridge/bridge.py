"""
AudioBridge - bridge.py
Unified speech-to-text and text-to-speech pipeline for AI agents.

STT backends (in priority order):
  1. OpenAI Whisper API  (OPENAI_API_KEY env var)
  2. faster-whisper      (pip install faster-whisper)
  3. SpeechRecognition   (pip install SpeechRecognition)

TTS backends (in priority order):
  1. OpenAI TTS API      (OPENAI_API_KEY env var)
  2. pyttsx3             (pip install pyttsx3) — offline, zero cost
  3. gTTS                (pip install gTTS) — Google, requires network

Usage:
    from AudioBridge import AudioBridge

    ab = AudioBridge()

    # Transcribe audio file → text
    text = ab.transcribe("meeting.wav")

    # Synthesize text → audio file
    ab.speak("Hello, I am your AI assistant.", output="response.mp3")

    # Grab text from microphone (if SpeechRecognition available)
    text = ab.listen(duration=5)
"""
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class AudioResult:
    text: str = ""
    language: str = ""
    duration_s: float = 0.0
    backend: str = ""
    error: str = ""

    @property
    def ok(self) -> bool:
        return not self.error and bool(self.text)


class AudioBridge:
    """
    Unified STT + TTS gateway for AI agents.

    Args:
        stt_backend: "auto" | "openai" | "faster_whisper" | "speechrecognition"
        tts_backend: "auto" | "openai" | "pyttsx3" | "gtts"
        language:    Default language code (default: "en").
        model:       Whisper model size ("tiny","base","small","medium","large").
        openai_key:  Override OPENAI_API_KEY env var.
    """

    def __init__(
        self,
        stt_backend: str = "auto",
        tts_backend: str = "auto",
        language: str = "en",
        model: str = "base",
        openai_key: Optional[str] = None,
    ):
        self.stt_backend = stt_backend
        self.tts_backend = tts_backend
        self.language = language
        self.model = model
        self._openai_key = openai_key or os.getenv("OPENAI_API_KEY", "")

    # ── STT ───────────────────────────────────────────────────────────────────

    def transcribe(self, audio_path: str) -> AudioResult:
        """
        Transcribe an audio file to text.

        Args:
            audio_path: Path to WAV, MP3, M4A, FLAC, etc.

        Returns:
            AudioResult with .text, .language, .backend
        """
        path = Path(audio_path)
        if not path.exists():
            return AudioResult(error=f"File not found: {audio_path}")

        if self.stt_backend in ("openai", "auto") and self._openai_key:
            return self._stt_openai(path)

        if self.stt_backend in ("faster_whisper", "auto"):
            try:
                return self._stt_faster_whisper(path)
            except ImportError:
                pass

        if self.stt_backend in ("speechrecognition", "auto"):
            try:
                return self._stt_speechrecognition(path)
            except ImportError:
                pass

        return AudioResult(error="No STT backend available. "
                           "Install: openai, faster-whisper, or SpeechRecognition")

    def listen(self, duration: float = 5.0) -> AudioResult:
        """Record from microphone for `duration` seconds and transcribe."""
        try:
            import speech_recognition as sr
            recognizer = sr.Recognizer()
            with sr.Microphone() as source:
                print(f"[AudioBridge] Listening for {duration}s...")
                audio = recognizer.listen(source, phrase_time_limit=duration)
            text = recognizer.recognize_google(audio, language=self.language)
            return AudioResult(text=text, backend="speechrecognition_mic")
        except ImportError:
            return AudioResult(error="pip install SpeechRecognition pyaudio")
        except Exception as e:
            return AudioResult(error=str(e))

    # ── TTS ───────────────────────────────────────────────────────────────────

    def speak(self, text: str, output: Optional[str] = None) -> bool:
        """
        Convert text to speech.

        Args:
            text:   Text to synthesize.
            output: Optional file path (e.g. "response.mp3").
                    If None, plays audio immediately (pyttsx3 only).

        Returns:
            True on success.
        """
        if self.tts_backend in ("openai", "auto") and self._openai_key:
            return self._tts_openai(text, output)

        if self.tts_backend in ("pyttsx3", "auto"):
            try:
                return self._tts_pyttsx3(text, output)
            except ImportError:
                pass

        if self.tts_backend in ("gtts", "auto"):
            try:
                return self._tts_gtts(text, output)
            except ImportError:
                pass

        print(f"[AudioBridge] No TTS backend available. Text: {text}")
        return False

    # ── STT implementations ───────────────────────────────────────────────────

    def _stt_openai(self, path: Path) -> AudioResult:
        import openai
        client = openai.OpenAI(api_key=self._openai_key)
        with open(path, "rb") as f:
            transcript = client.audio.transcriptions.create(
                model="whisper-1", file=f, language=self.language
            )
        return AudioResult(text=transcript.text, backend="openai_whisper")

    def _stt_faster_whisper(self, path: Path) -> AudioResult:
        from faster_whisper import WhisperModel
        wm = WhisperModel(self.model, device="cpu", compute_type="int8")
        segments, info = wm.transcribe(str(path), language=self.language or None)
        text = " ".join(s.text.strip() for s in segments)
        return AudioResult(
            text=text,
            language=info.language,
            duration_s=info.duration,
            backend="faster_whisper",
        )

    def _stt_speechrecognition(self, path: Path) -> AudioResult:
        import speech_recognition as sr
        recognizer = sr.Recognizer()
        with sr.AudioFile(str(path)) as source:
            audio = recognizer.record(source)
        text = recognizer.recognize_google(audio, language=self.language)
        return AudioResult(text=text, backend="speechrecognition")

    # ── TTS implementations ───────────────────────────────────────────────────

    def _tts_openai(self, text: str, output: Optional[str]) -> bool:
        import openai
        client = openai.OpenAI(api_key=self._openai_key)
        response = client.audio.speech.create(
            model="tts-1", voice="alloy", input=text
        )
        out = output or "speech.mp3"
        response.stream_to_file(out)
        print(f"[AudioBridge] TTS → {out}")
        return True

    def _tts_pyttsx3(self, text: str, output: Optional[str]) -> bool:
        import pyttsx3
        engine = pyttsx3.init()
        if output:
            engine.save_to_file(text, output)
            engine.runAndWait()
            print(f"[AudioBridge] TTS → {output}")
        else:
            engine.say(text)
            engine.runAndWait()
        return True

    def _tts_gtts(self, text: str, output: Optional[str]) -> bool:
        from gtts import gTTS
        tts = gTTS(text=text, lang=self.language)
        out = output or "speech.mp3"
        tts.save(out)
        print(f"[AudioBridge] TTS (gTTS) → {out}")
        return True

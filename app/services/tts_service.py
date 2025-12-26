import os
import tempfile
from google.cloud import texttospeech
from app.core.config import settings
from typing import Optional


class TTSService:
    """Service for Google Cloud Text-to-Speech operations"""

    # Voice configurations for supported languages
    VOICE_CONFIGS = {
        "vi-VN": "vi-VN-Wavenet-A",
        "en-US": "en-US-Neural2-F",
        "ja-JP": "ja-JP-Wavenet-A",
        "zh-CN": "cmn-CN-Wavenet-A",
        "ko-KR": "ko-KR-Wavenet-A"
    }

    # Supported languages
    SUPPORTED_LANGUAGES = set(VOICE_CONFIGS.keys())

    def __init__(self):
        """Initialize TTS service with Google credentials"""
        self._setup_credentials()
        self._client: Optional[texttospeech.TextToSpeechClient] = None

    def _setup_credentials(self):
        """Setup Google Cloud credentials from environment variable"""
        credentials_json = settings.GOOGLE_CREDENTIALS_JSON

        if credentials_json:
            try:
                # Create temporary credentials file
                fd, path = tempfile.mkstemp(suffix='.json')
                with os.fdopen(fd, 'w') as f:
                    f.write(credentials_json)

                # Set environment variable for Google libraries
                os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = path
                print("✅ TTS: Loaded Google credentials from GOOGLE_CREDENTIALS_JSON")
            except Exception as e:
                print(f"⚠️ TTS: Error setting up credentials: {e}")
        else:
            if os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
                print("✅ TTS: Using existing GOOGLE_APPLICATION_CREDENTIALS")
            else:
                print("⚠️ TTS: No Google credentials found")

    def _get_client(self) -> texttospeech.TextToSpeechClient:
        """Get or create TTS client (lazy initialization)"""
        if self._client is None:
            self._client = texttospeech.TextToSpeechClient()
        return self._client

    def validate_language(self, language_code: str) -> bool:
        """Check if language code is supported"""
        return language_code in self.SUPPORTED_LANGUAGES

    def synthesize_speech(self, text: str, language_code: str) -> bytes:
        """
        Convert text to speech and return audio content.

        Args:
            text: Text to convert
            language_code: Language code (vi-VN, en-US, etc.)

        Returns:
            MP3 audio bytes

        Raises:
            Exception: If TTS synthesis fails
        """
        client = self._get_client()

        # Create synthesis input
        synthesis_input = texttospeech.SynthesisInput(text=text)

        # Select voice
        voice_name = self.VOICE_CONFIGS.get(language_code, self.VOICE_CONFIGS["en-US"])
        voice = texttospeech.VoiceSelectionParams(
            language_code=language_code,
            name=voice_name,
            ssml_gender=texttospeech.SsmlVoiceGender.FEMALE
        )

        # Configure audio
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3
        )

        # Perform synthesis
        response = client.synthesize_speech(
            input=synthesis_input,
            voice=voice,
            audio_config=audio_config
        )

        return response.audio_content


# Singleton instance
_tts_service: Optional[TTSService] = None


def get_tts_service() -> TTSService:
    """Get singleton TTS service instance"""
    global _tts_service
    if _tts_service is None:
        _tts_service = TTSService()
    return _tts_service

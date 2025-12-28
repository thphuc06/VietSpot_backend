import os
import tempfile
from google.cloud import speech
from app.core.config import settings
from typing import Optional, Dict, Set


class STTService:
    """Service for Google Cloud Speech-to-Text operations"""

    # Supported languages (same as TTS)
    SUPPORTED_LANGUAGES: Set[str] = {
        "vi-VN", "en-US", "ja-JP", "zh-CN", "ko-KR"
    }

    # Audio format configurations
    AUDIO_FORMAT_CONFIGS: Dict[str, Dict] = {
        "webm": {
            "encoding": speech.RecognitionConfig.AudioEncoding.WEBM_OPUS,
            "sample_rate_hertz": 48000,
        },
        "mp3": {
            "encoding": speech.RecognitionConfig.AudioEncoding.MP3,
        },
        "wav": {
            "encoding": speech.RecognitionConfig.AudioEncoding.LINEAR16,
        }
    }

    # Limits
    MAX_FILE_SIZE_MB = 10
    MAX_AUDIO_DURATION_SECONDS = 60

    def __init__(self):
        """Initialize STT service with Google credentials"""
        self._setup_credentials()
        self._client: Optional[speech.SpeechClient] = None

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
                print("✅ STT: Loaded Google credentials from GOOGLE_CREDENTIALS_JSON")
            except Exception as e:
                print(f"⚠️ STT: Error setting up credentials: {e}")
        else:
            if os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
                print("✅ STT: Using existing GOOGLE_APPLICATION_CREDENTIALS")
            else:
                print("⚠️ STT: No Google credentials found")

    def _get_client(self) -> speech.SpeechClient:
        """Get or create Speech client (lazy initialization)"""
        if self._client is None:
            self._client = speech.SpeechClient()
        return self._client

    def validate_language(self, language_code: str) -> bool:
        """Check if language code is supported"""
        return language_code in self.SUPPORTED_LANGUAGES

    def transcribe_audio(
        self,
        audio_content: bytes,
        language_code: str,
        audio_format: str
    ) -> dict:
        """
        Transcribe audio to text using Google Cloud Speech-to-Text.

        Args:
            audio_content: Raw audio bytes
            language_code: Language code (vi-VN, en-US, etc.)
            audio_format: Audio format (webm, mp3, wav)

        Returns:
            dict with keys: transcript, confidence

        Raises:
            ValueError: Invalid audio format or empty audio
            Exception: Google API errors
        """
        # Validate format
        if audio_format not in self.AUDIO_FORMAT_CONFIGS:
            raise ValueError(f"Định dạng không được hỗ trợ: {audio_format}")

        if len(audio_content) == 0:
            raise ValueError("File âm thanh trống")

        # Get client
        client = self._get_client()

        # Configure recognition
        format_config = self.AUDIO_FORMAT_CONFIGS[audio_format]
        config_params = {
            "encoding": format_config["encoding"],
            "language_code": language_code,
            "enable_automatic_punctuation": True,
            "use_enhanced": True  # Better accuracy
        }

        # Only set sample_rate_hertz if specified (WAV/MP3 can auto-detect)
        if "sample_rate_hertz" in format_config:
            config_params["sample_rate_hertz"] = format_config["sample_rate_hertz"]

        config = speech.RecognitionConfig(**config_params)

        # Create audio object
        audio = speech.RecognitionAudio(content=audio_content)

        # Transcribe (synchronous for audio < 1 minute)
        try:
            response = client.recognize(config=config, audio=audio)
        except Exception as e:
            raise Exception(f"Lỗi Google Speech API: {str(e)}")

        # Parse response
        if not response.results:
            return {
                "transcript": "",
                "confidence": 0.0
            }

        # Get best result
        result = response.results[0]
        alternative = result.alternatives[0]

        return {
            "transcript": alternative.transcript,
            "confidence": alternative.confidence
        }


# Singleton instance
_stt_service: Optional[STTService] = None


def get_stt_service() -> STTService:
    """Get singleton STT service instance"""
    global _stt_service
    if _stt_service is None:
        _stt_service = STTService()
    return _stt_service

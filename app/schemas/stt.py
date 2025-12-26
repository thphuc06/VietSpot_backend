from pydantic import BaseModel
from typing import Optional


class STTResponse(BaseModel):
    """Response model for speech-to-text transcription"""
    success: bool = True
    transcript: str
    language: str
    confidence: Optional[float] = None  # 0.0 to 1.0
    audio_duration: Optional[float] = None  # in seconds

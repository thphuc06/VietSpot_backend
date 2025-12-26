from pydantic import BaseModel, Field


class TTSRequest(BaseModel):
    """Request model for text-to-speech conversion"""
    text: str = Field(
        ...,
        description="Text to convert to speech",
        min_length=1,
        max_length=5000  # Google TTS limit
    )
    language: str = Field(
        default="vi-VN",
        description="Language code: vi-VN, en-US, ja-JP, zh-CN, ko-KR"
    )

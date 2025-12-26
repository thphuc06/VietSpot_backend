from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse
from io import BytesIO

from app.schemas.tts import TTSRequest
from app.services.tts_service import get_tts_service

router = APIRouter(prefix="/tts", tags=["Text-to-Speech"])


@router.post("", response_class=StreamingResponse)
async def text_to_speech(request: TTSRequest):
    """
    Convert text to speech using Google Cloud Text-to-Speech API.

    This is a public endpoint that doesn't require authentication.

    Parameters:
    - **text**: Text to convert (1-5000 characters)
    - **language**: Language code (default: vi-VN)
      - vi-VN: Vietnamese
      - en-US: English
      - ja-JP: Japanese
      - zh-CN: Chinese (Mandarin)
      - ko-KR: Korean

    Returns:
    - Audio file in MP3 format with female voice

    Example:
    ```json
    {
        "text": "Xin chào, chào mừng bạn đến Việt Nam!",
        "language": "vi-VN"
    }
    ```
    """
    try:
        tts_service = get_tts_service()

        # Validate language code
        if not tts_service.validate_language(request.language):
            supported = ", ".join(sorted(tts_service.SUPPORTED_LANGUAGES))
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Ngôn ngữ không được hỗ trợ: {request.language}. "
                       f"Các ngôn ngữ hỗ trợ: {supported}"
            )

        # Generate speech
        audio_content = tts_service.synthesize_speech(
            text=request.text,
            language_code=request.language
        )

        # Return audio as streaming response
        return StreamingResponse(
            BytesIO(audio_content),
            media_type="audio/mpeg",
            headers={
                "Content-Disposition": f"inline; filename=tts_{request.language}.mp3"
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"TTS Error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi khi chuyển đổi văn bản thành giọng nói: {str(e)}"
        )


@router.get("/languages")
async def get_supported_languages():
    """
    Get list of supported languages for text-to-speech.

    Returns:
    - List of language codes and their details
    """
    tts_service = get_tts_service()

    languages = {
        "vi-VN": {
            "name": "Vietnamese",
            "native_name": "Tiếng Việt",
            "voice": tts_service.VOICE_CONFIGS["vi-VN"]
        },
        "en-US": {
            "name": "English (US)",
            "native_name": "English",
            "voice": tts_service.VOICE_CONFIGS["en-US"]
        },
        "ja-JP": {
            "name": "Japanese",
            "native_name": "日本語",
            "voice": tts_service.VOICE_CONFIGS["ja-JP"]
        },
        "zh-CN": {
            "name": "Chinese (Mandarin)",
            "native_name": "中文",
            "voice": tts_service.VOICE_CONFIGS["zh-CN"]
        },
        "ko-KR": {
            "name": "Korean",
            "native_name": "한국어",
            "voice": tts_service.VOICE_CONFIGS["ko-KR"]
        }
    }

    return {
        "supported_languages": sorted(list(tts_service.SUPPORTED_LANGUAGES)),
        "details": languages
    }

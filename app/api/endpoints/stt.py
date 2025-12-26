from fastapi import APIRouter, HTTPException, status, UploadFile, File, Form
from app.schemas.stt import STTResponse
from app.services.stt_service import get_stt_service

router = APIRouter(prefix="/stt", tags=["Speech-to-Text"])


@router.post("/transcribe", response_model=STTResponse)
async def transcribe_audio(
    file: UploadFile = File(..., description="Audio file (webm, mp3, or wav)"),
    language: str = Form(default="vi-VN", description="Language code")
):
    """
    Transcribe audio to text using Google Cloud Speech-to-Text API.

    This is a public endpoint that doesn't require authentication.

    Parameters:
    - **file**: Audio file (webm, mp3, wav) - max 10MB
    - **language**: Language code (default: vi-VN)
      - vi-VN: Vietnamese
      - en-US: English
      - ja-JP: Japanese
      - zh-CN: Chinese (Mandarin)
      - ko-KR: Korean

    Returns:
    - Transcribed text with confidence score

    Example (cURL):
    ```bash
    curl -X POST "http://localhost:8000/api/stt/transcribe" \\
      -F "file=@recording.webm" \\
      -F "language=vi-VN"
    ```
    """
    try:
        stt_service = get_stt_service()

        # Validate language
        if not stt_service.validate_language(language):
            supported = ", ".join(sorted(stt_service.SUPPORTED_LANGUAGES))
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Ngôn ngữ không được hỗ trợ: {language}. "
                       f"Các ngôn ngữ hỗ trợ: {supported}"
            )

        # Validate audio format from filename
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tên file không hợp lệ"
            )

        file_ext = file.filename.split('.')[-1].lower()
        if file_ext not in ["webm", "mp3", "wav"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Định dạng không được hỗ trợ: {file_ext}. "
                       f"Hỗ trợ: webm, mp3, wav"
            )

        # Read and validate file size
        content = await file.read()
        file_size_mb = len(content) / (1024 * 1024)

        if file_size_mb > stt_service.MAX_FILE_SIZE_MB:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File quá lớn ({file_size_mb:.1f}MB). "
                       f"Kích thước tối đa: {stt_service.MAX_FILE_SIZE_MB}MB"
            )

        if len(content) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File âm thanh trống"
            )

        # Transcribe
        result = stt_service.transcribe_audio(
            audio_content=content,
            language_code=language,
            audio_format=file_ext
        )

        return STTResponse(
            success=True,
            transcript=result["transcript"],
            language=language,
            confidence=result.get("confidence"),
            audio_duration=None  # Not available in sync response
        )

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        print(f"STT Error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi khi nhận dạng giọng nói: {str(e)}"
        )


@router.get("/languages")
async def get_supported_languages():
    """
    Get list of supported languages for speech-to-text.

    Returns:
    - List of language codes and their details
    """
    stt_service = get_stt_service()

    languages = {
        "vi-VN": {
            "name": "Vietnamese",
            "native_name": "Tiếng Việt"
        },
        "en-US": {
            "name": "English (US)",
            "native_name": "English"
        },
        "ja-JP": {
            "name": "Japanese",
            "native_name": "日本語"
        },
        "zh-CN": {
            "name": "Chinese (Mandarin)",
            "native_name": "中文"
        },
        "ko-KR": {
            "name": "Korean",
            "native_name": "한국어"
        }
    }

    return {
        "supported_languages": sorted(list(stt_service.SUPPORTED_LANGUAGES)),
        "details": languages
    }

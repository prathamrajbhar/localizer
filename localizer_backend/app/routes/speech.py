"""
Speech (STT/TTS) routes
"""
import os
import time
import tempfile
from pathlib import Path
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status, Form
from fastapi.responses import FileResponse
from typing import Optional
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.core.config import SUPPORTED_LANGUAGES, get_settings
from app.schemas.speech import STTRequest, TTSRequest, STTResponse, TTSResponse
from app.services import speech_engine
from app.utils.file_manager import file_manager
from app.utils.logger import app_logger

settings = get_settings()

router = APIRouter(prefix="/speech", tags=["Speech"])

ALLOWED_AUDIO_FORMATS = {".wav", ".mp3", ".mp4", ".m4a", ".ogg", ".flac"}
MAX_AUDIO_SIZE = 100 * 1024 * 1024  # 100 MB


@router.post("/stt/test")
async def test_stt():
    """
    Test STT endpoint availability
    """
    return {
        "status": "available",
        "message": "Speech-to-Text service is operational",
        "supported_formats": list(ALLOWED_AUDIO_FORMATS),
        "max_file_size_mb": MAX_AUDIO_SIZE // (1024*1024)
    }


@router.post("/stt", response_model=STTResponse)
async def speech_to_text(
    file: UploadFile = File(...),
    language: Optional[str] = Form(None)
):
    """
    Convert speech to text (Speech-to-Text) - Direct processing
    
    Supported formats: WAV, MP3, MP4, M4A, OGG, FLAC
    Maximum size: 100 MB
    """
    # Validate file extension
    file_ext = "." + file.filename.split(".")[-1].lower() if "." in file.filename else ""
    if file_ext not in ALLOWED_AUDIO_FORMATS:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Audio format not supported. Allowed: {', '.join(ALLOWED_AUDIO_FORMATS)}"
        )
    
    # Check file size
    content = await file.read()
    if len(content) > MAX_AUDIO_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Maximum size: {MAX_AUDIO_SIZE // (1024*1024)} MB"
        )
    
    # Validate language if provided
    if language and language not in SUPPORTED_LANGUAGES and language != "en":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Language '{language}' not supported"
        )
    
    try:
        # Save audio file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as temp_file:
            temp_file.write(content)
            temp_audio_path = temp_file.name
        
        app_logger.info(f"Processing STT for file: {file.filename} ({len(content)} bytes)")
        
        # Validate audio file quality
        validation = speech_engine.validate_audio_file(temp_audio_path)
        if not validation.get("is_valid", True):
            if validation.get("is_silent", False):
                raise ValueError("Audio file appears to contain only silence or very low audio")
            if validation.get("sample_rate", 0) < 8000:
                raise ValueError("Audio sample rate too low (minimum 8kHz required)")
        
        # Perform STT directly
        result = await speech_engine.speech_to_text(
            audio_path=temp_audio_path,
            language=language
        )
        
        # Clean up temporary file
        os.unlink(temp_audio_path)
        
        app_logger.info(f"STT completed: {result['language']} detected")
        
        # Get language name from SUPPORTED_LANGUAGES or default
        language_name = SUPPORTED_LANGUAGES.get(result["language"], result["language"].title())
        
        return STTResponse(
            transcript=result["text"],
            language=result["language"],
            confidence=result["confidence"],
            processing_time=result.get("processing_time", result.get("duration", 0.0)),
            audio_duration=result["duration"]
        )
    
    except ValueError as e:
        # Clean up temp file if it exists
        try:
            os.unlink(temp_audio_path)
        except:
            pass
        app_logger.error(f"STT validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        # Clean up temp file if it exists
        try:
            os.unlink(temp_audio_path)
        except:
            pass
        app_logger.error(f"STT error: {e}")
        import traceback
        app_logger.error(f"STT traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Speech-to-text processing failed: {str(e)}"
        )


@router.post("/tts", response_model=TTSResponse)
async def text_to_speech(
    request: TTSRequest
):
    """
    Convert text to speech (Text-to-Speech) - Direct processing
    
    Supports all 22 Indian languages
    """
    # Validate input text
    if not request.text or len(request.text.strip()) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Text cannot be empty"
        )
    
    try:
        # Create unique output filename as MP3
        import uuid
        output_filename = f"tts_{request.language}_{uuid.uuid4().hex[:8]}.mp3"
        output_path = os.path.join(settings.OUTPUT_DIR, output_filename)
        
        # Ensure output directory exists
        os.makedirs(settings.OUTPUT_DIR, exist_ok=True)
        
        app_logger.info(f"Processing TTS for language: {request.language}")
        
        # Perform TTS directly
        result = await speech_engine.text_to_speech(
            text=request.text,
            language=request.language,
            output_path=output_path
        )
        
        app_logger.info(f"TTS completed: {result['language']} audio generated")
        
        # Get language name
        language_name = SUPPORTED_LANGUAGES.get(result["language"], result["language"].title())
        
        return TTSResponse(
            status="success",
            output_file=result["output_path"],
            duration=result.get("file_size_mb", 0.0) * 1024 * 1024,  # Convert MB to bytes for duration estimate
            language=result["language"],
            processing_time=result["generation_time"]
        )
    
    except ValueError as e:
        app_logger.error(f"TTS validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        app_logger.error(f"TTS error: {e}")
        import traceback
        app_logger.error(f"TTS traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Text-to-speech processing failed: {str(e)}"
        )


@router.post("/translate")
async def audio_localization(
    file: UploadFile = File(...),
    target_language: str = Form(...),
    domain: Optional[str] = Form("general")
):
    """
    Complete audio localization pipeline: STT → Translation → TTS
    
    Input: Audio file (.mp3, .wav, .mp4)
    Steps: Whisper STT → IndicTrans2/LLaMA Translation → VITS TTS
    Output: Localized audio file in storage/outputs/
    """
    # Validate target language
    if target_language not in SUPPORTED_LANGUAGES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Target language '{target_language}' not supported. Choose from: {list(SUPPORTED_LANGUAGES.keys())}"
        )
    
    # Validate file extension
    file_ext = "." + file.filename.split(".")[-1].lower() if "." in file.filename else ""
    if file_ext not in ALLOWED_AUDIO_FORMATS:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Audio format not supported. Allowed: {', '.join(ALLOWED_AUDIO_FORMATS)}"
        )
    
    # Check file size
    content = await file.read()
    if len(content) > MAX_AUDIO_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Maximum size: {MAX_AUDIO_SIZE // (1024*1024)} MB"
        )
    
    try:
        # Step 1: Save audio file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as temp_file:
            temp_file.write(content)
            temp_audio_path = temp_file.name
        
        app_logger.info(f"Starting audio localization: {file.filename} → {target_language}")
        start_time = time.time()
        
        # Step 2: Speech-to-Text (STT)
        stt_result = await speech_engine.speech_to_text(
            audio_path=temp_audio_path,
            language=None  # Auto-detect
        )
        
        source_text = stt_result["text"]
        detected_language = stt_result["language"]
        
        if not source_text.strip():
            raise ValueError("No speech detected in audio file")
        
        app_logger.info(f"STT completed: '{source_text[:100]}...' (Language: {detected_language})")
        
        # Step 3: Translation
        from app.services.nlp_engine import AdvancedNLPEngine
        nlp_engine = AdvancedNLPEngine()
        
        translation_result = await nlp_engine.translate(
            text=source_text,
            source_language=detected_language,
            target_languages=[target_language],
            domain=domain
        )
        
        # Extract single language result with better error handling
        if "translations" in translation_result and translation_result["translations"]:
            target_result = translation_result["translations"][0]
            translated_text = target_result.get("translated_text", source_text)
            confidence_score = target_result.get("confidence_score", 0.0)
        elif "translated_text" in translation_result:
            # Handle direct translation result format
            translated_text = translation_result["translated_text"]
            confidence_score = translation_result.get("confidence_score", 0.0)
        else:
            # Fallback to original text if translation fails
            app_logger.warning("Translation result format not recognized, using original text")
            translated_text = source_text
            confidence_score = 0.0
        
        app_logger.info(f"Translation completed: '{translated_text[:100]}...' (Confidence: {confidence_score})")
        
        # Step 4: Text-to-Speech (TTS)
        tts_result = await speech_engine.text_to_speech(
            text=translated_text,
            language=target_language
        )
        
        # Step 5: Save output to storage/outputs/
        output_filename = f"audio_localized_{target_language}_{int(time.time())}.mp3"
        output_path = os.path.join(settings.OUTPUT_DIR, output_filename)
        
        # Ensure output directory exists
        os.makedirs(settings.OUTPUT_DIR, exist_ok=True)
        
        # Copy the generated audio to outputs
        import shutil
        shutil.copy2(tts_result["output_path"], output_path)
        
        # Clean up temporary files
        os.unlink(temp_audio_path)
        if os.path.exists(tts_result["output_path"]):
            os.unlink(tts_result["output_path"])
        
        app_logger.info(f"Audio localization completed: {output_filename}")
        
        return {
            "status": "success",
            "message": "Audio localization completed successfully",
            "input_file": file.filename,
            "source_language": detected_language,
            "target_language": target_language,
            "domain": domain,
            "source_text": source_text,
            "translated_text": translated_text,
            "confidence_score": confidence_score,
            "output_file": output_filename,
            "output_path": f"/storage/outputs/{output_filename}",
            "processing_time_seconds": time.time() - start_time,
            "file_size_bytes": os.path.getsize(output_path) if os.path.exists(output_path) else 0
        }
        
    except Exception as e:
        app_logger.error(f"Audio localization failed: {str(e)}")
        # Clean up temporary files on error
        if 'temp_audio_path' in locals() and os.path.exists(temp_audio_path):
            os.unlink(temp_audio_path)
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Audio localization failed: {str(e)}"
        )


@router.post("/subtitles")
async def generate_subtitles(
    file: UploadFile = File(...),
    language: Optional[str] = Form(None),
    target_language: Optional[str] = Form(None),
    format: str = Form("srt"),  # srt or txt
    domain: Optional[str] = Form("general")
):
    """
    Generate subtitles/captions from audio for accessibility
    
    Input: Audio file (.mp3, .wav, .mp4)
    Output: Subtitle file (.srt or .txt) in storage/outputs/
    """
    # Validate format
    if format not in ["srt", "txt"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Format must be 'srt' or 'txt'"
        )
    
    # Validate file extension
    file_ext = "." + file.filename.split(".")[-1].lower() if "." in file.filename else ""
    if file_ext not in ALLOWED_AUDIO_FORMATS:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Audio format not supported. Allowed: {', '.join(ALLOWED_AUDIO_FORMATS)}"
        )
    
    # Check file size
    content = await file.read()
    if len(content) > MAX_AUDIO_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Maximum size: {MAX_AUDIO_SIZE // (1024*1024)} MB"
        )
    
    try:
        # Save audio file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as temp_file:
            temp_file.write(content)
            temp_audio_path = temp_file.name
        
        app_logger.info(f"Generating subtitles for: {file.filename} (Format: {format})")
        
        # Generate transcript with timestamps using Whisper
        transcript_result = await speech_engine.speech_to_text_with_timestamps(
            audio_path=temp_audio_path,
            language=language
        )
        
        detected_language = transcript_result.get("language", "unknown")
        segments = transcript_result.get("segments", [])
        
        # Translate segments if target language is specified
        if target_language and target_language != detected_language:
            app_logger.info(f"Translating subtitles from {detected_language} to {target_language}")
            
            # Validate target language
            if target_language not in SUPPORTED_LANGUAGES and target_language != "en":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Target language '{target_language}' not supported"
                )
            
            # Import NLP engine for translation
            from app.services.nlp_engine import AdvancedNLPEngine
            nlp_engine = AdvancedNLPEngine()
            
            # Translate each segment
            translated_segments = []
            for i, segment in enumerate(segments):
                if segment.get("text", "").strip():
                    try:
                        # Translate segment
                        translation_result = await nlp_engine.translate(
                            text=segment["text"].strip(),
                            source_language=detected_language,
                            target_languages=[target_language],
                            domain=domain
                        )
                        
                        # Extract translated text - handle both old and new response formats
                        if "translations" in translation_result and translation_result["translations"] and len(translation_result["translations"]) > 0:
                            # New format with translations array
                            translated_text = translation_result["translations"][0].get("translated_text", segment["text"].strip())
                        elif "translated_text" in translation_result:
                            # Direct format
                            translated_text = translation_result["translated_text"]
                        else:
                            translated_text = segment["text"].strip()  # Fallback
                        
                        # Create translated segment
                        translated_segments.append({
                            "start": segment["start"],
                            "end": segment["end"],
                            "text": translated_text
                        })
                        
                        app_logger.debug(f"Segment {i+1} translated: '{segment['text'].strip()}' → '{translated_text}'")
                        
                    except Exception as e:
                        app_logger.warning(f"Failed to translate segment {i+1}: {e}")
                        # Use original segment as fallback
                        translated_segments.append(segment)
                else:
                    translated_segments.append(segment)
            
            # Update transcript result with translated segments
            transcript_result["segments"] = translated_segments
            transcript_result["language"] = target_language
            transcript_result["translated"] = True
            transcript_result["original_language"] = detected_language
            
            app_logger.info(f"Translation completed: {len(translated_segments)} segments translated")
        
        # Generate subtitle content
        if format == "srt":
            subtitle_content = speech_engine.generate_srt_subtitles(transcript_result)
        else:  # txt format
            subtitle_content = speech_engine.generate_text_transcript(transcript_result)
        
        # Save subtitle file with target language in filename if translated
        if target_language and target_language != detected_language:
            output_filename = f"subtitles_{detected_language}_to_{target_language}_{format}_{int(time.time())}.{format}"
        else:
            output_filename = f"subtitles_{format}_{int(time.time())}.{format}"
        output_path = os.path.join(settings.OUTPUT_DIR, output_filename)
        
        # Ensure output directory exists
        os.makedirs(settings.OUTPUT_DIR, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(subtitle_content)
        
        # Clean up temporary files
        os.unlink(temp_audio_path)
        
        app_logger.info(f"Subtitles generated: {output_filename}")
        
        return {
            "status": "success",
            "message": "Subtitles generated successfully",
            "input_file": file.filename,
            "detected_language": transcript_result.get("original_language", transcript_result.get("language", "unknown")),
            "target_language": target_language if target_language else transcript_result.get("language", "unknown"),
            "translated": transcript_result.get("translated", False),
            "format": format,
            "output_file": output_filename,
            "output_path": f"/storage/outputs/{output_filename}",
            "subtitle_content": subtitle_content,  # Return full content without truncation
            "duration_seconds": transcript_result.get("duration", 0),
            "segment_count": len(transcript_result.get("segments", [])),
            "domain": domain
        }
        
    except Exception as e:
        app_logger.error(f"Subtitle generation failed: {str(e)}")
        # Clean up temporary files on error
        if 'temp_audio_path' in locals() and os.path.exists(temp_audio_path):
            os.unlink(temp_audio_path)
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Subtitle generation failed: {str(e)}"
        )


@router.post("/localize")
async def audio_localization(
    file: UploadFile = File(...),
    target_language: str = Form(...),
    domain: Optional[str] = Form("general")
):
    """
    Audio Localization Pipeline:
    1. Speech-to-Text (Whisper)
    2. Translation (IndicTrans2/LLaMA)
    3. Text-to-Speech (TTS)
    
    Input: Audio file (.mp3, .wav, .mp4, etc.)
    Output: Localized audio in target language
    """
    # Validate target language
    if target_language not in SUPPORTED_LANGUAGES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Target language '{target_language}' not supported. Choose from: {list(SUPPORTED_LANGUAGES.keys())}"
        )
    
    # Validate file extension
    file_ext = "." + file.filename.split(".")[-1].lower() if "." in file.filename else ""
    if file_ext not in ALLOWED_AUDIO_FORMATS:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Audio format not supported. Allowed: {', '.join(ALLOWED_AUDIO_FORMATS)}"
        )
    
    # Check file size
    content = await file.read()
    if len(content) > MAX_AUDIO_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Maximum size: {MAX_AUDIO_SIZE // (1024*1024)} MB"
        )
    
    try:
        # Save audio file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext, mode='wb') as temp_file:
            temp_file.write(content)
            temp_audio_path = temp_file.name
        
        app_logger.info(f"Starting audio localization: {file.filename} → {target_language}")
        start_time = time.time()
        
        # Initialize services using the same pattern as other routes
        from app.services.speech_engine import get_speech_engine
        speech_service = get_speech_engine()
        from app.services.nlp_engine import AdvancedNLPEngine
        nlp_engine = AdvancedNLPEngine()
        
        # Step 1: Speech-to-Text
        app_logger.info("Step 1: Converting speech to text...")
        stt_result = await speech_service.speech_to_text(
            audio_path=temp_audio_path,
            language=None  # Auto-detect
        )
        
        source_text = stt_result["text"]
        detected_language = stt_result["language"]
        
        # Step 2: Translation
        app_logger.info(f"Step 2: Translating from {detected_language} to {target_language}...")
        app_logger.info(f"Source text length: {len(source_text)} characters")
        app_logger.info(f"Source text preview: {source_text[:100]}...")
        
        translation_result = await nlp_engine.translate(
            text=source_text,
            source_language=detected_language,
            target_languages=[target_language],
            domain=domain
        )
        
        app_logger.info(f"Translation result keys: {list(translation_result.keys())}")
        if "translations" in translation_result:
            app_logger.info(f"Number of translations: {len(translation_result['translations'])}")
        
        # Extract single language result with better error handling
        if "translations" in translation_result and translation_result["translations"]:
            target_result = translation_result["translations"][0]
            translated_text = target_result.get("translated_text", source_text)
            confidence_score = target_result.get("confidence_score", 0.0)
            app_logger.info(f"Extracted translation from translations array: {translated_text[:100]}...")
        elif "translated_text" in translation_result:
            # Handle direct translation result format
            translated_text = translation_result["translated_text"]
            confidence_score = translation_result.get("confidence_score", 0.0)
            app_logger.info(f"Extracted translation from direct format: {translated_text[:100]}...")
        else:
            # Fallback to original text if translation fails
            app_logger.warning("Translation result format not recognized, using original text")
            translated_text = source_text
            confidence_score = 0.0
        
        app_logger.info(f"Final translated text length: {len(translated_text)} characters")
        app_logger.info(f"Final translated text: {translated_text}")
        
        # Step 3: Text-to-Speech
        app_logger.info("Step 3: Converting translated text to speech...")
        tts_result = await speech_service.text_to_speech(
            text=translated_text,
            language=target_language
        )
        
        # Move output to storage/outputs
        output_filename = f"audio_localized_{target_language}_{int(time.time())}.mp3"
        output_path = os.path.join(settings.OUTPUT_DIR, output_filename)
        
        # Copy TTS result to outputs directory
        import shutil
        shutil.copy2(tts_result["output_path"], output_path)
        
        # Get file size
        file_size = os.path.getsize(output_path)
        
        processing_time = time.time() - start_time
        
        # Clean up temporary files
        os.unlink(temp_audio_path)
        if os.path.exists(tts_result["output_path"]):
            os.unlink(tts_result["output_path"])
        
        app_logger.info(f"Audio localization completed in {processing_time:.2f}s")
        
        return {
            "status": "success",
            "message": "Audio localization completed successfully",
            "input_file": file.filename,
            "target_language": target_language,
            "domain": domain,
            "pipeline_steps": {
                "stt": {
                    "detected_language": detected_language,
                    "transcribed_text": source_text,  # Return full text without truncation
                    "duration_seconds": stt_result.get("duration", 0)
                },
                "translation": {
                    "translated_text": translated_text,  # Return full translation without truncation
                    "confidence_score": confidence_score
                },
                "tts": {
                    "generated": True,
                    "format": "mp3"
                }
            },
            "processing_time_seconds": processing_time,
            "output_file": output_filename,
            "output_path": f"/speech/download/{output_filename}",
            "file_size_bytes": file_size
        }
        
    except Exception as e:
        app_logger.error(f"Audio localization failed: {str(e)}")
        # Clean up temporary files on error
        if 'temp_audio_path' in locals() and os.path.exists(temp_audio_path):
            os.unlink(temp_audio_path)
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Audio localization failed: {str(e)}"
        )


@router.get("/download/{filename}")
async def download_audio(
    filename: str
):
    """
    Download generated audio file
    """
    audio_path = os.path.join(settings.OUTPUT_DIR, filename)
    
    if not os.path.exists(audio_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audio file not found"
        )
    
    return FileResponse(
        path=audio_path,
        filename=filename,
        media_type="audio/mpeg"
    )


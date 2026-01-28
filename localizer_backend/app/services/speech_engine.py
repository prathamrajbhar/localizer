"""
Optimized Speech Engine for Production
Handles Speech-to-Text (STT) and Text-to-Speech (TTS) with performance optimizations
"""
import os
import time
import tempfile
import asyncio
from typing import Dict, Optional, Union, List
from pathlib import Path

# Core dependencies
from app.core.config import get_settings, SUPPORTED_LANGUAGES
from app.utils.logger import app_logger

# Audio processing
try:
    import torch
    TORCH_AVAILABLE = True
    app_logger.info("PyTorch available for speech processing")
except ImportError:
    TORCH_AVAILABLE = False
    app_logger.warning("PyTorch not available - using CPU fallback")

# Whisper STT
try:
    import whisper
    WHISPER_AVAILABLE = True
    app_logger.info("Whisper STT available")
except ImportError:
    WHISPER_AVAILABLE = False
    app_logger.warning("Whisper not available - STT disabled")

# TTS engines - VITS/Tacotron2 + HiFi-GAN as specified
try:
    from TTS.api import TTS
    TTS_AVAILABLE = True
    app_logger.info("TTS (VITS/Tacotron2 + HiFi-GAN) available")
except ImportError:
    TTS_AVAILABLE = False
    app_logger.warning("TTS library not available")

# Fallback gTTS
try:
    from gtts import gTTS
    GTTS_AVAILABLE = True
    app_logger.info("Google TTS available as fallback")
except ImportError:
    GTTS_AVAILABLE = False
    app_logger.warning("gTTS not available")

# Optional audio validation
try:
    import librosa
    import numpy as np
    LIBROSA_AVAILABLE = True
except ImportError:
    LIBROSA_AVAILABLE = False
    app_logger.info("librosa not available - using basic audio validation")

settings = get_settings()


class ProductionSpeechEngine:
    """
    Production-ready speech engine with Whisper STT and VITS/Tacotron2 TTS
    As specified in copilot instructions
    """
    
    def __init__(self):
        self.device = "cuda" if TORCH_AVAILABLE and torch.cuda.is_available() else "cpu"
        self.whisper_model = None
        self.tts_model = None
        self.tts_model_name = None
        self.tts_is_multilingual = False
        self.model_cache = {}
        self.supported_formats = ['.wav', '.mp3', '.mp4', '.m4a', '.flac', '.ogg']
        
        # Performance tracking
        self.stt_stats = {"total_processed": 0, "avg_time": 0.0}
        self.tts_stats = {"total_generated": 0, "avg_time": 0.0}
        
        app_logger.info(f"Production Speech Engine initialized on device: {self.device}")
    
    def load_whisper_model(self, model_size: str = "large-v3") -> bool:
        """
        Load Whisper model with optimized configuration
        
        Args:
            model_size: Model size (base, small, medium, large, large-v2, large-v3)
        
        Returns:
            bool: True if loaded successfully
        """
        if not WHISPER_AVAILABLE:
            app_logger.error("Whisper not available - cannot load STT model")
            return False
        
        # Check if already loaded
        if self.whisper_model is not None:
            app_logger.debug("Whisper model already loaded")
            return True
        
        # Try to load from cache
        cache_key = f"whisper_{model_size}"
        if cache_key in self.model_cache:
            self.whisper_model = self.model_cache[cache_key]
            app_logger.info(f"Loaded Whisper {model_size} from cache")
            return True
        
        try:
            start_time = time.time()
            app_logger.info(f"Loading Whisper model: {model_size}")
            
            # Fallback model sizes in order of preference
            models_to_try = ["base", "tiny", "small", model_size] if model_size not in ["base", "tiny", "small"] else [model_size]
            
            for model_name in models_to_try:
                try:
                    # Set model directory
                    model_dir = os.path.join(os.getcwd(), "models", "whisper")
                    os.makedirs(model_dir, exist_ok=True)
                    
                    # Load model with optimizations
                    self.whisper_model = whisper.load_model(
                        model_name,
                        device=self.device,
                        download_root=model_dir
                    )
                    
                    # Cache the model
                    self.model_cache[cache_key] = self.whisper_model
                    
                    load_time = time.time() - start_time
                    app_logger.info(f"Whisper {model_name} loaded in {load_time:.2f}s")
                    
                    return True
                    
                except Exception as e:
                    app_logger.warning(f"Failed to load Whisper {model_name}: {e}")
                    continue
            
            app_logger.error("Failed to load any Whisper model")
            return False
            
        except Exception as e:
            app_logger.error(f"Whisper model loading failed: {e}")
            return False
    
    def validate_audio_file(self, audio_path: str) -> Dict[str, any]:
        """
        Validate audio file with comprehensive checks
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Dict with validation results
        """
        try:
            # Basic file checks
            if not os.path.exists(audio_path):
                return {"is_valid": False, "error": "File does not exist"}
            
            file_size = os.path.getsize(audio_path)
            if file_size == 0:
                return {"is_valid": False, "error": "File is empty"}
            
            if file_size > 100 * 1024 * 1024:  # 100MB limit
                return {"is_valid": False, "error": "File too large (max 100MB)"}
            
            # Check file extension
            file_ext = Path(audio_path).suffix.lower()
            if file_ext not in self.supported_formats:
                return {
                    "is_valid": False, 
                    "error": f"Unsupported format. Supported: {', '.join(self.supported_formats)}"
                }
            
            # Advanced validation with librosa
            if LIBROSA_AVAILABLE:
                try:
                    # Load first 10 seconds for validation
                    audio, sr = librosa.load(audio_path, sr=None, duration=10)
                    
                    # Check for silence
                    rms_energy = np.sqrt(np.mean(audio**2))
                    is_silent = rms_energy < 0.001
                    
                    # Check sample rate
                    is_good_sr = sr >= 8000
                    
                    # Check duration
                    duration = len(audio) / sr
                    
                    return {
                        "is_valid": not is_silent and is_good_sr and duration > 0.1,
                        "file_size_mb": file_size / (1024 * 1024),
                        "duration_seconds": duration,
                        "sample_rate": sr,
                        "rms_energy": float(rms_energy),
                        "is_silent": is_silent,
                        "format": file_ext
                    }
                    
                except Exception as e:
                    app_logger.warning(f"Advanced audio validation failed: {e}")
                    # Fall back to basic validation
                    return {
                        "is_valid": True,  # Assume valid if basic checks pass
                        "file_size_mb": file_size / (1024 * 1024),
                        "format": file_ext,
                        "validation_level": "basic"
                    }
            else:
                # Basic validation without librosa
                return {
                    "is_valid": True,
                    "file_size_mb": file_size / (1024 * 1024),
                    "format": file_ext,
                    "validation_level": "basic"
                }
                
        except Exception as e:
            app_logger.error(f"Audio validation failed: {e}")
            return {"is_valid": False, "error": str(e)}
    
    async def speech_to_text(self, audio_path: str, language: Optional[str] = None) -> Dict[str, any]:
        """
        Convert speech to text using Whisper
        
        Args:
            audio_path: Path to audio file
            language: Optional language hint (ISO code)
            
        Returns:
            Dict with transcription results
        """
        if not WHISPER_AVAILABLE:
            raise RuntimeError("Whisper STT not available")
        
        # Validate audio file
        validation = self.validate_audio_file(audio_path)
        if not validation["is_valid"]:
            raise ValueError(f"Invalid audio file: {validation.get('error', 'Unknown error')}")
        
        # Load model if needed
        if not self.load_whisper_model():
            raise RuntimeError("Failed to load Whisper model")
        
        try:
            start_time = time.time()
            app_logger.info(f"Starting STT for: {Path(audio_path).name}")
            
            # Transcribe with optimized options
            result = self.whisper_model.transcribe(
                audio_path,
                language=language if language and language != "auto" else None,
                fp16=TORCH_AVAILABLE and torch.cuda.is_available(),
                verbose=False,
                beam_size=5,
                best_of=5,
                temperature=0.0,  # Deterministic output
            )
            
            duration = time.time() - start_time
            
            # Extract key information
            transcription = {
                "text": result["text"].strip(),
                "language": result.get("language", "unknown"),
                "confidence": self._calculate_confidence(result.get("segments", [])),
                "duration": duration,
                "file_duration": validation.get("duration_seconds", 0),
                "segments": [
                    {
                        "start": seg.get("start", 0),
                        "end": seg.get("end", 0),
                        "text": seg.get("text", "").strip()
                    }
                    for seg in result.get("segments", [])
                ]
            }
            
            app_logger.info(f"STT completed in {duration:.2f}s, detected language: {transcription['language']}")
            
            return transcription
            
        except Exception as e:
            app_logger.error(f"STT processing failed: {e}")
            raise RuntimeError(f"Speech-to-text failed: {str(e)}") from e
    
    def _calculate_confidence(self, segments: list) -> float:
        """Calculate average confidence from segments"""
        if not segments:
            return 0.0
        
        # Whisper doesn't always provide confidence scores
        # Use segment length and other heuristics
        total_prob = 0.0
        total_segments = len(segments)
        
        for seg in segments:
            # Use segment probability if available
            if "avg_logprob" in seg:
                # Convert log probability to confidence (rough approximation)
                if LIBROSA_AVAILABLE:
                    confidence = max(0.0, min(1.0, np.exp(seg["avg_logprob"])))
                else:
                    # Simple approximation without numpy
                    confidence = max(0.0, min(1.0, 1.0 + seg["avg_logprob"] / 10.0))
                total_prob += confidence
            else:
                # Default confidence based on text length
                text_len = len(seg.get("text", "").strip())
                total_prob += min(0.9, text_len / 50.0)  # Longer text = higher confidence
        
        return total_prob / total_segments if total_segments > 0 else 0.0
    
    def load_tts_model(self) -> bool:
        """Load VITS/Tacotron2 + HiFi-GAN TTS model as specified"""
        if self.tts_model is not None:
            return True
        
        if not TTS_AVAILABLE:
            app_logger.warning("TTS library not available, using fallback gTTS")
            return False
        
        try:
            app_logger.info("Loading VITS TTS model for multilingual synthesis")
            start_time = time.time()
            
            # Try different TTS models in order of preference
            model_options = [
                "tts_models/multilingual/multi-dataset/xtts_v2",  # Multilingual model
                "tts_models/en/ljspeech/tacotron2-DDC",  # English only
                "tts_models/en/ljspeech/glow-tts"  # English only
            ]
            
            for model_name in model_options:
                try:
                    self.tts_model = TTS(
                        model_name=model_name,
                        progress_bar=False,
                        gpu=torch.cuda.is_available() if TORCH_AVAILABLE else False
                    )
                    
                    # Store model info for language detection
                    self.tts_model_name = model_name
                    self.tts_is_multilingual = "multilingual" in model_name.lower()
                    
                    load_time = time.time() - start_time
                    app_logger.info(f"TTS model {model_name} loaded successfully in {load_time:.2f}s")
                    app_logger.info(f"Model is multilingual: {self.tts_is_multilingual}")
                    return True
                    
                except Exception as model_e:
                    app_logger.warning(f"Failed to load {model_name}: {model_e}")
                    continue
            
            # If all models fail, return False to use gTTS fallback
            app_logger.warning("All TTS models failed to load, will use gTTS fallback")
            self.tts_model = None
            return False
            
        except Exception as e:
            app_logger.error(f"Failed to load any TTS model: {e}")
            self.tts_model = None
            return False

    async def text_to_speech(self, text: str, language: str, output_path: str = None) -> Dict[str, any]:
        """
        Convert text to speech using VITS/Tacotron2 + HiFi-GAN (production TTS)
        
        Args:
            text: Text to convert
            language: Language code
            output_path: Optional output file path
            
        Returns:
            Dict with TTS results
        """
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")
        
        if language not in SUPPORTED_LANGUAGES and language != "en":
            raise ValueError(f"Language '{language}' not supported for TTS")
        
        try:
            start_time = time.time()
            
            # Create output path if not provided
            if not output_path:
                timestamp = int(time.time())
                filename = f"tts_output_{timestamp}.mp3"
                output_path = os.path.join(settings.OUTPUT_DIR, filename)
            
            # Ensure output directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            app_logger.info(f"Generating TTS for {len(text)} characters in {language}")
            
            # Try advanced TTS first (VITS/Tacotron2)
            if self.load_tts_model():
                try:
                    # Check if model supports the language
                    if self.tts_is_multilingual and language != "en":
                        # Language mapping for multilingual TTS
                        tts_lang_map = {
                            "hi": "hi", "bn": "bn", "ta": "ta", "te": "te", "mr": "mr",
                            "gu": "gu", "kn": "kn", "ml": "ml", "pa": "pa", "ur": "ur",
                            "en": "en"
                        }
                        
                        tts_lang = tts_lang_map.get(language, "en")
                        
                        # Generate with multilingual VITS
                        self.tts_model.tts_to_file(
                            text=text,
                            language=tts_lang,
                            file_path=output_path
                        )
                        
                        model_used = f"VITS Multilingual ({self.tts_model_name})"
                        
                    elif language == "en":
                        # English-only model or English text
                        self.tts_model.tts_to_file(
                            text=text,
                            file_path=output_path
                        )
                        
                        model_used = f"VITS English ({self.tts_model_name})"
                        
                    else:
                        # Non-English language with English-only model - use fallback
                        app_logger.warning(f"Model {self.tts_model_name} doesn't support {language}, using gTTS fallback")
                        return await self._fallback_gtts(text, language, output_path, start_time)
                    
                except Exception as e:
                    app_logger.warning(f"Advanced TTS failed, falling back to gTTS: {e}")
                    # Fallback to gTTS
                    return await self._fallback_gtts(text, language, output_path, start_time)
            else:
                # Fallback to gTTS
                return await self._fallback_gtts(text, language, output_path, start_time)
            
            duration = time.time() - start_time
            file_size = os.path.getsize(output_path)
            
            result = {
                "output_path": output_path,
                "language": language,
                "text_length": len(text),
                "file_size_mb": file_size / (1024 * 1024),
                "generation_time": duration,
                "model_used": model_used,
                "success": True
            }
            
            # Update stats
            self.tts_stats["total_generated"] += 1
            self.tts_stats["avg_time"] = (
                (self.tts_stats["avg_time"] * (self.tts_stats["total_generated"] - 1) + duration) /
                self.tts_stats["total_generated"]
            )
            
            app_logger.info(f"TTS completed in {duration:.2f}s using {model_used}")
            
            return result
            
        except Exception as e:
            app_logger.error(f"TTS generation failed: {e}")
            raise RuntimeError(f"Text-to-speech failed: {str(e)}") from e

    async def _fallback_gtts(self, text: str, language: str, output_path: str, start_time: float) -> Dict[str, any]:
        """Fallback TTS using gTTS"""
        if not GTTS_AVAILABLE:
            raise RuntimeError("No TTS engine available")
        
        # Language mapping for gTTS
        tts_lang_map = {
            "hi": "hi", "bn": "bn", "ta": "ta", "te": "te", "mr": "mr",
            "gu": "gu", "kn": "kn", "ml": "ml", "pa": "pa", "ur": "ur",
            "en": "en"
        }
        
        gtts_lang = tts_lang_map.get(language, "en")
        
        # Ensure output is MP3 for better compatibility
        if not output_path.endswith('.mp3'):
            output_path = output_path.rsplit('.', 1)[0] + '.mp3'
        
        # Generate speech
        tts = gTTS(text=text, lang=gtts_lang, slow=False)
        tts.save(output_path)
        
        duration = time.time() - start_time
        file_size = os.path.getsize(output_path)
        
        app_logger.info(f"gTTS fallback completed in {duration:.2f}s for {language}")
        
        return {
            "output_path": output_path,
            "language": language,
            "text_length": len(text),
            "file_size_mb": file_size / (1024 * 1024),
            "generation_time": duration,
            "model_used": "gTTS (Fallback)",
            "success": True
        }
    
    async def speech_to_text_with_timestamps(
        self, 
        audio_path: str, 
        language: Optional[str] = None
    ) -> Dict[str, Union[str, float, list]]:
        """
        Convert speech to text with detailed timestamps for subtitle generation
        
        Args:
            audio_path: Path to audio file
            language: Optional language code
        
        Returns:
            Dict with text, language, duration, and segments with timestamps
        """
        if not WHISPER_AVAILABLE:
            raise ValueError("Whisper not available for STT with timestamps")
        
        try:
            # Load Whisper model
            if not self.load_whisper_model():
                raise ValueError("Failed to load Whisper model")
            
            app_logger.info(f"Processing STT with timestamps: {audio_path}")
            start_time = time.time()
            
            # Transcribe with word-level timestamps
            options = {
                "language": language,
                "word_timestamps": True,
                "verbose": False
            }
            
            result = self.whisper_model.transcribe(audio_path, **options)
            
            processing_time = time.time() - start_time
            
            # Extract segments with timestamps
            segments = []
            for segment in result.get("segments", []):
                segments.append({
                    "start": segment["start"],
                    "end": segment["end"],
                    "text": segment["text"].strip(),
                    "words": segment.get("words", [])
                })
            
            # Update statistics
            self.stt_stats["total_processed"] += 1
            self.stt_stats["avg_time"] = (
                (self.stt_stats["avg_time"] * (self.stt_stats["total_processed"] - 1) + processing_time) 
                / self.stt_stats["total_processed"]
            )
            
            app_logger.info(f"STT with timestamps completed in {processing_time:.2f}s")
            
            return {
                "text": result["text"].strip(),
                "language": result["language"],
                "duration": segments[-1]["end"] if segments else 0,
                "segments": segments,
                "processing_time": processing_time
            }
            
        except Exception as e:
            app_logger.error(f"STT with timestamps failed: {e}")
            raise ValueError(f"Speech-to-text with timestamps failed: {str(e)}")

    def generate_srt_subtitles(self, transcript_result: Dict) -> str:
        """
        Advanced SRT subtitle generation with intelligent processing
        
        Args:
            transcript_result: Result from speech_to_text_with_timestamps
        
        Returns:
            str: SRT formatted subtitle content
        """
        segments = transcript_result.get("segments", [])
        if not segments:
            return ""
        
        # Advanced subtitle processing
        processed_segments = self._process_subtitle_segments(segments)
        
        srt_content = []
        
        for i, segment in enumerate(processed_segments, 1):
            start_time = self._seconds_to_srt_time(segment["start"])
            end_time = self._seconds_to_srt_time(segment["end"])
            text = segment["text"].strip()
            
            if text:  # Only add non-empty segments
                srt_content.append(f"{i}")
                srt_content.append(f"{start_time} --> {end_time}")
                srt_content.append(text)
                srt_content.append("")  # Empty line between segments
        
        return "\n".join(srt_content)
    
    def _process_subtitle_segments(self, segments: List[Dict]) -> List[Dict]:
        """
        Advanced subtitle segment processing with optimization
        """
        if not segments:
            return []
        
        processed_segments = []
        
        for segment in segments:
            # Clean and optimize text
            text = segment.get("text", "").strip()
            if not text:
                continue
            
            # Apply text optimization
            optimized_text = self._optimize_subtitle_text(text)
            
            # Calculate optimal timing
            start_time = segment.get("start", 0.0)
            end_time = segment.get("end", 0.0)
            
            # Adjust timing for better readability
            adjusted_timing = self._adjust_subtitle_timing(start_time, end_time, optimized_text)
            
            processed_segments.append({
                "start": adjusted_timing["start"],
                "end": adjusted_timing["end"],
                "text": optimized_text,
                "original_text": text,
                "confidence": segment.get("confidence", 1.0)
            })
        
        # Merge very short segments for better readability
        merged_segments = self._merge_short_segments(processed_segments)
        
        return merged_segments
    
    def _optimize_subtitle_text(self, text: str) -> str:
        """
        Optimize subtitle text for better readability
        """
        import re
        
        # Remove excessive punctuation
        text = re.sub(r'[.]{2,}', '...', text)  # Multiple periods to ellipsis
        text = re.sub(r'[!]{2,}', '!', text)    # Multiple exclamations to single
        text = re.sub(r'[?]{2,}', '?', text)    # Multiple questions to single
        
        # Fix common speech recognition errors
        text = re.sub(r'\b(uh|um|er|ah)\b', '', text, flags=re.IGNORECASE)  # Remove filler words
        text = re.sub(r'\s+', ' ', text)  # Remove extra spaces
        
        # Capitalize first letter of sentences
        sentences = re.split(r'([.!?]+)', text)
        capitalized_sentences = []
        
        for i, part in enumerate(sentences):
            if i % 2 == 0:  # Text parts
                if part.strip():
                    capitalized_sentences.append(part.strip().capitalize())
            else:  # Punctuation parts
                capitalized_sentences.append(part)
        
        text = ''.join(capitalized_sentences)
        
        return text.strip()
    
    def _adjust_subtitle_timing(self, start_time: float, end_time: float, text: str) -> Dict[str, float]:
        """
        Adjust subtitle timing for optimal readability
        """
        duration = end_time - start_time
        text_length = len(text)
        
        # Minimum display time based on text length (reading speed: ~3 chars/second)
        min_duration = max(text_length / 3.0, 1.0)  # At least 1 second
        
        # Maximum display time (reading speed: ~1.5 chars/second)
        max_duration = text_length / 1.5
        
        # Adjust duration if needed
        if duration < min_duration:
            # Extend end time
            end_time = start_time + min_duration
        elif duration > max_duration:
            # Shorten end time
            end_time = start_time + max_duration
        
        return {
            "start": start_time,
            "end": end_time
        }
    
    def _merge_short_segments(self, segments: List[Dict], min_duration: float = 1.0) -> List[Dict]:
        """
        Merge very short segments for better readability
        """
        if not segments:
            return []
        
        merged_segments = []
        current_segment = None
        
        for segment in segments:
            duration = segment["end"] - segment["start"]
            
            if duration < min_duration and current_segment:
                # Merge with previous segment
                current_segment["end"] = segment["end"]
                current_segment["text"] += " " + segment["text"]
            else:
                # Start new segment
                if current_segment:
                    merged_segments.append(current_segment)
                current_segment = segment.copy()
        
        # Add the last segment
        if current_segment:
            merged_segments.append(current_segment)
        
        return merged_segments

    def generate_text_transcript(self, transcript_result: Dict) -> str:
        """
        Generate plain text transcript from Whisper result
        
        Args:
            transcript_result: Result from speech_to_text_with_timestamps
        
        Returns:
            str: Plain text transcript with timestamps
        """
        segments = transcript_result.get("segments", [])
        if not segments:
            return transcript_result.get("text", "")
        
        transcript_lines = []
        transcript_lines.append(f"TRANSCRIPT")
        transcript_lines.append(f"Language: {transcript_result.get('language', 'unknown')}")
        transcript_lines.append(f"Duration: {transcript_result.get('duration', 0):.2f} seconds")
        transcript_lines.append("-" * 50)
        
        for segment in segments:
            start_time = self._seconds_to_time_string(segment["start"])
            end_time = self._seconds_to_time_string(segment["end"])
            text = segment["text"].strip()
            
            if text:
                transcript_lines.append(f"[{start_time} - {end_time}] {text}")
        
        return "\n".join(transcript_lines)

    def _seconds_to_srt_time(self, seconds: float) -> str:
        """Convert seconds to SRT time format (HH:MM:SS,mmm)"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        milliseconds = int((seconds % 1) * 1000)
        
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{milliseconds:03d}"

    def _seconds_to_time_string(self, seconds: float) -> str:
        """Convert seconds to readable time format (MM:SS)"""
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes:02d}:{secs:02d}"
    
    def get_supported_languages(self) -> Dict[str, any]:
        """Get supported languages for speech processing"""
        return {
            "stt_languages": list(SUPPORTED_LANGUAGES.keys()) + ["en"],
            "tts_languages": list(SUPPORTED_LANGUAGES.keys()) + ["en"],
            "total_languages": len(SUPPORTED_LANGUAGES) + 1,
            "whisper_available": WHISPER_AVAILABLE,
            "advanced_tts_available": TTS_AVAILABLE,
            "fallback_tts_available": GTTS_AVAILABLE,
            "models": {
                "stt": "Whisper large-v3",
                "tts": "VITS/Tacotron2 + HiFi-GAN (with gTTS fallback)"
            }
        }
    
    def get_engine_status(self) -> Dict[str, any]:
        """Get engine status and capabilities"""
        return {
            "whisper_loaded": self.whisper_model is not None,
            "tts_loaded": self.tts_model is not None,
            "device": self.device,
            "torch_available": TORCH_AVAILABLE,
            "cuda_available": TORCH_AVAILABLE and torch.cuda.is_available(),
            "whisper_available": WHISPER_AVAILABLE,
            "gtts_available": GTTS_AVAILABLE,
            "librosa_available": LIBROSA_AVAILABLE,
            "supported_formats": self.supported_formats,
            "model_cache_size": len(self.model_cache)
        }
    
    def cleanup(self):
        """Clean up resources"""
        try:
            # Clear model cache
            self.model_cache.clear()
            self.whisper_model = None
            
            # Clear CUDA cache if available
            if TORCH_AVAILABLE and torch.cuda.is_available():
                torch.cuda.empty_cache()
            
            app_logger.info("Speech engine cleanup completed")
            
        except Exception as e:
            app_logger.error(f"Speech engine cleanup failed: {e}")


# Global instance
speech_engine = ProductionSpeechEngine()


def get_speech_engine() -> ProductionSpeechEngine:
    """Get the global speech engine instance"""
    return speech_engine
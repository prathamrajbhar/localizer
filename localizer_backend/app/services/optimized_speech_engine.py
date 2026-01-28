"""
Optimized Speech Engine with Performance Improvements
Faster processing with model caching, smaller models, and async optimizations
"""
import os
import time
import tempfile
import asyncio
from typing import Dict, Optional, Union, List
from pathlib import Path
import threading
from concurrent.futures import ThreadPoolExecutor

# Core dependencies
from app.core.config import get_settings, SUPPORTED_LANGUAGES
from app.utils.logger import app_logger

# Audio processing
try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

# Whisper STT
try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False

settings = get_settings()


class OptimizedSpeechEngine:
    """
    Optimized Speech Engine with performance improvements:
    - Model caching and reuse
    - Smaller, faster models by default
    - Async processing for I/O operations
    - Memory optimization
    - Progress tracking
    """
    
    def __init__(self):
        self.device = "cuda" if TORCH_AVAILABLE and torch.cuda.is_available() else "cpu"
        self.model_cache = {}
        self.whisper_model = None
        self.current_model_size = None
        
        # Performance settings
        self.default_model_size = "base"  # Much faster than large-v3
        self.fast_model_size = "tiny"     # Fastest for quick processing
        self.quality_model_size = "small" # Good balance
        
        # Thread pool for async operations
        self.executor = ThreadPoolExecutor(max_workers=2)
        
        app_logger.info(f"Optimized Speech Engine initialized on device: {self.device}")
    
    def _get_optimal_model_size(self, audio_duration: float, quality_preference: str = "balanced") -> str:
        """
        Choose optimal model size based on audio duration and quality preference
        
        Args:
            audio_duration: Duration of audio in seconds
            quality_preference: "fast", "balanced", or "quality"
        
        Returns:
            Optimal model size
        """
        if quality_preference == "fast" or audio_duration > 300:  # 5+ minutes
            return self.fast_model_size
        elif quality_preference == "quality" and audio_duration < 60:  # < 1 minute
            return self.quality_model_size
        else:
            return self.default_model_size
    
    async def load_whisper_model_async(self, model_size: str = None) -> bool:
        """
        Asynchronously load Whisper model with caching
        
        Args:
            model_size: Model size to load (default: auto-select)
        
        Returns:
            True if model loaded successfully
        """
        if model_size is None:
            model_size = self.default_model_size
        
        # Check if model is already loaded
        if self.whisper_model is not None and self.current_model_size == model_size:
            app_logger.debug(f"Whisper {model_size} already loaded")
            return True
        
        # Try to load from cache
        cache_key = f"whisper_{model_size}"
        if cache_key in self.model_cache:
            self.whisper_model = self.model_cache[cache_key]
            self.current_model_size = model_size
            app_logger.info(f"Loaded Whisper {model_size} from cache")
            return True
        
        try:
            app_logger.info(f"Loading Whisper model: {model_size}")
            start_time = time.time()
            
            # Load model in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            self.whisper_model = await loop.run_in_executor(
                self.executor,
                self._load_whisper_model_sync,
                model_size
            )
            
            if self.whisper_model is not None:
                # Cache the model
                self.model_cache[cache_key] = self.whisper_model
                self.current_model_size = model_size
                
                load_time = time.time() - start_time
                app_logger.info(f"Whisper {model_size} loaded in {load_time:.2f}s")
                return True
            else:
                app_logger.error(f"Failed to load Whisper {model_size}")
                return False
                
        except Exception as e:
            app_logger.error(f"Whisper model loading failed: {e}")
            return False
    
    def _load_whisper_model_sync(self, model_size: str):
        """Synchronous model loading for thread pool execution"""
        try:
            # Set model directory
            model_dir = os.path.join(os.getcwd(), "models", "whisper")
            os.makedirs(model_dir, exist_ok=True)
            
            # Load model with optimizations
            model = whisper.load_model(
                model_size,
                device=self.device,
                download_root=model_dir
            )
            
            return model
            
        except Exception as e:
            app_logger.warning(f"Failed to load Whisper {model_size}: {e}")
            return None
    
    async def speech_to_text_optimized(
        self, 
        audio_path: str, 
        language: Optional[str] = None,
        quality_preference: str = "balanced",
        with_timestamps: bool = False
    ) -> Dict[str, Union[str, float, list]]:
        """
        Optimized speech-to-text with automatic model selection
        
        Args:
            audio_path: Path to audio file
            language: Optional language code
            quality_preference: "fast", "balanced", or "quality"
            with_timestamps: Whether to include word-level timestamps
        
        Returns:
            Dict with text, language, duration, and optional segments
        """
        if not WHISPER_AVAILABLE:
            raise ValueError("Whisper not available for STT")
        
        try:
            # Get audio duration for model selection
            audio_duration = await self._get_audio_duration(audio_path)
            optimal_model_size = self._get_optimal_model_size(audio_duration, quality_preference)
            
            app_logger.info(f"Processing STT: {audio_path} (duration: {audio_duration:.1f}s, model: {optimal_model_size})")
            
            # Load optimal model
            if not await self.load_whisper_model_async(optimal_model_size):
                raise ValueError(f"Failed to load Whisper model: {optimal_model_size}")
            
            start_time = time.time()
            
            # Transcribe in thread pool
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                self.executor,
                self._transcribe_audio_sync,
                audio_path,
                language,
                with_timestamps
            )
            
            processing_time = time.time() - start_time
            
            # Extract segments if timestamps requested
            segments = []
            if with_timestamps and "segments" in result:
                for segment in result.get("segments", []):
                    segments.append({
                        "start": segment["start"],
                        "end": segment["end"],
                        "text": segment["text"].strip(),
                        "words": segment.get("words", [])
                    })
            
            app_logger.info(f"STT completed in {processing_time:.2f}s (model: {optimal_model_size})")
            
            return {
                "text": result["text"].strip(),
                "language": result["language"],
                "duration": audio_duration,
                "segments": segments if with_timestamps else [],
                "processing_time": processing_time,
                "model_used": optimal_model_size
            }
            
        except Exception as e:
            app_logger.error(f"Optimized STT failed: {e}")
            raise ValueError(f"Speech-to-text failed: {str(e)}")
    
    def _transcribe_audio_sync(self, audio_path: str, language: Optional[str], with_timestamps: bool):
        """Synchronous transcription for thread pool execution"""
        options = {
            "language": language,
            "verbose": False
        }
        
        if with_timestamps:
            options["word_timestamps"] = True
        
        return self.whisper_model.transcribe(audio_path, **options)
    
    async def _get_audio_duration(self, audio_path: str) -> float:
        """Get audio duration without loading full audio"""
        try:
            # Use ffprobe for fast duration detection
            import subprocess
            result = subprocess.run([
                'ffprobe', '-v', 'quiet', '-show_entries', 'format=duration',
                '-of', 'csv=p=0', audio_path
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                return float(result.stdout.strip())
            else:
                # Fallback: estimate from file size (rough approximation)
                file_size = os.path.getsize(audio_path)
                return file_size / (16000 * 2)  # Rough estimate for 16kHz audio
                
        except Exception as e:
            app_logger.warning(f"Could not get audio duration: {e}")
            return 60.0  # Default assumption
    
    async def speech_to_text_with_timestamps_optimized(
        self, 
        audio_path: str, 
        language: Optional[str] = None,
        quality_preference: str = "balanced"
    ) -> Dict[str, Union[str, float, list]]:
        """
        Optimized STT with timestamps using automatic model selection
        """
        return await self.speech_to_text_optimized(
            audio_path=audio_path,
            language=language,
            quality_preference=quality_preference,
            with_timestamps=True
        )
    
    def cleanup(self):
        """Clean up resources"""
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=True)
        self.model_cache.clear()
        self.whisper_model = None


# Global optimized speech engine instance
_optimized_speech_engine = None

def get_optimized_speech_engine() -> OptimizedSpeechEngine:
    """Get or create optimized speech engine instance"""
    global _optimized_speech_engine
    if _optimized_speech_engine is None:
        _optimized_speech_engine = OptimizedSpeechEngine()
    return _optimized_speech_engine

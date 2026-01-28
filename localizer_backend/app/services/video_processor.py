"""
Video Processing Service for Video Localization
Handles video file processing, audio extraction, subtitle generation, and ffmpeg operations
"""
import os
import time
import tempfile
import subprocess
from typing import Dict, Optional, List, Union
from pathlib import Path

# Core dependencies
from app.core.config import get_settings, SUPPORTED_LANGUAGES
from app.utils.logger import app_logger

# Video processing
try:
    import ffmpeg
    FFMPEG_PYTHON_AVAILABLE = True
    app_logger.info("ffmpeg-python available for video processing")
except ImportError:
    FFMPEG_PYTHON_AVAILABLE = False
    app_logger.warning("ffmpeg-python not available - using subprocess fallback")

settings = get_settings()


class VideoProcessor:
    """
    Production-ready video processor for localization tasks
    Handles audio extraction, subtitle generation, and video merging
    """
    
    def __init__(self):
        self.supported_video_formats = ['.mp4', '.avi', '.mov', '.mkv', '.webm', '.m4v']
        self.supported_audio_formats = ['.mp3', '.wav', '.aac', '.m4a']
        
        # Check ffmpeg availability
        self._check_ffmpeg()
        
        app_logger.info("Video Processor initialized")
    
    def _check_ffmpeg(self) -> bool:
        """Check if ffmpeg is available in system"""
        try:
            result = subprocess.run(['ffmpeg', '-version'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                app_logger.info("FFmpeg found in system PATH")
                return True
            else:
                app_logger.warning("FFmpeg not found in system PATH")
                return False
        except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
            app_logger.warning("FFmpeg not available")
            return False
    
    def extract_audio_from_video(
        self, 
        video_path: str, 
        output_format: str = "wav"
    ) -> Dict[str, Union[str, bool]]:
        """
        Extract audio from video file
        
        Args:
            video_path: Path to input video file
            output_format: Audio output format (wav, mp3, aac)
        
        Returns:
            Dict with audio_path, success status, and metadata
        """
        try:
            # Generate output audio path
            video_name = Path(video_path).stem
            audio_filename = f"extracted_audio_{video_name}_{int(time.time())}.{output_format}"
            audio_path = os.path.join(tempfile.gettempdir(), audio_filename)
            
            app_logger.info(f"Extracting audio from video: {video_path} → {audio_path}")
            
            if FFMPEG_PYTHON_AVAILABLE:
                # Use ffmpeg-python library
                stream = ffmpeg.input(video_path)
                audio = stream.audio
                out = ffmpeg.output(audio, audio_path, acodec='pcm_s16le' if output_format == 'wav' else 'aac')
                ffmpeg.run(out, quiet=True, overwrite_output=True)
            else:
                # Use subprocess fallback
                cmd = [
                    'ffmpeg', '-i', video_path,
                    '-vn',  # No video
                    '-acodec', 'pcm_s16le' if output_format == 'wav' else 'aac',
                    '-ar', '16000',  # Sample rate
                    '-ac', '1',  # Mono
                    '-y',  # Overwrite output
                    audio_path
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
                if result.returncode != 0:
                    raise subprocess.CalledProcessError(result.returncode, cmd, result.stderr)
            
            # Verify output file exists
            if not os.path.exists(audio_path):
                raise FileNotFoundError(f"Audio extraction failed - output file not created")
            
            file_size = os.path.getsize(audio_path)
            app_logger.info(f"Audio extraction completed: {audio_path} ({file_size} bytes)")
            
            return {
                "success": True,
                "audio_path": audio_path,
                "format": output_format,
                "file_size_bytes": file_size,
                "message": "Audio extracted successfully"
            }
            
        except Exception as e:
            app_logger.error(f"Audio extraction failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Audio extraction failed"
            }
    
    def get_video_info(self, video_path: str) -> Dict[str, Union[str, float, int]]:
        """
        Get video file information and metadata
        
        Args:
            video_path: Path to video file
        
        Returns:
            Dict with video metadata (duration, resolution, format, etc.)
        """
        try:
            if FFMPEG_PYTHON_AVAILABLE:
                # Use ffmpeg-python to probe video
                probe = ffmpeg.probe(video_path)
                
                video_stream = next((stream for stream in probe['streams'] 
                                   if stream['codec_type'] == 'video'), None)
                audio_stream = next((stream for stream in probe['streams'] 
                                   if stream['codec_type'] == 'audio'), None)
                
                info = {
                    "duration": float(probe['format']['duration']) if 'duration' in probe['format'] else 0,
                    "file_size": int(probe['format']['size']) if 'size' in probe['format'] else 0,
                    "format_name": probe['format']['format_name'],
                    "bit_rate": int(probe['format']['bit_rate']) if 'bit_rate' in probe['format'] else 0
                }
                
                if video_stream:
                    info.update({
                        "width": int(video_stream['width']),
                        "height": int(video_stream['height']),
                        "video_codec": video_stream['codec_name'],
                        "fps": eval(video_stream.get('r_frame_rate', '0/1'))
                    })
                
                if audio_stream:
                    info.update({
                        "audio_codec": audio_stream['codec_name'],
                        "audio_sample_rate": int(audio_stream.get('sample_rate', 0)),
                        "audio_channels": int(audio_stream.get('channels', 0))
                    })
                
                return info
            else:
                # Basic info using subprocess
                cmd = ['ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_format', video_path]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                
                if result.returncode != 0:
                    raise subprocess.CalledProcessError(result.returncode, cmd, result.stderr)
                
                import json
                probe_data = json.loads(result.stdout)
                format_info = probe_data.get('format', {})
                
                return {
                    "duration": float(format_info.get('duration', 0)),
                    "file_size": int(format_info.get('size', 0)),
                    "format_name": format_info.get('format_name', 'unknown'),
                    "bit_rate": int(format_info.get('bit_rate', 0))
                }
                
        except Exception as e:
            app_logger.error(f"Failed to get video info: {e}")
            return {
                "duration": 0,
                "file_size": 0,
                "format_name": "unknown",
                "error": str(e)
            }
    
    def merge_video_with_subtitles(
        self, 
        video_path: str, 
        subtitle_path: str, 
        output_path: str
    ) -> Dict[str, Union[str, bool]]:
        """
        Merge video with subtitle file (burn subtitles into video)
        
        Args:
            video_path: Path to input video file
            subtitle_path: Path to SRT subtitle file
            output_path: Path for output video file
        
        Returns:
            Dict with success status and output information
        """
        try:
            app_logger.info(f"Merging video with subtitles: {video_path} + {subtitle_path}")
            
            # Normalize paths for cross-platform compatibility
            video_path = os.path.normpath(video_path)
            subtitle_path = os.path.normpath(subtitle_path)
            output_path = os.path.normpath(output_path)
            
            # Escape subtitle path for ffmpeg (especially important on Windows)
            if os.name == 'nt':  # Windows
                # Replace backslashes with forward slashes and escape colons
                escaped_subtitle_path = subtitle_path.replace('\\', '/').replace(':', '\\:')
            else:  # Unix-like systems
                escaped_subtitle_path = subtitle_path.replace(':', '\\:')
            
            if FFMPEG_PYTHON_AVAILABLE:
                # Use ffmpeg-python library
                input_video = ffmpeg.input(video_path)
                output = ffmpeg.output(
                    input_video, 
                    output_path,
                    vf=f"subtitles='{escaped_subtitle_path}'",
                    acodec='copy'  # Copy audio without re-encoding
                )
                try:
                    ffmpeg.run(output, quiet=True, overwrite_output=True)
                except ffmpeg.Error as e:
                    app_logger.error(f"FFmpeg-python error: {e}")
                    app_logger.error(f"FFmpeg stderr: {e.stderr.decode() if e.stderr else 'No stderr'}")
                    raise
            else:
                # Use subprocess fallback
                cmd = [
                    'ffmpeg', '-i', video_path,
                    '-vf', f"subtitles='{escaped_subtitle_path}'",
                    '-acodec', 'copy',  # Copy audio
                    '-y',  # Overwrite output
                    output_path
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
                if result.returncode != 0:
                    app_logger.error(f"FFmpeg stderr: {result.stderr}")
                    app_logger.error(f"FFmpeg stdout: {result.stdout}")
                    raise subprocess.CalledProcessError(result.returncode, cmd, result.stderr)
            
            # Verify output file exists
            if not os.path.exists(output_path):
                raise FileNotFoundError("Video merging failed - output file not created")
            
            file_size = os.path.getsize(output_path)
            app_logger.info(f"Video merging completed: {output_path} ({file_size} bytes)")
            
            return {
                "success": True,
                "output_path": output_path,
                "file_size_bytes": file_size,
                "message": "Video with subtitles created successfully"
            }
            
        except Exception as e:
            app_logger.error(f"Video merging failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Video merging failed"
            }
    
    def merge_video_with_audio(
        self, 
        video_path: str, 
        audio_path: str, 
        output_path: str
    ) -> Dict[str, Union[str, bool]]:
        """
        Replace video audio track with translated audio
        
        Args:
            video_path: Path to input video file
            audio_path: Path to translated audio file
            output_path: Path for output video file
        
        Returns:
            Dict with success status and output information
        """
        try:
            app_logger.info(f"Merging video with translated audio: {video_path} + {audio_path}")
            
            if FFMPEG_PYTHON_AVAILABLE:
                # Use ffmpeg-python library
                input_video = ffmpeg.input(video_path)
                input_audio = ffmpeg.input(audio_path)
                
                output = ffmpeg.output(
                    input_video['v'], input_audio['a'],
                    output_path,
                    vcodec='copy',  # Copy video without re-encoding
                    acodec='aac',   # Re-encode audio to AAC
                    strict='experimental'
                )
                ffmpeg.run(output, quiet=True, overwrite_output=True)
            else:
                # Use subprocess fallback
                cmd = [
                    'ffmpeg', '-i', video_path, '-i', audio_path,
                    '-c:v', 'copy',  # Copy video
                    '-c:a', 'aac',   # Re-encode audio
                    '-map', '0:v:0', '-map', '1:a:0',  # Map video and audio
                    '-y',  # Overwrite output
                    output_path
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
                if result.returncode != 0:
                    raise subprocess.CalledProcessError(result.returncode, cmd, result.stderr)
            
            # Verify output file exists
            if not os.path.exists(output_path):
                raise FileNotFoundError("Video audio merging failed - output file not created")
            
            file_size = os.path.getsize(output_path)
            app_logger.info(f"Video audio merging completed: {output_path} ({file_size} bytes)")
            
            return {
                "success": True,
                "output_path": output_path,
                "file_size_bytes": file_size,
                "message": "Video with translated audio created successfully"
            }
            
        except Exception as e:
            app_logger.error(f"Video audio merging failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Video audio merging failed"
            }
    
    def validate_video_file(self, video_path: str) -> Dict[str, Union[bool, str]]:
        """
        Validate video file format and accessibility
        
        Args:
            video_path: Path to video file
        
        Returns:
            Dict with validation results
        """
        try:
            if not os.path.exists(video_path):
                return {"is_valid": False, "error": "File does not exist"}
            
            file_ext = Path(video_path).suffix.lower()
            if file_ext not in self.supported_video_formats:
                return {
                    "is_valid": False, 
                    "error": f"Unsupported format: {file_ext}. Supported: {self.supported_video_formats}"
                }
            
            # Get basic video info to validate
            info = self.get_video_info(video_path)
            
            if info.get('duration', 0) <= 0:
                return {"is_valid": False, "error": "Invalid or corrupted video file"}
            
            if info.get('duration', 0) > 3600:  # 1 hour limit
                return {"is_valid": False, "error": "Video too long (max 1 hour)"}
            
            return {
                "is_valid": True,
                "duration": info.get('duration'),
                "file_size": info.get('file_size'),
                "format": info.get('format_name')
            }
            
        except Exception as e:
            return {"is_valid": False, "error": str(e)}
    
    def cleanup_temp_files(self, file_paths: List[str]):
        """Clean up temporary files"""
        for file_path in file_paths:
            try:
                if os.path.exists(file_path):
                    os.unlink(file_path)
                    app_logger.debug(f"Cleaned up temp file: {file_path}")
            except Exception as e:
                app_logger.warning(f"Failed to cleanup {file_path}: {e}")


# Global instance
video_processor = VideoProcessor()


def get_video_processor() -> VideoProcessor:
    """Get the global video processor instance"""
    return video_processor
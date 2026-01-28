"""
Production Optimizations
Model caching, memory management, and performance improvements
"""
import gc
import psutil
import time
from typing import Dict, Any, Optional
from functools import lru_cache, wraps
import threading
from contextlib import contextmanager

from app.utils.logger import app_logger
from app.core.config import get_settings

settings = get_settings()


class ModelCache:
    """Intelligent model caching system"""
    
    def __init__(self, max_memory_gb: float = 8.0):
        self.cache = {}
        self.access_times = {}
        self.load_times = {}
        self.max_memory_gb = max_memory_gb
        self._lock = threading.Lock()
        
        app_logger.info(f"Model cache initialized with {max_memory_gb}GB limit")
    
    def get_memory_usage(self) -> float:
        """Get current memory usage in GB"""
        process = psutil.Process()
        return process.memory_info().rss / (1024 ** 3)
    
    def cache_model(self, key: str, model: Any, tokenizer: Any = None) -> bool:
        """
        Cache a model with intelligent memory management
        
        Args:
            key: Model cache key
            model: Model object
            tokenizer: Optional tokenizer
        
        Returns:
            True if cached successfully
        """
        with self._lock:
            current_memory = self.get_memory_usage()
            
            if current_memory > self.max_memory_gb * 0.8:  # 80% threshold
                app_logger.warning(f"Memory usage high ({current_memory:.2f}GB), clearing cache")
                self._clear_least_used()
            
            self.cache[key] = {
                "model": model,
                "tokenizer": tokenizer,
                "size_mb": self._estimate_model_size(model)
            }
            self.access_times[key] = time.time()
            self.load_times[key] = time.time()
            
            app_logger.info(f"Cached model: {key} (estimated {self._estimate_model_size(model):.1f}MB)")
            return True
    
    def get_model(self, key: str) -> Optional[Dict[str, Any]]:
        """Get model from cache"""
        with self._lock:
            if key in self.cache:
                self.access_times[key] = time.time()
                app_logger.debug(f"Cache hit: {key}")
                return self.cache[key]
            
            app_logger.debug(f"Cache miss: {key}")
            return None
    
    def _estimate_model_size(self, model: Any) -> float:
        """Estimate model size in MB"""
        try:
            if hasattr(model, 'get_memory_footprint'):
                return model.get_memory_footprint() / (1024 ** 2)
            elif hasattr(model, 'num_parameters'):
                # Rough estimate: 4 bytes per parameter
                return model.num_parameters() * 4 / (1024 ** 2)
            else:
                return 100.0  # Default estimate
        except:
            return 100.0
    
    def _clear_least_used(self):
        """Clear least recently used models"""
        if not self.cache:
            return
        
        # Sort by access time (oldest first)
        sorted_keys = sorted(self.access_times.keys(), key=lambda k: self.access_times[k])
        
        # Remove oldest 25% of models
        to_remove = max(1, len(sorted_keys) // 4)
        
        for key in sorted_keys[:to_remove]:
            del self.cache[key]
            del self.access_times[key]
            del self.load_times[key]
            app_logger.info(f"Evicted model from cache: {key}")
        
        # Force garbage collection
        gc.collect()
    
    def remove_model(self, key: str) -> bool:
        """Remove a specific model from cache"""
        with self._lock:
            if key in self.cache:
                del self.cache[key]
                del self.access_times[key]
                del self.load_times[key]
                gc.collect()
                app_logger.info(f"Removed model from cache: {key}")
                return True
            return False
    
    def clear_all(self):
        """Clear all cached models"""
        with self._lock:
            self.cache.clear()
            self.access_times.clear()
            self.load_times.clear()
            gc.collect()
            app_logger.info("Cleared all model cache")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self._lock:
            current_memory = self.get_memory_usage()
            total_size = sum(item["size_mb"] for item in self.cache.values())
            
            return {
                "cached_models": len(self.cache),
                "total_estimated_size_mb": total_size,
                "current_memory_gb": current_memory,
                "memory_limit_gb": self.max_memory_gb,
                "memory_usage_percent": (current_memory / self.max_memory_gb) * 100,
                "models": list(self.cache.keys())
            }


# Global model cache instance
model_cache = ModelCache()


def cached_model(cache_key: str):
    """Decorator for caching model loading"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Check cache first
            cached = model_cache.get_model(cache_key)
            if cached:
                return cached["model"], cached["tokenizer"]
            
            # Load model if not cached
            app_logger.info(f"Loading model: {cache_key}")
            start_time = time.time()
            
            result = func(*args, **kwargs)
            
            load_time = time.time() - start_time
            app_logger.info(f"Model loaded in {load_time:.2f}s: {cache_key}")
            
            # Cache the result
            if isinstance(result, tuple) and len(result) == 2:
                model, tokenizer = result
                model_cache.cache_model(cache_key, model, tokenizer)
            else:
                model_cache.cache_model(cache_key, result)
            
            return result
        
        return wrapper
    return decorator


@contextmanager
def memory_monitor(operation_name: str):
    """Context manager to monitor memory usage"""
    process = psutil.Process()
    start_memory = process.memory_info().rss / (1024 ** 2)  # MB
    start_time = time.time()
    
    app_logger.debug(f"Starting {operation_name} - Memory: {start_memory:.1f}MB")
    
    try:
        yield
    finally:
        end_memory = process.memory_info().rss / (1024 ** 2)  # MB
        end_time = time.time()
        
        memory_diff = end_memory - start_memory
        duration = end_time - start_time
        
        app_logger.info(
            f"Completed {operation_name} - "
            f"Duration: {duration:.2f}s, "
            f"Memory: {end_memory:.1f}MB ({memory_diff:+.1f}MB)"
        )


class PerformanceMonitor:
    """Monitor performance metrics"""
    
    def __init__(self):
        self.metrics = {
            "requests": 0,
            "translation_time": [],
            "memory_usage": [],
            "error_count": 0
        }
        self._lock = threading.Lock()
    
    def start_request(self):
        """Start tracking a request"""
        with self._lock:
            self.metrics["requests"] += 1
    
    def end_request(self, duration: float = 0):
        """End tracking a request"""
        if duration > 0:
            self.record_translation_time(duration)
    
    def record_request(self):
        """Record a request"""
        with self._lock:
            self.metrics["requests"] += 1
    
    def record_translation_time(self, duration: float):
        """Record translation duration"""
        with self._lock:
            self.metrics["translation_time"].append(duration)
            # Keep only last 1000 measurements
            if len(self.metrics["translation_time"]) > 1000:
                self.metrics["translation_time"] = self.metrics["translation_time"][-1000:]
    
    def record_memory_usage(self):
        """Record current memory usage"""
        memory_gb = psutil.Process().memory_info().rss / (1024 ** 3)
        with self._lock:
            self.metrics["memory_usage"].append(memory_gb)
            # Keep only last 100 measurements
            if len(self.metrics["memory_usage"]) > 100:
                self.metrics["memory_usage"] = self.metrics["memory_usage"][-100:]
    
    def record_error(self):
        """Record an error"""
        with self._lock:
            self.metrics["error_count"] += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        with self._lock:
            translation_times = self.metrics["translation_time"]
            memory_usage = self.metrics["memory_usage"]
            
            stats = {
                "total_requests": self.metrics["requests"],
                "total_errors": self.metrics["error_count"],
                "error_rate": self.metrics["error_count"] / max(1, self.metrics["requests"])
            }
            
            if translation_times:
                stats.update({
                    "avg_translation_time": sum(translation_times) / len(translation_times),
                    "min_translation_time": min(translation_times),
                    "max_translation_time": max(translation_times)
                })
            
            if memory_usage:
                stats.update({
                    "avg_memory_gb": sum(memory_usage) / len(memory_usage),
                    "max_memory_gb": max(memory_usage),
                    "current_memory_gb": memory_usage[-1] if memory_usage else 0
                })
            
            return stats
    
    def record_translation(self, source_lang: str, target_lang: str, text_length: int):
        """Record translation metrics"""
        with self._lock:
            # This could be expanded to track per-language metrics
            pass
    
    def get_memory_info(self) -> Dict[str, Any]:
        """Get memory information"""
        process = psutil.Process()
        return {
            "rss_gb": process.memory_info().rss / (1024 ** 3),
            "vms_gb": process.memory_info().vms / (1024 ** 3)
        }
    
    def get_system_info(self) -> Dict[str, Any]:
        """Get system information"""
        return {
            "cpu_percent": psutil.cpu_percent(),
            "cpu_count": psutil.cpu_count(),
            "available_memory_gb": psutil.virtual_memory().available / (1024 ** 3),
            "total_memory_gb": psutil.virtual_memory().total / (1024 ** 3)
        }
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get all metrics"""
        return self.get_stats()
    
    def reset_stats(self):
        """Reset all statistics"""
        with self._lock:
            self.metrics = {
                "requests": 0,
                "translation_time": [],
                "memory_usage": [],
                "error_count": 0
            }


# Global performance monitor
performance_monitor = PerformanceMonitor()


def optimize_torch_settings():
    """Optimize PyTorch settings for production"""
    try:
        import torch
        
        # Enable optimizations
        torch.backends.cudnn.benchmark = True
        torch.backends.cudnn.deterministic = False
        
        # Memory management
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            # Set memory fraction if on GPU
            torch.cuda.set_per_process_memory_fraction(0.8)
        
        # Threading
        torch.set_num_threads(min(4, psutil.cpu_count()))
        
        app_logger.info("PyTorch optimizations applied")
        
    except ImportError:
        app_logger.warning("PyTorch not available for optimization")


@lru_cache(maxsize=1000)
def cached_language_detection(text_hash: str, text: str) -> Dict[str, Any]:
    """Cached language detection to avoid repeated computation"""
    from app.services.nlp_engine import nlp_engine
    return nlp_engine.detect_language(text)


def cleanup_resources():
    """Cleanup resources for graceful shutdown"""
    app_logger.info("Cleaning up resources...")
    
    # Clear model cache
    model_cache.clear_all()
    
    # Clear PyTorch cache
    try:
        import torch
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    except ImportError:
        pass
    
    # Force garbage collection
    gc.collect()
    
    app_logger.info("Resource cleanup completed")


def get_system_info() -> Dict[str, Any]:
    """Get system information for monitoring"""
    try:
        import torch
        cuda_available = torch.cuda.is_available()
        if cuda_available:
            gpu_name = torch.cuda.get_device_name(0)
            gpu_memory = torch.cuda.get_device_properties(0).total_memory / (1024**3)
        else:
            gpu_name = None
            gpu_memory = 0
    except ImportError:
        cuda_available = False
        gpu_name = None
        gpu_memory = 0
    
    return {
        "cpu_count": psutil.cpu_count(),
        "cpu_percent": psutil.cpu_percent(),
        "memory_total_gb": psutil.virtual_memory().total / (1024**3),
        "memory_available_gb": psutil.virtual_memory().available / (1024**3),
        "memory_percent": psutil.virtual_memory().percent,
        "disk_usage_percent": psutil.disk_usage('/').percent,
        "cuda_available": cuda_available,
        "gpu_name": gpu_name,
        "gpu_memory_gb": gpu_memory
    }


# Global instances for application-wide use
model_cache = ModelCache()
perf_monitor = PerformanceMonitor()

# For backward compatibility
performance_monitor = perf_monitor
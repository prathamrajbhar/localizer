"""
Prometheus metrics for monitoring
"""
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from fastapi import Response
from app.utils.logger import app_logger

# Define metrics
translation_requests = Counter(
    "translation_requests_total",
    "Total number of translation requests",
    ["source_language", "target_language"]
)

translation_duration = Histogram(
    "translation_duration_seconds",
    "Translation job duration in seconds",
    ["language_pair"]
)

stt_requests = Counter(
    "stt_requests_total",
    "Total number of STT requests",
    ["language"]
)

tts_requests = Counter(
    "tts_requests_total",
    "Total number of TTS requests",
    ["language"]
)

active_jobs = Gauge(
    "active_jobs",
    "Number of active jobs",
    ["job_type"]
)

job_failures = Counter(
    "job_failures_total",
    "Total number of failed jobs",
    ["job_type", "error_type"]
)

bleu_score_avg = Gauge(
    "bleu_score_average",
    "Average BLEU score",
    ["language_pair"]
)

comet_score_avg = Gauge(
    "comet_score_average",
    "Average COMET score",
    ["language_pair"]
)

# Direct job tracking metrics
active_jobs_count = Gauge(
    "active_jobs_count",
    "Number of active background jobs",
    ["job_type", "status"]
)

model_load_time = Histogram(
    "model_load_time_seconds",
    "Model loading time in seconds",
    ["model_name"]
)

feedback_ratings = Counter(
    "feedback_ratings_total",
    "Total feedback ratings",
    ["rating"]
)


class MetricsCollector:
    """Metrics collection utilities"""
    
    @staticmethod
    def record_translation(source_lang: str, target_lang: str, duration: float):
        """Record translation metrics"""
        translation_requests.labels(
            source_language=source_lang,
            target_language=target_lang
        ).inc()
        
        translation_duration.labels(
            language_pair=f"{source_lang}-{target_lang}"
        ).observe(duration)
    
    @staticmethod
    def record_stt(language: str):
        """Record STT request"""
        stt_requests.labels(language=language).inc()
    
    @staticmethod
    def record_tts(language: str):
        """Record TTS request"""
        tts_requests.labels(language=language).inc()
    
    @staticmethod
    def set_active_jobs(job_type: str, count: int):
        """Set active jobs count"""
        active_jobs.labels(job_type=job_type).set(count)
    
    @staticmethod
    def record_job_failure(job_type: str, error_type: str):
        """Record job failure"""
        job_failures.labels(job_type=job_type, error_type=error_type).inc()
    
    @staticmethod
    def update_bleu_score(language_pair: str, score: float):
        """Update BLEU score"""
        bleu_score_avg.labels(language_pair=language_pair).set(score)
    
    @staticmethod
    def update_comet_score(language_pair: str, score: float):
        """Update COMET score"""
        comet_score_avg.labels(language_pair=language_pair).set(score)
    
    @staticmethod
    def record_model_load_time(model_name: str, duration: float):
        """Record model loading time"""
        model_load_time.labels(model_name=model_name).observe(duration)
    
    @staticmethod
    def record_feedback(rating: int):
        """Record feedback rating"""
        feedback_ratings.labels(rating=str(rating)).inc()


def get_metrics() -> Response:
    """Get Prometheus metrics"""
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )


# Global metrics collector
metrics = MetricsCollector()


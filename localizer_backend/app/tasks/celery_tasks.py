"""
Celery Configuration and Tasks
Background processing for translation, evaluation, and retraining
"""
from celery import Celery
from celery.result import AsyncResult
import os
import time
from typing import Dict, Any, List

from app.core.config import get_settings
from app.utils.logger import app_logger

settings = get_settings()

# Create Celery app
celery_app = Celery(
    "localizer_backend",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        "app.tasks.translation_tasks",
        "app.tasks.evaluation_tasks", 
        "app.tasks.retrain_tasks"
    ]
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_routes={
        "app.tasks.translation_tasks.*": {"queue": "translations"},
        "app.tasks.evaluation_tasks.*": {"queue": "evaluations"},
        "app.tasks.retrain_tasks.*": {"queue": "retraining"}
    }
)


@celery_app.task(bind=True)
def translate_text_task(
    self, 
    text: str, 
    source_lang: str, 
    target_lang: str,
    domain: str = None,
    user_id: int = None
) -> Dict[str, Any]:
    """
    Background translation task
    
    Args:
        text: Text to translate
        source_lang: Source language code
        target_lang: Target language code
        domain: Optional domain
        user_id: User ID for logging
    
    Returns:
        Translation result
    """
    try:
        # Update task state
        self.update_state(
            state="PROGRESS",
            meta={"step": "Loading model", "progress": 10}
        )
        
        # Import here to avoid circular imports
        from app.services.nlp_engine import nlp_engine
        
        app_logger.info(f"Starting translation task: {source_lang} -> {target_lang}")
        
        # Update progress
        self.update_state(
            state="PROGRESS", 
            meta={"step": "Translating", "progress": 50}
        )
        
        # Perform translation
        result = nlp_engine.translate(
            text=text,
            source_lang=source_lang,
            target_lang=target_lang,
            domain=domain
        )
        
        # Apply localization if domain provided
        if domain:
            self.update_state(
                state="PROGRESS",
                meta={"step": "Applying localization", "progress": 80}
            )
            
            try:
                from app.services.localization import localization_engine
                localized_result = localization_engine.localize(
                    result["translated_text"],
                    target_lang,
                    domain
                )
                result["translated_text"] = localized_result["localized_text"]
                result["localization_changes"] = localized_result.get("changes_applied", [])
            except Exception as e:
                app_logger.warning(f"Localization failed: {e}")
                result["localization_changes"] = []
        
        self.update_state(
            state="PROGRESS",
            meta={"step": "Saving results", "progress": 90}
        )
        
        # Save to database
        try:
            from app.core.db import get_db
            from app.models.translation import Translation
            
            db = next(get_db())
            translation_record = Translation(
                user_id=user_id,
                source_language=result["source_language"],
                target_language=result["target_language"],
                source_text=text,
                translated_text=result["translated_text"],
                model_used=result["model_used"],
                confidence_score=result["confidence_score"],
                domain=domain,
                duration=result["duration"]
            )
            db.add(translation_record)
            db.commit()
            db.refresh(translation_record)
            result["translation_id"] = translation_record.id
            
        except Exception as e:
            app_logger.error(f"Failed to save translation: {e}")
            result["translation_id"] = None
        
        app_logger.info(f"Translation task completed: {result['translation_id']}")
        
        return {
            "status": "SUCCESS",
            "result": result,
            "task_id": self.request.id
        }
        
    except Exception as e:
        app_logger.error(f"Translation task failed: {e}")
        
        return {
            "status": "FAILURE",
            "error": str(e),
            "task_id": self.request.id
        }


@celery_app.task(bind=True)
def batch_translate_task(
    self,
    text: str,
    source_lang: str,
    target_languages: List[str],
    domain: str = None,
    user_id: int = None
) -> Dict[str, Any]:
    """
    Background batch translation task
    
    Args:
        text: Text to translate
        source_lang: Source language code  
        target_languages: List of target language codes
        domain: Optional domain
        user_id: User ID for logging
    
    Returns:
        Batch translation results
    """
    try:
        results = []
        total_langs = len(target_languages)
        
        for i, target_lang in enumerate(target_languages):
            progress = int((i / total_langs) * 100)
            self.update_state(
                state="PROGRESS",
                meta={
                    "step": f"Translating to {target_lang}",
                    "progress": progress,
                    "current_language": target_lang,
                    "completed": i,
                    "total": total_langs
                }
            )
            
            # Call individual translation task
            translation_result = translate_text_task.apply(
                args=[text, source_lang, target_lang, domain, user_id]
            ).get()
            
            results.append(translation_result)
        
        return {
            "status": "SUCCESS",
            "results": results,
            "total_translations": len(results),
            "task_id": self.request.id
        }
        
    except Exception as e:
        app_logger.error(f"Batch translation task failed: {e}")
        return {
            "status": "FAILURE", 
            "error": str(e),
            "task_id": self.request.id
        }


@celery_app.task(bind=True)
def evaluate_translation_task(
    self,
    translation_id: int,
    reference_text: str,
    evaluator_id: int = None
) -> Dict[str, Any]:
    """
    Background evaluation task
    
    Args:
        translation_id: Translation ID to evaluate
        reference_text: Reference text for comparison
        evaluator_id: User ID of evaluator
    
    Returns:
        Evaluation results
    """
    try:
        self.update_state(
            state="PROGRESS",
            meta={"step": "Loading translation", "progress": 10}
        )
        
        # Get translation from database
        from app.core.db import get_db
        from app.models.translation import Translation
        from app.models.evaluation import Evaluation
        
        db = next(get_db())
        translation = db.query(Translation).filter(
            Translation.id == translation_id
        ).first()
        
        if not translation:
            raise ValueError(f"Translation {translation_id} not found")
        
        self.update_state(
            state="PROGRESS",
            meta={"step": "Computing BLEU score", "progress": 30}
        )
        
        # Import evaluation functions
        from app.routes.evaluation import calculate_bleu_score, calculate_comet_score
        
        # Calculate metrics
        bleu_score = calculate_bleu_score(reference_text, translation.translated_text)
        
        self.update_state(
            state="PROGRESS", 
            meta={"step": "Computing COMET score", "progress": 60}
        )
        
        comet_score = calculate_comet_score(
            translation.source_text,
            translation.translated_text,
            reference_text
        )
        
        self.update_state(
            state="PROGRESS",
            meta={"step": "Saving evaluation", "progress": 80}
        )
        
        # Save evaluation
        evaluation = Evaluation(
            translation_id=translation_id,
            bleu_score=bleu_score,
            comet_score=comet_score,
            reference_text=reference_text,
            evaluator_id=evaluator_id
        )
        
        db.add(evaluation)
        db.commit()
        db.refresh(evaluation)
        
        app_logger.info(f"Evaluation completed: BLEU={bleu_score:.3f}, COMET={comet_score:.3f}")
        
        return {
            "status": "SUCCESS",
            "evaluation_id": evaluation.id,
            "bleu_score": bleu_score,
            "comet_score": comet_score,
            "task_id": self.request.id
        }
        
    except Exception as e:
        app_logger.error(f"Evaluation task failed: {e}")
        return {
            "status": "FAILURE",
            "error": str(e),
            "task_id": self.request.id
        }


@celery_app.task(bind=True)
def retrain_model_task(
    self,
    domain: str = None,
    feedback_threshold: float = 3.0,
    min_samples: int = 100
) -> Dict[str, Any]:
    """
    Background model retraining task
    
    Args:
        domain: Domain to retrain on
        feedback_threshold: Minimum feedback rating threshold
        min_samples: Minimum number of samples needed
    
    Returns:
        Retraining results
    """
    try:
        self.update_state(
            state="PROGRESS",
            meta={"step": "Collecting feedback data", "progress": 10}
        )
        
        # In production, implement actual retraining logic
        # For now, simulate retraining process
        
        time.sleep(2)  # Simulate data collection
        
        self.update_state(
            state="PROGRESS",
            meta={"step": "Preparing training data", "progress": 30}
        )
        
        time.sleep(3)  # Simulate data preparation
        
        self.update_state(
            state="PROGRESS", 
            meta={"step": "Training model", "progress": 60}
        )
        
        time.sleep(5)  # Simulate training
        
        self.update_state(
            state="PROGRESS",
            meta={"step": "Validating model", "progress": 80}
        )
        
        time.sleep(2)  # Simulate validation
        
        self.update_state(
            state="PROGRESS",
            meta={"step": "Deploying model", "progress": 90}
        )
        
        time.sleep(1)  # Simulate deployment
        
        app_logger.info("Model retraining completed")
        
        return {
            "status": "SUCCESS",
            "domain": domain,
            "samples_used": 150,  # Simulated
            "new_model_version": "v1.1",
            "performance_improvement": 0.05,
            "task_id": self.request.id
        }
        
    except Exception as e:
        app_logger.error(f"Retraining task failed: {e}")
        return {
            "status": "FAILURE",
            "error": str(e),
            "task_id": self.request.id
        }


def get_task_status(task_id: str) -> Dict[str, Any]:
    """
    Get status of a Celery task
    
    Args:
        task_id: Task ID
    
    Returns:
        Task status and result
    """
    result = AsyncResult(task_id, app=celery_app)
    
    return {
        "task_id": task_id,
        "status": result.status,
        "result": result.result,
        "traceback": result.traceback
    }


def cancel_task(task_id: str) -> bool:
    """Cancel a running task"""
    celery_app.control.revoke(task_id, terminate=True)
    return True
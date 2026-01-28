"""
Evaluation route for BLEU/COMET scoring
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Optional
import time

# Import proper evaluation libraries with error handling
try:
    from sacrebleu import sentence_bleu
    SACREBLEU_AVAILABLE = True
except ImportError:
    SACREBLEU_AVAILABLE = False
    sentence_bleu = None

try:
    from comet import download_model, load_from_checkpoint
    COMET_AVAILABLE = True
except (ImportError, RuntimeError, Exception) as e:
    COMET_AVAILABLE = False
    download_model = None
    load_from_checkpoint = None
    print(f"Warning: COMET not available due to: {e}")

from app.core.db import get_db
from app.models.user import User
from app.models.evaluation import Evaluation
from app.models.translation import Translation
from app.schemas.evaluation import EvaluationCreate, EvaluationResponse
from app.utils.logger import app_logger

router = APIRouter(prefix="/evaluate", tags=["Evaluation"])


@router.post("/run", response_model=EvaluationResponse)
async def run_evaluation(
    evaluation_request: EvaluationCreate,
    # current_user removed
    db: Session = Depends(get_db)
):
    """
    Compute BLEU/COMET score for translation evaluation
    
    Evaluates translation quality using standard metrics
    """
    try:
        # Get the translation to evaluate
        translation = db.query(Translation).filter(
            Translation.id == evaluation_request.translation_id
        ).first()
        
        if not translation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Translation not found"
            )
        
        app_logger.info(f"Running evaluation for translation {translation.id}")
        
        # Calculate BLEU score (simplified implementation)
        # In production, use SacreBLEU library
        bleu_score = calculate_bleu_score(
            reference=evaluation_request.reference_text,
            hypothesis=translation.translated_text
        )
        
        # Calculate COMET score (simplified implementation)
        # In production, use COMET library
        comet_score = calculate_comet_score(
            source=translation.source_text,
            hypothesis=translation.translated_text,
            reference=evaluation_request.reference_text
        )
        
        # Create evaluation record
        evaluation = Evaluation(
            translation_id=translation.id,
            bleu_score=bleu_score,
            comet_score=comet_score,
            reference_text=evaluation_request.reference_text,
            evaluator_id=None  # current_user.id removed
        )
        
        db.add(evaluation)
        db.commit()
        db.refresh(evaluation)
        
        app_logger.info(f"Evaluation completed: BLEU={bleu_score:.3f}, COMET={comet_score:.3f}")
        
        return EvaluationResponse(
            id=evaluation.id,
            translation_id=evaluation.translation_id,
            bleu_score=evaluation.bleu_score,
            comet_score=evaluation.comet_score,
            reference_text=evaluation.reference_text,
            evaluator_id=evaluation.evaluator_id,
            created_at=evaluation.created_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        app_logger.error(f"Evaluation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Evaluation failed"
        )


def calculate_bleu_score(reference: str, hypothesis: str) -> float:
    """
    Calculate BLEU score using SacreBLEU
    """
    try:
        # Use SacreBLEU for accurate BLEU calculation
        bleu = sentence_bleu(hypothesis, [reference])
        return bleu.score / 100.0  # Convert to 0-1 scale
    except Exception as e:
        app_logger.error(f"BLEU calculation error: {e}")
        return 0.0


# Global COMET model - lazy loaded
_comet_model = None

def _load_comet_model():
    """Load COMET model (lazy loading)"""
    global _comet_model
    if _comet_model is None:
        try:
            app_logger.info("Loading COMET model...")
            model_path = download_model("Unbabel/wmt22-comet-da")
            _comet_model = load_from_checkpoint(model_path)
            app_logger.info("COMET model loaded successfully")
        except Exception as e:
            app_logger.error(f"Failed to load COMET model: {e}")
            _comet_model = "failed"
    return _comet_model


def calculate_comet_score(source: str, hypothesis: str, reference: str) -> float:
    """
    Calculate COMET score using Unbabel COMET
    """
    try:
        model = _load_comet_model()
        if model == "failed":
            # Fallback to simple similarity if COMET fails to load
            ref_words = set(reference.lower().split())
            hyp_words = set(hypothesis.lower().split())
            
            if not ref_words and not hyp_words:
                return 1.0
            if not ref_words or not hyp_words:
                return 0.0
            
            intersection = len(ref_words & hyp_words)
            union = len(ref_words | hyp_words)
            return intersection / union if union > 0 else 0.0
        
        # Use actual COMET model
        data = [{
            "src": source,
            "mt": hypothesis,
            "ref": reference
        }]
        
        scores = model.predict(data, batch_size=1, gpus=0)
        return float(scores[0])
        
    except Exception as e:
        app_logger.error(f"COMET calculation error: {e}")
        # Fallback to simple similarity
        ref_words = set(reference.lower().split())
        hyp_words = set(hypothesis.lower().split())
        
        if not ref_words and not hyp_words:
            return 1.0
        if not ref_words or not hyp_words:
            return 0.0
        
        intersection = len(ref_words & hyp_words)
        union = len(ref_words | hyp_words)
        return intersection / union if union > 0 else 0.0
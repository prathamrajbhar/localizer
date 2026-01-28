#!/usr/bin/env python3
"""
Model Download and Setup Script for Indian Language Localizer Backend

This script downloads and sets up all required models for the translation service:
- IndicTrans2 EN-Indic model for English to Indian languages
- IndicTrans2 Indic-EN model for Indian languages to English
- Whisper large-v3 for speech recognition

Models are saved to the saved_model directory for local caching.
"""

import os
import sys
import logging
from pathlib import Path
from huggingface_hub import snapshot_download
import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import whisper

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Model configurations
MODELS = {
    "indicTrans2_en_indic": {
        "repo_id": "ai4bharat/IndicTrans2-en-indic-1B",
        "local_dir": "saved_model/IndicTrans2-en-indic-1B",
        "description": "IndicTrans2 English to Indian Languages"
    },
    "indicTrans2_indic_en": {
        "repo_id": "ai4bharat/IndicTrans2-indic-en-1B", 
        "local_dir": "saved_model/IndicTrans2-indic-en-1B",
        "description": "IndicTrans2 Indian Languages to English"
    },
    "whisper_large_v3": {
        "model_name": "large-v3",
        "local_dir": "saved_model/whisper-large-v3",
        "description": "Whisper Large V3 for Speech Recognition"
    }
}

def create_directories():
    """Create necessary directories for model storage"""
    base_dir = Path("saved_model")
    base_dir.mkdir(exist_ok=True)
    
    for model_config in MODELS.values():
        if "local_dir" in model_config:
            Path(model_config["local_dir"]).mkdir(parents=True, exist_ok=True)
    
    logger.info("Created model directories")

def download_indicTrans2_models():
    """Download IndicTrans2 models from Hugging Face"""
    for model_key in ["indicTrans2_en_indic", "indicTrans2_indic_en"]:
        model_config = MODELS[model_key]
        
        logger.info(f"Downloading {model_config['description']}...")
        
        try:
            # Download model files
            snapshot_download(
                repo_id=model_config["repo_id"],
                local_dir=model_config["local_dir"],
                local_dir_use_symlinks=False,
                resume_download=True
            )
            
            # Test loading the model
            logger.info(f"Testing {model_config['description']} loading...")
            tokenizer = AutoTokenizer.from_pretrained(
                model_config["local_dir"],
                trust_remote_code=True
            )
            model = AutoModelForSeq2SeqLM.from_pretrained(
                model_config["local_dir"],
                trust_remote_code=True,
                torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32
            )
            
            logger.info(f"✅ {model_config['description']} downloaded and verified successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to download {model_config['description']}: {e}")
            return False
    
    return True

def download_whisper_model():
    """Download Whisper large-v3 model"""
    model_config = MODELS["whisper_large_v3"]
    
    logger.info(f"Downloading {model_config['description']}...")
    
    try:
        # Download Whisper model
        model = whisper.load_model(
            model_config["model_name"],
            download_root=model_config["local_dir"]
        )
        
        logger.info(f"✅ {model_config['description']} downloaded successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to download {model_config['description']}: {e}")
        return False

def verify_models():
    """Verify all models are properly downloaded and accessible"""
    logger.info("Verifying model installations...")
    
    success_count = 0
    total_models = len(MODELS)
    
    for model_key, model_config in MODELS.items():
        local_path = Path(model_config["local_dir"])
        
        if local_path.exists() and any(local_path.iterdir()):
            logger.info(f"✅ {model_config['description']} - Files present")
            success_count += 1
        else:
            logger.error(f"❌ {model_config['description']} - Missing files")
    
    logger.info(f"Model verification complete: {success_count}/{total_models} models ready")
    return success_count == total_models

def main():
    """Main function to download and setup all models"""
    logger.info("Starting model download and setup process...")
    
    # Create directories
    create_directories()
    
    # Download models
    indicTrans2_success = download_indicTrans2_models()
    whisper_success = download_whisper_model()
    
    # Verify installations
    verification_success = verify_models()
    
    if indicTrans2_success and whisper_success and verification_success:
        logger.info("🎉 All models downloaded and verified successfully!")
        logger.info("Models are ready for use in the translation service.")
        return True
    else:
        logger.error("❌ Some models failed to download. Please check the logs above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
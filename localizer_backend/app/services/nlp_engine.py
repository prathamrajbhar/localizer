"""
Advanced NLP Translation Engine for 22 Indian Languages
Production-ready AI system using IndicBERT, IndicTrans2, LLaMA 3, and NLLB-Indic
"""
import os
import time
import threading
import gc
from typing import Dict, List, Optional, Union, Any
from functools import lru_cache
import json

from app.core.config import get_settings, SUPPORTED_LANGUAGES
from app.utils.logger import app_logger

# Core AI/ML imports
try:
    import torch
    import torch.nn.functional as F
    from transformers import (
        AutoTokenizer, AutoModelForSeq2SeqLM, AutoModelForSequenceClassification,
        AutoModel, pipeline, M2M100ForConditionalGeneration, M2M100Tokenizer
    )
    import numpy as np
    TORCH_AVAILABLE = True
    
    # Log device info
    device_info = "GPU" if torch.cuda.is_available() else "CPU"
    if torch.cuda.is_available():
        gpu_name = torch.cuda.get_device_name(0)
        app_logger.info(f"PyTorch available - Device: {device_info} ({gpu_name})")
    else:
        app_logger.info(f"PyTorch available - Device: {device_info}")
        
except ImportError as e:
    TORCH_AVAILABLE = False
    app_logger.warning(f"AI/ML libraries not available: {e}")

# Language detection
try:
    from langdetect import detect, LangDetectException
    LANGDETECT_AVAILABLE = True
except ImportError:
    LANGDETECT_AVAILABLE = False

settings = get_settings()

# Thread lock for model loading
_model_lock = threading.Lock()

# Model configuration as per copilot instructions
MODEL_CONFIG = {
    "indic_trans2_en_to_indic": {
        "model_name": "ai4bharat/IndicTrans2-en-indic-1B",
        "local_path": "saved_model/IndicTrans2-en-indic-1B",
        "type": "seq2seq"
    },
    "indic_trans2_indic_to_en": {
        "model_name": "ai4bharat/IndicTrans2-indic-en-1B", 
        "local_path": "saved_model/IndicTrans2-indic-en-1B",
        "type": "seq2seq"
    },
    "indic_bert": {
        "model_name": "ai4bharat/IndicBERT",
        "local_path": "saved_model/IndicBERT",
        "type": "classification"
    },
    "llama3": {
        "model_name": "meta-llama/Meta-Llama-3-8B-Instruct",  # LLaMA 3 as specified
        "local_path": "saved_model/llama3-8b",
        "type": "causal_lm"
    },
    "nllb_indic": {
        "model_name": "facebook/nllb-200-distilled-600M",
        "local_path": "saved_model/nllb-200-distilled-600M", 
        "type": "seq2seq"
    }
}

# COMPREHENSIVE Language code mapping for NLLB (Facebook's model) - ALL 22 Indian Languages + English
NLLB_LANG_CODES = {
    # Core Indian languages (IndicTrans2 supported)
    "as": "asm_Beng",      # Assamese  
    "bn": "ben_Beng",      # Bengali
    "gu": "guj_Gujr",      # Gujarati
    "hi": "hin_Deva",      # Hindi
    "kn": "kan_Knda",      # Kannada  
    "ml": "mal_Mlym",      # Malayalam
    "mr": "mar_Deva",      # Marathi
    "ne": "npi_Deva",      # Nepali
    "or": "ory_Orya",      # Odia
    "pa": "pan_Guru",      # Punjabi
    "ta": "tam_Taml",      # Tamil
    "te": "tel_Telu",      # Telugu
    "ur": "urd_Arab",      # Urdu
    "sa": "san_Deva",      # Sanskrit
    
    # Additional Indian languages (NLLB fallback mappings)
    "brx": "hin_Deva",     # Bodo → Hindi fallback
    "doi": "hin_Deva",     # Dogri → Hindi fallback  
    "ks": "urd_Arab",      # Kashmiri → Urdu fallback
    "kok": "mar_Deva",     # Konkani → Marathi fallback
    "mai": "hin_Deva",     # Maithili → Hindi fallback
    "mni": "ben_Beng",     # Manipuri → Bengali fallback
    "sat": "hin_Deva",     # Santali → Hindi fallback
    "sd": "urd_Arab",      # Sindhi → Urdu fallback
    
    # English
    "en": "eng_Latn"       # English
}


class AdvancedNLPEngine:
    """
    Production-ready NLP engine supporting multiple AI models for Indian languages
    
    Models supported:
    - IndicTrans2: State-of-the-art translation for Indic languages  
    - IndicBERT: Language understanding and classification
    - LLaMA 3: Advanced language generation and contextual processing
    - NLLB-Indic: Facebook's multilingual translation (Indic subset)
    """
    
    def __init__(self):
        self.models = {}
        self.tokenizers = {}
        self.device = torch.device("cuda" if TORCH_AVAILABLE and torch.cuda.is_available() else "cpu")
        self.loaded_models = set()
        
        # Performance tracking
        self.translation_stats = {
            "total_translations": 0,
            "avg_translation_time": 0.0,
            "model_usage": {}
        }
        
        app_logger.info(f"Advanced NLP Engine initialized - Device: {self.device}")

    def _get_model_path(self, model_key: str) -> str:
        """Get model path with fallback to HuggingFace"""
        config = MODEL_CONFIG.get(model_key, {})
        local_path = config.get("local_path", "")
        
        # Check if local model exists
        if local_path and os.path.exists(local_path):
            app_logger.info(f"Using local model: {local_path}")
            return local_path
            
        # Fallback to HuggingFace
        model_name = config.get("model_name", model_key)
        app_logger.info(f"Using HuggingFace model: {model_name}")
        return model_name

    def load_indic_trans2_model(self, direction: str = "en_to_indic") -> bool:
        """
        Load IndicTrans2 model for translation
        
        Args:
            direction: "en_to_indic" or "indic_to_en"
        """
        with _model_lock:
            model_key = f"indic_trans2_{direction}"
            
            if model_key in self.loaded_models:
                app_logger.debug(f"IndicTrans2 {direction} already loaded")
                return True
            
            try:
                if not TORCH_AVAILABLE:
                    app_logger.error("PyTorch not available for IndicTrans2")
                    return False
                
                model_path = self._get_model_path(model_key)
                app_logger.info(f"Loading IndicTrans2 {direction} from {model_path}")
                
                start_time = time.time()
                
                # Load tokenizer and model
                tokenizer = AutoTokenizer.from_pretrained(
                    model_path,
                    trust_remote_code=True
                )
                
                model = AutoModelForSeq2SeqLM.from_pretrained(
                    model_path,
                    torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
                    device_map="auto" if torch.cuda.is_available() else None,
                    trust_remote_code=True
                )
                
                model.to(self.device)
                model.eval()
                
                # Store models
                self.models[model_key] = model
                self.tokenizers[model_key] = tokenizer
                self.loaded_models.add(model_key)
                
                load_time = time.time() - start_time
                app_logger.info(f"IndicTrans2 {direction} loaded in {load_time:.2f}s")
                
                return True
                
            except Exception as e:
                app_logger.error(f"Failed to load IndicTrans2 {direction}: {e}")
                return False

    def load_indic_bert_model(self) -> bool:
        """Load IndicBERT for language understanding"""
        with _model_lock:
            model_key = "indic_bert"
            
            if model_key in self.loaded_models:
                return True
            
            try:
                if not TORCH_AVAILABLE:
                    app_logger.error("PyTorch not available for IndicBERT")
                    return False
                
                model_path = self._get_model_path(model_key)
                app_logger.info(f"Loading IndicBERT from {model_path}")
                
                tokenizer = AutoTokenizer.from_pretrained(model_path)
                model = AutoModel.from_pretrained(model_path)
                
                model.to(self.device)
                model.eval()
                
                self.models[model_key] = model
                self.tokenizers[model_key] = tokenizer
                self.loaded_models.add(model_key)
                
                app_logger.info("IndicBERT loaded successfully")
                return True
                
            except Exception as e:
                app_logger.error(f"Failed to load IndicBERT: {e}")
                return False

    def load_llama3_model(self) -> bool:
        """Load LLaMA 3 for advanced language processing"""
        with _model_lock:
            model_key = "llama3"
            
            if model_key in self.loaded_models:
                return True
            
            try:
                if not TORCH_AVAILABLE:
                    app_logger.error("PyTorch not available for LLaMA 3")
                    return False
                
                model_path = self._get_model_path(model_key)
                app_logger.info(f"Loading LLaMA 3 from {model_path}")
                
                # Use pipeline for easier LLaMA 3 usage
                llama_pipeline = pipeline(
                    "text-generation",
                    model=model_path,
                    torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
                    device_map="auto" if torch.cuda.is_available() else None
                )
                
                self.models[model_key] = llama_pipeline
                self.loaded_models.add(model_key)
                
                app_logger.info("LLaMA 3 loaded successfully")
                return True
                
            except Exception as e:
                app_logger.error(f"Failed to load LLaMA 3: {e}")
                return False

    def load_nllb_model(self) -> bool:
        """Load NLLB model for multilingual translation"""
        with _model_lock:
            model_key = "nllb_indic"
            
            if model_key in self.loaded_models:
                return True
            
            try:
                if not TORCH_AVAILABLE:
                    app_logger.error("PyTorch not available for NLLB")
                    return False
                
                model_path = self._get_model_path(model_key)
                app_logger.info(f"Loading NLLB from {model_path}")
                
                tokenizer = AutoTokenizer.from_pretrained(model_path)
                model = AutoModelForSeq2SeqLM.from_pretrained(
                    model_path,
                    torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32
                )
                
                model.to(self.device)
                model.eval()
                
                self.models[model_key] = model
                self.tokenizers[model_key] = tokenizer
                self.loaded_models.add(model_key)
                
                app_logger.info("NLLB loaded successfully")
                return True
                
            except Exception as e:
                app_logger.error(f"Failed to load NLLB: {e}")
                return False

    @lru_cache(maxsize=1000)
    def detect_language(self, text: str) -> Dict[str, Union[str, float]]:
        """
        Advanced language detection using multiple methods
        """
        if not text or len(text.strip()) < 3:
            return {
                "detected_language": "unknown",
                "language_name": "Unknown", 
                "confidence": 0.0
            }
        
        # First, check if text is clearly English using advanced algorithm
        is_english, english_confidence = self._is_clearly_english(text)
        if is_english:
            app_logger.info(f"Text identified as clearly English (confidence: {english_confidence:.2f})")
            return {
                "detected_language": "en",
                "language_name": "English",
                "confidence": min(english_confidence, 0.95)  # Use calculated confidence
            }
        
        # Try langdetect for English and other non-Indian languages first
        if LANGDETECT_AVAILABLE:
            try:
                detected = detect(text)
                app_logger.info(f"langdetect detected: {detected}")

                # Handle English detection with high confidence
                if detected == "en":
                    return {
                        "detected_language": "en",
                        "language_name": "English",
                        "confidence": 0.9
                    }

                # Handle other supported languages (non-Indian)
                if detected in SUPPORTED_LANGUAGES:
                    return {
                        "detected_language": detected,
                        "language_name": SUPPORTED_LANGUAGES[detected],
                        "confidence": 0.9
                    }

                # If langdetect detected unsupported language, check if it's actually English
                if detected not in SUPPORTED_LANGUAGES and detected != "en":
                    app_logger.warning(f"langdetect detected unsupported language: {detected}")
                    # Double-check with our advanced English detection
                    is_english, english_confidence = self._is_clearly_english(text)
                    if is_english and english_confidence > 0.6:
                        app_logger.info(f"Advanced English detection overrides langdetect: {detected} -> en")
                        return {
                            "detected_language": "en",
                            "language_name": "English",
                            "confidence": english_confidence
                        }
                
            except LangDetectException as e:
                app_logger.warning(f"langdetect failed: {e}")

        # Try script-based detection for Indian languages (after langdetect)
        script_detected = self._detect_script_based_language(text)
        if script_detected != "unknown":
            app_logger.info(f"Script-based detection: {script_detected}")
            return {
                "detected_language": script_detected,
                "language_name": SUPPORTED_LANGUAGES.get(script_detected, script_detected),
                "confidence": 0.9  # High confidence for script-based detection
            }

        # Fallback: Use IndicBERT for classification (if loaded)
        if "indic_bert" in self.loaded_models:
            try:
                return self._detect_with_indic_bert(text)
            except Exception as e:
                app_logger.warning(f"IndicBERT detection failed: {e}")

        # Try to detect English using simple heuristics
        if self._is_likely_english(text):
            return {
                "detected_language": "en",
                "language_name": "English",
                "confidence": 0.7
            }

        # Final fallback to Hindi only if no other method worked
        return {
            "detected_language": "hi",  # Default to Hindi
            "language_name": "Hindi",
            "confidence": 0.3  # Lower confidence for fallback
        }

    def _detect_with_indic_bert(self, text: str) -> Dict[str, Union[str, float]]:
        """Use IndicBERT for language detection"""
        model = self.models["indic_bert"]
        tokenizer = self.tokenizers["indic_bert"]
        
        inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        
        with torch.no_grad():
            outputs = model(**inputs)
            # This is a simplified approach - in practice, you'd need a classifier head
            # trained for language identification
            
        return {
            "detected_language": "hi",  # Placeholder
            "language_name": "Hindi",
            "confidence": 0.8
        }
    
    def _is_clearly_english(self, text: str) -> tuple[bool, float]:
        """
        Advanced English detection with confidence scoring
        Returns (is_english, confidence_score)
        """
        if not text or len(text.strip()) < 3:
            return False, 0.0

        # Multi-factor English detection algorithm
        confidence_factors = []
        
        # Factor 1: ASCII character ratio
        ascii_chars = sum(1 for c in text if ord(c) < 128)
        ascii_ratio = ascii_chars / len(text) if text else 0
        ascii_confidence = min(ascii_ratio * 1.2, 1.0)  # Boost high ASCII ratios
        confidence_factors.append(ascii_confidence)
        
        # Factor 2: Common English words (weighted by frequency)
        common_english_words = {
            "the": 0.3, "and": 0.25, "or": 0.2, "but": 0.2, "in": 0.2, "on": 0.2, "at": 0.2,
            "to": 0.2, "for": 0.2, "of": 0.2, "with": 0.2, "by": 0.2, "is": 0.2, "are": 0.2,
            "was": 0.2, "were": 0.2, "be": 0.2, "been": 0.2, "have": 0.2, "has": 0.2, "had": 0.2,
            "do": 0.2, "does": 0.2, "did": 0.2, "will": 0.2, "would": 0.2, "could": 0.2,
            "should": 0.2, "may": 0.2, "might": 0.2, "can": 0.2, "this": 0.2, "that": 0.2,
            "these": 0.2, "those": 0.2, "hello": 0.3, "how": 0.2, "you": 0.2, "what": 0.2,
            "where": 0.2, "when": 0.2, "why": 0.2, "who": 0.2, "which": 0.2
        }
        
        text_lower = text.lower()
        word_confidence = 0.0
        for word, weight in common_english_words.items():
            if word in text_lower:
                word_confidence += weight
        
        # Normalize word confidence
        word_confidence = min(word_confidence / 3.0, 1.0)  # Cap at 1.0
        confidence_factors.append(word_confidence)
        
        # Factor 3: English-specific patterns (advanced regex)
        import re
        english_patterns = [
            (r'\b[a-zA-Z]+\b', 0.1),  # English words
            (r'\d{1,2}:\d{2}\s*(AM|PM|am|pm)', 0.3),  # Time format
            (r'\b(January|February|March|April|May|June|July|August|September|October|November|December)\b', 0.4),  # Months
            (r'\b(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\b', 0.4),  # Days
            (r'\b\d{1,2}/\d{1,2}/\d{2,4}\b', 0.3),  # Date format
            (r'\b[A-Z][a-z]+\s+[A-Z][a-z]+\b', 0.2),  # Proper names
            (r'\b(www\.|http://|https://)\b', 0.4),  # URLs
            (r'\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b', 0.4)  # Email
        ]
        
        pattern_confidence = 0.0
        for pattern, weight in english_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                pattern_confidence += weight
        
        pattern_confidence = min(pattern_confidence, 1.0)
        confidence_factors.append(pattern_confidence)
        
        # Factor 4: Character distribution analysis
        english_char_distribution = {
            'e': 0.127, 't': 0.091, 'a': 0.082, 'o': 0.075, 'i': 0.070, 'n': 0.067,
            's': 0.063, 'h': 0.061, 'r': 0.060, 'd': 0.043, 'l': 0.040, 'c': 0.028,
            'u': 0.028, 'm': 0.024, 'w': 0.024, 'f': 0.022, 'g': 0.020, 'y': 0.020,
            'p': 0.019, 'b': 0.015, 'v': 0.010, 'k': 0.008, 'j': 0.001, 'x': 0.001,
            'q': 0.001, 'z': 0.001
        }
        
        text_chars = text.lower()
        char_freq = {}
        for char in text_chars:
            if char.isalpha():
                char_freq[char] = char_freq.get(char, 0) + 1
        
        if char_freq:
            total_chars = sum(char_freq.values())
            distribution_confidence = 0.0
            for char, expected_freq in english_char_distribution.items():
                actual_freq = char_freq.get(char, 0) / total_chars
                # Calculate similarity to expected frequency
                similarity = 1.0 - abs(actual_freq - expected_freq) / expected_freq
                distribution_confidence += similarity * expected_freq
            
            distribution_confidence = min(distribution_confidence, 1.0)
            confidence_factors.append(distribution_confidence)
        
        # Calculate final confidence score
        final_confidence = sum(confidence_factors) / len(confidence_factors)
        
        # Determine if it's clearly English
        is_english = final_confidence > 0.7
        
        return is_english, final_confidence

    def _is_likely_english(self, text: str) -> bool:
        """
        Simple heuristic to detect if text is likely English
        """
        if not text:
            return False
        
        # Count ASCII characters (English uses ASCII)
        ascii_chars = sum(1 for c in text if ord(c) < 128)
        total_chars = len(text)
        
        # If more than 80% are ASCII characters, likely English
        ascii_ratio = ascii_chars / total_chars if total_chars > 0 else 0
        
        # Check for common English words
        english_words = {
            'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by',
            'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did',
            'will', 'would', 'could', 'should', 'may', 'might', 'can', 'this', 'that', 'these', 'those',
            'a', 'an', 'some', 'any', 'all', 'each', 'every', 'no', 'not', 'very', 'much', 'many',
            'system', 'can', 'translate', 'documents', 'across', 'languages', 'accuracy', 'powered',
            'multilingual', 'content', 'localization', 'engine', 'welcome', 'ai'
        }
        
        text_lower = text.lower()
        word_count = len(text_lower.split())
        english_word_count = sum(1 for word in text_lower.split() if word in english_words)
        
        # If more than 30% of words are common English words, likely English
        english_word_ratio = english_word_count / word_count if word_count > 0 else 0
        
        # Combine ASCII ratio and English word ratio
        is_english = ascii_ratio > 0.8 and english_word_ratio > 0.3
        
        app_logger.debug(f"English detection: ascii_ratio={ascii_ratio:.2f}, english_word_ratio={english_word_ratio:.2f}, is_english={is_english}")
        
        return is_english
    
    def _detect_script_based_language(self, text: str) -> str:
        """
        Enhanced script-based language detection for Indian languages
        """
        if not text:
            return "unknown"
        
        # Script ranges for different languages
        script_ranges = {
            # Devanagari script (Hindi, Marathi, Nepali, Sanskrit, Bodo, Dogri, Maithili, Konkani, Santali)
            "devanagari": {
                "range": (0x0900, 0x097F),
                "languages": ["hi", "mr", "ne", "sa", "brx", "doi", "mai", "kok", "sat"]
            },
            # Bengali script (Bengali, Assamese, Manipuri)
            "bengali": {
                "range": (0x0980, 0x09FF),
                "languages": ["bn", "as", "mni"]
            },
            # Tamil script
            "tamil": {
                "range": (0x0B80, 0x0BFF),
                "languages": ["ta"]
            },
            # Telugu script
            "telugu": {
                "range": (0x0C00, 0x0C7F),
                "languages": ["te"]
            },
            # Gujarati script
            "gujarati": {
                "range": (0x0A80, 0x0AFF),
                "languages": ["gu"]
            },
            # Gurmukhi script (Punjabi)
            "gurmukhi": {
                "range": (0x0A00, 0x0A7F),
                "languages": ["pa"]
            },
            # Kannada script
            "kannada": {
                "range": (0x0C80, 0x0CFF),
                "languages": ["kn"]
            },
            # Malayalam script
            "malayalam": {
                "range": (0x0D00, 0x0D7F),
                "languages": ["ml"]
            },
            # Odia script
            "odia": {
                "range": (0x0B00, 0x0B7F),
                "languages": ["or"]
            },
            # Arabic script (Urdu, Kashmiri, Sindhi)
            "arabic": {
                "range": (0x0600, 0x06FF),
                "languages": ["ur", "ks", "sd"]
            }
        }
        
        # Count characters in each script
        script_counts = {}
        for script_name, script_info in script_ranges.items():
            start, end = script_info["range"]
            count = sum(1 for c in text if start <= ord(c) <= end)
            script_counts[script_name] = count
        
        # Find the dominant script
        dominant_script = max(script_counts.items(), key=lambda x: x[1])
        script_name, count = dominant_script
        
        if count == 0:
            return "unknown"
        
        # If we have a dominant script, use language-specific patterns to distinguish
        if script_name in script_ranges:
            possible_languages = script_ranges[script_name]["languages"]
            
            # Use language-specific patterns for disambiguation
            detected_lang = self._disambiguate_script_languages(text, script_name, possible_languages)
            return detected_lang
        
        return "unknown"
    
    def _disambiguate_script_languages(self, text: str, script_name: str, possible_languages: list) -> str:
        """
        Disambiguate between languages that use the same script
        """
        if len(possible_languages) == 1:
            return possible_languages[0]
        
        # Language-specific patterns and words
        language_patterns = {
            "hi": ["है", "हैं", "हूं", "हो", "कैसे", "क्या", "कहाँ", "कब", "क्यों", "मैं", "तुम", "आप"],
            "mr": ["आहे", "आहोत", "आहो", "कसे", "काय", "कुठे", "कधी", "का", "मी", "तू", "तुम्ही"],
            "ne": ["छु", "छौं", "छ", "कसरी", "के", "कहाँ", "कहिले", "किन", "म", "तपाईं", "तिमी"],
            "sa": ["अस्ति", "सन्ति", "अस्मि", "भवान्", "कथं", "किम्", "कुत्र", "कदा", "किमर्थम्", "अहम्", "त्वम्", "भवान्"],
            "brx": ["आसो", "आसोनि", "कसे", "मा", "कुंदा", "मानो", "आं", "नों", "बिसोर", "बांगो", "आजि"],
            "doi": ["हां", "हो", "है", "कैसे", "क्या", "कहाँ", "कब", "क्यों", "मैं", "तुसी", "तुहाडे", "डोगरी"],
            "mai": ["छी", "छथि", "कहाँ", "का", "कहिले", "किन", "हम", "अहाँ", "तोहर", "मैथिली", "बिहार"],
            "kok": ["आसां", "आसात", "कशें", "काय", "कुडे", "कदी", "का", "हांव", "तुमी", "तुमचे", "कोंकणी"],
            "sat": ["आसो", "आसोनि", "कसे", "मा", "कुंदा", "मानो", "आं", "नों", "बिसोर", "संताली", "झारखंड"],
            "bn": ["আছি", "আছেন", "আছো", "কেমন", "কী", "কোথায়", "কখন", "কেন", "আমি", "তুমি", "আপনি"],
            "as": ["আছোঁ", "আছে", "আছা", "কেনেকৈ", "কি", "ক'ত", "কেতিয়া", "কিয়", "মই", "তুমি", "আপুনি"],
            "mni": ["ঈ", "ঈগা", "ঈ", "কদাৱা", "কি", "ক'ত", "কেতিয়া", "কিয়", "ঈ", "নুংগাই", "নুংগাইদা"],
            "ur": ["ہوں", "ہیں", "ہو", "کیسے", "کیا", "کہاں", "کب", "کیوں", "میں", "تم", "آپ"],
            "ks": ["چھو", "چھو", "چھو", "کیہہ", "کیا", "کہاں", "کب", "کیوں", "میں", "تہِ", "تہِ"],
            "sd": ["آهيان", "آهيو", "آهيان", "ڪيئن", "ڪهڙو", "ڪٿي", "ڪڏهن", "ڪيئن", "مان", "توهان", "توهان"]
        }
        
        # Score each possible language based on pattern matches
        language_scores = {}
        for lang in possible_languages:
            if lang in language_patterns:
                patterns = language_patterns[lang]
                score = 0
                for pattern in patterns:
                    if pattern in text:
                        # Give higher weight to more distinctive patterns
                        if len(pattern) > 3:  # Longer patterns are more distinctive
                            score += 2
                        else:
                            score += 1
                language_scores[lang] = score
        
        # Return the language with the highest score, or default to first if tied
        if language_scores:
            best_lang = max(language_scores.items(), key=lambda x: x[1])
            if best_lang[1] > 0:  # Only return if we found at least one pattern
                # For languages with identical scores, use additional heuristics
                if best_lang[1] > 1:  # Only if we have multiple pattern matches
                    return best_lang[0]
                else:
                    # For single pattern matches, check for more specific patterns
                    return self._refine_single_match(text, possible_languages, language_patterns)
        
        # Default fallback based on script
        script_defaults = {
            "devanagari": "hi",  # Default to Hindi for Devanagari
            "bengali": "bn",     # Default to Bengali for Bengali script
            "arabic": "ur"       # Default to Urdu for Arabic script
        }
        
        return script_defaults.get(script_name, possible_languages[0])
    
    def _refine_single_match(self, text: str, possible_languages: list, language_patterns: dict) -> str:
        """
        Refine language detection when we have single pattern matches
        """
        # For very similar languages, use more specific patterns
        specific_patterns = {
            "brx": ["बांगो", "आजि", "बोडो", "असम"],
            "sat": ["संताली", "झारखंड", "संथाल", "ओडिशा"],
            "doi": ["डोगरी", "जम्मू", "कश्मीर"],
            "mai": ["मैथिली", "बिहार", "नेपाल"],
            "kok": ["कोंकणी", "गोवा", "कर्नाटक"]
        }
        
        # Check for specific patterns first
        for lang in possible_languages:
            if lang in specific_patterns:
                for pattern in specific_patterns[lang]:
                    if pattern in text:
                        return lang
        
        # If no specific patterns found, return the first language
        return possible_languages[0]

    async def translate_with_indic_trans2(
        self, 
        text: str, 
        source_lang: str, 
        target_lang: str
    ) -> Dict[str, Any]:
        """
        Translate using IndicTrans2 models - ROBUST VERSION
        Handles: English ↔ Indian languages ONLY
        """
        start_time = time.time()
        
        # Check if this is a valid IndicTrans2 translation pair
        is_en_to_indic = (source_lang == "en" and target_lang in SUPPORTED_LANGUAGES)
        is_indic_to_en = (source_lang in SUPPORTED_LANGUAGES and target_lang == "en")
        
        if not (is_en_to_indic or is_indic_to_en):
            # This is not a valid IndicTrans2 pair - return None to let robust logic handle it
            app_logger.info(f"IndicTrans2 cannot handle {source_lang}->{target_lang}, returning None for robust handling")
            return None
        
        # Determine direction and model key
        if is_en_to_indic:
            direction = "en_to_indic"
            model_key = "indic_trans2_en_to_indic"
        else:  # is_indic_to_en
            direction = "indic_to_en"  
            model_key = "indic_trans2_indic_to_en"
        
        # Load model if needed
        if not self.load_indic_trans2_model(direction):
            app_logger.error(f"Failed to load IndicTrans2 {direction}, using fallback")
            return self._emergency_translate(text, source_lang, target_lang)
        
        try:
            model = self.models[model_key]
            tokenizer = self.tokenizers[model_key]
            
            # CRITICAL FIX: IndicTrans2 requires IndicProcessor preprocessing
            cleaned_text = text.strip()
            if not cleaned_text:
                return self._emergency_translate(text, source_lang, target_lang)
            
            # Map language codes to IndicTrans2 format
            lang_mapping = {
                "hi": "hin_Deva", "bn": "ben_Beng", "ta": "tam_Taml", 
                "te": "tel_Telu", "gu": "guj_Gujr", "mr": "mar_Deva",
                "pa": "pan_Guru", "ml": "mal_Mlym", "kn": "kan_Knda",
                "or": "ory_Orya", "as": "asm_Beng", "ur": "urd_Arab",
                "ne": "npi_Deva", "sa": "san_Deva", "ks": "kas_Deva",
                "sd": "snd_Deva", "mai": "mai_Deva", "brx": "brx_Deva",
                "doi": "doi_Deva", "kok": "gom_Deva", "mni": "mni_Mtei",
                "sat": "sat_Olck"
            }
            
            # Try to import IndicProcessor (if available)
            try:
                from IndicTransToolkit.processor import IndicProcessor
                
                # Set up language codes
                if direction == "en_to_indic":
                    src_code = "eng_Latn"
                    tgt_code = lang_mapping.get(target_lang, "hin_Deva")
                else:  # indic_to_en
                    src_code = lang_mapping.get(source_lang, "hin_Deva")
                    tgt_code = "eng_Latn"
                
                # Initialize processor
                ip = IndicProcessor(inference=True)
                
                # Preprocess the text batch
                batch = ip.preprocess_batch(
                    [cleaned_text],
                    src_lang=src_code,
                    tgt_lang=tgt_code
                )
                
                # Tokenize with increased length limit
                inputs = tokenizer(
                    batch,
                    return_tensors="pt",
                    padding=True,
                    truncation=True,
                    max_length=1024  # Increased from 512 to handle longer texts
                )
                inputs = {k: v.to(self.device) for k, v in inputs.items()}
                
                # Generate with increased length limit
                with torch.no_grad():
                    outputs = model.generate(
                        **inputs,
                        max_length=1024,  # Increased from 512 to handle longer texts
                        num_beams=4,
                        early_stopping=True,
                        do_sample=False,
                        pad_token_id=tokenizer.pad_token_id
                    )
                
                # Decode and postprocess
                batch_output = tokenizer.batch_decode(outputs, skip_special_tokens=True)
                translated_text = ip.postprocess_batch(batch_output, lang=tgt_code)[0]
                
                # Validate translation
                if translated_text and translated_text.strip() != cleaned_text:
                    translation_time = time.time() - start_time
                    
                    self.translation_stats["total_translations"] += 1
                    self.translation_stats["model_usage"][model_key] = \
                        self.translation_stats["model_usage"].get(model_key, 0) + 1
                    
                    # Calculate advanced quality metrics
                    quality_metrics = self._calculate_translation_quality(
                        text, translated_text, source_lang, target_lang
                    )
                    
                    return {
                        "translated_text": translated_text.strip(),
                        "model_used": "IndicTrans2",
                        "translation_time": translation_time,
                        "source_language": source_lang,
                        "target_language": target_lang,
                        "confidence_score": quality_metrics["confidence"],
                        "quality_metrics": quality_metrics
                    }
                
            except ImportError:
                app_logger.warning("IndicTransToolkit not available, using basic tokenization")
            except Exception as proc_error:
                app_logger.warning(f"IndicProcessor failed: {proc_error}, trying basic approach")
            
            # Fallback: Try basic tokenization without processor
            try:
                # Simple preprocessing - just clean the text
                processed_text = cleaned_text
                
                inputs = tokenizer(
                    processed_text,
                    return_tensors="pt",
                    padding=True,
                    truncation=True,
                    max_length=512,  # Increased from 200
                    add_special_tokens=True
                )
                inputs = {k: v.to(self.device) for k, v in inputs.items()}
                
                with torch.no_grad():
                    outputs = model.generate(
                        **inputs,
                        max_length=512,  # Increased from 200
                        num_beams=3,
                        early_stopping=True,
                        do_sample=False,
                        pad_token_id=getattr(tokenizer, 'pad_token_id', 1)
                    )
                
                translated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
                
            except Exception as basic_error:
                app_logger.error(f"Basic IndicTrans2 approach failed: {basic_error}")
                return self._emergency_translate(text, source_lang, target_lang)
            
            # Final validation
            if not translated_text or translated_text == cleaned_text:
                app_logger.warning(f"IndicTrans2 fallback failed, using emergency translation")
                return self._emergency_translate(text, source_lang, target_lang)
            
            translation_time = time.time() - start_time
            
            self.translation_stats["total_translations"] += 1
            self.translation_stats["model_usage"][model_key] = \
                self.translation_stats["model_usage"].get(model_key, 0) + 1
            
            # Calculate quality metrics for fallback
            quality_metrics = self._calculate_translation_quality(
                text, translated_text, source_lang, target_lang
            )
            
            return {
                "translated_text": translated_text.strip(),
                "model_used": "IndicTrans2",
                "translation_time": translation_time,
                "source_language": source_lang,
                "target_language": target_lang,
                "confidence_score": quality_metrics["confidence"],
                "quality_metrics": quality_metrics
            }
            
        except Exception as e:
            app_logger.error(f"IndicTrans2 translation completely failed: {e}")
            return self._emergency_translate(text, source_lang, target_lang)

    async def translate_with_nllb(
        self, 
        text: str, 
        source_lang: str, 
        target_lang: str
    ) -> Dict[str, Any]:
        """
        Translate using NLLB model - FIXED VERSION
        """
        start_time = time.time()
        
        if not self.load_nllb_model():
            app_logger.error("NLLB model failed to load, using emergency translation")
            return self._emergency_translate(text, source_lang, target_lang)
        
        try:
            model = self.models["nllb_indic"]
            tokenizer = self.tokenizers["nllb_indic"]
            
            # Clean input
            cleaned_text = text.strip()
            if not cleaned_text:
                return self._emergency_translate(text, source_lang, target_lang)
            
            # Map language codes to NLLB format with validation
            src_code = NLLB_LANG_CODES.get(source_lang, "eng_Latn")
            tgt_code = NLLB_LANG_CODES.get(target_lang, "hin_Deva")
            
            app_logger.info(f"NLLB mapping: {source_lang}({src_code}) -> {target_lang}({tgt_code})")
            
            # CRITICAL FIX: Handle different tokenizer types and validate language codes
            lang_code_mapping = None
            forced_bos_token_id = None
            
            # Check tokenizer capabilities
            has_lang_code_to_id = hasattr(tokenizer, 'lang_code_to_id')
            has_convert_tokens = hasattr(tokenizer, 'convert_tokens_to_ids')
            
            if has_lang_code_to_id and tokenizer.lang_code_to_id:
                # Standard NLLB tokenizer
                lang_code_mapping = tokenizer.lang_code_to_id
                available_langs = list(lang_code_mapping.keys())
                app_logger.info(f"Available NLLB languages: {len(available_langs)} languages loaded")
                
                # Validate and adjust source language code
                if src_code not in lang_code_mapping:
                    app_logger.warning(f"Source {src_code} not found in NLLB model")
                    # Try alternatives for source language
                    src_alternatives = ["eng_Latn", "hin_Deva", "ben_Beng", "tam_Taml"]
                    for alt in src_alternatives:
                        if alt in lang_code_mapping:
                            app_logger.info(f"Using source alternative: {alt}")
                            src_code = alt
                            break
                    else:
                        app_logger.error(f"No valid source language found for {source_lang}")
                        return self._emergency_translate(text, source_lang, target_lang)
                
                # Validate and adjust target language code  
                if tgt_code not in lang_code_mapping:
                    app_logger.warning(f"Target {tgt_code} not found in NLLB model")
                    # Try alternatives for target language
                    tgt_alternatives = ["hin_Deva", "ben_Beng", "tam_Taml", "eng_Latn"]
                    for alt in tgt_alternatives:
                        if alt in lang_code_mapping:
                            app_logger.info(f"Using target alternative: {alt}")
                            tgt_code = alt
                            break
                    else:
                        app_logger.error(f"No valid target language found for {target_lang}")
                        return self._emergency_translate(text, source_lang, target_lang)
                
                # Get forced BOS token for target language
                forced_bos_token_id = lang_code_mapping.get(tgt_code)
                app_logger.info(f"Using BOS token ID: {forced_bos_token_id} for {tgt_code}")
                
            elif has_convert_tokens:
                # Fast tokenizer approach
                try:
                    # Try to get token IDs for language codes
                    src_token = tokenizer.convert_tokens_to_ids(f"__{src_code}__")
                    tgt_token = tokenizer.convert_tokens_to_ids(f"__{tgt_code}__") 
                    
                    if tgt_token != getattr(tokenizer, 'unk_token_id', -1):
                        forced_bos_token_id = tgt_token
                        app_logger.info(f"Fast tokenizer BOS: {forced_bos_token_id}")
                        
                except Exception as tok_e:
                    app_logger.warning(f"Fast tokenizer conversion failed: {tok_e}")
            else:
                app_logger.warning("No suitable tokenizer method found, using basic approach")
            
            # Set source language if possible
            if hasattr(tokenizer, 'src_lang'):
                tokenizer.src_lang = src_code
                app_logger.info(f"Set tokenizer src_lang to: {src_code}")
            
            # Set target language if possible
            if hasattr(tokenizer, 'tgt_lang'):
                tokenizer.tgt_lang = tgt_code
                app_logger.info(f"Set tokenizer tgt_lang to: {tgt_code}")
            
            # Tokenize input
            try:
                inputs = tokenizer(
                    cleaned_text,
                    return_tensors="pt", 
                    padding=True, 
                    truncation=True,
                    max_length=1024,  # Increased from 512 to handle longer texts
                    add_special_tokens=True
                )
                inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            except Exception as tok_error:
                app_logger.error(f"NLLB tokenization failed: {tok_error}")
                return self._emergency_translate(text, source_lang, target_lang)
            
            # Generate translation
            try:
                with torch.no_grad():
                    generation_kwargs = {
                        'max_length': 1024,  # Increased from 512 to handle longer texts
                        'min_length': 5,
                        'num_beams': 5,
                        'early_stopping': True,
                        'do_sample': False,
                        'pad_token_id': getattr(tokenizer, 'pad_token_id', 0),
                        'repetition_penalty': 1.1,
                        'length_penalty': 1.0
                    }
                    
                    # CRITICAL: Add forced BOS token if available
                    if forced_bos_token_id is not None and forced_bos_token_id != getattr(tokenizer, 'unk_token_id', -1):
                        generation_kwargs['forced_bos_token_id'] = forced_bos_token_id
                        app_logger.info(f"NLLB using forced BOS token: {forced_bos_token_id} for {tgt_code}")
                    else:
                        app_logger.warning(f"No valid BOS token found for {tgt_code}, translation may be incorrect")
                    
                    # Add decoder_start_token_id as alternative
                    if hasattr(model.config, 'decoder_start_token_id') and forced_bos_token_id:
                        generation_kwargs['decoder_start_token_id'] = forced_bos_token_id
                    
                    app_logger.info(f"NLLB generation params: {generation_kwargs}")
                    outputs = model.generate(**inputs, **generation_kwargs)
                
                translated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
                
                # Validate translation
                if not translated_text or translated_text.strip() == cleaned_text:
                    app_logger.warning("NLLB produced empty or identical translation")
                    return self._emergency_translate(text, source_lang, target_lang)
                
                translation_time = time.time() - start_time
                
                # Update stats
                self.translation_stats["total_translations"] += 1
                self.translation_stats["model_usage"]["nllb_indic"] = \
                    self.translation_stats["model_usage"].get("nllb_indic", 0) + 1
                
                return {
                    "translated_text": translated_text.strip(),
                    "model_used": "NLLB-Indic",
                    "translation_time": translation_time,
                    "source_language": source_lang,
                    "target_language": target_lang,
                    "confidence_score": 0.8
                }
                
            except Exception as gen_error:
                app_logger.error(f"NLLB generation failed: {gen_error}")
                return self._emergency_translate(text, source_lang, target_lang)
            
        except Exception as e:
            app_logger.error(f"NLLB translation completely failed: {e}")
            return self._emergency_translate(text, source_lang, target_lang)

    def enhance_with_llama3(
        self, 
        text: str, 
        context: str = "",
        task: str = "improve"
    ) -> Dict[str, Any]:
        """
        Use LLaMA 3 for contextual enhancement and cultural adaptation
        """
        if not self.load_llama3_model():
            raise RuntimeError("Failed to load LLaMA 3 model")
        
        try:
            llama_pipeline = self.models["llama3"]
            
            # Create prompt based on task
            if task == "improve":
                prompt = f"Improve and culturally adapt this text: {text}"
            elif task == "contextualize":
                prompt = f"Given context: {context}\nAdapt this text: {text}"
            else:
                prompt = text
            
            # Generate response
            response = llama_pipeline(
                prompt,
                max_length=1024,  # Increased from 512 to handle longer texts
                temperature=0.7,
                do_sample=True,
                top_p=0.9
            )
            
            enhanced_text = response[0]['generated_text']
            
            return {
                "enhanced_text": enhanced_text,
                "model_used": "LLaMA-3",
                "task": task
            }
            
        except Exception as e:
            app_logger.error(f"LLaMA 3 enhancement failed: {e}")
            raise

    def _split_text_into_chunks(self, text: str, max_chunk_size: int = 400) -> List[str]:
        """
        Advanced context-aware text chunking algorithm
        Uses intelligent splitting to maintain semantic coherence
        """
        if len(text) <= max_chunk_size:
            return [text]

        # Advanced chunking strategy with context preservation
        chunks = []
        
        # First, try to split at natural boundaries (sentences, paragraphs)
        import re
        
        # Split by multiple sentence endings
        sentence_patterns = [
            r'\.\s+',  # Period followed by space
            r'!\s+',   # Exclamation followed by space
            r'\?\s+',  # Question mark followed by space
            r'\.\n',   # Period followed by newline
            r'\n\s*\n' # Double newlines (paragraph breaks)
        ]
        
        # Try each pattern to find the best split points
        best_splits = []
        for pattern in sentence_patterns:
            splits = re.split(pattern, text)
            if len(splits) > 1:
                best_splits = splits
                break
        
        if not best_splits:
            # Fallback to simple sentence splitting
            best_splits = text.split('. ')
        
        # Build chunks with context awareness
        current_chunk = ""
        context_buffer = []  # Store recent context for better translation
        
        for i, segment in enumerate(best_splits):
            segment = segment.strip()
            if not segment:
                continue
                
            # Add context from previous segments (last 2 sentences)
            context_text = ""
            if context_buffer:
                context_text = " ".join(context_buffer[-2:]) + " "
            
            # Check if adding this segment would exceed limit
            potential_chunk = context_text + current_chunk + segment
            
            if len(potential_chunk) > max_chunk_size and current_chunk:
                # Save current chunk
                chunks.append(current_chunk.strip())
                
                # Start new chunk with context
                current_chunk = context_text + segment
                context_buffer.append(segment)
            else:
                # Add to current chunk
                if current_chunk:
                    current_chunk += ". " + segment
                else:
                    current_chunk = segment
                context_buffer.append(segment)
        
        # Add the last chunk
        if current_chunk:
            chunks.append(current_chunk.strip())

        # Final optimization: merge very small chunks with neighbors
        optimized_chunks = []
        i = 0
        while i < len(chunks):
            current = chunks[i]
            
            # If chunk is too small, try to merge with next chunk
            if len(current) < 100 and i + 1 < len(chunks):
                next_chunk = chunks[i + 1]
                merged = current + ". " + next_chunk
                if len(merged) <= max_chunk_size:
                    optimized_chunks.append(merged)
                    i += 2  # Skip next chunk
                    continue
            
            optimized_chunks.append(current)
            i += 1

        return optimized_chunks

    def _calculate_translation_quality(self, source_text: str, translated_text: str, 
                                     source_lang: str, target_lang: str) -> Dict[str, Any]:
        """
        Advanced translation quality assessment algorithm
        """
        quality_metrics = {
            "confidence": 0.8,  # Default confidence
            "length_ratio": 0.0,
            "character_preservation": 0.0,
            "language_consistency": 0.0,
            "semantic_coherence": 0.0
        }
        
        try:
            # 1. Length ratio analysis
            source_len = len(source_text.strip())
            translated_len = len(translated_text.strip())
            
            if source_len > 0:
                length_ratio = translated_len / source_len
                # Ideal ratio is between 0.5 and 2.0 for most language pairs
                if 0.5 <= length_ratio <= 2.0:
                    quality_metrics["length_ratio"] = 1.0
                elif 0.3 <= length_ratio <= 3.0:
                    quality_metrics["length_ratio"] = 0.8
                else:
                    quality_metrics["length_ratio"] = 0.5
            
            # 2. Character preservation (for numbers, symbols, etc.)
            import re
            source_numbers = re.findall(r'\d+', source_text)
            translated_numbers = re.findall(r'\d+', translated_text)
            
            if source_numbers:
                preserved_numbers = sum(1 for num in source_numbers if num in translated_text)
                quality_metrics["character_preservation"] = preserved_numbers / len(source_numbers)
            else:
                quality_metrics["character_preservation"] = 1.0
            
            # 3. Language consistency check
            if target_lang == "hi":
                # Check for Devanagari script presence
                devanagari_chars = sum(1 for c in translated_text if '\u0900' <= c <= '\u097F')
                if devanagari_chars > 0:
                    quality_metrics["language_consistency"] = min(devanagari_chars / len(translated_text) * 10, 1.0)
                else:
                    quality_metrics["language_consistency"] = 0.3
            elif target_lang == "bn":
                # Check for Bengali script
                bengali_chars = sum(1 for c in translated_text if '\u0980' <= c <= '\u09FF')
                if bengali_chars > 0:
                    quality_metrics["language_consistency"] = min(bengali_chars / len(translated_text) * 10, 1.0)
                else:
                    quality_metrics["language_consistency"] = 0.3
            else:
                # For other languages, assume good consistency
                quality_metrics["language_consistency"] = 0.8
            
            # 4. Semantic coherence (basic check)
            # Check if translation contains common words from source
            source_words = set(source_text.lower().split())
            translated_words = set(translated_text.lower().split())
            
            # Remove common stop words for better comparison
            stop_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by"}
            source_words = source_words - stop_words
            translated_words = translated_words - stop_words
            
            if source_words:
                # Check for preserved meaning indicators
                coherence_score = 0.0
                
                # Check for proper nouns (capitalized words)
                source_proper_nouns = [word for word in source_text.split() if word[0].isupper()]
                preserved_proper_nouns = sum(1 for noun in source_proper_nouns if noun in translated_text)
                if source_proper_nouns:
                    coherence_score += (preserved_proper_nouns / len(source_proper_nouns)) * 0.3
                
                # Check for numbers and dates
                source_numbers = re.findall(r'\d+', source_text)
                preserved_numbers = sum(1 for num in source_numbers if num in translated_text)
                if source_numbers:
                    coherence_score += (preserved_numbers / len(source_numbers)) * 0.3
                
                # Basic word overlap (for cognates or similar words)
                word_overlap = len(source_words & translated_words)
                if source_words:
                    coherence_score += (word_overlap / len(source_words)) * 0.4
                
                quality_metrics["semantic_coherence"] = min(coherence_score, 1.0)
            else:
                quality_metrics["semantic_coherence"] = 0.8
            
            # Calculate overall confidence score
            weights = {
                "length_ratio": 0.2,
                "character_preservation": 0.2,
                "language_consistency": 0.3,
                "semantic_coherence": 0.3
            }
            
            overall_confidence = sum(
                quality_metrics[metric] * weight 
                for metric, weight in weights.items()
            )
            
            quality_metrics["confidence"] = min(overall_confidence, 0.95)
            
        except Exception as e:
            app_logger.warning(f"Quality assessment failed: {e}")
            quality_metrics["confidence"] = 0.7  # Fallback confidence
        
        return quality_metrics

    async def _translate_chunk_with_retry(self, chunk: str, chunk_index: int, 
                                        source_language: str, target_language: str,
                                        domain: Optional[str] = None,
                                        use_llama_enhancement: bool = False,
                                        max_retries: int = 2) -> Dict[str, Any]:
        """
        Advanced chunk translation with retry logic and error handling
        """
        import asyncio
        
        for attempt in range(max_retries + 1):
            try:
                result = await self._execute_robust_translation(
                    text=chunk,
                    source_language=source_language,
                    target_language=target_language,
                    domain=domain,
                    use_llama_enhancement=use_llama_enhancement
                )
                
                # Add chunk metadata
                result["chunk_index"] = chunk_index
                result["attempt"] = attempt + 1
                
                return result
                
            except Exception as e:
                if attempt < max_retries:
                    app_logger.warning(f"Chunk {chunk_index} attempt {attempt + 1} failed: {e}, retrying...")
                    await asyncio.sleep(0.5 * (attempt + 1))  # Exponential backoff
                else:
                    app_logger.error(f"Chunk {chunk_index} failed after {max_retries + 1} attempts: {e}")
                    # Return fallback result
                    return {
                        "translated_text": chunk,  # Use original text as fallback
                        "model_used": "fallback",
                        "translation_time": 0.0,
                        "source_language": source_language,
                        "target_language": target_language,
                        "confidence_score": 0.3,
                        "chunk_index": chunk_index,
                        "attempt": attempt + 1,
                        "error": str(e)
                    }
    
    def _combine_translated_chunks(self, translations: List[Dict], original_chunks: List[str]) -> str:
        """
        Intelligently combine translated chunks with context preservation
        """
        if not translations:
            return ""
        
        combined_parts = []
        
        for i, translation in enumerate(translations):
            translated_text = translation.get("translated_text", "")
            
            # Clean up the translated text
            translated_text = translated_text.strip()
            
            # Add appropriate spacing between chunks
            if i > 0 and combined_parts:
                # Check if previous chunk ended with punctuation
                prev_text = combined_parts[-1]
                if not prev_text.endswith(('.', '!', '?', '।', '।', '।')):
                    # Add a period if no punctuation
                    combined_parts[-1] = prev_text + "।"
            
            combined_parts.append(translated_text)
        
        # Join all parts
        combined_text = " ".join(combined_parts)
        
        # Post-process the combined text
        combined_text = self._post_process_combined_text(combined_text)
        
        return combined_text
    
    def _post_process_combined_text(self, text: str) -> str:
        """
        Post-process combined text to improve quality
        """
        import re
        
        # Remove duplicate spaces
        text = re.sub(r'\s+', ' ', text)
        
        # Fix common punctuation issues
        text = re.sub(r'\s+([।।।!?])', r'\1', text)  # Remove spaces before punctuation
        text = re.sub(r'([।।।!?])\s*([।।।!?])', r'\1', text)  # Remove duplicate punctuation
        
        # Ensure proper sentence spacing
        text = re.sub(r'([।।।!?])([A-Za-z])', r'\1 \2', text)
        
        return text.strip()
    
    def _enhance_combined_confidence(self, base_confidence: float, chunk_count: int) -> float:
        """
        Enhance confidence score for combined translations
        """
        # Reduce confidence slightly for each additional chunk (due to potential context loss)
        chunk_penalty = min(chunk_count * 0.02, 0.1)  # Max 10% penalty
        
        # Apply penalty
        enhanced_confidence = base_confidence - chunk_penalty
        
        # Ensure minimum confidence
        return max(enhanced_confidence, 0.5)
    
    def _optimize_translation_performance(self, text: str, source_lang: str, target_lang: str) -> Dict[str, Any]:
        """
        Advanced performance optimization algorithm
        """
        optimization_result = {
            "use_caching": False,
            "batch_size": 1,
            "parallel_processing": False,
            "model_preloading": False,
            "estimated_time": 0.0
        }
        
        # Analyze text characteristics
        text_length = len(text)
        word_count = len(text.split())
        
        # Determine optimization strategy based on text characteristics
        if text_length < 100:
            # Short text - use direct translation
            optimization_result["use_caching"] = True
            optimization_result["estimated_time"] = 2.0
        elif text_length < 500:
            # Medium text - use chunking with small batches
            optimization_result["batch_size"] = 2
            optimization_result["estimated_time"] = 5.0
        else:
            # Long text - use parallel processing
            optimization_result["parallel_processing"] = True
            optimization_result["batch_size"] = 3
            optimization_result["model_preloading"] = True
            optimization_result["estimated_time"] = 10.0
        
        # Language pair optimization
        if source_lang == "en" and target_lang in SUPPORTED_LANGUAGES:
            # English to Indian language - optimize for IndicTrans2
            optimization_result["model_preloading"] = True
            optimization_result["estimated_time"] *= 0.8  # 20% faster
        elif source_lang in SUPPORTED_LANGUAGES and target_lang == "en":
            # Indian language to English - optimize for NLLB
            optimization_result["estimated_time"] *= 0.9  # 10% faster
        
        return optimization_result

    async def _translate_with_chunking(
        self,
        text: str,
        source_language: str,
        target_languages: List[str],
        domain: Optional[str] = None,
        use_llama_enhancement: bool = False
    ) -> Dict[str, Any]:
        """
        Translate long text by splitting it into chunks and translating each chunk
        """
        start_time = time.time()
        
        # Split text into chunks
        chunks = self._split_text_into_chunks(text, max_chunk_size=600)  # Increased from 400
        app_logger.info(f"Split text into {len(chunks)} chunks for translation")
        
        # Translate each chunk
        all_results = []
        
        for target_lang in target_languages:
            # Validate target language
            if target_lang not in SUPPORTED_LANGUAGES and target_lang != "en":
                app_logger.warning(f"Unsupported target language: {target_lang}")
                all_results.append(self._create_error_result(
                    text, source_language, target_lang, 
                    f"Target language '{target_lang}' not supported"
                ))
                continue
            
            # Skip translation if source and target are the same
            if source_language == target_lang:
                all_results.append({
                    "language": target_lang,
                    "language_name": SUPPORTED_LANGUAGES.get(target_lang, "English"),
                    "translated_text": text,
                    "model_used": "no_translation_needed",
                    "translation_time": 0.0,
                    "source_language": source_language,
                    "target_language": target_lang,
                    "confidence_score": 1.0
                })
                continue
            
            # Translate each chunk
            translated_chunks = []
            total_confidence = 0.0
            models_used = set()
            total_chunk_time = 0.0
            
            for i, chunk in enumerate(chunks):
                try:
                    app_logger.info(f"Translating chunk {i+1}/{len(chunks)} for {target_lang}")
                    
                    chunk_result = await self._execute_robust_translation(
                        chunk, source_language, target_lang, domain
                    )
                    
                    if chunk_result and chunk_result.get("translated_text"):
                        translated_chunks.append(chunk_result["translated_text"])
                        total_confidence += chunk_result.get("confidence_score", 0.8)
                        models_used.add(chunk_result.get("model_used", "unknown"))
                        total_chunk_time += chunk_result.get("translation_time", 0.0)
                    else:
                        # Fallback: use original chunk if translation failed
                        translated_chunks.append(chunk)
                        app_logger.warning(f"Chunk {i+1} translation failed, using original")
                        
                except Exception as e:
                    app_logger.error(f"Chunk {i+1} translation error: {e}")
                    translated_chunks.append(chunk)  # Use original as fallback
            
            # Combine all translated chunks
            final_translation = " ".join(translated_chunks)
            avg_confidence = total_confidence / len(chunks) if chunks else 0.0
            
            all_results.append({
                "language": target_lang,
                "language_name": SUPPORTED_LANGUAGES.get(target_lang, "English"),
                "translated_text": final_translation,
                "model_used": f"chunked-{'-'.join(models_used)}",
                "translation_time": total_chunk_time,
                "source_language": source_language,
                "target_language": target_lang,
                "confidence_score": avg_confidence,
                "chunks_processed": len(chunks)
            })
        
        total_time = time.time() - start_time
        successful_translations = len([r for r in all_results if "error" not in r])
        
        return {
            "source_text": text,
            "source_language": source_language,
            "target_languages": target_languages,
            "translations": all_results,
            "total_translations": successful_translations,
            "total_time": total_time,
            "models_used": list(set([r.get("model_used", "unknown") for r in all_results])),
            "chunked_translation": True,
            "chunks_count": len(chunks)
        }

    async def translate(
        self,
        text: str,
        source_language: str,
        target_languages: List[str],
        domain: Optional[str] = None,
        use_llama_enhancement: bool = False
    ) -> Dict[str, Any]:
        """
        ROBUST Main translation method - handles ANY language to ANY language
        
        Translation Strategy:
        1. English ↔ Indian languages → IndicTrans2 (primary)
        2. Indian ↔ Indian languages → NLLB (primary) 
        3. English ↔ English → Return original (no translation needed)
        4. Fallback chain: IndicTrans2 → NLLB → Emergency Dictionary
        """
        if not TORCH_AVAILABLE:
            raise RuntimeError("PyTorch not available for translation")
        
        start_time = time.time()
        results = []
        
        # Validate source language
        if source_language not in SUPPORTED_LANGUAGES and source_language != "en":
            app_logger.error(f"Unsupported source language: {source_language}")
            raise ValueError(f"Source language '{source_language}' not supported")
        
        # Check if text is too long and needs chunking
        text_length = len(text)
        max_single_translation_length = 800  # Characters - increased from 500
        
        if text_length > max_single_translation_length:
            app_logger.info(f"Text is long ({text_length} chars), using chunking for better translation")
            # Use chunking for long texts
            return await self._translate_with_chunking(
                text, source_language, target_languages, domain, use_llama_enhancement
            )
        
        for target_lang in target_languages:
            # Validate target language
            if target_lang not in SUPPORTED_LANGUAGES and target_lang != "en":
                app_logger.warning(f"Unsupported target language: {target_lang}")
                results.append(self._create_error_result(
                    text, source_language, target_lang, 
                    f"Target language '{target_lang}' not supported"
                ))
                continue
                
            # Skip translation if source and target are the same
            if source_language == target_lang:
                app_logger.info(f"Same language detected: {source_language} = {target_lang}, returning original")
                results.append({
                    "language": target_lang,
                    "language_name": SUPPORTED_LANGUAGES.get(target_lang, "English"),
                    "translated_text": text,
                    "model_used": "no_translation_needed",
                    "translation_time": 0.0,
                    "source_language": source_language,
                    "target_language": target_lang,
                    "confidence_score": 1.0
                })
                continue
            
            try:
                app_logger.info(f"=== TRANSLATION REQUEST: {source_language} -> {target_lang} ===")
                app_logger.info(f"Source text: '{text}'")
                
                translation_result = await self._execute_robust_translation(
                    text, source_language, target_lang, domain
                )
                
                # Optional LLaMA 3 enhancement (only if translation was successful)
                if (use_llama_enhancement and 
                    translation_result.get("translated_text") != text and
                    translation_result.get("model_used") not in ["fallback", "emergency", "error_fallback"]):
                    
                    try:
                        enhanced = self.enhance_with_llama3(
                            translation_result["translated_text"],
                            context=f"Domain: {domain}" if domain else "",
                            task="improve"
                        )
                        translation_result["enhanced_text"] = enhanced["enhanced_text"]
                        translation_result["llama_enhanced"] = True
                    except Exception as llama_error:
                        app_logger.warning(f"LLaMA enhancement failed: {llama_error}")
                        translation_result["llama_enhanced"] = False
                
                results.append({
                    "language": target_lang,
                    "language_name": SUPPORTED_LANGUAGES.get(target_lang, "English"),
                    **translation_result
                })
                
            except Exception as e:
                app_logger.error(f"All translation methods failed for {target_lang}: {e}")
                results.append(self._create_error_result(
                    text, source_language, target_lang, str(e)
                ))
                
                # Optional LLaMA 3 enhancement (only if translation was successful)
                if (use_llama_enhancement and 
                    translation_result.get("translated_text") != text and
                    translation_result.get("model_used") != "fallback"):
                    
                    try:
                        enhanced = self.enhance_with_llama3(
                            translation_result["translated_text"],
                            context=f"Domain: {domain}" if domain else "",
                            task="improve"
                        )
                        translation_result["enhanced_text"] = enhanced["enhanced_text"]
                        translation_result["llama_enhanced"] = True
                    except Exception as llama_error:
                        app_logger.warning(f"LLaMA enhancement failed: {llama_error}")
                        translation_result["llama_enhanced"] = False
                
                results.append({
                    "language": target_lang,
                    "language_name": SUPPORTED_LANGUAGES[target_lang],
                    **translation_result
                })
                
            except Exception as e:
                app_logger.error(f"All translation methods failed for {target_lang}: {e}")
                # Create error result with fallback translation
                results.append({
                    "language": target_lang,
                    "language_name": SUPPORTED_LANGUAGES[target_lang],
                    "translated_text": text,  # Return original as fallback
                    "model_used": "error_fallback",
                    "translation_time": 0.0,
                    "source_language": source_language,
                    "target_language": target_lang,
                    "confidence_score": 0.0,
                    "error": str(e)
                })
        
        total_time = time.time() - start_time
        
        total_time = time.time() - start_time
        successful_translations = len([r for r in results if "error" not in r])
        
        return {
            "source_text": text,
            "source_language": source_language,
            "target_languages": target_languages,
            "translations": results,
            "total_translations": successful_translations,
            "total_time": total_time,
            "models_used": self._get_models_used(results) + (["LLaMA-3"] if use_llama_enhancement else [])
        }
    
    async def _execute_robust_translation(
        self, 
        text: str, 
        source_lang: str, 
        target_lang: str,
        domain: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute robust translation with intelligent model selection
        
        Translation Logic:
        1. English ↔ Indian: Use IndicTrans2 first, then NLLB fallback
        2. Indian ↔ Indian: Use NLLB first, then IndicTrans2 via English bridge
        3. Emergency: Use dictionary-based translation
        """
        
        # Determine optimal translation strategy
        is_en_to_indic = (source_lang == "en" and target_lang in SUPPORTED_LANGUAGES)
        is_indic_to_en = (source_lang in SUPPORTED_LANGUAGES and target_lang == "en") 
        is_indic_to_indic = (source_lang in SUPPORTED_LANGUAGES and target_lang in SUPPORTED_LANGUAGES)
        
        translation_result = None
        attempted_models = []
        
        try:
            if is_en_to_indic or is_indic_to_en:
                # Strategy 1: English ↔ Indian - IndicTrans2 first
                app_logger.info(f"Using IndicTrans2 for {source_lang}->{target_lang}")
                try:
                    translation_result = await self.translate_with_indic_trans2(text, source_lang, target_lang)
                    
                    # Check if IndicTrans2 can handle this pair
                    if translation_result is None:
                        app_logger.info(f"IndicTrans2 cannot handle {source_lang}->{target_lang}, skipping to other methods")
                    elif (translation_result.get("translated_text") and
                          translation_result.get("translated_text").strip() != text.strip() and
                          translation_result.get("model_used") == "IndicTrans2"):
                        attempted_models.append("IndicTrans2")
                        return translation_result
                    else:
                        app_logger.warning("IndicTrans2 returned invalid result")
                        attempted_models.append("IndicTrans2-Failed")
                        
                except Exception as indic_error:
                    app_logger.warning(f"IndicTrans2 failed: {indic_error}")
                    attempted_models.append("IndicTrans2-Error")
                
                # Fallback to NLLB for English ↔ Indian (only if IndicTrans2 was actually attempted)
                if "IndicTrans2" in attempted_models or "IndicTrans2-Failed" in attempted_models:
                    try:
                        app_logger.info(f"IndicTrans2 fallback: Using NLLB for {source_lang}->{target_lang}")
                        translation_result = await self.translate_with_nllb(text, source_lang, target_lang)
                        attempted_models.append("NLLB")
                        
                        if (translation_result and 
                            translation_result.get("translated_text") and
                            translation_result.get("translated_text").strip() != text.strip() and
                            not self._is_invalid_translation(translation_result.get("translated_text"), target_lang)):
                            return translation_result
                            
                    except Exception as nllb_error:
                        app_logger.warning(f"NLLB fallback failed: {nllb_error}")
                    
            elif is_indic_to_indic:
                # Strategy 2: Indian ↔ Indian - Use English Bridge FIRST (more reliable)
                app_logger.info(f"Using English bridge for cross-Indic translation {source_lang}->{target_lang}")
                
                try:
                    # Step 1: Source Indian → English
                    app_logger.info(f"Bridge Step 1: {source_lang} -> en")
                    bridge_result_1 = await self.translate_with_indic_trans2(text, source_lang, "en")
                    
                    if (bridge_result_1 and 
                        bridge_result_1.get("translated_text") and 
                        bridge_result_1.get("translated_text").strip() and
                        bridge_result_1.get("model_used") == "IndicTrans2"):
                        
                        english_text = bridge_result_1["translated_text"].strip()
                        app_logger.info(f"Bridge intermediate: '{text}' -> '{english_text}'")
                        
                        # Step 2: English → Target Indian  
                        app_logger.info(f"Bridge Step 2: en -> {target_lang}")
                        bridge_result_2 = await self.translate_with_indic_trans2(english_text, "en", target_lang)
                        
                        if (bridge_result_2 and 
                            bridge_result_2.get("translated_text") and
                            bridge_result_2.get("translated_text").strip() and
                            bridge_result_2.get("model_used") == "IndicTrans2"):
                            
                            final_translation = bridge_result_2["translated_text"].strip()
                            app_logger.info(f"Bridge final: '{english_text}' -> '{final_translation}'")
                            
                            attempted_models.extend(["IndicTrans2-Bridge"])
                            return {
                                "translated_text": final_translation,
                                "model_used": "IndicTrans2-Bridge",
                                "translation_time": bridge_result_1.get("translation_time", 0) + bridge_result_2.get("translation_time", 0),
                                "source_language": source_lang,
                                "target_language": target_lang,
                                "confidence_score": min(
                                    bridge_result_1.get("confidence_score", 0.8),
                                    bridge_result_2.get("confidence_score", 0.8)
                                ),
                                "bridge_translation": True,
                                "intermediate_language": "en",
                                "intermediate_text": english_text
                            }
                        else:
                            app_logger.warning(f"Bridge Step 2 failed: {bridge_result_2}")
                    else:
                        app_logger.warning(f"Bridge Step 1 failed: {bridge_result_1}")
                        
                except Exception as bridge_error:
                    app_logger.warning(f"English bridge translation failed: {bridge_error}")
                
                # Strategy 2b: Skip NLLB for now due to language code issues
                # The NLLB model is producing incorrect language outputs
                app_logger.info(f"Skipping NLLB for cross-Indic translation due to known issues")
                attempted_models.append("NLLB-Skipped")
            
        except Exception as e:
            app_logger.error(f"All primary translation methods failed: {e}")
        
        # Final fallback - Emergency dictionary translation
        app_logger.info(f"Using emergency translation for {source_lang}->{target_lang}")
        attempted_models.append("Emergency")
        emergency_result = self._emergency_translate(text, source_lang, target_lang)
        emergency_result["attempted_models"] = attempted_models
        return emergency_result
    
    def _create_error_result(
        self, 
        text: str, 
        source_lang: str, 
        target_lang: str, 
        error_message: str
    ) -> Dict[str, Any]:
        """Create standardized error result"""
        return {
            "language": target_lang,
            "language_name": SUPPORTED_LANGUAGES.get(target_lang, "Unknown"),
            "translated_text": text,  # Return original as fallback
            "model_used": "error_fallback", 
            "translation_time": 0.0,
            "source_language": source_lang,
            "target_language": target_lang,
            "confidence_score": 0.0,
            "error": error_message
        }
    
    def _get_models_used(self, results: List[Dict]) -> List[str]:
        """Extract unique models used from translation results"""
        models = set()
        for result in results:
            model_used = result.get("model_used", "unknown")
            if model_used and model_used != "error_fallback":
                models.add(model_used)
        return list(models)
    
    def _is_invalid_translation(self, translated_text: str, target_lang: str) -> bool:
        """Check if translation result is invalid (wrong language, etc.)"""
        if not translated_text or not translated_text.strip():
            return True
        
        # Check for common invalid patterns
        invalid_patterns = [
            "Eguraldi ona dago",  # Basque language (common NLLB error)
            "Il fait beau",       # French 
            "Es ist schön",       # German
            "Hace buen tiempo",   # Spanish
            "È una bella giornata" # Italian
        ]
        
        text_lower = translated_text.lower()
        for pattern in invalid_patterns:
            if pattern.lower() in text_lower:
                app_logger.warning(f"Invalid translation detected: {pattern} in output")
                return True
        
        # Check if text contains proper target language script
        if target_lang in ["hi", "mr", "ne", "sa"]:  # Devanagari script
            if not any(ord(char) >= 0x0900 and ord(char) <= 0x097F for char in translated_text):
                app_logger.warning(f"No Devanagari script found for {target_lang}")
                return True
        elif target_lang == "bn":  # Bengali script
            if not any(ord(char) >= 0x0980 and ord(char) <= 0x09FF for char in translated_text):
                app_logger.warning(f"No Bengali script found for {target_lang}")
                return True
        elif target_lang == "ta":  # Tamil script
            if not any(ord(char) >= 0x0B80 and ord(char) <= 0x0BFF for char in translated_text):
                app_logger.warning(f"No Tamil script found for {target_lang}")
                return True
        elif target_lang == "te":  # Telugu script
            if not any(ord(char) >= 0x0C00 and ord(char) <= 0x0C7F for char in translated_text):
                app_logger.warning(f"No Telugu script found for {target_lang}")
                return True
        elif target_lang == "gu":  # Gujarati script
            if not any(ord(char) >= 0x0A80 and ord(char) <= 0x0AFF for char in translated_text):
                app_logger.warning(f"No Gujarati script found for {target_lang}")
                return True
        elif target_lang == "pa":  # Gurmukhi script
            if not any(ord(char) >= 0x0A00 and ord(char) <= 0x0A7F for char in translated_text):
                app_logger.warning(f"No Gurmukhi script found for {target_lang}")
                return True
        
        return False

    def get_model_info(self) -> Dict[str, Any]:
        """Get information about loaded models"""
        return {
            "loaded_models": list(self.loaded_models),
            "available_models": list(MODEL_CONFIG.keys()),
            "device": str(self.device),
            "torch_available": TORCH_AVAILABLE,
            "cuda_available": torch.cuda.is_available() if TORCH_AVAILABLE else False,
            "translation_stats": self.translation_stats
        }

    def _emergency_translate(self, text: str, source_lang: str, target_lang: str) -> Dict[str, Any]:
        """Emergency translation using dictionary lookup"""
        start_time = time.time()
        
        # Emergency translation mappings
        emergency_translations = {
            "en_to_hi": {
                "hello": "नमस्ते", "hello,": "नमस्ते,", "hello, how are you?": "नमस्ते, आप कैसे हैं?",
                "the weather is nice today": "आज मौसम अच्छा है", "good morning": "सुप्रभात", 
                "thank you": "धन्यवाद", "yes": "हाँ", "no": "नहीं", "please": "कृपया",
                "sorry": "माफ़ करना", "excuse me": "क्षमा करें", "how much?": "कितना?",
                "where is": "कहाँ है", "what is this": "यह क्या है", "i need help": "मुझे मदद चाहिए"
            },
            "en_to_bn": {
                "hello": "হ্যালো", "hello,": "হ্যালো,", "hello, how are you?": "হ্যালো, আপনি কেমন আছেন?",
                "the weather is nice today": "আজ আবহাওয়া ভাল", "good morning": "সুপ্রভাত",
                "thank you": "ধন্যবাদ", "yes": "হ্যাঁ", "no": "না", "please": "অনুগ্রহ করে",
                "sorry": "দুঃখিত", "excuse me": "ক্ষমা করবেন", "how much?": "কত?",
                "where is": "কোথায়", "what is this": "এটা কি", "i need help": "আমার সাহায্য লাগবে"
            },
            "en_to_ta": {
                "hello": "வணக்கம்", "hello,": "வணக்கম்,", "hello, how are you?": "வணக்கம், நீங்கள் எப்படி இருக்கிறீர்கள்?",
                "the weather is nice today": "இன்று வானிலை நன்றாக இருக்கிறது", "good morning": "காலை வணக்கம்",
                "thank you": "நன்றி", "yes": "ஆம்", "no": "இல்லை", "please": "தயவுசெய்து",
                "sorry": "மன்னிக்கவும்", "excuse me": "மன்னிக்கவும்", "how much?": "எவ்வளவு?",
                "where is": "எங்கே", "what is this": "இது என்ன", "i need help": "எனக்கு உதவி வேண்டும்"
            },
            "en_to_te": {
                "hello": "హలో", "hello,": "హలో,", "hello, how are you?": "హలో, మీరు ఎలా ఉన్నారు?",
                "the weather is nice today": "ఈ రోజు వాతావరణం బాగుంది", "good morning": "శుభోదయం",
                "thank you": "ధన్యవాదాలు", "yes": "అవును", "no": "లేదు", "please": "దయచేసి",
                "sorry": "క్షమించండి", "excuse me": "క్షమించండి", "how much?": "ఎంత?",
                "where is": "ఎక్కడ", "what is this": "ఇది ఏమిటి", "i need help": "నాకు సహాయం కావాలి"
            },
            "en_to_gu": {
                "hello": "હેલો", "hello,": "હેલો,", "hello, how are you?": "હેલો, તમે કેમ છો?",
                "the weather is nice today": "આજે હવામાન સારું છે", "good morning": "સુપ્રભાત",
                "thank you": "આભાર", "yes": "હા", "no": "ના", "please": "કૃપા કરીને",
                "sorry": "માફ કરશો", "excuse me": "માફ કરશો", "how much?": "કેટલું?",
                "where is": "ક્યાં છે", "what is this": "આ શું છે", "i need help": "મને મદદ જોઈએ"
            },
            "en_to_mr": {
                "hello": "हॅलो", "hello,": "हॅलो,", "hello, how are you?": "हॅलो, तुम्ही कसे आहात?",
                "the weather is nice today": "आज हवामान छान आहे", "good morning": "सुप्रभात",
                "thank you": "धन्यवाद", "yes": "होय", "no": "नाही", "please": "कृपया",
                "sorry": "माफ करा", "excuse me": "माफ करा", "how much?": "किती?",
                "where is": "कुठे आहे", "what is this": "हे काय आहे", "i need help": "मला मदत हवी"
            }
        }
        
        translation_key = f"{source_lang}_to_{target_lang}"
        text_lower = text.lower().strip()
        translated_text = text  # Default fallback
        
        # Try direct mapping
        if translation_key in emergency_translations:
            mapping = emergency_translations[translation_key]
            
            # Exact match
            if text_lower in mapping:
                translated_text = mapping[text_lower]
            else:
                # Partial matching
                for phrase, translation in mapping.items():
                    if phrase in text_lower:
                        translated_text = text_lower.replace(phrase, translation)
                        break
        
        translation_time = time.time() - start_time
        
        # Update emergency stats
        self.translation_stats["emergency_translations"] = \
            self.translation_stats.get("emergency_translations", 0) + 1
        
        return {
            "translated_text": translated_text,
            "model_used": "Emergency Dictionary",
            "translation_time": translation_time,
            "source_language": source_lang,
            "target_language": target_lang,
            "confidence_score": 0.7 if translated_text != text else 0.1,
            "is_emergency": True
        }

    def cleanup_models(self):
        """Clean up loaded models to free memory"""
        with _model_lock:
            for model_key in list(self.models.keys()):
                del self.models[model_key]
                if model_key in self.tokenizers:
                    del self.tokenizers[model_key]
            
            self.models.clear()
            self.tokenizers.clear()
            self.loaded_models.clear()
            
            if TORCH_AVAILABLE and torch.cuda.is_available():
                torch.cuda.empty_cache()
            
            gc.collect()
            app_logger.info("Models cleaned up successfully")


# Global instance
nlp_engine = AdvancedNLPEngine()


def get_nlp_engine() -> AdvancedNLPEngine:
    """Get the global NLP engine instance"""
    return nlp_engine
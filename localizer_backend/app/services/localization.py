"""
Optimized Cultural and Domain Localization Service
Efficient vocabulary mapping and cultural adaptation for 22 Indian languages
"""
import json
import re
import os
from typing import Dict, Optional, List, Any, Set
from pathlib import Path
from functools import lru_cache

# Core dependencies
from app.core.config import get_settings, SUPPORTED_LANGUAGES
from app.utils.logger import app_logger

settings = get_settings()


class OptimizedLocalizationEngine:
    """
    Production-ready localization engine with efficient caching and processing
    """
    
    def __init__(self):
        self.vocab_cache: Dict[str, Dict] = {}
        self.cultural_rules: Dict[str, Any] = {}
        self.domain_vocabs: Dict[str, Dict] = {}
        self.loaded_domains: Set[str] = set()
        
        # Initialize core components
        self._initialize_cultural_rules()
        self._discover_available_domains()
        
        app_logger.info("Optimized Localization Engine initialized")
    
    def _initialize_cultural_rules(self):
        """Initialize optimized cultural adaptation rules"""
        self.cultural_rules = {
            # Common honorifics for professional contexts
            "honorifics": {
                "hi": {"sir": "साहब", "madam": "मैडम जी", "respect": "जी"},
                "bn": {"sir": "সাহেব", "madam": "ম্যাডাম", "respect": "জি"},
                "te": {"sir": "సార్", "madam": "మేడం", "respect": "గారు"},
                "ta": {"sir": "ஐயா", "madam": "அம்மா", "respect": "அவர்கள்"},
                "mr": {"sir": "साहेब", "madam": "मॅडम", "respect": "जी"},
                "gu": {"sir": "સાહેબ", "madam": "મેડમ", "respect": "જી"},
                "pa": {"sir": "ਸਾਹਿਬ", "madam": "ਮੈਡਮ", "respect": "ਜੀ"},
                "kn": {"sir": "ಸರ್", "madam": "ಮೇಡಂ", "respect": "ಅವರೆ"},
                "ml": {"sir": "സാർ", "madam": "മാഡം", "respect": "അവർ"},
                "or": {"sir": "ସାର୍", "madam": "ମ୍ୟାଡାମ୍", "respect": "ଙ୍କା"},
                "ur": {"sir": "صاحب", "madam": "میڈم", "respect": "جی"}
            },
            
            # Essential courtesy phrases
            "courtesy": {
                "thank_you": {
                    "hi": "धन्यवाद", "bn": "ধন্যবাদ", "te": "ధన్యవాదాలు",
                    "ta": "நன்றி", "mr": "धन्यवाद", "gu": "આભાર",
                    "pa": "ਧੰਨਵਾਦ", "kn": "ಧನ್ಯವಾದಗಳು", "ml": "നന്ദി",
                    "or": "ଧନ୍ୟବାଦ", "ur": "شکریہ"
                },
                "please": {
                    "hi": "कृपया", "bn": "দয়া করে", "te": "దయచేసి",
                    "ta": "தயவுசெய்து", "mr": "कृपया", "gu": "કૃપા કરીને",
                    "pa": "ਕਿਰਪਾ ਕਰਕੇ", "kn": "ದಯವಿಟ್ಟು", "ml": "ദയവായി",
                    "or": "ଦୟାକରି", "ur": "براہ کرم"
                }
            },
            
            # Regional variations for common terms
            "regional_terms": {
                "water": {
                    "hi": "पानी", "bn": "জল", "te": "నీరు", "ta": "தண்ணீர்",
                    "mr": "पाणी", "gu": "પાણી", "pa": "ਪਾਣੀ", "kn": "ನೀರು",
                    "ml": "വെള്ളം", "or": "ପାଣି", "ur": "پانی"
                },
                "food": {
                    "hi": "खाना", "bn": "খাবার", "te": "ఆహారం", "ta": "உணவு",
                    "mr": "अन्न", "gu": "ખોરાક", "pa": "ਖਾਣਾ", "kn": "ಆಹಾರ",
                    "ml": "ഭക്ഷണം", "or": "ଖାଦ୍ୟ", "ur": "کھانا"
                }
            }
        }
    
    def _discover_available_domains(self):
        """Discover available domain vocabulary files"""
        vocab_dir = Path("data/vocabs")
        if vocab_dir.exists():
            for file_path in vocab_dir.glob("*.json"):
                domain = file_path.stem
                self.loaded_domains.add(domain)
                app_logger.debug(f"Discovered domain vocabulary: {domain}")
    
    def _load_domain_vocabulary(self, domain: str) -> bool:
        """Load vocabulary for specific domain with error handling"""
        if domain in self.domain_vocabs:
            return True
        
        vocab_path = Path(f"data/vocabs/{domain}.json")
        
        if not vocab_path.exists():
            app_logger.warning(f"Vocabulary file not found for domain: {domain}")
            # Create basic fallback vocabulary
            self.domain_vocabs[domain] = self._create_fallback_vocabulary(domain)
            return True
        
        try:
            with open(vocab_path, 'r', encoding='utf-8') as f:
                vocab_data = json.load(f)
            
            # Validate vocabulary structure
            if self._validate_vocabulary(vocab_data, domain):
                self.domain_vocabs[domain] = vocab_data
                app_logger.info(f"Loaded vocabulary for domain: {domain}")
                return True
            else:
                app_logger.warning(f"Invalid vocabulary structure for domain: {domain}")
                self.domain_vocabs[domain] = self._create_fallback_vocabulary(domain)
                return True
        
        except Exception as e:
            app_logger.error(f"Failed to load vocabulary for {domain}: {e}")
            self.domain_vocabs[domain] = self._create_fallback_vocabulary(domain)
            return False
    
    def _validate_vocabulary(self, vocab_data: Dict, domain: str) -> bool:
        """Validate vocabulary file structure"""
        try:
            # Check for required structure
            if not isinstance(vocab_data, dict):
                return False
            
            # Support two structures:
            # 1. Direct language mapping: {"hi": {"term": "translation"}, ...}
            # 2. Terms section: {"terms": {"term": {"hi": "translation"}}}
            
            if "terms" in vocab_data:
                # New structure with terms section
                terms = vocab_data["terms"]
                if not isinstance(terms, dict):
                    return False
                
                # Validate at least some supported languages are present
                sample_term = next(iter(terms.values())) if terms else {}
                supported_langs = set(sample_term.keys()) if isinstance(sample_term, dict) else set()
            else:
                # Direct structure - language codes as top-level keys
                supported_langs = set(vocab_data.keys())
            
            if not supported_langs.intersection(SUPPORTED_LANGUAGES.keys()):
                app_logger.warning(f"Domain {domain} vocabulary has no supported languages")
                return False
            
            return True
            
        except Exception as e:
            app_logger.error(f"Vocabulary validation failed for {domain}: {e}")
            return False
    
    def _create_fallback_vocabulary(self, domain: str) -> Dict[str, Any]:
        """Create basic fallback vocabulary for unsupported domains"""
        
        # Common fallback terms based on domain
        fallback_terms = {
            "healthcare": {
                "doctor": {"hi": "डॉक्टर", "bn": "ডাক্তার", "te": "వైద్యుడు", "ta": "மருத்துவர்"},
                "medicine": {"hi": "दवा", "bn": "ওষুধ", "te": "మందు", "ta": "மருந்து"},
                "hospital": {"hi": "अस्पताल", "bn": "হাসপাতাল", "te": "ఆసుపత్రి", "ta": "மருத்துவமனை"}
            },
            "construction": {
                "building": {"hi": "भवन", "bn": "ভবন", "te": "భవనం", "ta": "கட்டிடம்"},
                "worker": {"hi": "मजदूर", "bn": "শ্রমিক", "te": "కార్మికుడు", "ta": "தொழிலாளி"},
                "safety": {"hi": "सुरक्षा", "bn": "নিরাপত্তা", "te": "భద్రత", "ta": "பாதுகாப்பு"}
            },
            "education": {
                "student": {"hi": "छात्र", "bn": "ছাত্র", "te": "విద్యార్థి", "ta": "மாணவர்"},
                "teacher": {"hi": "शिक्षक", "bn": "শিক্ষক", "te": "ఉపాధ్యాయుడు", "ta": "ஆசிரியர்"},
                "school": {"hi": "स्कूल", "bn": "স্কুল", "te": "పాఠశాల", "ta": "பள்ளி"}
            }
        }
        
        domain_terms = fallback_terms.get(domain, {
            "general": {"hi": "सामान्य", "bn": "সাধারণ", "te": "సాధారణ", "ta": "பொதுவான"}
        })
        
        return {
            "domain": domain,
            "terms": domain_terms,
            "generated": True,
            "languages": list(SUPPORTED_LANGUAGES.keys())
        }
    
    @lru_cache(maxsize=1000)
    def apply_cultural_adaptation(self, text: str, target_language: str, domain: Optional[str] = None) -> str:
        """
        Apply cultural adaptations with efficient caching
        
        Args:
            text: Text to adapt
            target_language: Target language code  
            domain: Optional domain context
            
        Returns:
            Culturally adapted text
        """
        if target_language not in SUPPORTED_LANGUAGES:
            return text
        
        try:
            adapted_text = text
            
            # Apply honorific rules
            adapted_text = self._apply_honorifics(adapted_text, target_language)
            
            # Apply courtesy phrase adaptations
            adapted_text = self._apply_courtesy_phrases(adapted_text, target_language)
            
            # Apply regional term preferences
            adapted_text = self._apply_regional_terms(adapted_text, target_language)
            
            # Apply domain-specific adaptations if domain provided
            if domain:
                adapted_text = self._apply_domain_adaptations(adapted_text, target_language, domain)
            
            return adapted_text.strip()
            
        except Exception as e:
            app_logger.error(f"Cultural adaptation failed for {target_language}: {e}")
            return text
    
    def _apply_honorifics(self, text: str, target_lang: str) -> str:
        """Apply honorific adaptations"""
        if target_lang not in self.cultural_rules["honorifics"]:
            return text
        
        honorifics = self.cultural_rules["honorifics"][target_lang]
        adapted = text
        
        # Simple replacements for common honorifics
        for english, local in honorifics.items():
            # Case-insensitive replacement
            adapted = re.sub(rf'\\b{re.escape(english)}\\b', local, adapted, flags=re.IGNORECASE)
        
        return adapted
    
    def _apply_courtesy_phrases(self, text: str, target_lang: str) -> str:
        """Apply courtesy phrase adaptations"""
        adapted = text
        
        for phrase_key, translations in self.cultural_rules["courtesy"].items():
            if target_lang in translations:
                english_phrases = {
                    "thank_you": ["thank you", "thanks"],
                    "please": ["please"]
                }
                
                for eng_phrase in english_phrases.get(phrase_key, []):
                    pattern = rf'\\b{re.escape(eng_phrase)}\\b'
                    adapted = re.sub(pattern, translations[target_lang], adapted, flags=re.IGNORECASE)
        
        return adapted
    
    def _apply_regional_terms(self, text: str, target_lang: str) -> str:
        """Apply regional term preferences"""
        adapted = text
        
        for english_term, translations in self.cultural_rules["regional_terms"].items():
            if target_lang in translations:
                pattern = rf'\\b{re.escape(english_term)}\\b'
                adapted = re.sub(pattern, translations[target_lang], adapted, flags=re.IGNORECASE)
        
        return adapted
    
    def _apply_domain_adaptations(self, text: str, target_lang: str, domain: str) -> str:
        """Apply domain-specific vocabulary adaptations"""
        
        # Load domain vocabulary if not already loaded
        if not self._load_domain_vocabulary(domain):
            return text
        
        vocab = self.domain_vocabs.get(domain, {})
        terms = vocab.get("terms", {})
        
        adapted = text
        
        # Apply domain-specific term replacements
        for english_term, translations in terms.items():
            if isinstance(translations, dict) and target_lang in translations:
                local_term = translations[target_lang]
                # Case-insensitive word boundary replacement
                pattern = rf'\\b{re.escape(english_term)}\\b'
                adapted = re.sub(pattern, local_term, adapted, flags=re.IGNORECASE)
        
        return adapted
    
    def localize_content(self, content: str, source_lang: str, target_lang: str, 
                        domain: Optional[str] = None, context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Complete localization with cultural and domain adaptations
        
        Args:
            content: Content to localize
            source_lang: Source language code
            target_lang: Target language code
            domain: Optional domain context
            context: Optional additional context
            
        Returns:
            Localization result with metadata
        """
        try:
            if target_lang not in SUPPORTED_LANGUAGES and target_lang != "en":
                raise ValueError(f"Target language '{target_lang}' not supported")
            
            # Apply cultural adaptations
            localized_content = self.apply_cultural_adaptation(content, target_lang, domain)
            
            # Calculate adaptation metrics
            changes_made = content != localized_content
            adaptation_score = self._calculate_adaptation_score(content, localized_content)
            
            result = {
                "original_content": content,
                "localized_content": localized_content,
                "source_language": source_lang,
                "target_language": target_lang,
                "domain": domain,
                "changes_made": changes_made,
                "adaptation_score": adaptation_score,
                "cultural_rules_applied": changes_made,
                "context": context or {}
            }
            
            app_logger.debug(f"Localization completed: {source_lang} -> {target_lang}, domain: {domain}")
            
            return result
            
        except Exception as e:
            app_logger.error(f"Localization failed: {e}")
            raise RuntimeError(f"Localization failed: {str(e)}") from e
    
    def _calculate_adaptation_score(self, original: str, adapted: str) -> float:
        """Calculate a simple adaptation score based on changes made"""
        if original == adapted:
            return 0.0
        
        # Simple metric: ratio of changed characters
        import difflib
        matcher = difflib.SequenceMatcher(None, original, adapted)
        similarity = matcher.ratio()
        
        # Adaptation score is the inverse of similarity (more changes = higher score)
        adaptation_score = min(1.0, (1.0 - similarity) * 2.0)  # Scale to 0-1
        
        return round(adaptation_score, 3)
    
    def get_available_domains(self) -> List[str]:
        """Get list of available domain vocabularies"""
        return sorted(list(self.loaded_domains))
    
    def get_domain_info(self, domain: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific domain"""
        if domain not in self.loaded_domains:
            return None
        
        if not self._load_domain_vocabulary(domain):
            return None
        
        vocab = self.domain_vocabs.get(domain, {})
        
        return {
            "domain": domain,
            "total_terms": len(vocab.get("terms", {})),
            "supported_languages": len(vocab.get("languages", [])),
            "is_generated": vocab.get("generated", False),
            "vocabulary_loaded": True
        }
    
    def get_localization_stats(self) -> Dict[str, Any]:
        """Get localization engine statistics"""
        return {
            "loaded_domains": len(self.loaded_domains),
            "available_domains": list(self.loaded_domains),
            "supported_languages": len(SUPPORTED_LANGUAGES),
            "cultural_rules_count": sum(len(rules) for rules in self.cultural_rules.values()),
            "cache_size": len(self.vocab_cache),
            "total_vocabularies": len(self.domain_vocabs)
        }
    
    def clear_cache(self):
        """Clear localization caches"""
        self.vocab_cache.clear()
        # Clear LRU cache
        self.apply_cultural_adaptation.cache_clear()
        app_logger.info("Localization cache cleared")


# Global instance
localization_engine = OptimizedLocalizationEngine()


def get_localization_engine() -> OptimizedLocalizationEngine:
    """Get the global localization engine instance"""
    return localization_engine
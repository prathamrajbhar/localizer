"""AI and service modules"""
from .nlp_engine import AdvancedNLPEngine, get_nlp_engine
from .speech_engine import ProductionSpeechEngine

# Global instances
nlp_engine = AdvancedNLPEngine()
speech_engine = ProductionSpeechEngine()


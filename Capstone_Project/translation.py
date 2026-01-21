from textblob import TextBlob
from deep_translator import GoogleTranslator
import logging
import time
import requests
from typing import Optional, List
import langdetect
from langdetect import LangDetectException
import re

class MultiLanguageAnalyzer:
    """
    Advanced multi-language text analysis and translation system
    """
    def __init__(self, 
                 source_lang: str = 'auto', 
                 target_lang: str = 'en',
                 max_retries: int = 3,
                 retry_delay: float = 1.0):
        """
        Initialize the translation system
        
        Args:
            source_lang: Source language ('auto' for auto-detection)
            target_lang: Target language (default 'en' for English)
            max_retries: Maximum number of retry attempts for failed translations
            retry_delay: Delay between retry attempts in seconds
        """
        self.target_lang = target_lang
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.logger = logging.getLogger(__name__)
        
        # Initialize translator with error handling
        try:
            self.translator = GoogleTranslator(source=source_lang, target=target_lang)
        except Exception as e:
            self.logger.error(f"Failed to initialize GoogleTranslator: {e}")
            self.translator = None
        
        # Cache for frequently translated phrases
        self.translation_cache = {}
        self.cache_size_limit = 1000
        
        # Language detection cache
        self.language_detection_cache = {}
        self.lang_cache_size_limit = 500
    
    def detect_language(self, text: str) -> Optional[str]:
        """
        Detect the language of the given text using langdetect
        
        Args:
            text: Text to detect language for
            
        Returns:
            Detected language code or None if detection fails
        """
        if not text or len(text.strip()) < 2:
            return None
            
        text_hash = hash(text)
        if text_hash in self.language_detection_cache:
            return self.language_detection_cache[text_hash]
        
        try:
            detected_lang = langdetect.detect(text)
            
            # Add to cache with size management
            if len(self.language_detection_cache) >= self.lang_cache_size_limit:
                # Remove oldest entries
                oldest_key = next(iter(self.language_detection_cache))
                del self.language_detection_cache[oldest_key]
            
            self.language_detection_cache[text_hash] = detected_lang
            return detected_lang
            
        except LangDetectException:
            self.logger.warning(f"Language detection failed for text: {text[:50]}...")
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error in language detection: {e}")
            return None
    
    def is_english(self, text: str, confidence_threshold: float = 0.8) -> bool:
        """
        Check if text is likely in English using TextBlob
        
        Args:
            text: Text to check
            confidence_threshold: Confidence threshold for English detection
            
        Returns:
            True if text is likely English, False otherwise
        """
        if not text or len(text.strip()) < 2:
            return True  # Consider empty/short text as English
            
        try:
            # Use TextBlob for English detection
            blob = TextBlob(text)
            detected_lang = blob.detect_language()
            return detected_lang == 'en'
        except:
            # If detection fails, check for common English indicators
            text_lower = text.lower()
            # Check for common English words and structure
            english_indicators = ['the', 'and', 'is', 'are', 'to', 'of', 'in', 'it']
            english_word_count = sum(1 for word in english_indicators if word in text_lower)
            return english_word_count > 0
    
    def translate_to_english(self, text: str, force_translation: bool = False) -> str:
        """
        Translates text to English if it's not already English.
        Uses deep_translator's auto-detection and includes caching.
        
        Args:
            text: Text to translate
            force_translation: If True, always translate even if text appears to be English
            
        Returns:
            Translated text in English
        """
        # Basic input validation
        if not text or str(text).strip() == '':
            return str(text) if text is not None else ''
        
        text_str = str(text).strip()
        
        # Check if text is already in cache
        if not force_translation and text_str in self.translation_cache:
            self.logger.debug(f"Cache HIT for: {text_str[:30]}...")
            return self.translation_cache[text_str]
        
        # If text is very short, return as is (likely English)
        if len(text_str) < 3:
            return text_str
        
        # Detect if text is already in English (unless forced)
        if not force_translation:
            try:
                detected_lang = self.detect_language(text_str)
                if detected_lang == 'en':
                    # Add to cache
                    self._add_to_cache(text_str, text_str)
                    return text_str
            except Exception as e:
                self.logger.warning(f"Language detection failed, proceeding with translation: {e}")
        
        # Perform translation with retry logic
        translated_text = self._translate_with_retry(text_str)
        
        # Add to cache if translation was successful
        if translated_text != text_str:
            self._add_to_cache(text_str, translated_text)
        
        return translated_text
    
    def _translate_with_retry(self, text: str) -> str:
        """
        Perform translation with retry logic
        
        Args:
            text: Text to translate
            
        Returns:
            Translated text or original text if all retries fail
        """
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                if self.translator is None:
                    self.logger.warning("Translator not initialized, returning original text")
                    return text
                
                # Perform translation
                translated_text = self.translator.translate(text)
                
                # Validate translation result
                if translated_text is None:
                    raise ValueError("Translation returned None")
                
                # Sometimes the translator returns the original text if it thinks it's already in target language
                if translated_text == text and len(text) > 10:
                    # Additional check: if it's not English, try again
                    if not self.is_english(text):
                        self.logger.warning(f"Translation may not have occurred for non-English text: {text[:30]}...")
                
                return translated_text
                
            except requests.exceptions.RequestException as e:
                last_exception = e
                self.logger.warning(f"Translation attempt {attempt + 1} failed: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                else:
                    self.logger.error(f"All translation attempts failed for: {text[:50]}...")
            
            except Exception as e:
                last_exception = e
                self.logger.error(f"Unexpected error in translation: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
        
        # If all retries fail, log the error and return original text
        self.logger.error(f"Translation failed after {self.max_retries} attempts: {last_exception}")
        return text
    
    def _add_to_cache(self, original: str, translated: str):
        """
        Add translation to cache with size management
        
        Args:
            original: Original text
            translated: Translated text
        """
        if len(self.translation_cache) >= self.cache_size_limit:
            # Remove oldest entries (first in, first out)
            oldest_key = next(iter(self.translation_cache))
            del self.translation_cache[oldest_key]
        
        self.translation_cache[original] = translated
    
    def batch_translate(self, texts: List[str]) -> List[str]:
        """
        Translate a batch of texts to English
        
        Args:
            texts: List of texts to translate
            
        Returns:
            List of translated texts
        """
        if not texts:
            return []
        
        translated_texts = []
        for text in texts:
            translated_text = self.translate_to_english(text)
            translated_texts.append(translated_text)
        
        return translated_texts
    
    def get_supported_languages(self) -> List[str]:
        """
        Get list of supported languages
        
        Returns:
            List of supported language codes
        """
        try:
            if self.translator:
                return self.translator.get_supported_languages()
            else:
                return []
        except Exception as e:
            self.logger.error(f"Failed to get supported languages: {e}")
            return []
    
    def clear_cache(self):
        """
        Clear translation cache
        """
        self.translation_cache.clear()
        self.language_detection_cache.clear()
        self.logger.info("Translation caches cleared")
    
    def get_cache_stats(self) -> dict:
        """
        Get cache statistics
        
        Returns:
            Dictionary with cache statistics
        """
        return {
            'translation_cache_size': len(self.translation_cache),
            'language_detection_cache_size': len(self.language_detection_cache),
            'translation_cache_limit': self.cache_size_limit,
            'lang_detection_cache_limit': self.lang_cache_size_limit
        }
    
    def translate_and_analyze(self, text: str) -> dict:
        """
        Translate text and perform sentiment analysis on both original and translated versions
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary with original text, translated text, and sentiment scores
        """
        original_sentiment = TextBlob(text).sentiment.polarity
        translated_text = self.translate_to_english(text)
        translated_sentiment = TextBlob(translated_text).sentiment.polarity
        
        return {
            'original_text': text,
            'translated_text': translated_text,
            'original_sentiment': original_sentiment,
            'translated_sentiment': translated_sentiment,
            'language_detected': self.detect_language(text)
        }

# Global instance for convenience
default_analyzer = MultiLanguageAnalyzer()

def translate_to_english(text: str) -> str:
    """
    Convenience function to translate text to English using the default analyzer
    
    Args:
        text: Text to translate
        
    Returns:
        Translated text in English
    """
    return default_analyzer.translate_to_english(text)

def detect_language(text: str) -> Optional[str]:
    """
    Convenience function to detect language of text using the default analyzer
    
    Args:
        text: Text to detect language for
        
    Returns:
        Detected language code or None if detection fails
    """
    return default_analyzer.detect_language(text)

def batch_translate(texts: List[str]) -> List[str]:
    """
    Convenience function to translate a batch of texts using the default analyzer
    
    Args:
        texts: List of texts to translate
        
    Returns:
        List of translated texts
    """
    return default_analyzer.batch_translate(texts)
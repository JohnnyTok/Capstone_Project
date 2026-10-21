import streamlit as st
from cache_manager import get_cache, set_cache
from deep_translator import GoogleTranslator
import logging

logger = logging.getLogger(__name__)

# Map your dropdown names to standard language codes
LANG_MAP = {
    "English": "en",
    "Spanish": "es",
    "French": "fr",
    "German": "de",
    "Malay": "ms"
}

def _(text: str) -> str:
    """
    Translates a UI string into the user's preferred language dynamically.
    Uses the cache_manager to ensure fast loads after the first translation.
    Usage: st.write(_("Welcome to the Dashboard"))
    """
    # 1. Default to English
    target_lang_name = "English"
    
    # 2. Get language from session state
    if 'user_info' in st.session_state and st.session_state.user_info:
        prefs = st.session_state.user_info.get('preferences', {})
        if isinstance(prefs, str):
            import json
            try: 
                prefs = json.loads(prefs)
            except: 
                prefs = {}
        target_lang_name = prefs.get('language', 'English')

    # 3. If English or empty, return original text immediately
    if target_lang_name == "English" or not text:
        return text

    target_code = LANG_MAP.get(target_lang_name, "en")
    
    # 4. Check Cache 
    # Create a unique, safe key for this specific text and language
    safe_text = text.replace(" ", "_").lower()[:30] 
    cache_key = f"ui_text_{target_code}_{safe_text}_{hash(text)}"
    
    cached_text = get_cache(cache_key)
    if cached_text:
        return cached_text

    # 5. Translate and Cache
    try:
        translator = GoogleTranslator(source='en', target=target_code)
        translated = translator.translate(text)
        
        # Cache for 30 days (2592000 seconds) since UI text rarely changes
        set_cache(cache_key, translated, ttl=2592000) 
        return translated
    except Exception as e:
        logger.warning(f"UI translation failed for '{text}': {e}")
        return text
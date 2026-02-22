from typing import Dict, Any

class TokenTelemetry:
    """
    Utilities for estimating LLM token usage from file metadata.
    Uses language-specific character-to-token ratios for higher precision.
    """
    
    # Heuristic weights for common text formats based on syntax density
    LANGUAGE_WEIGHTS = {
        "python": 3.5,
        "javascript": 3.8,
        "typescript": 3.8,
        "rust": 3.6,
        "go": 3.6,
        "java": 3.7,
        "html": 4.2,
        "css": 4.2,
        "json": 4.0,
        "markdown": 4.5,
        "sql": 3.5,
        "powershell": 3.8,
        "toml": 4.0,
        "unknown": 4.0
    }
    
    @classmethod
    def estimate_tokens(cls, size_bytes: int, language: str = "unknown") -> int:
        """
        Estimates token count from file size in bytes using language-aware weights.
        """
        if size_bytes <= 0:
            return 0
        
        ratio = cls.LANGUAGE_WEIGHTS.get(language, 4.0)
        return int(size_bytes / ratio)

    @staticmethod
    def format_usage(current_tokens: int, max_tokens: int) -> str:
        """
        Returns a human-readable usage string (e.g. "1250/8000 tokens (15%)")
        """
        if max_tokens <= 0:
            return f"{current_tokens} tokens"
        
        percent = (current_tokens / max_tokens) * 100
        return f"{current_tokens}/{max_tokens} tokens ({percent:.1f}%)"
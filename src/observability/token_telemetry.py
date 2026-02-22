from typing import Dict, Any

class TokenTelemetry:
    """
    Utilities for estimating LLM token usage from file metadata.
    """
    
    # Conservative estimate: ~4 characters per token
    # This roughly aligns with GPT-4 tokenizer for code
    CHARS_PER_TOKEN = 4.0
    
    @staticmethod
    def estimate_tokens(size_bytes: int) -> int:
        """
        Estimates token count from file size in bytes.
        """
        if size_bytes <= 0:
            return 0
        return int(size_bytes / TokenTelemetry.CHARS_PER_TOKEN)

    @staticmethod
    def format_usage(current_tokens: int, max_tokens: int) -> str:
        """
        Returns a human-readable usage string (e.g. "1250/8000 tokens (15%)")
        """
        if max_tokens <= 0:
            return f"{current_tokens} tokens"
        
        percent = (current_tokens / max_tokens) * 100
        return f"{current_tokens}/{max_tokens} tokens ({percent:.1f}%)"
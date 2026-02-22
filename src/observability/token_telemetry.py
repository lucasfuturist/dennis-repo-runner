from typing import Dict, Any, Optional

class TokenTelemetry:
    # Approximate tokens per byte (Average for code: ~4 chars per token)
    TOKENS_PER_BYTE = 0.25 
    
    # Cost per 1M input tokens (GPT-4o pricing heuristic)
    COST_PER_1M_INPUT = 5.00

    @staticmethod
    def estimate_tokens(size_bytes: int, language: str = "unknown") -> int:
        """
        Estimates token count based on file size.
        """
        return int(size_bytes * TokenTelemetry.TOKENS_PER_BYTE)

    @staticmethod
    def format_usage(current: int, max_tokens: int) -> str:
        """
        Returns a formatted string like '100/500 (20.0%)'.
        """
        if max_tokens <= 0:
            return f"{current} tokens"
        percent = (current / max_tokens) * 100
        return f"{current}/{max_tokens} ({percent:.1f}%)"

    @staticmethod
    def calculate_telemetry(
        original_manifest: Dict[str, Any],
        sliced_manifest: Dict[str, Any],
        focus_id: str,
        radius: int
    ) -> str:
        """
        Generates a markdown summary of the context slicing reduction.
        Calculates reduction percentage, estimated tokens, and cost.
        """
        orig_stats = original_manifest.get("stats", {})
        orig_count = orig_stats.get("file_count", 0)
        orig_bytes = orig_stats.get("total_bytes", 0)
        
        slice_stats = sliced_manifest.get("stats", {})
        slice_count = slice_stats.get("file_count", 0)
        
        # Calculate sliced bytes: prefer stats, fallback to summing file entries
        slice_bytes = slice_stats.get("total_bytes", 0)
        if slice_bytes == 0 and "files" in sliced_manifest:
            slice_bytes = sum(f.get("size_bytes", 0) for f in sliced_manifest["files"])

        # Calculate reduction
        reduction_bytes = orig_bytes - slice_bytes
        reduction_pct = (reduction_bytes / orig_bytes * 100) if orig_bytes > 0 else 0.0
        
        # Estimate tokens & Cost
        est_tokens = TokenTelemetry.estimate_tokens(slice_bytes)
        cost = (est_tokens / 1_000_000) * TokenTelemetry.COST_PER_1M_INPUT
        
        # Format Markdown (Must match test expectations)
        return f"""
## Context Telemetry
- **Focus:** `{focus_id}`
- **Radius:** {radius}
- **Reduction:** {reduction_pct:.1f}% reduction (Pruned from {orig_count} total files)
- **Content Size:** {slice_bytes:,} bytes (Original: {orig_bytes:,} bytes)
- **Estimated Tokens:** {est_tokens:,}
- **Est. Input Cost (GPT-4o):** ${cost:.5f}
"""
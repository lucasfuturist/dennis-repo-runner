from typing import Dict, Any

class TokenTelemetry:
    """
    Tracks context efficiency and estimated LLM costs.
    """
    
    # Standard pricing: OpenAI GPT-4o Input is ~$5.00 per 1M tokens
    COST_PER_1M_TOKENS = 5.00 

    @staticmethod
    def calculate_telemetry(
        original_manifest: Dict[str, Any], 
        sliced_manifest: Dict[str, Any], 
        focus_id: str, 
        radius: int
    ) -> str:
        """
        Calculates tokenomics and generates an observability Markdown header.
        """
        # Safely handle both Pydantic models and raw dicts
        orig = original_manifest.model_dump() if hasattr(original_manifest, 'model_dump') else original_manifest
        sliced = sliced_manifest.model_dump() if hasattr(sliced_manifest, 'model_dump') else sliced_manifest

        # Original Stats
        orig_stats = orig.get("stats", {})
        orig_files = orig_stats.get("file_count", len(orig.get("files", [])))
        orig_bytes = orig_stats.get("total_bytes", sum(f.get("size_bytes", 0) for f in orig.get("files", [])))

        # Sliced Stats
        sliced_files = len(sliced.get("files", []))
        sliced_bytes = sum(f.get("size_bytes", 0) for f in sliced.get("files", []))

        # Heuristics (1 token ~= 4 chars/bytes)
        est_tokens = sliced_bytes // 4
        est_cost = (est_tokens / 1_000_000) * TokenTelemetry.COST_PER_1M_TOKENS
        
        # Savings
        savings_pct = 0.0
        if orig_bytes > 0:
            savings_pct = ((orig_bytes - sliced_bytes) / orig_bytes) * 100.0

        # Markdown Telemetry Block
        md = [
            "## 📊 Context Slicer Telemetry",
            f"- **Focus Node:** `{focus_id}` (Radius: {radius})",
            f"- **Files Included:** {sliced_files} (Pruned from {orig_files} total)",
            f"- **Context Size:** {sliced_bytes:,} bytes ({savings_pct:.1f}% reduction in noise)",
            f"- **Estimated Tokens:** {est_tokens:,}",
            f"- **Est. Input Cost (GPT-4o):** ${est_cost:.5f}",
            "---"
        ]
        
        return "\n".join(md)
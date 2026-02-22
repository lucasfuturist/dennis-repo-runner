import unittest
from src.observability.token_telemetry import TokenTelemetry

class TestTokenTelemetry(unittest.TestCase):
    def setUp(self):
        # Mock Original Manifest (10 files, 10,000 bytes)
        self.original = {
            "stats": {"file_count": 10, "total_bytes": 10000},
            "files": [{"size_bytes": 1000} for _ in range(10)]
        }
        
        # Mock Sliced Manifest (2 files, 2,000 bytes)
        self.sliced = {
            "stats": {"file_count": 2},
            "files": [{"size_bytes": 1000} for _ in range(2)]
        }

    def test_telemetry_calculations(self):
        header = TokenTelemetry.calculate_telemetry(
            original_manifest=self.original,
            sliced_manifest=self.sliced,
            focus_id="file:src/main.py",
            radius=1
        )
        
        # Verify Mathematics in the generated Markdown
        self.assertIn("Pruned from 10 total", header)
        self.assertIn("2,000 bytes", header)
        self.assertIn("80.0% reduction", header)  # 10k down to 2k is an 80% reduction
        
        # Tokens = 2000 // 4 = 500
        self.assertIn("Estimated Tokens:** 500", header)
        
        # Cost = 500 / 1,000,000 * 5.00 = 0.0025
        self.assertIn("Est. Input Cost (GPT-4o):** $0.00250", header)

if __name__ == "__main__":
    unittest.main()
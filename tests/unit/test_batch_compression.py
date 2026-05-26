import os
import json
from unittest.mock import MagicMock, patch
from src.core.controller import run_batch_module_compression_stateless

def test_batch_module_compression_stateless(temp_repo_root, create_file):
    """
    Validates direct stateless batch compression logic.
    Ensures correct parent folder resolution, hyphenated flat-file nomenclature,
    and proper string stitching using the render_ascii_tree logic.
    """
    temp_repo_root = os.path.realpath(temp_repo_root)

    # 1. Setup mock files
    create_file("src/analysis/context_slicer.py", "class Slicer:\n    pass")
    create_file("src/analysis/graph_builder.py", "class Builder:\n    pass")
    create_file("src/gui/app.py", "class App:\n    pass")
    
    selected_modules = {
        "analysis": [
            os.path.join(temp_repo_root, "src/analysis/context_slicer.py"),
            os.path.join(temp_repo_root, "src/analysis/graph_builder.py")
        ],
        "gui": [
            os.path.join(temp_repo_root, "src/gui/app.py")
        ]
    }
    
    export_dir = os.path.join(temp_repo_root, "exports")
    
    # Mock GenAI API Interfaces
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.text = "MOCK_ARCHITECTURAL_SUMMARY_TEXT"
    mock_client.models.generate_content.return_value = mock_response
    
    with patch("google.genai.Client", return_value=mock_client), \
         patch("os.environ.get", return_value="fake_gemini_key"):
        
        exported_paths = run_batch_module_compression_stateless(
            repo_root=temp_repo_root,
            selected_modules=selected_modules,
            export_dir=export_dir,
            delay=0.0
        )
        
    assert "analysis" in exported_paths
    assert "gui" in exported_paths
    
    # 2. Confirm strict flat-file naming: [FILEPATH-TO-REPO-ROOT-COMPRESSED.md]
    assert os.path.basename(exported_paths["analysis"]) == "src-analysis-compressed.md"
    assert os.path.basename(exported_paths["gui"]) == "src-gui-compressed.md"
    
    # 3. Verify stitched file contents
    analysis_out_path = exported_paths["analysis"]
    with open(analysis_out_path, "r", encoding="utf-8") as f:
        content_analysis = f.read()
        
    # Verify module header
    assert "Module: src/analysis" in content_analysis
    assert "## Module Directory Tree" in content_analysis
    
    # Verify ASCII tree contains correct leaves
    assert "├── context_slicer.py" in content_analysis
    assert "└── graph_builder.py" in content_analysis
    
    # Verify mock AI summary is stitched
    assert "MOCK_ARCHITECTURAL_SUMMARY_TEXT" in content_analysis
    
    # Verify GUI file
    gui_out_path = exported_paths["gui"]
    with open(gui_out_path, "r", encoding="utf-8") as f:
        content_gui = f.read()
        
    assert "Module: src/gui" in content_gui
    assert "└── app.py" in content_gui
    assert "MOCK_ARCHITECTURAL_SUMMARY_TEXT" in content_gui
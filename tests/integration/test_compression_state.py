import os
import json
from unittest.mock import patch
from src.core.controller import run_snapshot, run_export_compression_state

def test_compression_state_lifecycle(temp_repo_root, create_file):
    """
    Validates the end-to-end functionality of the compression-state sync.
    Ensures that empty initial states are handled, modifications queue items,
    and deletions remove items from the master list.
    """
    # Fix for Windows temp directories: resolve 8.3 short paths (FUTURI~1 -> futurist_)
    temp_repo_root = os.path.realpath(temp_repo_root)
    
    output_root = os.path.join(temp_repo_root, "snapshots")
    state_dir = os.path.join(temp_repo_root, "states")
    
    # 1. Setup Base files
    create_file("src/a.py", "print('a')")
    create_file("src/b.py", "print('b')")
    
    # Take initial snapshot (Mocked timestamp to prevent collision during fast test execution)
    with patch("src.core.controller.time.strftime", return_value="snap_1"):
        snap_1 = run_snapshot(
            repo_root=temp_repo_root,
            output_root=output_root,
            depth=10,
            ignore=[],
            include_extensions=[".py"],
            include_readme=False,
            write_current_pointer=True,
            skip_graph=True
        )
    
    # Run sync for the first time (base=empty)
    stats_1 = run_export_compression_state(
        output_root=output_root,
        base_id="empty",
        target_id=snap_1,
        state_dir=state_dir
    )
    
    assert stats_1["pending_compression"] == 2
    
    bool_path = os.path.join(state_dir, "file_changed_bool.json")
    with open(bool_path, "r", encoding="utf-8") as f:
        bool_state = json.load(f)
        
    assert bool_state["file:src/a.py"] == 1
    assert bool_state["file:src/b.py"] == 1
    
    # 2. Simulate LLM updating state
    master_path = os.path.join(state_dir, "master_compressed_context.json")
    master_mock = {
        "file:src/a.py": "COMPRESSED_A",
        "file:src/b.py": "COMPRESSED_B"
    }
    with open(master_path, "w", encoding="utf-8") as f:
        json.dump(master_mock, f)
        
    bool_state["file:src/a.py"] = 0
    bool_state["file:src/b.py"] = 0
    with open(bool_path, "w", encoding="utf-8") as f:
        json.dump(bool_state, f)
        
    # 3. Modify existing, add one, delete one
    create_file("src/a.py", "print('a modified')") # Modified
    create_file("src/c.py", "print('c')")          # Added
    os.remove(os.path.join(temp_repo_root, "src/b.py")) # Removed
    
    # Take target snapshot (Mocked timestamp)
    with patch("src.core.controller.time.strftime", return_value="snap_2"):
        snap_2 = run_snapshot(
            repo_root=temp_repo_root,
            output_root=output_root,
            depth=10,
            ignore=[],
            include_extensions=[".py"],
            include_readme=False,
            write_current_pointer=True,
            skip_graph=True
        )
    
    # Run sync again
    stats_2 = run_export_compression_state(
        output_root=output_root,
        base_id=snap_1,
        target_id=snap_2,
        state_dir=state_dir
    )
    
    # Should be 2 pending (A modified, C added)
    assert stats_2["pending_compression"] == 2
    
    with open(bool_path, "r", encoding="utf-8") as f:
        final_bools = json.load(f)
    with open(master_path, "r", encoding="utf-8") as f:
        final_master = json.load(f)
        
    # Validations
    assert final_bools.get("file:src/a.py") == 1 # Modified, so flipped back to 1
    assert final_bools.get("file:src/c.py") == 1 # Added, so 1
    assert "file:src/b.py" not in final_bools    # Deleted, must be removed to avoid ghost state
    assert "file:src/b.py" not in final_master   # Deleted from master context as well
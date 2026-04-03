# Module Export: gui

- repo_root: `C:/projects/repo-runner`
- snapshot_id: `BATCH_EXPORT`
- file_count: `7`
- tree_only: `False`
## Tree

```
└── src
    └── gui
        ├── __init__.py
        ├── app.py
        └── components
            ├── config_tabs.py
            ├── export_preview.py
            ├── preview_pane.py
            ├── progress_window.py
            └── tree_view.py
```

## File Contents

### `src/gui/__init__.py`

```
# src/gui/__init__.py
```

### `src/gui/app.py`

```
import os
import re
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import ctypes
import datetime
import time
import platform
import subprocess

from src.scanner.filesystem_scanner import FileSystemScanner
from src.normalize.path_normalizer import PathNormalizer
from src.core.controller import run_snapshot
from src.exporters.flatten_markdown_exporter import FlattenMarkdownExporter, FlattenOptions

from src.gui.components.config_tabs import ConfigTabs
from src.gui.components.tree_view import FileTreePanel
from src.gui.components.preview_pane import PreviewPanel
from src.gui.components.export_preview import ExportPreviewWindow
from src.gui.components.progress_window import ProgressWindow

# High DPI
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    pass

class RepoRunnerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("repo-runner Control Panel")
        self.geometry("1300x900")
        
        self.style = ttk.Style(self)
        self.style.theme_use('vista' if 'vista' in self.style.theme_names() else 'clam')
        
        self.repo_root = None
        self.scan_worker = None
        
        self._build_ui()

    def _build_ui(self):
        # Top Bar: Repository Selection
        top_bar = ttk.Frame(self, padding=10)
        top_bar.pack(side=tk.TOP, fill=tk.X)
        
        ttk.Label(top_bar, text="Repository Root:").pack(side=tk.LEFT)
        self.ent_root = ttk.Entry(top_bar)
        self.ent_root.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)
        ttk.Button(top_bar, text="Browse...", command=self._browse).pack(side=tk.LEFT)

        # Main Workspace: Paned Window
        main_paned = ttk.PanedWindow(self, orient=tk.VERTICAL)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Upper: Settings Tabs & Actions
        upper_frame = ttk.Frame(main_paned)
        main_paned.add(upper_frame, weight=0)
        
        self.config_tabs = ConfigTabs(upper_frame)
        self.config_tabs.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Wire the Quick Select Apply button
        self.config_tabs.btn_apply_selection.config(command=self._apply_quick_select)
        
        action_frame = ttk.Frame(upper_frame, padding=10)
        action_frame.pack(side=tk.RIGHT, fill=tk.Y)
        
        ttk.Button(action_frame, text="Scan Repository", command=self._start_scan, width=20).pack(pady=5)
        
        self.btn_snap = ttk.Button(action_frame, text="Snapshot Selection", command=self._snapshot, state=tk.DISABLED, width=20)
        self.btn_snap.pack(pady=5)
        
        self.btn_export = ttk.Button(action_frame, text="Quick Export (Preview)", command=self._quick_export, state=tk.DISABLED, width=20)
        self.btn_export.pack(pady=5)

        self.btn_batch_export = ttk.Button(action_frame, text="Batch Export Modules", command=self._batch_export, state=tk.DISABLED, width=20)
        self.btn_batch_export.pack(pady=5)

        # Lower: Tree and Preview
        lower_paned = ttk.PanedWindow(main_paned, orient=tk.HORIZONTAL)
        main_paned.add(lower_paned, weight=1)
        
        self.tree_panel = FileTreePanel(lower_paned, self._on_file_selected)
        lower_paned.add(self.tree_panel, weight=1)
        
        self.preview_panel = PreviewPanel(lower_paned)
        lower_paned.add(self.preview_panel, weight=2)

        # Status
        self.status_var = tk.StringVar(value="Ready")
        ttk.Label(self, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W).pack(side=tk.BOTTOM, fill=tk.X)

    def _browse(self):
        path = filedialog.askdirectory()
        if path:
            self.ent_root.delete(0, tk.END)
            self.ent_root.insert(0, path)
            self.repo_root = path

    def _start_scan(self):
        root = self.ent_root.get().strip()
        if not os.path.isdir(root):
            messagebox.showerror("Error", "Invalid Repository Path")
            return
        
        self.repo_root = root
        self.tree_panel.clear()
        self.preview_panel.clear()
        
        # Disable dependent buttons during scan
        self.config_tabs.btn_apply_selection.config(state=tk.DISABLED)
        self.btn_snap.config(state=tk.DISABLED)
        self.btn_export.config(state=tk.DISABLED)
        self.btn_batch_export.config(state=tk.DISABLED)
        
        # Get settings safely on Main Thread
        depth = self.config_tabs.depth_var.get()
        ignore = set(self.config_tabs.ignore_var.get().split())
        exts = self.config_tabs.ext_var.get().split()
        readme = self.config_tabs.include_readme_var.get()
        
        # Launch Progress Window
        self.progress_win = ProgressWindow(self, title="Scanning", message=f"Scanning {root}...")
        
        # Start Worker Thread
        self.scan_worker = threading.Thread(
            target=self._scan_thread,
            args=(root, depth, ignore, exts, readme),
            daemon=True
        )
        self.scan_worker.start()

    def _scan_thread(self, root, depth, ignore, exts, readme):
        try:
            scanner = FileSystemScanner(depth=depth, ignore_names=ignore)
            
            # Define callback for the scanner
            def on_progress(count):
                if self.progress_win.cancelled:
                    return False # Stop scanning
                
                # Update UI thread
                self.after(0, lambda: self.progress_win.update_message(f"Found {count} files..."))
                return True

            abs_files = scanner.scan([root], progress_callback=on_progress)
            
            if self.progress_win.cancelled:
                self.after(0, self._scan_cancelled)
                return

            self.after(0, lambda: self.progress_win.update_message("Filtering and Normalizing..."))
            
            # Filter
            filtered = []
            ext_set = set(e.lower() for e in exts)
            for f in abs_files:
                _, ext = os.path.splitext(f)
                is_readme = readme and os.path.basename(f).lower().startswith("readme")
                if not ext_set or ext.lower() in ext_set or is_readme:
                    filtered.append(f)
            
            # Normalize for tree
            normalizer = PathNormalizer(root)
            struct = {}
            for f in filtered:
                rel = normalizer.normalize(f)
                parts = rel.split('/')
                
                # Build nested dict
                curr = struct
                for i, p in enumerate(parts):
                    is_last = (i == len(parts) - 1)
                    if is_last:
                        if p not in curr:
                            curr[p] = {}
                        curr[p]['__metadata__'] = {'abs_path': f, 'stable_id': normalizer.file_id(rel)}
                    else:
                        curr = curr.setdefault(p, {})
            
            # Success
            self.after(0, lambda: self._scan_done(struct, len(filtered)))
            
        except Exception as e:
            self.after(0, lambda: self._scan_fail(str(e)))

    def _scan_done(self, struct, count):
        self.progress_win.close()
        self.tree_panel.populate(struct)
        self.status_var.set(f"Scan Complete. Found {count} files.")
        
        # Re-enable buttons
        self.config_tabs.btn_apply_selection.config(state=tk.NORMAL)
        self.btn_snap.config(state=tk.NORMAL)
        self.btn_export.config(state=tk.NORMAL)
        self.btn_batch_export.config(state=tk.NORMAL)

    def _scan_cancelled(self):
        self.progress_win.close()
        self.status_var.set("Scan Cancelled.")

    def _scan_fail(self, error):
        self.progress_win.close()
        messagebox.showerror("Scan Error", error)
        self.status_var.set("Scan Failed.")

    def _apply_quick_select(self):
        if not self.repo_root:
            return
            
        raw_text = self.config_tabs.txt_quick_select.get("1.0", tk.END).strip()
        
        if not raw_text:
            self.tree_panel.check_specific_files(set())
            self.status_var.set("Quick Select cleared.")
            return
            
        # Parse by comma or newline
        raw_paths = [p.strip() for p in re.split(r'[,\n]+', raw_text) if p.strip()]
        target_ids = set()
        
        repo_root_norm = self.repo_root.replace('\\', '/').lower().rstrip('/')
        
        for p in raw_paths:
            p = p.replace('\\', '/')
            if p.startswith("file:"):
                target_ids.add(p.lower())
                continue
            p_lower = p.lower()
            if p_lower.startswith(repo_root_norm):
                p = p[len(repo_root_norm):]
            while p.startswith('/') or p.startswith('./'):
                if p.startswith('/'):
                    p = p[1:]
                elif p.startswith('./'):
                    p = p[2:]
            if p:
                target_ids.add(f"file:{p.lower()}")
                
        matched_count = self.tree_panel.check_specific_files(target_ids)
        self.status_var.set(f"Quick Select applied. Mapped {len(target_ids)} inputs to {matched_count} tree items.")

    def _on_file_selected(self, abs_path, stable_id):
        self.preview_panel.load_file(abs_path, stable_id)

    def _snapshot(self):
        files = self.tree_panel.get_checked_files()
        if not files:
            messagebox.showwarning("Empty", "No files selected.")
            return
            
        out = filedialog.askdirectory(title="Select Snapshot Output Root")
        if not out: return
        
        self.btn_snap.config(state=tk.DISABLED)
        self.progress_win = ProgressWindow(self, title="Snapshotting", message="Calculating Hashes and Analyzing Imports...")
        
        def run():
            try:
                sid = run_snapshot(
                    repo_root=self.repo_root,
                    output_root=out,
                    depth=self.config_tabs.depth_var.get(),
                    ignore=self.config_tabs.ignore_var.get().split(),
                    include_extensions=[],
                    include_readme=False,
                    write_current_pointer=self.config_tabs.write_current_var.get(),
                    explicit_file_list=files
                )
                self.after(0, lambda: self._snapshot_done(sid))
            except Exception as e:
                self.after(0, lambda: self._snapshot_fail(str(e)))

        threading.Thread(target=run, daemon=True).start()

    def _snapshot_done(self, sid):
        self.progress_win.close()
        self.btn_snap.config(state=tk.NORMAL)
        self.status_var.set(f"Snapshot Created: {sid}")
        messagebox.showinfo("Success", f"Snapshot Created: {sid}")

    def _snapshot_fail(self, error):
        self.progress_win.close()
        self.btn_snap.config(state=tk.NORMAL)
        self.status_var.set("Snapshot Failed.")
        messagebox.showerror("Error", error)

    def _quick_export(self):
        files = self.tree_panel.get_checked_files()
        if not files:
            messagebox.showwarning("Empty", "No files selected.")
            return

        tree_only = self.config_tabs.export_tree_only_var.get()
        self.status_var.set("Generating Export Preview...")
        self.btn_export.config(state=tk.DISABLED)
        
        def run_export():
            try:
                normalizer = PathNormalizer(self.repo_root)
                manifest_files = []
                for abs_p in files:
                    rel = normalizer.normalize(abs_p)
                    manifest_files.append({"path": rel, "size_bytes": 0, "sha256": "pre-snapshot"})
                    
                dummy_manifest = {"files": manifest_files}
                options = FlattenOptions(tree_only=tree_only, include_readme=True, scope="full")
                exporter = FlattenMarkdownExporter()
                
                content = exporter.generate_content(
                    repo_root=self.repo_root,
                    manifest=dummy_manifest,
                    options=options,
                    title=f"Quick Export: {os.path.basename(self.repo_root)}",
                    snapshot_id="QUICK_EXPORT_PREVIEW"
                )
                
                self.after(0, lambda: self._quick_export_done(content))
            except Exception as e:
                self.after(0, lambda: self._quick_export_fail(str(e)))

        threading.Thread(target=run_export, daemon=True).start()

    def _quick_export_done(self, content):
        self.btn_export.config(state=tk.NORMAL)
        self.status_var.set("Export Preview Ready.")
        default_name = f"flattened_{os.path.basename(self.repo_root)}_{datetime.date.today()}.md"
        ExportPreviewWindow(self, content, default_name)

    def _quick_export_fail(self, error):
        self.btn_export.config(state=tk.NORMAL)
        self.status_var.set("Export Failed.")
        messagebox.showerror("Export Error", error)

    def _batch_export(self):
        modules = self.tree_panel.get_modules()
        if not modules:
            messagebox.showinfo("No Modules Found", "Please click a folder checkbox in the tree to lock it as a Module Root.")
            return

        # Automatic path generation
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        folder_name = f"{timestamp}_CONTEXT"
        out_dir = os.path.join(self.repo_root, ".context", "compressed-context", folder_name)

        # Create directories safely
        os.makedirs(out_dir, exist_ok=True)
        
        self.status_var.set(f"Batch Exporting {len(modules)} modules...")
        self.btn_batch_export.config(state=tk.DISABLED)
        tree_only = self.config_tabs.export_tree_only_var.get()

        def run_batch():
            try:
                normalizer = PathNormalizer(self.repo_root)
                exporter = FlattenMarkdownExporter()

                for mod_name, abs_files in modules.items():
                    manifest_files = []
                    for abs_p in abs_files:
                        rel = normalizer.normalize(abs_p)
                        manifest_files.append({"path": rel, "size_bytes": 0, "sha256": "pre-snapshot"})

                    dummy_manifest = {"files": manifest_files}
                    options = FlattenOptions(tree_only=tree_only, include_readme=True, scope="full")

                    content = exporter.generate_content(
                        repo_root=self.repo_root,
                        manifest=dummy_manifest,
                        options=options,
                        title=f"Module Export: {mod_name}",
                        snapshot_id="BATCH_EXPORT"
                    )

                    safe_name = re.sub(r'[\\/*?:"<>|]', "", mod_name)
                    out_path = os.path.join(out_dir, f"{safe_name}-context.md")
                    
                    with open(out_path, "w", encoding="utf-8") as f:
                        f.write(content)

                self.after(0, lambda: self._batch_export_done(out_dir, len(modules)))
            except Exception as e:
                self.after(0, lambda: self._batch_export_fail(str(e)))

        threading.Thread(target=run_batch, daemon=True).start()

    def _batch_export_done(self, out_dir, count):
        self.btn_batch_export.config(state=tk.NORMAL)
        self.status_var.set(f"Batch Export Complete. Saved {count} modules to {out_dir}")
        messagebox.showinfo("Success", f"Exported {count} module files to:\n{out_dir}")
        try:
            # Automatically open the new timestamped context folder
            if platform.system() == "Windows":
                os.startfile(out_dir)
            elif platform.system() == "Darwin":
                subprocess.call(["open", out_dir])
            else:
                subprocess.call(["xdg-open", out_dir])
        except:
            pass

    def _batch_export_fail(self, error):
        self.btn_batch_export.config(state=tk.NORMAL)
        self.status_var.set("Batch Export Failed.")
        messagebox.showerror("Batch Export Error", error)

def run_gui():
    RepoRunnerApp().mainloop()
```

### `src/gui/components/config_tabs.py`

```
import tkinter as tk
from tkinter import ttk

class ConfigTabs(ttk.Notebook):
    def __init__(self, parent):
        super().__init__(parent)
        
        # Variables
        self.depth_var = tk.IntVar(value=25)
        self.ignore_var = tk.StringVar(value=".git node_modules __pycache__ dist build .next .expo .venv")
        self.ext_var = tk.StringVar(value="")
        self.include_readme_var = tk.BooleanVar(value=True)
        self.write_current_var = tk.BooleanVar(value=True)
        
        # New: Export options
        self.export_tree_only_var = tk.BooleanVar(value=False)
        
        self._build_scan_tab()
        self._build_ignore_tab()
        self._build_output_tab()

    def _build_scan_tab(self):
        tab = ttk.Frame(self, padding=10)
        self.add(tab, text=" Scan Settings ")
        
        # Depth
        row1 = ttk.Frame(tab)
        row1.pack(fill=tk.X, pady=5)
        ttk.Label(row1, text="Maximum Traversal Depth:", width=25).pack(side=tk.LEFT)
        ttk.Spinbox(row1, from_=0, to=100, textvariable=self.depth_var, width=10).pack(side=tk.LEFT)
        
        # Extensions
        row2 = ttk.Frame(tab)
        row2.pack(fill=tk.X, pady=5)
        ttk.Label(row2, text="Include Extensions:", width=25).pack(side=tk.LEFT)
        ttk.Entry(row2, textvariable=self.ext_var).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Label(row2, text="(space separated, e.g. .ts .py)", font=("Segoe UI", 8), foreground="gray").pack(side=tk.LEFT, padx=5)

        # Readme
        row3 = ttk.Frame(tab)
        row3.pack(fill=tk.X, pady=5)
        ttk.Checkbutton(row3, text="Always include README files (overrides extension filter)", variable=self.include_readme_var).pack(side=tk.LEFT)

        # Quick Select
        row4 = ttk.Frame(tab)
        row4.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        
        lbl_frame = ttk.Frame(row4)
        lbl_frame.pack(fill=tk.X)
        ttk.Label(lbl_frame, text="Quick Select (Comma or newline separated paths):").pack(side=tk.LEFT)
        
        # Stored reference to wire in app.py
        self.btn_apply_selection = ttk.Button(lbl_frame, text="Apply Selection", state=tk.DISABLED)
        self.btn_apply_selection.pack(side=tk.RIGHT)
        
        self.txt_quick_select = tk.Text(row4, height=4, font=("Segoe UI", 9))
        self.txt_quick_select.pack(fill=tk.BOTH, expand=True, pady=(2, 0))

    def _build_ignore_tab(self):
        tab = ttk.Frame(self, padding=10)
        self.add(tab, text=" Ignore Rules ")
        
        ttk.Label(tab, text="Directory and File names to ignore:").pack(anchor=tk.W, pady=(0, 5))
        txt_ignore = tk.Text(tab, height=4, font=("Segoe UI", 9))
        txt_ignore.pack(fill=tk.BOTH, expand=True)
        
        # Sync the text box with the variable
        txt_ignore.insert("1.0", self.ignore_var.get())
        def sync_var(event=None):
            self.ignore_var.set(txt_ignore.get("1.0", tk.END).strip())
        txt_ignore.bind("<KeyRelease>", sync_var)

    def _build_output_tab(self):
        tab = ttk.Frame(self, padding=10)
        self.add(tab, text=" Output / Export ")
        
        # Snapshot Config
        lbl_snap = ttk.Label(tab, text="Snapshot Config", font=("Segoe UI", 9, "bold"))
        lbl_snap.pack(anchor=tk.W, pady=(0, 5))
        
        ttk.Checkbutton(tab, text="Update 'current.json' pointer on snapshot", variable=self.write_current_var).pack(anchor=tk.W, pady=2)
        
        ttk.Separator(tab, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=15)
        
        # Export Config
        lbl_exp = ttk.Label(tab, text="Quick Export Config", font=("Segoe UI", 9, "bold"))
        lbl_exp.pack(anchor=tk.W, pady=(0, 5))
        
        ttk.Checkbutton(tab, text="Tree Only (No file contents)", variable=self.export_tree_only_var).pack(anchor=tk.W, pady=2)

        ttk.Label(tab, text="Note: Snapshots are always created in a timestamped subfolder.", 
                  font=("Segoe UI", 8, "italic"), foreground="gray").pack(side=tk.BOTTOM, anchor=tk.W, pady=10)
```

### `src/gui/components/export_preview.py`

```
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

class ExportPreviewWindow(tk.Toplevel):
    def __init__(self, parent, content, default_filename="export.md"):
        super().__init__(parent)
        self.title("Export Preview & Token Estimator")
        self.geometry("1100x800")
        
        self.content = content
        self.default_filename = default_filename
        
        self._build_ui()
        
        # Behavior: Focus on this window
        self.focus_force()

    def _build_ui(self):
        # Toolbar
        toolbar = ttk.Frame(self, padding=5)
        toolbar.pack(side=tk.TOP, fill=tk.X)
        
        # Actions
        btn_frame = ttk.Frame(toolbar)
        btn_frame.pack(side=tk.LEFT)
        ttk.Button(btn_frame, text="💾 Save to File...", command=self._save).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="📋 Copy to Clipboard", command=self._copy).pack(side=tk.LEFT, padx=2)
        
        # Stats Calculation
        lines = self.content.count('\n') + 1
        chars = len(self.content)
        est_tokens = chars // 4
        
        # Context Health Logic
        if est_tokens < 8192:
            status_color = "#008000" # Green
            model_hint = "Fits: GPT-4 (8k)"
        elif est_tokens < 32768:
            status_color = "#228B22" # Forest Green
            model_hint = "Fits: GPT-4 (32k)"
        elif est_tokens < 128000:
            status_color = "#B8860B" # Dark Goldenrod
            model_hint = "Fits: GPT-4 Turbo / Claude 3 (128k)"
        elif est_tokens < 200000:
            status_color = "#FF8C00" # Dark Orange
            model_hint = "Fits: Claude 3.5 Sonnet (200k)"
        elif est_tokens < 1000000:
            status_color = "#FF4500" # Orange Red
            model_hint = "Fits: Gemini 1.5 Pro (1M)"
        else:
            status_color = "#FF0000" # Red
            model_hint = "⚠ EXCEEDS 1M TOKENS (Chunking Required)"

        # Stats Display
        stats_frame = ttk.Frame(toolbar)
        stats_frame.pack(side=tk.RIGHT, padx=10)

        # Basic Stats
        lbl_basic = ttk.Label(
            stats_frame, 
            text=f"Lines: {lines:,}  |  Chars: {chars:,}  |  ", 
            font=("Segoe UI", 9)
        )
        lbl_basic.pack(side=tk.LEFT)

        # Token Stats (Bold + Color)
        lbl_tokens = tk.Label(
            stats_frame, 
            text=f"~{est_tokens:,} Tokens", 
            font=("Segoe UI", 9, "bold"),
            fg=status_color
        )
        lbl_tokens.pack(side=tk.LEFT)
        
        # Model Hint
        lbl_hint = tk.Label(
            stats_frame,
            text=f"  [{model_hint}]",
            font=("Segoe UI", 8, "italic"),
            fg="gray"
        )
        lbl_hint.pack(side=tk.LEFT)

        # Separator
        ttk.Separator(self, orient=tk.HORIZONTAL).pack(fill=tk.X)

        # Content Area
        container = ttk.Frame(self)
        container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.text_area = tk.Text(container, wrap=tk.NONE, font=("Consolas", 10), undo=False)
        self.text_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        ysb = ttk.Scrollbar(container, orient=tk.VERTICAL, command=self.text_area.yview)
        ysb.pack(side=tk.RIGHT, fill=tk.Y)
        
        xsb = ttk.Scrollbar(self, orient=tk.HORIZONTAL, command=self.text_area.xview)
        xsb.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.text_area.configure(yscrollcommand=ysb.set, xscrollcommand=xsb.set)
        
        # Insert content (read-only state after insert)
        # Note: For massive files (100MB+), inserting into Tkinter Text widget is slow.
        # We truncate the preview visually if it's absurdly large, but keep the full content for saving/copying.
        
        PREVIEW_LIMIT = 5_000_000 # 5MB Preview Limit
        
        if chars > PREVIEW_LIMIT:
            preview_text = self.content[:PREVIEW_LIMIT] + f"\n\n... [Preview Truncated due to size ({chars:,} chars). Full content preserved for Save/Copy] ..."
            self.text_area.insert("1.0", preview_text)
            
            # Add a warning banner
            lbl_warn = ttk.Label(self, text=f"⚠ Preview truncated for performance. Full output ({chars:,} chars) is ready to save.", background="#fff3cd", anchor=tk.CENTER)
            lbl_warn.pack(side=tk.TOP, fill=tk.X, before=container)
        else:
            self.text_area.insert("1.0", self.content)
            
        self.text_area.configure(state=tk.DISABLED)

    def _save(self):
        out_path = filedialog.asksaveasfilename(
            defaultextension=".md",
            filetypes=[("Markdown", "*.md"), ("All Files", "*.*")],
            initialfile=self.default_filename,
            title="Save Export"
        )
        if out_path:
            try:
                # We write self.content (the full string), not the truncated preview
                with open(out_path, "w", encoding="utf-8") as f:
                    f.write(self.content)
                messagebox.showinfo("Saved", f"Successfully saved to:\n{out_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save file:\n{e}")

    def _copy(self):
        self.clipboard_clear()
        self.clipboard_append(self.content)
        messagebox.showinfo("Copied", "Content copied to clipboard!")
```

### `src/gui/components/preview_pane.py`

```
import tkinter as tk
from tkinter import ttk
from src.fingerprint.file_fingerprint import FileFingerprint
from src.analysis.import_scanner import ImportScanner

class PreviewPanel(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        
        # Metadata Header (Brief)
        self.lbl_meta = ttk.Label(self, text="Select a file to preview properties.", 
                                  background="#f0f0f0", padding=5, relief=tk.RIDGE)
        self.lbl_meta.pack(fill=tk.X, side=tk.TOP)
        
        # Text Area
        container = ttk.Frame(self)
        container.pack(fill=tk.BOTH, expand=True)
        
        self.text_preview = tk.Text(container, wrap=tk.NONE, font=("Consolas", 10), undo=False)
        self.text_preview.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(container, orient=tk.VERTICAL, command=self.text_preview.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.text_preview.configure(yscrollcommand=scrollbar.set)
        
        # --- Syntax Highlighting Tags ---
        # A very basic "poor man's highlighter"
        self.text_preview.tag_configure("keyword", foreground="#0000FF") # Blue
        self.text_preview.tag_configure("string", foreground="#A31515")  # Red
        self.text_preview.tag_configure("comment", foreground="#008000") # Green
        self.text_preview.tag_configure("header", foreground="#800080", font=("Consolas", 10, "bold")) # Purple

    def clear(self):
        self.text_preview.delete("1.0", tk.END)
        self.lbl_meta.config(text="Select a file to preview properties.")

    def load_file(self, abs_path, stable_id):
        self.clear()
        try:
            # 1. Fingerprint (Size, SHA, Lang)
            fp = FileFingerprint.fingerprint(abs_path)
            
            # 2. Scan Imports (Lazy load on click using detected language)
            scan_res = ImportScanner.scan(abs_path, fp['language'])
            
            # Extract the actual lists from the dictionary
            actual_imports = scan_res.get('imports', [])
            actual_symbols = scan_res.get('symbols', [])
            
            # 3. Update Brief Header Label
            import_count = len(actual_imports)
            symbol_count = len(actual_symbols)
            self.lbl_meta.config(text=f" ID: {stable_id}  |  {fp['language']}  |  {import_count} Imports  |  {symbol_count} Symbols")

            # 4. Construct Detailed Metadata Header
            header_lines = [
                f"Path:    {abs_path}",
                f"SHA256:  {fp['sha256']}",
                f"Size:    {fp['size_bytes']:,} bytes",
                "-" * 60,
                "IMPORTS FOUND:",
            ]
            
            if actual_imports:
                for imp in actual_imports:
                    header_lines.append(f"  • {imp}")
            else:
                header_lines.append("  (none)")
                
            header_lines.append("")
            header_lines.append("SYMBOLS DEFINED:")
            
            if actual_symbols:
                for sym in actual_symbols:
                    header_lines.append(f"  ♦ {sym}")
            else:
                header_lines.append("  (none)")
                
            header_lines.append("-" * 60)
            header_lines.append("") # Spacer line
            
            full_header = "\n".join(header_lines)
            
            # 5. Insert Header
            self.text_preview.insert("1.0", full_header, "header")

            # 6. Append Real File Content
            if fp['size_bytes'] > 250_000:
                self.text_preview.insert(tk.END, "\n<< File too large for preview >>")
            else:
                try:
                    with open(abs_path, 'r', encoding='utf-8', errors='replace') as f:
                        content = f.read()
                        self.text_preview.insert(tk.END, content)
                        # Apply minimal highlighting after insert
                        self._highlight_syntax(content)
                except Exception as e:
                    self.text_preview.insert(tk.END, f"\n<< Error reading file: {e} >>")
                    
        except Exception as e:
            self.text_preview.insert("1.0", f"<< Error processing file: {e} >>")

    def _highlight_syntax(self, content):
        """Very basic highlighting for common keywords. 
           This is not a full lexer, just a visual aid."""
        keywords = {
            "def", "class", "import", "from", "return", "if", "else", "elif", 
            "for", "while", "try", "except", "with", "as", "pass", "lambda",
            "const", "let", "var", "function", "export", "interface", "type"
        }
        
        # We start searching after the header (heuristic: header is ~15 lines)
        start_index = "15.0" 
        
        for kw in keywords:
            # Search for whole words only
            idx = start_index
            while True:
                # search pattern, stop index, nocase, count, regexp...
                # using a regex to ensure word boundaries would be better, but simpler approach first:
                # We'll just search for the string. To do word boundaries in Tkinter search requires strict mode.
                idx = self.text_preview.search(kw, idx, stopindex=tk.END)
                if not idx:
                    break
                
                # Check length to calculate end index
                end_idx = f"{idx}+{len(kw)}c"
                
                # Apply tag
                self.text_preview.tag_add("keyword", idx, end_idx)
                
                # Move to next
                idx = end_idx
```

### `src/gui/components/progress_window.py`

```
import tkinter as tk
from tkinter import ttk

class ProgressWindow(tk.Toplevel):
    def __init__(self, parent, title="Processing...", message="Please wait"):
        super().__init__(parent)
        self.title(title)
        self.geometry("400x150")
        self.resizable(False, False)
        
        # Modal behavior
        self.transient(parent)
        self.grab_set()
        
        self.cancelled = False
        
        # Center the window
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (self.winfo_width() // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (self.winfo_height() // 2)
        self.geometry(f"+{x}+{y}")
        
        self._build_ui(message)
        
    def _build_ui(self, message):
        frame = ttk.Frame(self, padding=20)
        frame.pack(fill=tk.BOTH, expand=True)
        
        self.lbl_msg = ttk.Label(frame, text=message, wraplength=360)
        self.lbl_msg.pack(pady=(0, 15), anchor=tk.W)
        
        self.progress = ttk.Progressbar(frame, mode='indeterminate')
        self.progress.pack(fill=tk.X, pady=(0, 15))
        self.progress.start(15)
        
        self.btn_cancel = ttk.Button(frame, text="Cancel", command=self.cancel)
        self.btn_cancel.pack(anchor=tk.E)
        
    def update_message(self, text):
        self.lbl_msg.config(text=text)
        
    def update_progress(self, current: int, total: int = 0):
        """
        Dynamically shifts from indeterminate to determinate if total is known.
        """
        if total > 0:
            if self.progress.cget('mode') == 'indeterminate':
                self.progress.stop()
                self.progress.config(mode='determinate', maximum=total)
            self.progress['value'] = current
        else:
            if self.progress.cget('mode') == 'determinate':
                self.progress.config(mode='indeterminate')
                self.progress.start(15)
        
    def cancel(self):
        self.cancelled = True
        self.lbl_msg.config(text="Cancelling... please wait.")
        self.btn_cancel.state(['disabled'])

    def close(self):
        self.grab_release()
        self.destroy()
```

### `src/gui/components/tree_view.py`

```
import os
import tkinter as tk
from tkinter import ttk

class FileTreePanel(ttk.Frame):
    def __init__(self, parent, on_select_callback):
        super().__init__(parent)
        self.on_select_callback = on_select_callback
        
        tools = ttk.Frame(self)
        tools.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Button(tools, text="☑ Check All", command=lambda: self._bulk_toggle(True), width=12).pack(side=tk.LEFT)
        ttk.Button(tools, text="☐ Uncheck All", command=lambda: self._bulk_toggle(False), width=12).pack(side=tk.LEFT, padx=5)
        
        container = ttk.Frame(self)
        container.pack(fill=tk.BOTH, expand=True)
        
        self.tree = ttk.Treeview(container, columns=("check", "size", "id"), selectmode="browse")
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(container, orient=tk.VERTICAL, command=self.tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.column("#0", width=300, minwidth=200)
        self.tree.heading("#0", text="File / Folder Name", anchor=tk.W)
        
        self.tree.column("check", width=40, minwidth=40, stretch=False, anchor=tk.CENTER)
        self.tree.heading("check", text="Inc.")
        
        self.tree.column("size", width=80, anchor=tk.E)
        self.tree.heading("size", text="Size")
        
        self.tree.column("id", width=150)
        self.tree.heading("id", text="Stable ID")
        
        # UI Tags for locked modules
        self.tree.tag_configure("locked", foreground="#999999")
        self.tree.tag_configure("module_root", font=("Segoe UI", 9, "bold"), foreground="#0055AA")
        
        self.tree.bind("<Button-1>", self._on_click)
        self.tree.bind("<<TreeviewSelect>>", self._on_selection_change)

    def clear(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

    def _on_click(self, event):
        region = self.tree.identify_region(event.x, event.y)
        if region == "cell":
            column = self.tree.identify_column(event.x)
            item_id = self.tree.identify_row(event.y)
            
            if column == "#1" and item_id:
                tags = self.tree.item(item_id, "tags")
                if "locked" in tags:
                    # Ignore clicks on locked children
                    return "break"
                
                self._toggle_item(item_id)
                return "break"
        return

    def _set_node_state(self, item_id, check_state, add_tags=None, remove_tags=None):
        vals = list(self.tree.item(item_id, "values"))
        vals[0] = check_state
        self.tree.item(item_id, values=vals)

        tags = list(self.tree.item(item_id, "tags"))
        changed = False
        if add_tags:
            for t in add_tags:
                if t not in tags:
                    tags.append(t)
                    changed = True
        if remove_tags:
            for t in remove_tags:
                if t in tags:
                    tags.remove(t)
                    changed = True
        if changed:
            self.tree.item(item_id, tags=tags)

    def _lock_children(self, parent_id, lock: bool):
        for child in self.tree.get_children(parent_id):
            tags = list(self.tree.item(child, "tags"))
            state = "☑" if lock else "☐"

            # Always strip module_root if a parent asserts a lock over this node
            if "module_root" in tags:
                tags.remove("module_root")

            if lock:
                if "locked" not in tags:
                    tags.append("locked")
            else:
                if "locked" in tags:
                    tags.remove("locked")

            self.tree.item(child, tags=tags)
            vals = list(self.tree.item(child, "values"))
            vals[0] = state
            self.tree.item(child, values=vals)

            self._lock_children(child, lock)

    def _toggle_item(self, item_id):
        current_vals = list(self.tree.item(item_id, "values"))
        current_check = current_vals[0]
        new_state = "☐" if current_check == "☑" else "☑"
        
        tags = list(self.tree.item(item_id, "tags"))
        if "folder" in tags:
            if new_state == "☑":
                self._set_node_state(item_id, "☑", add_tags=["module_root"])
                self._lock_children(item_id, True)
            else:
                self._set_node_state(item_id, "☐", remove_tags=["module_root"])
                self._lock_children(item_id, False)
        else:
            self._set_node_state(item_id, new_state)

    def _bulk_toggle(self, checked: bool):
        """Standard check/uncheck that clears all locks."""
        state = "☑" if checked else "☐"
        def recurse(item_id):
            self._set_node_state(item_id, state, remove_tags=["locked", "module_root"])
            for child in self.tree.get_children(item_id):
                recurse(child)
                
        for child in self.tree.get_children(""):
            recurse(child)

    def check_specific_files(self, target_stable_ids: set) -> int:
        self._bulk_toggle(False)
        matched = [0]
        
        def traverse_and_check(item_id) -> bool:
            vals = list(self.tree.item(item_id, "values"))
            tags = self.tree.item(item_id, "tags")
            is_file = tags and tags[0] != "folder"
            
            has_checked_child = False
            
            if is_file:
                stable_id = vals[2]
                if stable_id in target_stable_ids:
                    vals[0] = "☑"
                    self.tree.item(item_id, values=vals)
                    matched[0] += 1
                    return True
            else:
                for child in self.tree.get_children(item_id):
                    if traverse_and_check(child):
                        has_checked_child = True
                        
                if has_checked_child:
                    self.tree.item(item_id, open=True)
                    
            return has_checked_child

        for child in self.tree.get_children():
            traverse_and_check(child)
            
        return matched[0]

    def _on_selection_change(self, event):
        selected = self.tree.selection()
        if selected:
            tags = self.tree.item(selected[0], "tags")
            if tags and tags[0] != "folder":
                stable_id = self.tree.item(selected[0], "values")[2]
                self.on_select_callback(tags[0], stable_id)

    def populate(self, tree_structure):
        self.clear()
        
        def insert_node(parent_id, structure):
            keys = sorted(structure.keys())
            folders = [k for k in keys if k != '__metadata__' and '__metadata__' not in structure[k]]
            files = [k for k in keys if k != '__metadata__' and '__metadata__' in structure[k]]
            
            for name in folders + files:
                node_data = structure[name]
                is_file = '__metadata__' in node_data
                
                values = ["☑", "", ""]
                
                if is_file:
                    meta = node_data['__metadata__']
                    try:
                        size = os.path.getsize(meta['abs_path'])
                        values = ["☑", f"{size:,} B", meta['stable_id']]
                    except OSError:
                        values = ["☑", "Err", meta['stable_id']]
                    icon = "📄 "
                else:
                    icon = "📁 "

                item_id = self.tree.insert(parent_id, "end", text=f"{icon}{name}", values=values, open=False)
                
                if is_file:
                    self.tree.item(item_id, tags=(node_data['__metadata__']['abs_path'], "file"))
                else:
                    self.tree.item(item_id, tags=("folder",))
                    insert_node(item_id, node_data)

        insert_node("", tree_structure)

    def get_checked_files(self, parent_id="") -> list:
        paths = []
        for item_id in self.tree.get_children(parent_id):
            vals = self.tree.item(item_id, "values")
            if vals[0] == "☑":
                tags = self.tree.item(item_id, "tags")
                if tags and tags[0] != "folder":
                    paths.append(tags[0])
            paths.extend(self.get_checked_files(item_id))
        return paths

    def get_modules(self) -> dict:
        """
        Returns a dictionary of { "module_name": [list_of_abs_paths] }
        for all nodes explicitly tagged as module_root.
        """
        modules = {}
        def traverse(item_id):
            tags = self.tree.item(item_id, "tags")
            if "module_root" in tags:
                raw_text = self.tree.item(item_id, "text")
                name = raw_text.replace("📁 ", "").strip()
                paths = self.get_checked_files(item_id)
                modules[name] = paths
            else:
                for child in self.tree.get_children(item_id):
                    traverse(child)

        for child in self.tree.get_children(""):
            traverse(child)

        return modules
```

---
## Context Stats
- **Total Characters:** 43,722
- **Estimated Tokens:** ~10,930 (assuming ~4 chars/token)
- **Model Fit:** GPT-4 (32k)

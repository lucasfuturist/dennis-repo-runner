import os
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import ctypes
import datetime
import time

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
        
        action_frame = ttk.Frame(upper_frame, padding=10)
        action_frame.pack(side=tk.RIGHT, fill=tk.Y)
        
        ttk.Button(action_frame, text="Scan Repository", command=self._start_scan, width=20).pack(pady=5)
        
        self.btn_snap = ttk.Button(action_frame, text="Snapshot Selection", command=self._snapshot, state=tk.DISABLED, width=20)
        self.btn_snap.pack(pady=5)
        
        self.btn_export = ttk.Button(action_frame, text="Quick Export (Preview)", command=self._quick_export, state=tk.DISABLED, width=20)
        self.btn_export.pack(pady=5)

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
                    # Check if p is a file (last part) or dir
                    is_last = (i == len(parts) - 1)
                    
                    if is_last:
                        # File leaf
                        # We might need to handle the case where a directory was previously created 
                        # with the same name (unlikely in valid FS, but possible in logic).
                        # For now, simplistic approach:
                        if p not in curr:
                            curr[p] = {}
                        curr[p]['__metadata__'] = {'abs_path': f, 'stable_id': normalizer.file_id(rel)}
                    else:
                        # Directory node
                        curr = curr.setdefault(p, {})
            
            # Success
            self.after(0, lambda: self._scan_done(struct, len(filtered)))
            
        except Exception as e:
            self.after(0, lambda: self._scan_fail(str(e)))

    def _scan_done(self, struct, count):
        self.progress_win.close()
        self.tree_panel.populate(struct)
        self.status_var.set(f"Scan Complete. Found {count} files.")
        self.btn_snap.config(state=tk.NORMAL)
        self.btn_export.config(state=tk.NORMAL)

    def _scan_cancelled(self):
        self.progress_win.close()
        self.status_var.set("Scan Cancelled.")

    def _scan_fail(self, error):
        self.progress_win.close()
        messagebox.showerror("Scan Error", error)
        self.status_var.set("Scan Failed.")

    def _on_file_selected(self, abs_path, stable_id):
        self.preview_panel.load_file(abs_path, stable_id)

    def _snapshot(self):
        files = self.tree_panel.get_checked_files()
        if not files:
            messagebox.showwarning("Empty", "No files selected.")
            return
            
        out = filedialog.askdirectory(title="Select Snapshot Output Root")
        if not out: return
        
        # UI Locking
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
                    manifest_files.append({
                        "path": rel,
                        "size_bytes": 0,
                        "sha256": "pre-snapshot"
                    })
                    
                dummy_manifest = {"files": manifest_files}
                
                options = FlattenOptions(
                    tree_only=tree_only,
                    include_readme=True, 
                    scope="full"
                )
                
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

def run_gui():
    RepoRunnerApp().mainloop()
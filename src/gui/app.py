import os
import re
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import ctypes
import datetime
import platform
import subprocess
import sys
import json

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
        self._load_default_ignores()

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
        
        self.btn_compress = ttk.Button(action_frame, text="Compress Context (LLM)", command=self._compress_context, state=tk.DISABLED, width=20)
        self.btn_compress.pack(pady=5)

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

    def _load_default_ignores(self, repo_path=None):
        """
        Populates the ignore box with safe defaults and dynamically merges
        entries from the repository's .gitignore file if one exists.
        """
        # Critical baseline to prevent scanning our own outputs or heavy caches
        ignores = {".git", "node_modules", "__pycache__", "dist", "build", ".next", ".expo", ".venv", ".pytest_cache", "snapshots", "compression_state"}
        
        if repo_path:
            gitignore_path = os.path.join(repo_path, ".gitignore")
            if os.path.exists(gitignore_path):
                try:
                    with open(gitignore_path, "r", encoding="utf-8") as f:
                        for line in f:
                            line = line.strip()
                            if line and not line.startswith("#"):
                                # Clean trailing/leading slashes for exact name matching
                                line = line.strip("/")
                                if line.startswith("/"): 
                                    line = line[1:]
                                # Ignore complex globs (*), focus on static directory/file names
                                if line and "*" not in line:
                                    ignores.add(line)
                except Exception:
                    pass
        
        if hasattr(self, 'config_tabs') and hasattr(self.config_tabs, 'ignore_var'):
            self.config_tabs.ignore_var.set(" ".join(sorted(list(ignores))))

    def _browse(self):
        path = filedialog.askdirectory()
        if path:
            self.ent_root.delete(0, tk.END)
            self.ent_root.insert(0, path)
            self.repo_root = path
            # Dynamically read the .gitignore of the selected repo
            self._load_default_ignores(path)

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
        self.btn_compress.config(state=tk.DISABLED)
        
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
        self.btn_compress.config(state=tk.NORMAL)

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

    def _compress_context(self):
        if not self.repo_root:
            messagebox.showwarning("Error", "Please scan a repository first.")
            return

        env_path = os.path.join(self.repo_root, ".env")
        if not os.path.exists(env_path):
            messagebox.showwarning("Missing Configuration", f"Could not find '.env' file at repo root.\n\nPlease create {env_path} and add:\nGEMINI_API_KEY=\"your_key_here\"")
            return

        confirm = messagebox.askyesno(
            "Execute Context Compression?",
            "WARNING: This will make real HTTP calls to the Gemini API and consume AI Tokens.\n\n"
            "This process will:\n"
            "1. Snapshot the current codebase state.\n"
            "2. Identify any files modified since the last run.\n"
            "3. Send those specific files to Gemini for summarization.\n"
            "4. Output a final 'compressed_context.md' artifact.\n\n"
            "Do you want to proceed?"
        )
        if not confirm:
            return

        out_root = filedialog.askdirectory(title="Select Output Root (for Snapshots and State)")
        if not out_root: return
        
        state_dir = os.path.join(out_root, "compression_state")
        current_json = os.path.join(out_root, "current.json")
        
        # Capture base_id BEFORE we take a new snapshot and overwrite current.json
        base_id = "empty"
        if os.path.exists(current_json):
            try:
                with open(current_json, 'r') as f:
                    base_id = json.load(f).get("current_snapshot_id", "empty")
            except Exception:
                pass

        # Capture GUI ignore rules, depth, and extensions for the snapshot phase
        depth_val = str(self.config_tabs.depth_var.get())
        ignore_list = self.config_tabs.ignore_var.get().split()
        ext_list = self.config_tabs.ext_var.get().split()
        include_readme = self.config_tabs.include_readme_var.get()

        self.btn_compress.config(state=tk.DISABLED)
        self.btn_snap.config(state=tk.DISABLED)
        self.btn_export.config(state=tk.DISABLED)
        self.btn_batch_export.config(state=tk.DISABLED)
        self.progress_win = ProgressWindow(self, title="Context Compression Orchestrator", message="Initializing Pipeline...")

        def run_part1():
            try:
                python_exe = sys.executable
                
                # Phase 1: Snapshot (using inherited GUI rules)
                self.after(0, lambda: self.progress_win.update_message("Phase 1/4: Generating strict snapshot..."))
                
                snap_cmd = [
                    python_exe, "-m", "src.entry_point", "snapshot", self.repo_root, 
                    "--output-root", out_root, "--depth", depth_val
                ]
                if ignore_list:
                    snap_cmd.extend(["--ignore"] + ignore_list)
                if ext_list:
                    snap_cmd.extend(["--include-extensions"] + ext_list)
                if not include_readme:
                    snap_cmd.append("--no-include-readme")

                subprocess.run(snap_cmd, check=True, capture_output=True)

                # Phase 2: Diff State
                self.after(0, lambda: self.progress_win.update_message("Phase 2/4: Syncing deterministic state queues..."))
                subprocess.run(
                    [python_exe, "-m", "src.entry_point", "export", "compression-state", 
                     "--base", base_id, "--target", "current", "--output-root", out_root, "--state-dir", state_dir],
                    check=True, capture_output=True
                )
                
                # Move to main thread to show Dialog
                self.after(0, lambda: self._show_compression_dialog(state_dir, out_root))
                
            except subprocess.CalledProcessError as e:
                err_msg = e.stderr.decode('utf-8') if e.stderr else str(e)
                self.after(0, lambda: self._compress_context_fail(f"Pipeline Step Failed:\n{err_msg}"))
            except Exception as e:
                self.after(0, lambda: self._compress_context_fail(str(e)))

        threading.Thread(target=run_part1, daemon=True).start()

    def _show_compression_dialog(self, state_dir, out_root):
        self.progress_win.close()
        
        from src.gui.components.compression_queue_dialog import CompressionQueueDialog
        dialog = CompressionQueueDialog(
            parent=self, 
            state_dir=state_dir, 
            repo_root=self.repo_root, 
            on_confirm_callback=lambda: self._run_part2(state_dir, out_root),
            on_cancel_callback=self._compress_context_abort
        )
        
        if not dialog.has_pending:
            messagebox.showinfo("Up to date", "No files have been modified. Context is already fully compressed!")
            dialog.destroy()
            self._compress_context_abort()

    def _run_part2(self, state_dir, out_root):
        self.progress_win = ProgressWindow(self, title="Context Compression Orchestrator", message="Initializing LLM...")
        final_out = os.path.join(out_root, "compressed_context.md")
        
        def run_part2_thread():
            try:
                python_exe = sys.executable
                
                # Phase 3: LLM
                self.after(0, lambda: self.progress_win.update_message("Phase 3/4: Starting LLM Compressor..."))
                llm_script = os.path.join(self.repo_root, "scripts", "llm_compressor.py")
                
                # Use Popen to stream stdout line-by-line
                process = subprocess.Popen(
                    [python_exe, "-u", llm_script, "--repo-root", self.repo_root, "--state-dir", state_dir],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1
                )
                
                output_log = []
                for line in iter(process.stdout.readline, ''):
                    clean_line = line.strip()
                    if not clean_line:
                        continue
                        
                    output_log.append(clean_line)
                    
                    # Show the raw tail of the logs to ensure nothing is hidden
                    log_tail = "\n".join(output_log[-4:])
                    display_msg = f"Phase 3/4: Compressing via LLM...\n\n{log_tail}"
                    self.after(0, lambda m=display_msg: self.progress_win.update_message(m))

                process.wait()
                
                if process.returncode != 0:
                    err_msg = "\n".join(output_log[-15:]) # Grab tail of logs for context
                    raise Exception(f"LLM Compressor Failed (Code {process.returncode}):\n{err_msg}")

                # Phase 4: Stitch
                self.after(0, lambda: self.progress_win.update_message("Phase 4/4: Stitching final markdown artifact..."))
                stitch_script = os.path.join(self.repo_root, "scripts", "llm_stitcher.py")
                subprocess.run(
                    [python_exe, stitch_script, "--state-dir", state_dir, "--output", final_out],
                    check=True, capture_output=True
                )

                self.after(0, lambda: self._compress_context_done(final_out))

            except subprocess.CalledProcessError as e:
                err_msg = e.stderr.decode('utf-8') if e.stderr else str(e)
                self.after(0, lambda: self._compress_context_fail(f"Pipeline Step Failed:\n{err_msg}"))
            except Exception as e:
                self.after(0, lambda: self._compress_context_fail(str(e)))
                
        threading.Thread(target=run_part2_thread, daemon=True).start()

    def _compress_context_done(self, out_path):
        self.progress_win.close()
        self.btn_compress.config(state=tk.NORMAL)
        self.btn_snap.config(state=tk.NORMAL)
        self.btn_export.config(state=tk.NORMAL)
        self.btn_batch_export.config(state=tk.NORMAL)
        self.status_var.set(f"Compression Complete: {out_path}")
        messagebox.showinfo("Success", f"Context Compression Pipeline Completed!\n\nFinal Artifact saved to:\n{out_path}")
        
        try:
            if platform.system() == "Windows":
                os.startfile(out_path)
            elif platform.system() == "Darwin":
                subprocess.call(["open", out_path])
        except:
            pass

    def _compress_context_fail(self, error):
        if hasattr(self, 'progress_win') and self.progress_win:
            self.progress_win.close()
        self.btn_compress.config(state=tk.NORMAL)
        self.btn_snap.config(state=tk.NORMAL)
        self.btn_export.config(state=tk.NORMAL)
        self.btn_batch_export.config(state=tk.NORMAL)
        self.status_var.set("Compression Pipeline Failed.")
        messagebox.showerror("Pipeline Error", error)
        
    def _compress_context_abort(self):
        self.btn_compress.config(state=tk.NORMAL)
        self.btn_snap.config(state=tk.NORMAL)
        self.btn_export.config(state=tk.NORMAL)
        self.btn_batch_export.config(state=tk.NORMAL)
        self.status_var.set("Compression Pipeline Aborted.")


def run_gui():
    RepoRunnerApp().mainloop()
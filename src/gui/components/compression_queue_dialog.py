import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
import subprocess

class CompressionQueueDialog(tk.Toplevel):
    def __init__(self, parent, state_dir, repo_root, on_confirm_callback, on_cancel_callback):
        super().__init__(parent)
        self.title("Pre-Compress Summary")
        self.geometry("1000x700")
        self.transient(parent)
        self.grab_set()
        
        self.state_dir = state_dir
        self.repo_root = repo_root
        self.on_confirm_callback = on_confirm_callback
        self.on_cancel_callback = on_cancel_callback
        
        self.bool_path = os.path.join(state_dir, "file_changed_bool.json")
        try:
            with open(self.bool_path, "r", encoding="utf-8") as f:
                self.queue = json.load(f)
        except Exception:
            self.queue = {}
            
        self.pending_files = sorted([k for k, v in self.queue.items() if v == 1])
        self.has_pending = len(self.pending_files) > 0
        
        # State array to track toggles in memory before saving
        self.file_states = {f: True for f in self.pending_files}

        if self.has_pending:
            self._build_ui()
            self.protocol("WM_DELETE_WINDOW", self._on_cancel)

    def _build_ui(self):
        # Top Label
        msg = "The following files have changed. Uncheck [X] to set their state to '0' and skip LLM compression."
        ttk.Label(self, text=msg, font=("Segoe UI", 10, "bold")).pack(pady=10, padx=10, anchor=tk.W)

        # Paned Window
        paned = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Left Pane: List
        left_frame = ttk.Frame(paned)
        paned.add(left_frame, weight=1)

        self.listbox = tk.Listbox(left_frame, font=("Consolas", 10), selectmode=tk.SINGLE)
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(left_frame, orient="vertical", command=self.listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.listbox.config(yscrollcommand=scrollbar.set)
        
        self.listbox.bind("<<ListboxSelect>>", self._on_select)
        self.listbox.bind("<Double-1>", self._on_double_click)

        self._refresh_list()

        # Right Pane: Preview
        right_frame = ttk.Frame(paned)
        paned.add(right_frame, weight=2)
        
        ttk.Label(right_frame, text="File Preview (Git Diff or Current Content):").pack(anchor=tk.W)
        self.text_preview = tk.Text(right_frame, wrap=tk.NONE, font=("Consolas", 10), state=tk.DISABLED)
        self.text_preview.pack(fill=tk.BOTH, expand=True, pady=5)
        
        x_scroll = ttk.Scrollbar(right_frame, orient="horizontal", command=self.text_preview.xview)
        x_scroll.pack(fill=tk.X)
        self.text_preview.config(xscrollcommand=x_scroll.set)

        # Bottom Actions
        action_frame = ttk.Frame(self)
        action_frame.pack(fill=tk.X, pady=10, padx=10)

        ttk.Button(action_frame, text="Toggle Included/Skipped", command=self._toggle_selected).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(action_frame, text="Cancel", command=self._on_cancel).pack(side=tk.RIGHT, padx=5)
        ttk.Button(action_frame, text="Confirm & Compress", command=self._on_confirm).pack(side=tk.RIGHT, padx=5)

    def _refresh_list(self):
        self.listbox.delete(0, tk.END)
        for f in self.pending_files:
            status = "[X]" if self.file_states[f] else "[ ]"
            clean_name = f.replace("file:", "")
            self.listbox.insert(tk.END, f"{status} {clean_name}")
            
            # Color coding for skipped items
            if not self.file_states[f]:
                self.listbox.itemconfig(tk.END, {'fg': 'gray'})

    def _on_select(self, event):
        selection = self.listbox.curselection()
        if not selection:
            return
            
        index = selection[0]
        stable_id = self.pending_files[index]
        rel_path = stable_id.replace("file:", "")
        abs_path = os.path.join(self.repo_root, rel_path)

        self.text_preview.config(state=tk.NORMAL)
        self.text_preview.delete("1.0", tk.END)

        # 1. Try to get Git Diff
        try:
            res = subprocess.run(["git", "diff", "HEAD", "--", rel_path], cwd=self.repo_root, capture_output=True, text=True)
            if res.stdout.strip():
                self.text_preview.insert(tk.END, f"--- GIT DIFF: {rel_path} ---\n\n")
                self.text_preview.insert(tk.END, res.stdout)
                self.text_preview.config(state=tk.DISABLED)
                return
        except Exception:
            pass

        # 2. Fallback to Raw File
        try:
            if os.path.exists(abs_path):
                with open(abs_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                self.text_preview.insert(tk.END, f"--- CURRENT FILE (Git diff unavailable): {rel_path} ---\n\n")
                self.text_preview.insert(tk.END, content)
            else:
                self.text_preview.insert(tk.END, f"File removed from disk: {rel_path}")
        except Exception as e:
            self.text_preview.insert(tk.END, f"Could not load preview:\n{e}")
            
        self.text_preview.config(state=tk.DISABLED)

    def _on_double_click(self, event):
        self._toggle_selected()

    def _toggle_selected(self):
        selection = self.listbox.curselection()
        if not selection:
            return
            
        index = selection[0]
        stable_id = self.pending_files[index]
        
        # Toggle state
        self.file_states[stable_id] = not self.file_states[stable_id]
        
        # Refresh UI and keep selection
        self._refresh_list()
        self.listbox.selection_set(index)

    def _on_confirm(self):
        # Update the JSON queue with user overrides
        for f in self.pending_files:
            if not self.file_states[f]:
                self.queue[f] = 0 # Mark as 0 to skip LLM API Call
                
        with open(self.bool_path, "w", encoding="utf-8") as f:
            json.dump(self.queue, f, indent=2)
            
        self.destroy()
        self.on_confirm_callback()

    def _on_cancel(self):
        self.destroy()
        self.on_cancel_callback()
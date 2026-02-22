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
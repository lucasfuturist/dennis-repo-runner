import tkinter as tk
from tkinter import ttk, filedialog, messagebox

class ExportPreviewWindow(tk.Toplevel):
    def __init__(self, parent, content, default_filename="export.md"):
        super().__init__(parent)
        self.title("Export Preview")
        self.geometry("1000x800")
        
        self.content = content
        self.default_filename = default_filename
        
        self._build_ui()
        
        # Behavior: Focus on this window
        self.focus_force()

    def _build_ui(self):
        # Toolbar
        toolbar = ttk.Frame(self, padding=5)
        toolbar.pack(side=tk.TOP, fill=tk.X)
        
        ttk.Button(toolbar, text="💾 Save to File...", command=self._save).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="📋 Copy to Clipboard", command=self._copy).pack(side=tk.LEFT, padx=2)
        
        # Stats
        lines = self.content.count('\n') + 1
        chars = len(self.content)
        lbl_stats = ttk.Label(toolbar, text=f"  |  {lines:,} lines  |  {chars:,} chars  |", font=("Segoe UI", 9))
        lbl_stats.pack(side=tk.LEFT, padx=10)

        ttk.Button(toolbar, text="Close", command=self.destroy).pack(side=tk.RIGHT, padx=2)
        
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
                with open(out_path, "w", encoding="utf-8") as f:
                    f.write(self.content)
                messagebox.showinfo("Saved", f"Successfully saved to:\n{out_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save file:\n{e}")

    def _copy(self):
        self.clipboard_clear()
        self.clipboard_append(self.content)
        messagebox.showinfo("Copied", "Content copied to clipboard!")
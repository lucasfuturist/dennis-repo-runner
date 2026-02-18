import tkinter as tk
from tkinter import ttk
from src.fingerprint.file_fingerprint import FileFingerprint

class PreviewPanel(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        
        # Metadata Header
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

    def clear(self):
        self.text_preview.delete("1.0", tk.END)
        self.lbl_meta.config(text="Select a file to preview properties.")

    def load_file(self, abs_path, stable_id):
        self.clear()
        try:
            fp = FileFingerprint.fingerprint(abs_path)
            self.lbl_meta.config(text=f" ID: {stable_id}  |  Size: {fp['size_bytes']}B  |  Lang: {fp['language']}  |  SHA: {fp['sha256'][:12]}")
            
            if fp['size_bytes'] > 250_000:
                self.text_preview.insert("1.0", "<< File too large for preview >>")
            else:
                with open(abs_path, 'r', encoding='utf-8', errors='replace') as f:
                    self.text_preview.insert("1.0", f.read())
        except Exception as e:
            self.text_preview.insert("1.0", f"<< Error loading file: {e} >>")
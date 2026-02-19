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

    def clear(self):
        self.text_preview.delete("1.0", tk.END)
        self.lbl_meta.config(text="Select a file to preview properties.")

    def load_file(self, abs_path, stable_id):
        self.clear()
        try:
            # 1. Fingerprint (Size, SHA, Lang)
            fp = FileFingerprint.fingerprint(abs_path)
            
            # 2. Scan Imports (Lazy load on click using detected language)
            imports = ImportScanner.scan(abs_path, fp['language'])
            
            # 3. Update Brief Header Label
            import_count = len(imports)
            self.lbl_meta.config(text=f" ID: {stable_id}  |  {fp['language']}  |  {import_count} Imports")

            # 4. Construct Detailed Metadata Header
            header_lines = [
                f"Path:    {abs_path}",
                f"SHA256:  {fp['sha256']}",
                f"Size:    {fp['size_bytes']:,} bytes",
                "-" * 60,
                "IMPORTS FOUND:",
            ]
            
            if imports:
                for imp in imports:
                    header_lines.append(f"  • {imp}")
            else:
                header_lines.append("  (none)")
                
            header_lines.append("-" * 60)
            header_lines.append("") # Spacer line
            
            full_header = "\n".join(header_lines)
            
            # 5. Insert Header
            self.text_preview.insert("1.0", full_header)

            # 6. Append Real File Content
            if fp['size_bytes'] > 250_000:
                self.text_preview.insert(tk.END, "<< File too large for preview >>")
            else:
                with open(abs_path, 'r', encoding='utf-8', errors='replace') as f:
                    self.text_preview.insert(tk.END, f.read())
                    
        except Exception as e:
            self.text_preview.insert("1.0", f"<< Error loading file: {e} >>")
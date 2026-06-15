import tkinter as tk
from tkinter import ttk
from src.core.controller import get_file_preview_data

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
            # Query backend securely via the Core Facade Layer
            data = get_file_preview_data(abs_path)
            
            lang = data["language"]
            sha256 = data["sha256"]
            size_bytes = data["size_bytes"]
            actual_imports = data["imports"]
            actual_symbols = data["symbols"]
            
            # Update Brief Header Label
            import_count = len(actual_imports)
            symbol_count = len(actual_symbols)
            self.lbl_meta.config(text=f" ID: {stable_id}  |  {lang}  |  {import_count} Imports  |  {symbol_count} Symbols")

            # Construct Detailed Metadata Header
            header_lines = [
                f"Path:    {abs_path}",
                f"SHA256:  {sha256}",
                f"Size:    {size_bytes:,} bytes",
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
            
            # Insert Header
            self.text_preview.insert("1.0", full_header, "header")

            # Append Real File Content
            if size_bytes > 250_000:
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
        """Very basic highlighting for common keywords."""
        keywords = {
            "def", "class", "import", "from", "return", "if", "else", "elif", 
            "for", "while", "try", "except", "with", "as", "pass", "lambda",
            "const", "let", "var", "function", "export", "interface", "type"
        }
        
        start_index = "15.0" 
        
        for kw in keywords:
            idx = start_index
            while True:
                idx = self.text_preview.search(kw, idx, stopindex=tk.END)
                if not idx:
                    break
                
                end_idx = f"{idx}+{len(kw)}c"
                self.text_preview.tag_add("keyword", idx, end_idx)
                idx = end_idx
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
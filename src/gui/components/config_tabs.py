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
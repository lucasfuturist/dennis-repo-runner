import tkinter as tk
from tkinter import ttk

class ProgressWindow(tk.Toplevel):
    def __init__(self, parent, title="Processing...", message="Please wait"):
        super().__init__(parent)
        self.title(title)
        self.geometry("400x150")
        self.resizable(False, False)
        
        # Modal behavior
        self.transient(parent)
        self.grab_set()
        
        self.cancelled = False
        
        # Center the window
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (self.winfo_width() // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (self.winfo_height() // 2)
        self.geometry(f"+{x}+{y}")
        
        self._build_ui(message)
        
    def _build_ui(self, message):
        frame = ttk.Frame(self, padding=20)
        frame.pack(fill=tk.BOTH, expand=True)
        
        self.lbl_msg = ttk.Label(frame, text=message, wraplength=360)
        self.lbl_msg.pack(pady=(0, 15), anchor=tk.W)
        
        self.progress = ttk.Progressbar(frame, mode='indeterminate')
        self.progress.pack(fill=tk.X, pady=(0, 15))
        self.progress.start(15)
        
        self.btn_cancel = ttk.Button(frame, text="Cancel", command=self.cancel)
        self.btn_cancel.pack(anchor=tk.E)
        
    def update_message(self, text):
        self.lbl_msg.config(text=text)
        
    def update_progress(self, current: int, total: int = 0):
        """
        Dynamically shifts from indeterminate to determinate if total is known.
        """
        if total > 0:
            if self.progress.cget('mode') == 'indeterminate':
                self.progress.stop()
                self.progress.config(mode='determinate', maximum=total)
            self.progress['value'] = current
        else:
            if self.progress.cget('mode') == 'determinate':
                self.progress.config(mode='indeterminate')
                self.progress.start(15)
        
    def cancel(self):
        self.cancelled = True
        self.lbl_msg.config(text="Cancelling... please wait.")
        self.btn_cancel.state(['disabled'])

    def close(self):
        self.grab_release()
        self.destroy()
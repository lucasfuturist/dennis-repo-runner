# src/entry_point.py
import sys
import multiprocessing

if sys.platform.startswith('win'):
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass

def launch():
    if len(sys.argv) > 1:
        from src.cli.main import main
        main()
    else:
        from src.gui.app import run_gui
        run_gui()

if __name__ == "__main__":
    multiprocessing.freeze_support()
    launch()
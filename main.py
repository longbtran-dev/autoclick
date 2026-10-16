"""
Auto Clicker Pro - Main Entry Point
High-Precision Auto Clicker with Graphical User Interface
"""

import ctypes
import os
import sys
import tkinter as tk

from gui import AutoClickerApp


def enable_high_dpi_awareness():
    """Enable High DPI awareness on Windows for crisp fonts and graphics."""
    try:
        # Windows 8.1+ Per-monitor DPI awareness
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        try:
            # Windows Vista+ System DPI awareness
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass


def is_admin() -> bool:
    """Check if the current process has administrator privileges."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False


def main():
    enable_high_dpi_awareness()

    root = tk.Tk()

    # Optional title suffix if running as Admin
    if is_admin():
        root.title("Auto Clicker Pro - [Administrator]")

    app = AutoClickerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()

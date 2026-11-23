"""
Member 5 - Tkinter interface.

This entry point preserves the original gui.py implementation and launch
command while providing the member-scoped app.py filename.
"""

from gui import PharmacyApp, main

__all__ = ["PharmacyApp", "main"]


if __name__ == "__main__":
    main()

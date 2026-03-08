"""utils/paths.py - Centralized path helpers for dev & PyInstaller exe."""
import sys, os

def resource_path(relative_path: str) -> str:
    """Resolve path to a bundled asset (image, audio, etc.).

    In dev mode returns path relative to project root.
    In PyInstaller bundle returns path inside _MEIPASS temp folder.
    """
    try:
        base = sys._MEIPASS          # PyInstaller bundle
    except AttributeError:
        # dev mode: go up one level from utils/ to project root
        base = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    return os.path.join(base, relative_path)


def data_dir() -> str:
    """Return writable directory for JSON data files & recorded audio.

    PyInstaller exe  → folder containing the .exe
    Dev mode         → project root
    """
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
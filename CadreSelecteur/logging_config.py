from pathlib import Path
import logging
from logging import FileHandler, Formatter
import sys
import tempfile

BASE_DIR = Path(__file__).resolve().parent
# Si on est dans un exécutable PyInstaller, ne pas écrire dans _MEIPASS (non modifiable) —
# utiliser un emplacement temporaire ou user data dir. Sinon, utiliser resources/ du package.
if getattr(sys, 'frozen', False):
    # Utiliser un dossier dans le répertoire temporaire spécifique à l'application
    RESOURCES_DIR = Path(tempfile.gettempdir()) / 'CadreSelecteur'
else:
    RESOURCES_DIR = BASE_DIR / 'resources'

# Créer le dossier (parents=True pour éviter WinError 3 si le parent n'existe pas)
RESOURCES_DIR.mkdir(parents=True, exist_ok=True)
LOG_PATH = RESOURCES_DIR / 'image_editor.log'

# Configure package logger to ensure file output even when test harness configures root logger
pkg_logger = logging.getLogger('CadreSelecteur')
pkg_logger.setLevel(logging.DEBUG)

# Avoid adding duplicate file handlers for the same path
_existing = [h for h in pkg_logger.handlers if isinstance(h, FileHandler) and getattr(h, 'baseFilename', None) == str(LOG_PATH)]
if not _existing:
    fh = FileHandler(str(LOG_PATH), encoding='utf-8')
    fh.setLevel(logging.DEBUG)
    fmt = Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(fmt)
    pkg_logger.addHandler(fh)

# Also ensure the root logger has at least one handler (useful for CLI runs)
root_logger = logging.getLogger()
if not root_logger.handlers:
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(Formatter('%(levelname)s: %(message)s'))
    root_logger.addHandler(ch)

__all__ = ['LOG_PATH', 'RESOURCES_DIR']

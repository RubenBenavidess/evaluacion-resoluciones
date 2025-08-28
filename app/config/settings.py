from pathlib import Path

SETTINGS_DIR = Path(__file__).resolve().parent
BASE_DIR = SETTINGS_DIR.parent
IMAGES_PATH = BASE_DIR / 'data'
IMAGES_PATH = IMAGES_PATH.resolve()

class Settings:
    BASE_PATH: Path = BASE_DIR
    DOC: Path = IMAGES_PATH / 'Resolucion-R-OCS-SE-009-Nro.074-2025.pdf'

settings = Settings()
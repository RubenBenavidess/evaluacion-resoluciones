from pathlib import Path

SETTINGS_DIR = Path(__file__).resolve().parent
BASE_DIR = SETTINGS_DIR.parent
IMAGES_PATH = BASE_DIR / 'data'
IMAGES_PATH = IMAGES_PATH.resolve()

class Settings:
    BASE_PATH: Path = BASE_DIR
    OLLAMA_HOST: str = 'http://localhost:11434'
    OCR_MODEL_NAME: str = 'llama3.2-vision'
    IMAGES: tuple[Path, ...] = (
            IMAGES_PATH / 'Resolucion-R-OCS-SE-009-Nro.074-2025_page-0001.jpg', 
            IMAGES_PATH / 'Resolucion-R-OCS-SE-009-Nro.074-2025_page-0002.jpg', 
            IMAGES_PATH / 'Resolucion-R-OCS-SE-009-Nro.074-2025_page-0003.jpg'
        )
    
settings = Settings()
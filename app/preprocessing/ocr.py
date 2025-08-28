from doctr.io import DocumentFile
from doctr.models import ocr_predictor
from config.settings import settings


def get_plain_text() -> str:
    
    doc = DocumentFile.from_pdf(settings.DOC)
    
    predictor = ocr_predictor(pretrained=True)
    
    result = predictor(doc)

    string_result = result.render()
    
    return string_result


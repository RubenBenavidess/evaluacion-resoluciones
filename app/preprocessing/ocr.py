from ollama import Client
from config.settings import settings

def get_ollama_client() -> Client:
    return Client(host=settings.OLLAMA_HOST)

def get_plain_text() -> str:
    
    client = get_ollama_client()

    messages = [
        {
            'role': 'system',
            'content': (
                'Devuelve SOLO texto plano en español.'
                'Respeta el orden del documento.'
            ),
        },
    ]

    for i, img in enumerate(settings.IMAGES, start=1):
        messages.append({
            'role': 'user',
            'content': f'Extrae todos los datos de la PÁGINA {i}.',
            'images': [str(img)], 
        })

    resp = client.chat(model=settings.OCR_MODEL_NAME, messages=messages, stream=False)
    print(resp.message.content)
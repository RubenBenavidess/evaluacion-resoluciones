# Evaluación Resoluciones

## Ejecútalo

TODO...

### Propósito

El propósito del presente proyecto es la automatización de generación de resoluciones del Órgano Superior Colegiado del Instituto Yaruquí del Ecuador.

### Resumen

TODO...

### Introducción

Para el proyecto, se determinó que una automatización de la índole presente, se puede solucionar a través de minería de texto, debido a que permite extraer conocimiento útil y específico. Un gran ejemplo es la NER (Named Entity Recognition), que permite obtener el nombre de entidades reconocidas. En ese sentido, la minería de texto es capaz de generar resoluciones a partir de documentos que describan las mismas.

Bajo este enfoque, se propuso aplicar una técnica de procesamiento de lenguaje natural, ya que permite analizar texto humano, extraer información y clasificarla adecuadamente. Además, NLP es justamente útil para el procesamiento de documentos grandes, exactamente como lo puede ser un documento de resoluciones. Sin embargo, cabe aclarar que la preparación y el procesamiento de los datos fue necesaria.

### Metodología

1. Comprensión de los datos

El documento que se trató consiste en un documento de resolución de un informe de auditoría realizado en el año 2024 determinando que se aprueba, así como otros procedimientos oficiales a realizar. Es un documento netamente de texto plano.

2. Preparación de los datos

Una vez que se ha comprendido los datos, el trabajo posterior consistió en:

- Tratamiento por OCR mediante Llama Vision de Ollama.
- Normalización del texto.
- NLP con expresiones regulares.

TODO...


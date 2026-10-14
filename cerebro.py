import json

from google import genai
from google.genai import types

from modelos import Apunte


MODELO_IA = "gemini-3.8-flash"
INSTRUCCION_SISTEMA = (
    "Actuá como un profesor paciente de bachillerato de El Salvador. "
    "Escribí siempre en español salvadoreño claro. Basate únicamente en lo que se ve en la imagen; "
    "no inventés temas ni completés información que no aparece. Si la foto está borrosa o algo no se distingue, "
    "decilo en el resumen en vez de inventar. En el examen, creá opciones incorrectas creíbles, no absurdas, "
    "y variá entre preguntas la posición de la respuesta correcta."
)
MENSAJE_USUARIO = "Analizá el contenido visible de esta página y prepará el apunte solicitado."
MENSAJE_IMAGEN_ILEGIBLE = (
    "No se pudo leer bien la página. Probá con una foto más nítida, bien iluminada y que muestre la hoja completa."
)


class ImagenIlegible(Exception):
    """Indica que no se pudo obtener un apunte válido de la imagen."""


def crear_cliente(api_key: str) -> genai.Client:
    if not api_key or not api_key.strip():
        raise ValueError("La llave de la API está vacía. Ingresá una llave válida para continuar.")
    return genai.Client(api_key=api_key)


def analizar_pagina(datos_imagen: bytes, tipo_mime: str, cliente: genai.Client) -> Apunte:
    if not datos_imagen:
        raise ValueError("No se recibió ninguna imagen para analizar.")

    respuesta = cliente.models.generate_content(
        model=MODELO_IA,
        contents=[
            types.Part.from_bytes(data=datos_imagen, mime_type=tipo_mime),
            MENSAJE_USUARIO,
        ],
        config=types.GenerateContentConfig(
            system_instruction=INSTRUCCION_SISTEMA,
            response_mime_type="application/json",
            response_schema=Apunte,
            temperature=0.4,
        ),
    )

    if isinstance(respuesta.parsed, Apunte):
        return respuesta.parsed

    try:
        if not respuesta.text:
            raise ValueError("La respuesta no contiene texto.")
        return Apunte.model_validate(json.loads(respuesta.text))
    except (json.JSONDecodeError, TypeError, ValueError):
        raise ImagenIlegible(MENSAJE_IMAGEN_ILEGIBLE) from None


def calificar(apunte: Apunte, respuestas: dict[int, int]) -> tuple[int, int]:
    aciertos = sum(
        respuestas.get(indice) == pregunta.correcta
        for indice, pregunta in enumerate(apunte.examen)
    )
    return aciertos, len(apunte.examen)
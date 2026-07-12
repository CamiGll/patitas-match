from google import genai
from pydantic import BaseModel

from src.models import PerfilAdoptante, PerfilPerro

MODEL = "gemini-2.5-flash"
TIMEOUT_MS = 30_000


class ExtractionError(Exception):
    """La extracción con IA falló tras agotar los reintentos."""


def _extract[T: BaseModel](texto: str, schema: type[T], client: genai.Client | None) -> T:
    if client is None:
        from src.clients import get_gemini

        client = get_gemini()

    ultimo_error: Exception | None = None
    for _ in range(2):  # un reintento ante fallas transitorias
        try:
            response = client.models.generate_content(
                model=MODEL,
                contents=texto,
                config={
                    "response_mime_type": "application/json",
                    "response_schema": schema,
                    "temperature": 0.1,
                    "http_options": {"timeout": TIMEOUT_MS},
                },
            )
            return schema.model_validate_json(response.text)
        except Exception as e:  # noqa: BLE001 — transitorio o respuesta inválida
            ultimo_error = e

    raise ExtractionError(
        f"No se pudo extraer el perfil con Gemini: {ultimo_error}"
    ) from ultimo_error


def extract_perfil_perro(texto: str, client: genai.Client | None = None) -> PerfilPerro:
    return _extract(texto, PerfilPerro, client)


def extract_perfil_adoptante(texto: str, client: genai.Client | None = None) -> PerfilAdoptante:
    return _extract(texto, PerfilAdoptante, client)

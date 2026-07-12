"""Golden set: llama a la API real de Gemini. Se corre con `pytest -m live` y GEMINI_API_KEY en el entorno."""

import json
import os
from pathlib import Path

import pytest

pytestmark = pytest.mark.live

CASOS = json.loads((Path(__file__).parent / "casos.json").read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def gemini_client():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        pytest.skip("GEMINI_API_KEY no está definida en el entorno")
    from google import genai

    return genai.Client(api_key=api_key)


@pytest.mark.parametrize("caso", CASOS, ids=[c["esperado"]["nombre"] for c in CASOS])
def test_extraccion_golden(caso, gemini_client):
    from src.extraction import extract_perfil_perro

    perfil = extract_perfil_perro(caso["historia"], client=gemini_client)
    assert perfil.model_dump() == caso["esperado"]

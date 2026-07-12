"""Motor de matching. Funciones puras: sin Streamlit, sin Supabase."""

from dataclasses import dataclass


@dataclass
class MatchResult:
    afinidad: int
    apto: bool
    motivo: str


def score_match(perro: dict, adoptante: dict) -> MatchResult:
    afinidad = 100
    apto = True
    motivo: list[str] = []

    # Reglas excluyentes (hard blocks)
    if not perro["apto_ninos"] and adoptante["tiene_ninos"]:
        apto = False
        afinidad = 0
        motivo.append("No compatible con niños.")

    if not perro["apto_gatos"] and adoptante["tiene_gatos"]:
        apto = False
        afinidad = 0
        motivo.append("No compatible con gatos.")

    # Penalizaciones (soft blocks) — solo si superó los filtros excluyentes
    if apto:
        if perro["necesita_patio"] and adoptante["tipo_vivienda"] == "departamento":
            afinidad -= 30
            motivo.append("Penalización: Sin patio.")

        if perro["energia"] == "alto" and adoptante["tipo_vivienda"] == "departamento":
            afinidad -= 20
            motivo.append("Penalización: Departamento para alta energía.")

        if not motivo:
            motivo.append("Estilo de vida acorde.")

    return MatchResult(afinidad=afinidad, apto=apto, motivo=" ".join(motivo))

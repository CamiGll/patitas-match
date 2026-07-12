from src.matching import score_match


def perro(**overrides) -> dict:
    base = {
        "nombre": "firulais",
        "edad": "adulto",
        "energia": "medio",
        "necesita_patio": False,
        "apto_ninos": True,
        "apto_gatos": True,
    }
    return {**base, **overrides}


def adoptante(**overrides) -> dict:
    base = {
        "id": 1,
        "nombre": "Ana",
        "tiene_ninos": False,
        "tiene_gatos": False,
        "tipo_vivienda": "casa",
    }
    return {**base, **overrides}


def test_hard_block_ninos():
    r = score_match(perro(apto_ninos=False), adoptante(tiene_ninos=True))
    assert r.afinidad == 0
    assert r.apto is False
    assert "No compatible con niños." in r.motivo


def test_hard_block_gatos():
    r = score_match(perro(apto_gatos=False), adoptante(tiene_gatos=True))
    assert r.afinidad == 0
    assert r.apto is False
    assert "No compatible con gatos." in r.motivo


def test_ambos_hard_blocks():
    r = score_match(
        perro(apto_ninos=False, apto_gatos=False),
        adoptante(tiene_ninos=True, tiene_gatos=True),
    )
    assert r.afinidad == 0
    assert r.apto is False
    assert "No compatible con niños." in r.motivo
    assert "No compatible con gatos." in r.motivo


def test_penalizacion_patio():
    r = score_match(perro(necesita_patio=True), adoptante(tipo_vivienda="departamento"))
    assert r.afinidad == 70
    assert r.apto is True
    assert "Sin patio" in r.motivo


def test_penalizacion_energia():
    r = score_match(perro(energia="alto"), adoptante(tipo_vivienda="departamento"))
    assert r.afinidad == 80
    assert r.apto is True
    assert "alta energía" in r.motivo


def test_penalizaciones_acumuladas():
    r = score_match(
        perro(necesita_patio=True, energia="alto"),
        adoptante(tipo_vivienda="departamento"),
    )
    assert r.afinidad == 50
    assert r.apto is True


def test_match_perfecto():
    r = score_match(perro(), adoptante())
    assert r.afinidad == 100
    assert r.apto is True
    assert r.motivo == "Estilo de vida acorde."

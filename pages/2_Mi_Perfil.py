import streamlit as st

from src import auth
from src.db import get_adoptante_por_usuario, guardar_adoptante
from src.extraction import ExtractionError, extract_perfil_adoptante

st.set_page_config(page_title="Mi Perfil — Patitas Match", page_icon="🏠", layout="centered")
auth.sidebar_user()
auth.require_login()

st.title("🏠 Mi Perfil de Adoptante")

sesion = auth.current_user()
client = auth.get_user_client()
perfil_db = get_adoptante_por_usuario(client, sesion["user_id"])

VIVIENDAS = ["casa", "departamento"]
NIVELES = ["alto", "medio", "bajo"]
EXPERIENCIAS = ["ninguna", "algo", "mucha"]

if perfil_db is None and "perfil_adoptante_extraido" not in st.session_state:
    st.write(
        "Contanos sobre tu hogar y estilo de vida en tus palabras. "
        "La IA arma tu perfil y después podés corregir lo que quieras."
    )
    descripcion = st.text_area(
        "Tu hogar y estilo de vida:",
        placeholder="Ej: Vivo en un departamento con mi pareja, sin chicos. Tenemos un gato. "
        "Trabajo fuera 8 horas y salgo a caminar todos los días...",
        height=150,
    )
    if st.button("Analizar con IA", type="primary") and descripcion:
        try:
            with st.spinner("Analizando tu descripción..."):
                perfil = extract_perfil_adoptante(descripcion)
            st.session_state["perfil_adoptante_extraido"] = perfil.model_dump()
        except ExtractionError:
            # NFR-A2: degradación elegante — formulario vacío, carga manual,
            # el texto original no se pierde.
            st.error("La IA no pudo procesar tu descripción — completá el formulario a mano.")
            st.session_state["perfil_adoptante_extraido"] = {}
        st.session_state["descripcion_adoptante"] = descripcion
        st.rerun()
    st.stop()

# Valores iniciales: fila existente > extracción recién hecha > defaults
extraido = st.session_state.get("perfil_adoptante_extraido", {})
base = perfil_db or extraido
if perfil_db:
    st.info("Este es tu perfil guardado. Podés corregirlo y volver a guardar.")
else:
    st.success("¡Listo! Revisá lo que entendió la IA y corregí lo que haga falta.")


def _idx(opciones: list[str], valor) -> int:
    return opciones.index(valor) if valor in opciones else 0


with st.form("perfil_adoptante"):
    nombre = st.text_input("Tu nombre", value=base.get("nombre") or "")
    col1, col2 = st.columns(2)
    with col1:
        tipo_vivienda = st.selectbox(
            "Tipo de vivienda", VIVIENDAS, index=_idx(VIVIENDAS, base.get("tipo_vivienda"))
        )
        nivel_actividad = st.selectbox(
            "Tu nivel de actividad", NIVELES, index=_idx(NIVELES, base.get("nivel_actividad"))
        )
        experiencia = st.selectbox(
            "Experiencia con perros",
            EXPERIENCIAS,
            index=_idx(EXPERIENCIAS, base.get("experiencia")),
        )
        horas_fuera = st.number_input(
            "Horas fuera de casa por día",
            min_value=0,
            max_value=24,
            value=int(base.get("horas_fuera") or 4),
        )
    with col2:
        tiene_patio = st.checkbox("Tengo patio", value=bool(base.get("tiene_patio")))
        tiene_ninos = st.checkbox("Hay niños en casa", value=bool(base.get("tiene_ninos")))
        tiene_gatos = st.checkbox("Tengo gatos", value=bool(base.get("tiene_gatos")))
        tiene_perros = st.checkbox("Tengo perros", value=bool(base.get("tiene_perros")))
        acepta_notificaciones = st.checkbox(
            "Quiero recibir avisos de matches por email",
            value=bool(base.get("acepta_notificaciones", True)),
        )
    guardar = st.form_submit_button("Guardar perfil", type="primary")

if guardar:
    if not nombre.strip():
        st.error("Contanos tu nombre para completar el perfil.")
        st.stop()
    datos = {
        "nombre": nombre.strip(),
        "tipo_vivienda": tipo_vivienda,
        "tiene_patio": tiene_patio,
        "tiene_ninos": tiene_ninos,
        "tiene_gatos": tiene_gatos,
        "tiene_perros": tiene_perros,
        "horas_fuera": int(horas_fuera),
        "nivel_actividad": nivel_actividad,
        "experiencia": experiencia,
        "acepta_notificaciones": acepta_notificaciones,
    }
    if perfil_db is None:
        datos.update(
            user_id=sesion["user_id"],
            email=sesion["email"],
            descripcion_original=st.session_state.get("descripcion_adoptante", ""),
        )
    try:
        guardar_adoptante(client, datos, adoptante_id=perfil_db["id"] if perfil_db else None)
    except Exception as e:
        st.error(f"No se pudo guardar el perfil: {e}")
        st.stop()
    st.session_state.pop("perfil_adoptante_extraido", None)
    st.session_state.pop("descripcion_adoptante", None)
    st.success("¡Perfil guardado! El refugio ya puede tenerte en cuenta para futuros matches.")
    st.balloons()

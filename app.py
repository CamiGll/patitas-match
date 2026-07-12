import streamlit as st

from src import auth
from src.db import find_perro_reciente, get_adoptantes, insert_matches, insert_perro
from src.extraction import ExtractionError, extract_perfil_perro
from src.matching import score_match

st.set_page_config(page_title="Patitas Match", page_icon="🐾", layout="centered")
auth.sidebar_user()
auth.require_staff()  # el registro de perros es solo para staff (plan-01 tarea 5)

st.title("🐾 Patitas Match")
st.subheader("Registro de perritos rescatados")
st.write("Ingresa la reseña informal. El sistema extraerá las variables con IA, creará el registro en la base de datos y calculará la afinidad con los postulantes reales.")

st.markdown("---")

descripcion = st.text_area(
    "Historia clínica/informal del rescatado:",
    placeholder="Ej: Encontramos a ramiro deambulando. Es un viejito de 9 años super tranquilo (energía baja). No tiene paciencia para nenes pero se lleva de diez con gatos. Ideal departamento.",
    height=150
)

if st.button("Analizar y Buscar Adoptantes", type="primary"):
    if descripcion:
        st.session_state.pop("confirmar_duplicado", None)

        # ① Extracción con IA
        with st.spinner("① Analizando texto con Google Gemini..."):
            try:
                perfil = extract_perfil_perro(descripcion)
            except ExtractionError as e:
                st.error(f"① La extracción con IA falló y no se registró nada. Detalle: {e}")
                st.stop()

        # El perfil pendiente sobrevive al rerun del checkbox anti-duplicados
        st.session_state["perfil"] = perfil.model_dump()
        st.session_state["descripcion"] = descripcion

if "perfil" in st.session_state:
    datos_perro = st.session_state["perfil"]

    st.success("¡Ficha técnica estructurada por IA correctamente!")
    st.json(datos_perro)

    # Cliente con el JWT del staff: las políticas RLS de staff permiten
    # escribir perros/matches y leer todos los adoptantes.
    supabase = auth.get_user_client()

    # Guardia anti-duplicados: mismo nombre registrado hace <10 minutos
    try:
        existente = find_perro_reciente(supabase, datos_perro["nombre"])
    except Exception as e:
        st.error(f"② No se pudo consultar la base de datos: {e}")
        st.stop()

    if existente:
        st.warning(
            f"Ya existe un perro llamado **{datos_perro['nombre']}** registrado hace "
            f"menos de 10 minutos (ID: {existente['id']}). ¿Es un duplicado?"
        )
        if not st.checkbox("Registrar de todos modos", key="confirmar_duplicado"):
            st.stop()

    # ② Guardar el perro
    with st.spinner("② Guardando en la base de datos..."):
        try:
            nuevo_perro_id = insert_perro(supabase, {
                "nombre": datos_perro["nombre"],
                "descripcion_original": st.session_state["descripcion"],
                "edad": datos_perro["edad"],
                "energia": datos_perro["energia"],
                "necesita_patio": datos_perro["necesita_patio"],
                "apto_ninos": datos_perro["apto_ninos"],
                "apto_gatos": datos_perro["apto_gatos"],
            })
        except Exception as e:
            st.error(f"② No se pudo guardar el perro; no se registró nada. Detalle: {e}")
            st.stop()

    st.success(f"¡Registro persistido en la nube! ID de Mascota: {nuevo_perro_id}")

    # ③ Matching
    st.markdown("### 🏆 Panel de Decisiones Automatizado")
    st.write(f"Evaluando adoptantes para **{datos_perro['nombre'].capitalize()}**...")

    with st.spinner("③ Calculando afinidades..."):
        try:
            adoptantes = get_adoptantes(supabase)

            filas_matches = []
            resultados_visuales = []
            for adoptante in adoptantes:
                resultado = score_match(datos_perro, adoptante)
                filas_matches.append({
                    "perro_id": nuevo_perro_id,
                    "adoptante_id": adoptante["id"],
                    "porcentaje_afinidad": resultado.afinidad,
                    "apto": resultado.apto,
                    "motivo": resultado.motivo,
                })
                resultados_visuales.append({
                    "Adoptante": f"{adoptante['nombre']} (ID: {adoptante['id']})",
                    "Afinidad": f"{resultado.afinidad}%",
                    "Estado": "✅ Apto" if resultado.apto else "❌ Descartado",
                    "Motivo": resultado.motivo,
                })

            insert_matches(supabase, filas_matches)
        except Exception as e:
            st.error(f"③ El matching falló (el perro sí quedó registrado con ID {nuevo_perro_id}). Detalle: {e}")
            st.stop()

    st.table(resultados_visuales)

    # Flujo completado: limpiar el estado pendiente para no re-insertar en el próximo rerun
    del st.session_state["perfil"]
    del st.session_state["descripcion"]

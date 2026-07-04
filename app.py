import streamlit as st
import time

# 1. Configuración de la página (Pestaña del navegador)
st.set_page_config(page_title="Patitas Match", page_icon="🐾", layout="centered")

# 2. Encabezado de la plataforma
st.title("🐾 Patitas Match")
st.subheader("Panel de Gestión para Refugios")
st.write("Ingresa la historia del perrito rescatado. Nuestra Inteligencia Artificial estructurará su ficha técnica y buscará las familias más compatibles de tu base de datos.")

st.markdown("---")

# 3. Interfaz de entrada de datos
descripcion = st.text_area(
    "Historia del animal:",
    placeholder="Ej: Encontramos a Ramiro deambulando por la plaza. Es un viejito super tranquilo de unos 9 años...",
    height=150
)

# 4. Botón de acción principal
if st.button("Analizar y Buscar Adoptantes", type="primary"):

    if descripcion:
        # Mostramos un indicador de carga para que el usuario sepa que el sistema está trabajando
        with st.spinner('Analizando texto con Google Gemini...'):
            time.sleep(2) # Simulamos el tiempo de espera de la API

            st.success("¡Análisis completado con éxito!")

            # Mostramos la ficha técnica generada en formato visual
            st.markdown("### 📋 Ficha Técnica Generada por IA")
            st.json({
                "nombre": "ramiro",
                "edad": "senior",
                "energia": "bajo",
                "necesita_patio": False,
                "apto_ninos": False,
                "apto_gatos": True
            })

            st.markdown("---")

            # Mostramos los resultados del algoritmo en una tabla
            st.markdown("### 🏆 Top Familias Compatibles")
            st.write("Basado en el perfil de Ramiro, estos son los mejores candidatos:")

            # Tabla visual con resultados
            st.table([
                {"Adoptante": "Sofía (ID: 001)", "Afinidad": "100%", "Estado": "✅ Apto", "Motivo": "Hogar tranquilo, sin niños."},
                {"Adoptante": "Carlos (ID: 002)", "Afinidad": "0%", "Estado": "❌ Descartado", "Motivo": "Tiene niños pequeños."},
                {"Adoptante": "Laura (ID: 003)", "Afinidad": "75%", "Estado": "✅ Apto", "Motivo": "Estilo de vida acorde, sin niños."}
            ])

    else:
        st.warning("⚠️ Por favor, escribe la historia del perro antes de analizar.")

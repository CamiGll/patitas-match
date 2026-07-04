import streamlit as st
import json
from google import genai
from pydantic import BaseModel, Field
from supabase import create_client, Client

# --- 1. CONFIGURACIÓN DE SECRETOS ---
# Esto reemplaza al mock conectándose a tus servicios reales
supabase: Client = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
gemini_client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])

# --- 2. ESQUEMA DE IA ---
class PerfilPerro(BaseModel):
    nombre: str = Field(description="Nombre del perro en minúsculas")
    edad: str = Field(description="cachorro, adulto o senior")
    energia: str = Field(description="alto, medio o bajo")
    necesita_patio: bool
    apto_ninos: bool
    apto_gatos: bool

# ... (Tu código de interfaz de Streamlit actual: título, text_area, etc) ...

if st.button("Analizar y Buscar Adoptantes", type="primary"):
    if descripcion:
        with st.spinner('Analizando texto con Google Gemini...'):
            
            # A. LLAMADA REAL A LA IA
            response = gemini_client.models.generate_content(
                model='gemini-2.5-flash',
                contents=descripcion,
                config={
                    'response_mime_type': 'application/json',
                    'response_schema': PerfilPerro,
                    'temperature': 0.1,
                },
            )
            
            # Convertimos la respuesta de texto a un diccionario de Python
            datos_perro = json.loads(response.text)
            
            # Mostramos en pantalla el resultado REAL, no el fijo
            st.success("¡Ficha técnica estructurada por IA correctamente!")
            st.json(datos_perro)
            
            # B. INSERCIÓN REAL EN LA BASE DE DATOS
            # Preparamos el diccionario con los datos limpios de Gemini + la descripción original
            datos_insertar = {
                "nombre": datos_perro["nombre"],
                "descripcion_original": descripcion,
                "edad": datos_perro["edad"],
                "energia": datos_perro["energia"],
                "necesita_patio": datos_perro["necesita_patio"],
                "apto_ninos": datos_perro["apto_ninos"],
                "apto_gatos": datos_perro["apto_gatos"]
            }
            
            # Ejecutamos la inserción
            res_perro = supabase.table('perros').insert(datos_insertar).execute()
            
            # Extraemos el ID del registro recién creado
            nuevo_perro_id = res_perro.data[0]["id"]
            st.success(f"¡Registro persistido en la nube! ID de Mascota: {nuevo_perro_id}")

            # C. MOTOR DE MATCHING
            st.markdown("### 🏆 Panel de Decisiones Automatizado")
            st.write(f"Evaluando adoptantes para **{datos_perro['nombre'].capitalize()}**...")

            # 1. Traemos a todos los adoptantes de la base de datos
            adoptantes_db = supabase.table("adoptantes").select("*").execute()
            adoptantes = adoptantes_db.data
            
            resultados_visuales = []

            # 2. Iteramos sobre cada adoptante para calcular el score
            for adoptante in adoptantes:
                afinidad = 100
                apto = True
                motivo = []
                
                # Reglas Excluyentes (Hard Blocks)
                if datos_perro["apto_ninos"] == False and adoptante["tiene_ninos"] == True:
                    apto = False
                    afinidad = 0
                    motivo.append("No compatible con niños.")
                
                if datos_perro["apto_gatos"] == False and adoptante["tiene_gatos"] == True:
                    apto = False
                    afinidad = 0
                    motivo.append("No compatible con gatos.")
                
                # Penalizaciones (Soft Blocks) - Solo si superó los filtros excluyentes
                if apto:
                    if datos_perro["necesita_patio"] == True and adoptante["tipo_vivienda"] == "departamento":
                        afinidad -= 30
                        motivo.append("Penalización: Sin patio.")
                    
                    if datos_perro["energia"] == "alto" and adoptante["tipo_vivienda"] == "departamento":
                        afinidad -= 20
                        motivo.append("Penalización: Departamento para alta energía.")
                    
                    if len(motivo) == 0:
                        motivo.append("Estilo de vida acorde.")
                
                # 3. Formateamos el motivo final
                motivo_texto = " ".join(motivo)
                
                # 4. Guardamos el resultado del cruce en el historial de Supabase
                supabase.table("historial_matches").insert({
                    "perro_id": nuevo_perro_id,
                    "adoptante_id": adoptante["id"],
                    "porcentaje_afinidad": afinidad,
                    "apto": apto,
                    "motivo": motivo_texto
                }).execute()
                
                # 5. Agregamos la fila formateada para mostrar en Streamlit
                estado_visual = "✅ Apto" if apto else "❌ Descartado"
                resultados_visuales.append({
                    "Adoptante": f"{adoptante['nombre']} (ID: {adoptante['id']})",
                    "Afinidad": f"{afinidad}%",
                    "Estado": estado_visual,
                    "Motivo": motivo_texto
                })
                
            # Mostramos la tabla dinámica final en la web
            st.table(resultados_visuales)

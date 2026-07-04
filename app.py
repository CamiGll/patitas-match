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
            res_perro = supabase.table('perros').insert(nuevo_perro).execute()
             
            # C. MOTOR DE MATCHING
            nuevo_perro_id = respuesta_db.data[0]["id"]
            st.success(f"¡Registro persistido en la nube! ID de Mascota: {nuevo_perro_id}")

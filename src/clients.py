import streamlit as st
from google import genai
from supabase import Client, create_client

# El estado de auth de un Client de supabase es mutable, así que los clientes
# que llevan sesión de usuario NUNCA se cachean ni se comparten entre sesiones
# de Streamlit. Solo el cliente de Gemini (sin estado por usuario) se cachea,
# con la credencial como argumento para que rotar la clave invalide el cache.


@st.cache_resource
def _gemini(api_key: str) -> genai.Client:
    return genai.Client(api_key=api_key)


def get_gemini() -> genai.Client:
    return _gemini(st.secrets["GEMINI_API_KEY"])


def anon_client() -> Client:
    """Cliente fresco con la anon key — para signup/login. Con RLS activo no ve datos."""
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])


def user_client(access_token: str) -> Client:
    """Cliente que consulta PostgREST con el JWT del usuario: RLS aplica sus políticas."""
    client = anon_client()
    client.postgrest.auth(access_token)
    return client


def service_client() -> Client:
    """Cliente service-role: salta RLS. Solo invocable desde rutas staff (plan-01 tarea 5)."""
    if not st.session_state.get("es_staff"):
        raise PermissionError(
            "service_client() solo puede usarse desde código protegido por require_staff()"
        )
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_SERVICE_KEY"])

import streamlit as st
from google import genai
from supabase import Client, create_client

# Los factories cacheados reciben las credenciales como argumento para que el
# cache se invalide solo si cambian los secretos (rotar una clave no debe
# requerir reiniciar la app).


@st.cache_resource
def _supabase(url: str, key: str) -> Client:
    return create_client(url, key)


@st.cache_resource
def _gemini(api_key: str) -> genai.Client:
    return genai.Client(api_key=api_key)


def get_supabase() -> Client:
    return _supabase(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])


def get_gemini() -> genai.Client:
    return _gemini(st.secrets["GEMINI_API_KEY"])

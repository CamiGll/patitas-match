import streamlit as st
from google import genai
from supabase import Client, create_client


@st.cache_resource
def get_supabase() -> Client:
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])


@st.cache_resource
def get_gemini() -> genai.Client:
    return genai.Client(api_key=st.secrets["GEMINI_API_KEY"])

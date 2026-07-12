import streamlit as st

from src import auth

st.set_page_config(page_title="Ingresar — Patitas Match", page_icon="🔑", layout="centered")
auth.sidebar_user()

st.title("🔑 Ingresar")

if auth.current_user():
    st.success(f"Ya estás conectada/o como {auth.current_user()['email']}.")
    st.page_link("pages/2_Mi_Perfil.py", label="Ir a Mi Perfil", icon="🏠")
    st.stop()

tab_login, tab_signup = st.tabs(["Iniciar sesión", "Crear cuenta"])

with tab_login:
    with st.form("login"):
        email = st.text_input("Email")
        password = st.text_input("Contraseña", type="password")
        enviar = st.form_submit_button("Iniciar sesión", type="primary")
    if enviar:
        try:
            auth.sign_in(email.strip(), password)
            st.rerun()
        except Exception as e:
            msg = str(e)
            if "Invalid login credentials" in msg:
                st.error("Email o contraseña incorrectos.")
            elif "Email not confirmed" in msg:
                st.error("Tu email todavía no está confirmado — revisá tu casilla (y spam).")
            else:
                st.error(f"No se pudo iniciar sesión: {msg}")

with tab_signup:
    st.write("Creá tu cuenta de adoptante. Después vas a completar tu perfil de hogar.")
    with st.form("signup"):
        email_s = st.text_input("Email", key="su_email")
        password_s = st.text_input("Contraseña (mínimo 6 caracteres)", type="password", key="su_pwd")
        crear = st.form_submit_button("Crear cuenta", type="primary")
    if crear:
        try:
            auth.sign_up(email_s.strip(), password_s)
            # La confirmación por email está activada en Supabase Auth (default):
            # el usuario debe confirmar antes de poder iniciar sesión.
            st.success(
                "¡Cuenta creada! Te enviamos un email de confirmación — "
                "abrí el link y después iniciá sesión acá."
            )
        except Exception as e:
            msg = str(e)
            if "already registered" in msg.lower():
                st.error("Ese email ya tiene una cuenta. Probá iniciar sesión.")
            elif "at least 6 characters" in msg:
                st.error("La contraseña debe tener al menos 6 caracteres.")
            else:
                st.error(f"No se pudo crear la cuenta: {msg}")

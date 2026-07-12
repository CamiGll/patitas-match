"""Sesión y guardas de acceso. La sesión (tokens) vive en st.session_state."""

import time

import streamlit as st
from supabase import Client

from src.clients import anon_client, user_client

SESSION_KEY = "sb_session"


def sign_up(email: str, password: str):
    return anon_client().auth.sign_up({"email": email, "password": password})


def sign_in(email: str, password: str) -> None:
    res = anon_client().auth.sign_in_with_password({"email": email, "password": password})
    st.session_state[SESSION_KEY] = {
        "access_token": res.session.access_token,
        "refresh_token": res.session.refresh_token,
        "expires_at": res.session.expires_at,
        "user_id": res.user.id,
        "email": res.user.email,
    }
    st.session_state.pop("es_staff", None)


def sign_out() -> None:
    st.session_state.pop(SESSION_KEY, None)
    st.session_state.pop("es_staff", None)


def current_user() -> dict | None:
    return st.session_state.get(SESSION_KEY)


def _session_valida() -> dict | None:
    """Devuelve la sesión, refrescando el token si está por vencer (lazy refresh)."""
    sesion = st.session_state.get(SESSION_KEY)
    if not sesion:
        return None
    if sesion["expires_at"] and sesion["expires_at"] - time.time() < 60:
        try:
            res = anon_client().auth.refresh_session(sesion["refresh_token"])
            sesion.update(
                access_token=res.session.access_token,
                refresh_token=res.session.refresh_token,
                expires_at=res.session.expires_at,
            )
        except Exception:
            sign_out()
            return None
    return sesion


def get_user_client() -> Client:
    sesion = _session_valida()
    if not sesion:
        raise RuntimeError("No hay sesión activa; usar require_login() antes.")
    return user_client(sesion["access_token"])


def require_login() -> None:
    if not _session_valida():
        st.warning("Necesitás iniciar sesión para ver esta página.")
        st.page_link("pages/1_Ingresar.py", label="Ir a Ingresar", icon="🔑")
        st.stop()


def is_staff() -> bool:
    if "es_staff" not in st.session_state:
        sesion = _session_valida()
        if not sesion:
            return False
        res = (
            get_user_client()
            .table("profiles_staff")
            .select("user_id")
            .eq("user_id", sesion["user_id"])
            .execute()
        )
        st.session_state["es_staff"] = bool(res.data)
    return st.session_state["es_staff"]


def require_staff() -> None:
    require_login()
    if not is_staff():
        st.error("Esta sección es solo para el staff del refugio.")
        st.page_link("pages/2_Mi_Perfil.py", label="Ir a Mi Perfil", icon="🏠")
        st.stop()


def sidebar_user() -> None:
    """Sidebar compartido: email conectado + logout, o link a Ingresar."""
    sesion = current_user()
    with st.sidebar:
        if sesion:
            st.caption(f"Conectada/o: {sesion['email']}")
            if st.button("Cerrar sesión"):
                sign_out()
                st.rerun()
        else:
            st.page_link("pages/1_Ingresar.py", label="Ingresar / Crear cuenta", icon="🔑")

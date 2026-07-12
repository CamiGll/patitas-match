from datetime import datetime, timedelta, timezone

from supabase import Client


def find_perro_reciente(client: Client, nombre: str, minutos: int = 10) -> dict | None:
    """Busca un perro con el mismo nombre creado en los últimos `minutos` (guardia anti-duplicados)."""
    limite = (datetime.now(timezone.utc) - timedelta(minutes=minutos)).isoformat()
    res = (
        client.table("perros")
        .select("id, nombre, creado_en")
        .eq("nombre", nombre)
        .gte("creado_en", limite)
        .limit(1)
        .execute()
    )
    return res.data[0] if res.data else None


def insert_perro(client: Client, datos: dict) -> int:
    res = client.table("perros").insert(datos).execute()
    return res.data[0]["id"]


def get_adoptantes(client: Client) -> list[dict]:
    return client.table("adoptantes").select("*").execute().data


def insert_matches(client: Client, rows: list[dict]) -> None:
    """Inserta todos los matches en una sola llamada (sin N+1)."""
    if rows:
        client.table("historial_matches").insert(rows).execute()

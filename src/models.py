from pydantic import BaseModel, Field


class PerfilPerro(BaseModel):
    nombre: str = Field(description="Nombre del perro en minúsculas")
    edad: str = Field(description="cachorro, adulto o senior")
    energia: str = Field(description="alto, medio o bajo")
    necesita_patio: bool
    apto_ninos: bool
    apto_gatos: bool

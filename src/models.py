from typing import Literal

from pydantic import BaseModel, Field


class PerfilPerro(BaseModel):
    nombre: str = Field(description="Nombre del perro en minúsculas")
    edad: Literal["cachorro", "adulto", "senior"]
    energia: Literal["alto", "medio", "bajo"]
    necesita_patio: bool
    apto_ninos: bool
    apto_gatos: bool


class PerfilAdoptante(BaseModel):
    tipo_vivienda: Literal["casa", "departamento"]
    tiene_patio: bool
    tiene_ninos: bool
    tiene_gatos: bool
    tiene_perros: bool = Field(description="Si tiene perros actualmente (no en el pasado)")
    horas_fuera: int = Field(ge=0, le=24, description="Horas por día fuera de casa")
    nivel_actividad: Literal["alto", "medio", "bajo"]
    experiencia: Literal["ninguna", "algo", "mucha"] = Field(
        description="Experiencia previa teniendo perros"
    )

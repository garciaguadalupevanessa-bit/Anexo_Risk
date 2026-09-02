"""
services.py

LÃ³gica de negocio y procesamiento para el mÃ³dulo de necesidades.

Esta capa conecta las rutas HTTP con la persistencia (models.py) y
centraliza las reglas de negocio, como:
- generaciÃ³n del tÃ­tulo por defecto;
- limpieza y truncado de direcciÃ³n;
- cambios de estado.
"""

from typing import Any, Optional

from modules.necesidades import models
from modules.necesidades.schemas import NeedCreate, NeedStatus, NeedType


# La ruta importa esta excepciÃ³n desde services.py.
# Reutilizamos la misma excepciÃ³n que utiliza models.py para que
# routes.py pueda capturarla correctamente.
InvalidStatusTransition = models.InvalidStatusTransition


LIMITES_LONGITUD = {
    "TITULO_MAX": 100,
    "DIRECCION_MAX": 300,
}


ETIQUETAS_CATEGORIA = {
    "agua": "ðŸ’§ Agua",
    "alimentos": "ðŸž Alimentos",
    "parafarmacia": "ðŸ’Š Parafarmacia",
    "ropa": "ðŸ‘• Ropa",
    "higiene": "ðŸ§´ Higiene",
    "refugio": "ðŸ  Refugio",
    "transporte": "ðŸš— Transporte",
    "otros": "ðŸ“¦ Otros",
}


def _extraer_valor(obj: Any, *claves: str, defecto: Any = None) -> Any:
    """Obtiene el primer campo disponible desde Pydantic o diccionario."""

    for clave in claves:
        if isinstance(obj, dict):
            if clave in obj and obj[clave] is not None:
                return obj[clave]

        elif hasattr(obj, clave):
            valor = getattr(obj, clave, None)
            if valor is not None:
                return valor

    return defecto


def truncar_texto(texto: Optional[str], max_len: int = 300) -> str:
    """Limpia espacios laterales y limita el texto a max_len caracteres."""

    if not texto:
        return ""

    return str(texto).strip()[:max_len]


def generar_titulo_predeterminado(tipo: str) -> str:
    """Genera un título automático basado en el valor de la categoría."""
    tipo_norm = (tipo or "otros").lower()
    return f"Necesidad de {tipo_norm}"


def procesar_datos_necesidad(datos: Any) -> dict[str, Any]:
    """
    Extrae, limpia y normaliza los datos de una necesidad.

    Es compatible tanto con objetos Pydantic como con diccionarios.
    """

    tipo = _extraer_valor(
        datos,
        "tipo",
        "need_type",
        "type",
        defecto="otros",
    )

    # Pydantic puede proporcionar el enum NeedType, mientras que un
    # diccionario puede proporcionar directamente el string.
    if isinstance(tipo, NeedType):
        tipo = tipo.value

    tipo = str(tipo).lower()

    titulo_raw = _extraer_valor(
        datos,
        "titulo",
        "title",
        defecto="",
    )

    if not titulo_raw or not str(titulo_raw).strip():
        titulo = generar_titulo_predeterminado(tipo)
    else:
        titulo = truncar_texto(
            str(titulo_raw),
            LIMITES_LONGITUD["TITULO_MAX"],
        )

    direccion_raw = _extraer_valor(
        datos,
        "direccion",
        "address",
        defecto="",
    )

    direccion = truncar_texto(
        direccion_raw,
        LIMITES_LONGITUD["DIRECCION_MAX"],
    )

    descripcion = _extraer_valor(
        datos,
        "descripcion",
        "description",
        defecto="",
    )

    if descripcion:
        descripcion = str(descripcion).strip()

    prioridad = _extraer_valor(
        datos,
        "prioridad",
        "priority",
        defecto="media",
    )

    if hasattr(prioridad, "value"):
        prioridad = prioridad.value

    estado = _extraer_valor(
        datos,
        "estado",
        "status",
        defecto="abierta",
    )

    if hasattr(estado, "value"):
        estado = estado.value

    latitud = float(
        _extraer_valor(
            datos,
            "latitud",
            "latitude",
            "lat",
            defecto=0.0,
        )
    )

    longitud = float(
        _extraer_valor(
            datos,
            "longitud",
            "longitude",
            "lng",
            "lon",
            defecto=0.0,
        )
    )

    return {
        "titulo": titulo,
        "tipo": tipo,
        "descripcion": descripcion,
        "direccion": direccion,
        "latitud": latitud,
        "longitud": longitud,
        "prioridad": prioridad,
        "estado": estado,
        "categoria_etiqueta": ETIQUETAS_CATEGORIA.get(
            tipo,
            ETIQUETAS_CATEGORIA["otros"],
        ),
    }


def create_need(need: NeedCreate) -> dict[str, Any]:
    """
    Crea una necesidad aplicando las reglas de negocio.

    El tÃ­tulo vacÃ­o se genera automÃ¡ticamente y la direcciÃ³n se limita
    a 300 caracteres antes de pasar los datos a la persistencia.
    """

    datos = procesar_datos_necesidad(need)

    # Reconstruimos NeedCreate para mantener la validaciÃ³n del esquema
    # antes de llegar a models.py.
    need_normalizada = NeedCreate(
        titulo=datos["titulo"],
        tipo=datos["tipo"],
        descripcion=datos["descripcion"],
        direccion=datos["direccion"],
        latitud=datos["latitud"],
        longitud=datos["longitud"],
        prioridad=datos["prioridad"],
    )

    return models.create_need(need_normalizada)


def get_need(need_id: int) -> dict[str, Any] | None:
    """Obtiene una necesidad por su identificador."""

    return models.get_need(need_id)


def list_needs(
    status: NeedStatus | None = None,
    need_type: NeedType | None = None,
) -> list[dict[str, Any]]:
    """Lista necesidades con filtros opcionales."""

    return models.list_needs(
        status=status,
        need_type=need_type,
    )


def update_need_status(
    need_id: int,
    status: NeedStatus,
) -> dict[str, Any] | None:
    """
    Cambia el estado de una necesidad.

    La validaciÃ³n de la transiciÃ³n se realiza en models.py, donde se
    mantiene la regla abierta -> cubierta.
    """

    return models.update_need_status(
        need_id=need_id,
        status=status,
    )


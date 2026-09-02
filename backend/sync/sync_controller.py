"""Sincronización del modo offline (Equipo 4, siguiente prioridad).

Router mínimo de la base común. TODO (Equipo 4): recibir las acciones
guardadas offline por el frontend (ver
frontend/js/siguiente/modo-offline/syncQueue.js) y aplicarlas sobre los
modelos de cada módulo (necesidades, voluntariado, donaciones, personas).
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Dict, Any
import sqlite3
from sync.services import process_sync_batch
from config import DATABASE_PATH

router = APIRouter(prefix="/api/sync", tags=["Offline Sync"])


def get_db():
    conn = sqlite3.connect(DATABASE_PATH)
    try:
        yield conn
    finally:
        conn.close()


class SyncOperation(BaseModel):
    operation_id: str
    entity_type: str
    entity_id: str
    operation_type: str
    payload: Dict[str, Any]
    client_created_at: str


class SyncBatchRequest(BaseModel):
    operations: List[SyncOperation]


class SyncResult(BaseModel):
    operation_id: str
    status: str


class SyncBatchResponse(BaseModel):
    results: List[SyncResult]


@router.post("/batch", response_model=SyncBatchResponse)
def sync_offline_batch(request: SyncBatchRequest, db: sqlite3.Connection = Depends(get_db)):
    """Recibe un lote de operaciones offline, las procesa y devuelve el estado de cada una."""
    try:
        operations_dict_list = [op.model_dump() for op in request.operations]
        results = process_sync_batch(db, operations_dict_list)
        return {"results": results}
    except Exception:
        raise HTTPException(status_code=500, detail="Error interno en sync batch.")

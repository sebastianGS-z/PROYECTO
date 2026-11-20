"""Regresiones de las rutas optimizadas del pipeline E3."""
from datetime import datetime

import pandas as pd

from src.tdl_e1.pipeline import _empty_record, puerta_calidad, resolver_duplicados


def test_resolucion_rapida_preserva_orden_si_no_hay_claves_duplicadas():
    frame = pd.DataFrame([_record(1, "2026-01-02"), _record(2, "2026-01-01")])
    result, conflicts = resolver_duplicados(frame)
    assert result["source_record_index"].tolist() == [1, 2]
    assert conflicts == []


def test_reglas_vectorizadas_envian_fila_invalida_a_cuarentena():
    record = _record(1, "2026-01-02")
    record.update({"precio_min": 12.0, "precio_max": 10.0, "precio_frecuente": 9.0})
    valid, quarantine = puerta_calidad(pd.DataFrame([record]), [])
    assert valid.empty
    assert len(quarantine) == 1
    assert "precio_min mayor que precio_max" in quarantine[0]["motivo"]
    assert "precio_frecuente menor que precio_min" in quarantine[0]["motivo"]


def _record(index: int, day: str) -> dict:
    record = _empty_record()
    record.update({
        "fecha": datetime.fromisoformat(day), "fuente": "sniim", "tipo_registro": "precio",
        "cultivo": "limon", "variante": "Limón", "variante_id": "1", "mercado": "100",
        "origen": "Colima", "presentacion": "kg", "source_file": f"data/bronce/{index}.html",
        "source_sha256": "a" * 64, "capturado_en": "2026-01-03T00:00:00Z",
        "source_record_index": index,
    })
    return record

import csv
from datetime import date, timedelta

import pytest

from calidad import psp
from calidad.psp import PspError

HOY = date.today().isoformat()


def test_cuatro_csv_con_encabezados_exactos():
    base = psp.CALIDAD_DIR
    for n in (1, 2):
        assert open(base / f"tiempo-integrante{n}.csv", encoding="utf-8").readline().strip() == ",".join(psp.COLUMNAS_TIEMPO)
        assert open(base / f"defectos-integrante{n}.csv", encoding="utf-8").readline().strip() == ",".join(psp.COLUMNAS_DEFECTOS)
    assert psp.COLUMNAS_TIEMPO == ["fecha", "inicio", "fin", "interrupcion_min", "fase", "actividad"]


def test_catalogo_tiene_los_10_tipos_psp_del_kit():
    cat = psp.cargar_catalogo()
    assert sorted(cat) == sorted(["documentacion", "sintaxis", "construccion", "asignacion", "interfaz", "verificacion", "datos", "funcion", "sistema", "entorno"])


def test_tiempo_neto_descuenta_interrupciones():
    assert psp.minutos_netos("09:00", "10:30", 10) == 80
    assert psp.minutos_netos("09:00", "09:30", 0) == 30


@pytest.mark.parametrize("ini,fin,inter", [("10:00", "09:00", 0), ("09:00", "09:30", 45), ("09:00", "10:00", -1)])
def test_tiempo_invalido(ini, fin, inter):
    with pytest.raises(PspError):
        psp.minutos_netos(ini, fin, inter)


def test_agregar_tiempo_y_resumen(tmp_path):
    f = tmp_path / "t.csv"
    f.write_text(",".join(psp.COLUMNAS_TIEMPO) + "\n", encoding="utf-8")
    psp.agregar_tiempo(f, HOY, "09:00", "10:30", 10, "codificacion", "Extractor base")
    psp.agregar_tiempo(f, HOY, "11:00", "11:30", 0, "Pruebas", "pytest")
    filas = list(csv.DictReader(f.open(encoding="utf-8")))
    assert filas[0]["fase"] == "codigo" and len(filas) == 2
    r = psp.resumen_tiempo(f)
    assert r["codigo"] == 80 and r["pruebas"] == 30 and r["TOTAL"] == 110


def test_fase_no_reconocida_y_fecha_incorrecta(tmp_path):
    f = tmp_path / "t.csv"
    with pytest.raises(PspError, match="Fase"):
        psp.agregar_tiempo(f, HOY, "09:00", "10:00", 0, "Vacaciones", "x")
    with pytest.raises(PspError, match="Fecha"):
        psp.agregar_tiempo(f, "2026-13-45", "09:00", "10:00", 0, "Pruebas", "x")
    with pytest.raises(PspError, match="futura"):
        psp.agregar_tiempo(f, (date.today() + timedelta(days=3)).isoformat(), "09:00", "10:00", 0, "Pruebas", "x")
    assert not f.exists()  # un registro inválido no deja rastro


def nuevo_defectos(tmp_path):
    f = tmp_path / "d.csv"
    f.write_text(",".join(psp.COLUMNAS_DEFECTOS) + "\n", encoding="utf-8")
    return f


def test_agregar_defecto_numera_automaticamente(tmp_path):
    f = nuevo_defectos(tmp_path)
    a = psp.agregar_defecto(f, HOY, "datos", "Codificación", "Pruebas", 15, "Parser ignora filas")
    b = psp.agregar_defecto(f, HOY, "funcion", "Codificación", "Pruebas", 5.5, "Sin reintento", defecto_origen="1")
    assert (a["numero"], b["numero"], b["defecto_origen"]) == ("1", "2", "1")
    assert psp.validar_csv_defectos(f) == 2


@pytest.mark.parametrize("kw,msg", [
    ({"tipo": "inventado"}, "inexistente"),
    ({"minutos_correccion": -3}, "negativo"),
    ({"fase_eliminado": "Magia"}, "Fase"),
    ({"fecha": "ayer"}, "Fecha"),
    ({"defecto_origen": "7"}, "defecto_origen"),
])
def test_validaciones_de_defecto(tmp_path, kw, msg):
    f = nuevo_defectos(tmp_path)
    args = dict(fecha=HOY, tipo="funcion", fase_introducido="Diseño", fase_eliminado="Pruebas", minutos_correccion=10, descripcion="x")
    args.update(kw)
    with pytest.raises(PspError, match=msg):
        psp.agregar_defecto(f, **args)


def test_numero_duplicado_rechazado(tmp_path):
    f = nuevo_defectos(tmp_path)
    psp.agregar_defecto(f, HOY, "documentacion", "Planeación", "Diseño", 1, "a", numero=1)
    with pytest.raises(PspError, match="duplicado"):
        psp.agregar_defecto(f, HOY, "documentacion", "Planeación", "Diseño", 1, "b", numero=1)


def test_validar_csv_detecta_duplicados_en_archivo(tmp_path):
    f = nuevo_defectos(tmp_path)
    with f.open("a", encoding="utf-8") as fh:
        fh.write(f"1,{HOY},documentacion,Diseño,Pruebas,3,,a\n1,{HOY},sintaxis,Diseño,Pruebas,3,,b\n")
    with pytest.raises(PspError, match="duplicado"):
        psp.validar_csv_defectos(f)


def test_cli(tmp_path, capsys):
    f = tmp_path / "t.csv"
    code = psp.main(["tiempo", "--archivo", str(f), "--fecha", HOY, "--inicio", "09:00", "--fin", "10:00",
                     "--interrupcion", "5", "--fase", "Revisión", "--actividad", "Revisar"])
    assert code == 0 and "55" in capsys.readouterr().out
    assert psp.main(["tiempo", "--archivo", str(f), "--fecha", HOY, "--inicio", "09:00", "--fin", "10:00",
                     "--fase", "X", "--actividad", "y"]) == 1


def test_fases_estilo_kit_y_sinonimos():
    assert psp.FASES == ["planeacion", "diseno", "codigo", "revision", "compilacion", "pruebas", "correccion", "documentacion"]
    assert psp.normalizar_fase("Codificación") == "codigo" and psp.normalizar_fase("Compilación/Ejecución") == "compilacion"
    assert psp.normalizar_fase("diseno") == "diseno"


def test_plantilla_del_kit_es_valida(tmp_path):
    """Las filas de ejemplo del Kit de arranque deben pasar la validación (con fechas pasadas)."""
    f = nuevo_defectos(tmp_path)
    with f.open("a", encoding="utf-8") as fh:
        fh.write("1,2026-11-03,datos,codigo,pruebas,25,,Precio leido como texto con signo de pesos\n"
                 "2,2026-11-04,interfaz,diseno,revision,10,,API devuelve fechas en UTC\n"
                 "3,2026-11-04,funcion,codigo,codigo,5,2,La correccion del defecto 2 duplico registros\n")
    assert psp.validar_csv_defectos(f) == 3

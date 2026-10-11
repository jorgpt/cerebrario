import builtins
import contextlib
import errno
import io
import json
import os
import pathlib
import shutil
import stat
import sys
import tempfile
import time
import unicodedata
import unittest
from pathlib import Path
from unittest import mock

CARPETA = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(CARPETA))

RAIZ = Path(tempfile.mkdtemp(prefix="pruebas-medico-")) / "Bitácora Claude"
CASA = RAIZ / "casa ñandú"
MEMORIA = CASA / ".claude" / "projects" / "C--demo" / "memory"
DATOS = RAIZ / "datos del médico"
for nombre in [k for k in os.environ if k.startswith("CLAUDE_PLUGIN_") or k == "CLAUDE_ENV_FILE"]:
    del os.environ[nombre]
for carpeta in (MEMORIA, DATOS, CASA / "AppData" / "Roaming"):
    carpeta.mkdir(parents=True, exist_ok=True)
(DATOS / "config.json").write_text(json.dumps({
    "usuario": "Ana",
    "fuentes": [{"id": "memoria", "nombre": "Memoria", "color": "#E64980", "raices": [[str(MEMORIA), False, ""]],
                 "memoria": True}]}, ensure_ascii=False), encoding="utf-8")
os.environ.update(HOME=str(CASA), USERPROFILE=str(CASA), APPDATA=str(CASA / "AppData" / "Roaming"),
                  CLAUDE_CONFIG_DIR=str(CASA / ".claude"), CEREBRO_CONFIG=str(DATOS / "config.json"),
                  PYTHONIOENCODING="utf-8")

import archivos  # noqa: E402
import cerebro as nucleo  # noqa: E402
import hook_choques  # noqa: E402
import medico  # noqa: E402
import ordenar  # noqa: E402
import recetas  # noqa: E402
import reglas  # noqa: E402

SERVIDOR = "servidor-falso.invalid"


def fm(nombre, descripcion):
    return f"---\nname: {nombre}\ndescription: {descripcion}\ntype: project\n---\n\n"


def escribir(nombre, texto, codificacion="utf-8", fin="\n"):
    ruta = MEMORIA / nombre
    ruta.write_bytes(texto.replace("\n", fin).encode(codificacion))
    return ruta


def nota_con_piezas(nombre="bitácora-señales.md", fin="\n"):
    cuerpo = fm(Path(nombre).stem, "Bitácora de señales del proyecto demo con entradas viejas y nuevas") + \
        "# Señales\n\n## Uno\n\nañejo uno\n\n## Dos\n\nañejo dos\n\n## Tres\n\nvigente tres\n"
    return escribir(nombre, cuerpo, fin=fin)


def indice(*notas, extra=0):
    renglones = ["# Índice", ""] + [f"- [{Path(n).stem}]({n}) — gancho de {Path(n).stem}" for n in notas]
    renglones += [f"- renglón de relleno {i}" for i in range(extra)]
    return escribir("MEMORY.md", "\n".join(renglones) + "\n")


def es_red(ruta):
    try:
        texto = os.fspath(ruta)
    except TypeError:
        return False
    if isinstance(texto, bytes):
        texto = texto.decode("utf-8", "replace")
    return texto.strip().replace("/", "\\").startswith("\\\\")


@contextlib.contextmanager
def sin_red():
    tocadas = []

    def envolver(real):
        def falso(ruta, *args, **kwargs):
            if es_red(ruta):
                tocadas.append(os.fspath(ruta))
                raise FileNotFoundError(errno.ENOENT, "prueba: acceso a red bloqueado", os.fspath(ruta))
            return real(ruta, *args, **kwargs)
        return falso

    blancos = [(os, "stat"), (os, "lstat"), (os, "open"), (os, "scandir"), (os, "listdir"), (os.path, "exists"),
               (os.path, "isfile"), (os.path, "isdir"), (os.path, "lexists"), (builtins, "open"), (io, "open")]
    accesor = getattr(pathlib, "_NormalAccessor", None)
    if accesor is not None:
        blancos += [(accesor, a) for a in ("stat", "lstat", "open", "scandir", "listdir") if hasattr(accesor, a)]
    with contextlib.ExitStack() as pila:
        for modulo, atributo in blancos:
            falso = envolver(getattr(modulo, atributo))
            pila.enter_context(mock.patch.object(modulo, atributo, staticmethod(falso) if isinstance(modulo, type) else falso))
        yield tocadas


class Base(unittest.TestCase):
    def setUp(self):
        for hijo in MEMORIA.iterdir():
            shutil.rmtree(hijo) if hijo.is_dir() else hijo.unlink()
        shutil.rmtree(DATOS / ordenar.RESPALDOS, ignore_errors=True)
        nucleo._listados.clear()


ENLACES_DE_RED = [f"[a](//{SERVIDOR}/share/a.md)", f"[b](<\\\\{SERVIDOR}\\share\\b.md>)",
                  f"[e](%5C%5C{SERVIDOR}%5Cshare%5Ce.md)", f"[f](%2F%2F{SERVIDOR}%2Fshare%2Ff.md)",
                  f"[[\\\\{SERVIDOR}\\share\\c]]", f"[[//{SERVIDOR}/share/d]]", f"[g](/\\{SERVIDOR}/share/g.md)",
                  f"[h](file://{SERVIDOR}/share/h.md)", f"[i](\\\\?\\UNC\\{SERVIDOR}\\share\\i.md)",
                  "[j](C:/fuera/de/la/carpeta.md)", "[k](../../../../fuera.md)"]
RUTAS_DE_RED = [f"`\\\\{SERVIDOR}\\share\\x.md`", f"`//{SERVIDOR}/share/y.md`", f"`%5C%5C{SERVIDOR}%5Cs%5Cz.md`",
                f"`file://{SERVIDOR}/s/w.md`"]


class PruebasM1(Base):
    def preparar(self):
        escribir("otra-ñandú.md", fm("otra-ñandú", "Otra nota de la memoria con eñe en el nombre del archivo"))
        texto = "Ver [otra](otra-ñandú.md) y [rota](falta-acción.md).\n" + "\n".join(ENLACES_DE_RED + RUTAS_DE_RED) + "\n"
        nota = escribir("señales.md", fm("señales", "Nota con enlaces sacados de un correo resumido en la memoria") + texto,
                        fin="\r\n")
        indice("señales.md", "otra-ñandú.md")
        return nota, texto

    def test_M1_enlaces_rotos_no_toca_la_red(self):
        nota, texto = self.preparar()
        with sin_red() as tocadas:
            rotos = medico.enlaces_rotos(str(nota), texto)
        self.assertEqual(tocadas, [])
        self.assertIn("falta-acción.md", rotos)
        self.assertNotIn("otra-ñandú.md", rotos)
        self.assertIn(f"//{SERVIDOR}/share/a.md", rotos)

    def test_M1_rutas_rotas_no_toca_la_red(self):
        nota, texto = self.preparar()
        with sin_red() as tocadas:
            medico.rutas_rotas(str(nota), texto)
        self.assertEqual(tocadas, [])

    def test_M1_hook_de_edicion_no_toca_la_red(self):
        nota, texto = self.preparar()
        datos = {"hook_event_name": "PostToolUse", "tool_name": "Edit",
                 "tool_input": {"file_path": str(nota), "old_string": "", "new_string": texto}}
        with sin_red() as tocadas:
            aviso = hook_choques.aviso_rutas(datos)
        self.assertEqual(tocadas, [])
        self.assertIn("falta-acción.md", aviso or "")

    def test_M1_medico_entero_no_toca_la_red(self):
        self.preparar()
        with sin_red() as tocadas:
            cerebro = nucleo.desde_disco()
            medico.revisar(cerebro, medico.alcance(cerebro))
        self.assertEqual(tocadas, [])

    def test_M1_reglas_no_miran_rutas_de_red_de_la_nota(self):
        proyecto = RAIZ / "proyecto demo"
        (proyecto / "src").mkdir(parents=True, exist_ok=True)
        cuerpo = " ".join(f"`{t}`" for t in (f"//{SERVIDOR}/share/x.py", f"\\\\{SERVIDOR}\\share\\y.py", f"//{SERVIDOR}.x",
                                              "src/a.py"))
        with sin_red() as tocadas:
            reglas.carpeta_dicha({"_cuerpo": cuerpo}, "demo", [("demo", {"raiz": str(proyecto)})],
                                 {"demo": proyecto}, {})
        self.assertEqual(tocadas, [])


class PruebasM2(Base):
    def planear(self, destino):
        ruta = nota_con_piezas()
        indice(ruta.name)
        return ordenar.planear(ruta, "2", destino=destino)

    def test_M2_destino_fuera_de_la_memoria_se_rechaza(self):
        for destino in ("..\\..\\..\\..\\.claude\\CLAUDE", "../../../CLAUDE", str(RAIZ / "fuera-absoluta"),
                        "sub/otra", "sub\\otra", "MEMORY", "memory.md", "CLAUDE", "CLAUDE.md", "C:fuera", ".."):
            plan, error = self.planear(destino)
            self.assertIsNone(plan, destino)
            self.assertTrue(error, destino)

    def test_M2_destino_hermano_con_acentos_se_acepta(self):
        escribir("señales-viejas ñ.md", fm("señales-viejas", "Destino con espacio y eñe en el nombre del archivo"))
        plan, error = self.planear("señales-viejas ñ")
        self.assertIsNone(error)
        self.assertEqual(plan["destino"].parent, MEMORIA)


class PruebasM3M4(Base):
    def preparar(self):
        escribir("despliegue.md", fm("despliegue", "Cómo se despliega el proyecto demo en el servidor de pruebas"))
        escribir("vieja.md", fm("vieja", "Nota vieja guardada en cp1252 por un editor antiguo de Windows")
                 + "Canción vieja: ver [[despliegue]] antes de tocar.\n", codificacion="cp1252", fin="\r\n")
        escribir("nueva.md", fm("nueva", "Nota nueva en UTF-8 que también nombra el despliegue del proyecto")
                 + "Ver [[despliegue]].\n")
        indice("despliegue.md", "vieja.md", "nueva.md")
        contexto, error = ordenar.resolver(str(MEMORIA / "despliegue.md"))
        self.assertIsNone(error)
        return contexto

    def test_M3_renombrar_avisa_las_notas_que_no_son_utf8(self):
        self.preparar()
        salida = io.StringIO()
        with contextlib.redirect_stdout(salida):
            ordenar.main_renombrar(str(MEMORIA / "despliegue.md"), "despliegue-nuevo")
        texto = salida.getvalue()
        self.assertIn("vieja.md", texto)
        self.assertIn("UTF-8", texto)

    def test_M4_nombres_que_rompen_enlaces_se_rechazan(self):
        contexto = self.preparar()
        for nuevo in ("despliegue#1", "desp]liegue", "desp[liegue", "desp^liegue", "desp|liegue", "a" * 300, "CON",
                      "con.txt", "LPT1", "nul"):
            plan, error = ordenar.planear_nombre(contexto, nuevo, nucleo.DATOS)
            self.assertIsNone(plan, nuevo)
            self.assertTrue(error, nuevo)

    def test_M4_nombre_con_enes_y_acentos_se_acepta(self):
        contexto = self.preparar()
        plan, error = ordenar.planear_nombre(contexto, "despliegue-ñandú acción", nucleo.DATOS)
        self.assertIsNone(error)
        self.assertEqual(plan["nueva"].name, "despliegue-ñandú acción.md")


class PruebasM5(Base):
    def test_M5_partir_no_se_cae_si_falla_el_deshacer(self):
        ruta = nota_con_piezas(fin="\r\n")
        indice(ruta.name)
        plan, error = ordenar.planear(ruta, "2")
        self.assertIsNone(error)
        real = ordenar.escribir_atomico
        llamadas = []

        def escribir_falla(destino, contenido):
            llamadas.append(destino)
            if len(llamadas) == 2:
                raise PermissionError("tomado por OneDrive")
            return real(destino, contenido)

        with mock.patch.object(ordenar, "escribir_atomico", escribir_falla), \
                mock.patch("os.remove", side_effect=PermissionError("tomado por el antivirus")):
            carpeta, _, error = ordenar.aplicar(plan, DATOS)
        self.assertIsNone(carpeta)
        self.assertIn("no pude deshacer", error)
        self.assertIn(plan["destino"].name, error)

    def test_M5_renombrar_no_se_cae_si_falla_el_deshacer(self):
        escribir("despliegue.md", fm("despliegue", "Cómo se despliega el proyecto demo en el servidor de pruebas"))
        indice("despliegue.md")
        contexto, _ = ordenar.resolver(str(MEMORIA / "despliegue.md"))
        plan, error = ordenar.planear_nombre(contexto, "despliegue-nuevo", DATOS)
        self.assertIsNone(error)
        with mock.patch("os.remove", side_effect=PermissionError("tomado por el antivirus")):
            carpeta, error = ordenar.aplicar_nombre(plan, DATOS)
        self.assertIsNone(carpeta)
        self.assertIn("no pude deshacer", error)


class PruebasM6(Base):
    def test_M6_anclas_en_un_renglon_enorme_no_tardan_el_cuadrado(self):
        nodo = {"_cuerpo": "Citas: " + " ".join(["codigo.cs:12"] * 120000) + "\nfin\n"}
        comienzo = time.perf_counter()
        lineas = medico.anclas_de_nodo(nodo)
        self.assertLess(time.perf_counter() - comienzo, 5)
        self.assertEqual(sum(len(g) for g in lineas.values()), 120000)
        self.assertEqual(list(lineas), [0])

    def test_M6_anclas_siguen_en_su_renglon_con_crlf(self):
        nodo = {"_cuerpo": "uno\r\nver `src/a.cs:3` y b.cs:4\r\notro c.cs:9\n"}
        lineas = medico.anclas_de_nodo(nodo)
        self.assertEqual(sorted(lineas), [5, nodo["_cuerpo"].index("otro")])
        self.assertEqual([x["nombre"] for x in lineas[5]], ["a", "b"])


class PruebasM7(Base):
    def test_M7_cache_de_anclas_no_pasa_opciones_a_git(self):
        repo = str(RAIZ / "repo demo")
        archivo = os.path.join(repo, "a.cs")
        cuando = 1700000000
        llave = f"{repo}|{cuando // 3600}"
        malo = str(RAIZ / "X.txt")
        cache = RAIZ / "anclas-git.json"
        cache.write_text(json.dumps({"commits": {llave: f"--output={malo}"}}), encoding="utf-8")
        pedidos = []

        def git_falso(_, argumentos, espera=None):
            pedidos.append(list(argumentos))
            if argumentos[:1] == ["rev-parse"]:
                return "b" * 40
            if argumentos[:1] == ["rev-list"]:
                return "a" * 40
            return ""

        with mock.patch.object(medico, "correr_git", git_falso), \
                mock.patch.object(medico, "fechas_de_renglones", lambda pedidos, repos: {("nota", 1): cuando}), \
                mock.patch.object(medico, "commits_por_archivo", lambda repo, relativas: {}):
            medico.anclas_movidas([{"_nota_ruta": "nota", "linea": 1, "archivo": archivo, "desde": 3}], [repo], cache)
        diffs = [p for p in pedidos if "diff" in p]
        self.assertTrue(diffs)
        self.assertFalse(any(a.startswith("--output") for p in pedidos for a in p))
        for p in diffs:
            self.assertIn("--end-of-options", p)
            self.assertLess(p.index("--end-of-options"), p.index("a" * 40))


class PruebasM8(Base):
    def test_M8_partir_avisa_si_el_indice_pasa_el_tope(self):
        ruta = nota_con_piezas()
        indice(ruta.name, extra=medico.LINEAS_INDICE - 3)
        salida = io.StringIO()
        with contextlib.redirect_stdout(salida):
            ordenar.main_partir(str(ruta), "2")
        self.assertIn("no se ve al arrancar", salida.getvalue())

    def test_M8_partir_no_avisa_con_indice_chico(self):
        ruta = nota_con_piezas()
        indice(ruta.name)
        salida = io.StringIO()
        with contextlib.redirect_stdout(salida):
            ordenar.main_partir(str(ruta), "2")
        self.assertNotIn("no se ve al arrancar", salida.getvalue())


class PruebasM9(Base):
    def test_M9_hardlink_sigue_compartido(self):
        nota = escribir("compartida ñ.md", "viejo\r\n")
        otra = RAIZ / "otra memoria compartida.md"
        if otra.exists():
            otra.unlink()
        try:
            os.link(nota, otra)
        except OSError as error:
            self.skipTest(f"sin hardlinks: {error}")
        archivos.escribir_atomico(nota, "nuevo con acción\r\n")
        self.assertEqual(otra.read_bytes(), "nuevo con acción\r\n".encode("utf-8"))
        self.assertEqual(os.stat(nota).st_nlink, 2)

    def test_M9_symlink_escribe_en_el_destino_real(self):
        real = RAIZ / "real señal.md"
        real.write_text("viejo\n", encoding="utf-8")
        enlace = MEMORIA / "enlace señal.md"
        try:
            os.symlink(real, enlace)
        except OSError as error:
            self.skipTest(f"sin symlinks: {error}")
        archivos.escribir_atomico(enlace, b"nuevo\n")
        self.assertTrue(os.path.islink(enlace))
        self.assertEqual(real.read_bytes(), b"nuevo\n")

    @unittest.skipIf(os.name == "nt", "los permisos POSIX solo aplican en Linux y macOS")
    def test_M9_conserva_permisos(self):
        nota = escribir("permisos.md", "viejo\n")
        os.chmod(nota, 0o644)
        archivos.escribir_atomico(nota, "nuevo\n")
        self.assertEqual(stat.S_IMODE(os.stat(nota).st_mode), 0o644)

    def test_M9_archivo_comun_sigue_atomico(self):
        nota = escribir("común.md", "viejo\n")
        archivos.escribir_atomico(nota, "nuevo\n")
        self.assertEqual(nota.read_bytes(), b"nuevo\n")
        self.assertEqual(sorted(p.name for p in MEMORIA.iterdir()), ["común.md"])


class PruebasM10(Base):
    def receta(self, nota, titulo):
        return {"ruta": str(MEMORIA / nota), "titulo": titulo, "donde": str(RAIZ / "proyecto demo"),
                "nota_titulo": titulo, "texto": "1. uno\n2. dos\n3. tres\n"}

    def test_M10_receta_sin_letras_latinas_tiene_nombre_propio(self):
        una = self.receta("デプロイ.md", "デプロイの手順")
        otra = self.receta("🚀.md", "🚀🚀")
        self.assertTrue(recetas.nombre_de(una))
        self.assertTrue(recetas.nombre_de(otra))
        self.assertNotEqual(recetas.destino_de(una), recetas.destino_de(otra))
        self.assertEqual(recetas.destino_de(una).parent.name, recetas.nombre_de(una))
        self.assertIn(f"name: {recetas.nombre_de(una)}\n", recetas.texto_de(una))

    def test_M10_receta_con_acentos_conserva_su_nombre(self):
        self.assertEqual(recetas.nombre_de(self.receta("señales.md", "Cómo se despliega")), "senales-como-se-despliega")


class PruebasM12(Base):
    def test_M12_enlace_que_difiere_solo_en_forma_unicode_lo_dice(self):
        nfd = unicodedata.normalize("NFD", "canción")
        escribir(f"{nfd}.md", fm(nfd, "Nota cuyo nombre de archivo está en NFD como sale de macOS"))
        escribir("otra.md", fm("otra", "Nota que cita a la canción con la ó compuesta como se teclea en Windows")
                 + "Ver [[canción]] y [la canción](canción.md).\n")
        indice(f"{nfd}.md", "otra.md")
        cerebro = nucleo.desde_disco()
        hallados = [h for h in medico.revisar(cerebro, medico.alcance(cerebro)) if h["regla"] == "enlaceRoto"]
        if not hallados:
            self.skipTest("este sistema de archivos no distingue NFC de NFD")
        self.assertTrue(all("Unicode" in h["texto"] + h.get("arreglo", "") for h in hallados), hallados)


class PruebasM14(Base):
    def test_M14_respaldar_borra_los_respaldos_viejos(self):
        base = DATOS / ordenar.RESPALDOS
        viejo = base / "20200101-000000-partir"
        viejo.mkdir(parents=True)
        (viejo / "1-nota ñ.md").write_text("viejo", encoding="utf-8")
        reciente = base / time.strftime("%Y%m%d-%H%M%S-renombrar", time.localtime(time.time() - 86400))
        reciente.mkdir()
        ajena = base / "mis cosas"
        ajena.mkdir()
        (base / ordenar.REGISTRO).write_text("registro\n", encoding="utf-8")
        nota = escribir("señales.md", "texto\n")
        with mock.patch.dict(nucleo.CONFIG, {"borrar_registros_dias": 90}):
            nueva = ordenar.respaldar(DATOS, [nota])
        self.assertFalse(viejo.exists())
        self.assertTrue(reciente.exists() and ajena.exists() and nueva.exists() and (base / ordenar.REGISTRO).exists())

    def test_M14_con_cero_dias_no_borra(self):
        viejo = DATOS / ordenar.RESPALDOS / "20200101-000000-partir"
        viejo.mkdir(parents=True)
        with mock.patch.dict(nucleo.CONFIG, {"borrar_registros_dias": 0}):
            ordenar.respaldar(DATOS, [escribir("señales.md", "texto\n")])
        self.assertTrue(viejo.exists())


def tearDownModule():
    shutil.rmtree(RAIZ.parent, ignore_errors=True)


if __name__ == "__main__":
    unittest.main(verbosity=2)

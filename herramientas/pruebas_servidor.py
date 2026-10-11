import http.client
import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path

CARPETA = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(CARPETA))

TEMPORAL = Path(tempfile.mkdtemp(prefix="pruebas-servidor-"))


def preparar_entorno(t):
    for nombre in [k for k in os.environ if k.startswith("CLAUDE_PLUGIN_") or k == "CLAUDE_ENV_FILE"]:
        del os.environ[nombre]
    casa = t / "casa"
    for carpeta in (casa, t / "claude-vacia", t / "memoria", t / "appdata"):
        carpeta.mkdir(parents=True, exist_ok=True)
    (t / "memoria" / "MEMORY.md").write_text("# Memoria\n\n- [Una](una.md) — una nota\n", encoding="utf-8")
    (t / "memoria" / "una.md").write_text("---\nname: una\ndescription: una nota\ntype: project\n---\n\nTexto.\n",
                                          encoding="utf-8")
    config = {"usuario": "Ana",
              "fuentes": [{"id": "memoria", "nombre": "Memoria", "color": "#E64980",
                           "raices": [[str(t / "memoria"), False, ""]], "memoria": True}]}
    ruta = t / "config.json"
    ruta.write_text(json.dumps(config, ensure_ascii=False), encoding="utf-8")
    os.environ.update(HOME=str(casa), USERPROFILE=str(casa), APPDATA=str(t / "appdata"),
                      CLAUDE_CONFIG_DIR=str(t / "claude-vacia"), CEREBRO_CONFIG=str(ruta), PYTHONIOENCODING="utf-8")


preparar_entorno(TEMPORAL)

import consultas
import firmas
import mapa
import servidor


def puerto_libre():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class EnVivo:
    def __enter__(self):
        self.web = servidor.Servidor(("127.0.0.1", 0), servidor.Manejador)
        self.puerto = self.web.server_address[1]
        self.hilo = threading.Thread(target=self.web.serve_forever, daemon=True)
        self.hilo.start()
        return self

    def __exit__(self, *_):
        self.web.shutdown()
        self.web.server_close()

    def pedir(self, camino, cabeceras=None):
        conexion = http.client.HTTPConnection("127.0.0.1", self.puerto, timeout=10)
        try:
            conexion.request("GET", camino, headers=dict({"Host": f"127.0.0.1:{self.puerto}"}, **(cabeceras or {})))
            respuesta = conexion.getresponse()
            return respuesta.status, respuesta.read()
        finally:
            conexion.close()


def reiniciar_clave():
    servidor._clave.clear()
    try:
        servidor.ARCHIVO_CLAVE.unlink()
    except OSError:
        pass


class Aislamiento(unittest.TestCase):
    def test_datos_en_carpeta_temporal(self):
        self.assertTrue(str(servidor.EN_VIVO.resolve()).startswith(str(TEMPORAL.resolve())), servidor.EN_VIVO)


class S1Surrogate(unittest.TestCase):
    def test_s1_decodificar_rechaza_surrogate_suelto(self):
        self.assertIsNone(servidor.decodificar(b'{"t":1,"k":"leer","f":"C:/x/\\ud800.md"}'))

    def test_s1_decodificar_acepta_par_valido(self):
        ev = servidor.decodificar(b'{"t":1,"k":"leer","f":"C:/x/\\ud83d\\ude00.md"}')
        self.assertEqual(ev["f"], "C:/x/\U0001F600.md")

    def test_s1_eventos_y_uso_siguen_andando(self):
        servidor.EN_VIVO.mkdir(parents=True, exist_ok=True)
        antes = servidor.uso
        servidor.uso = servidor.Uso()
        try:
            lector = servidor.Lector()
            lector.procesar(b'{"t":1,"e":"post","k":"leer","f":"C:/x/\\ud800.md"}\n', en_vivo=False)
            servidor.uso.resumen()
            servidor.uso.previos().encode("utf-8")
        finally:
            servidor.uso = antes


class S2ClaveAlArrancar(unittest.TestCase):
    def test_s2_clave_txt_existe_al_anunciar(self):
        reiniciar_clave()
        puerto = puerto_libre()
        proceso = subprocess.Popen([sys.executable, "-I", str(CARPETA / "servidor.py"), "--sin-navegador", "--puerto",
                                    str(puerto)], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=dict(os.environ))
        try:
            visto = []
            limite = time.monotonic() + 120
            while time.monotonic() < limite:
                linea = proceso.stdout.readline().decode("utf-8", "replace")
                if not linea:
                    break
                visto.append(linea)
                if "en vivo" in linea:
                    break
            self.assertTrue(any("en vivo" in v for v in visto), visto)
            self.assertTrue(servidor.ARCHIVO_CLAVE.is_file(), "clave.txt no existe tras el anuncio")
        finally:
            proceso.kill()
            proceso.wait(30)
            proceso.stdout.close()
            servidor._clave.clear()


class S3CarreraClave(unittest.TestCase):
    def test_s3_hilos_ven_la_misma_clave(self):
        servidor.EN_VIVO.mkdir(parents=True, exist_ok=True)
        for _ in range(30):
            reiniciar_clave()
            barrera = threading.Barrier(8)
            vistas = []

            def pedir():
                barrera.wait()
                vistas.append(servidor.clave())

            hilos = [threading.Thread(target=pedir) for _ in range(8)]
            for h in hilos:
                h.start()
            for h in hilos:
                h.join()
            guardada = servidor.ARCHIVO_CLAVE.read_text(encoding="utf-8").strip()
            self.assertEqual(set(vistas), {guardada})

    def test_s3_procesos_ven_la_misma_clave(self):
        reiniciar_clave()
        servidor.EN_VIVO.mkdir(parents=True, exist_ok=True)
        cuando = time.time() + 6
        codigo = ("import sys, time; sys.path.insert(0, sys.argv[1]); import servidor; "
                  "time.sleep(max(0, float(sys.argv[2]) - time.time())); print(servidor.clave())")
        procesos = [subprocess.Popen([sys.executable, "-I", "-c", codigo, str(CARPETA), str(cuando)],
                                     stdout=subprocess.PIPE, env=dict(os.environ)) for _ in range(6)]
        claves = {p.communicate(timeout=120)[0].decode().strip() for p in procesos}
        guardada = servidor.ARCHIVO_CLAVE.read_text(encoding="utf-8").strip()
        servidor._clave.clear()
        self.assertEqual(claves, {guardada})

    def test_s3_clave_corta_se_reemplaza(self):
        reiniciar_clave()
        servidor.EN_VIVO.mkdir(parents=True, exist_ok=True)
        servidor.ARCHIVO_CLAVE.write_text("corta", encoding="utf-8")
        nueva = servidor.clave()
        self.assertGreaterEqual(len(nueva), 20)
        self.assertEqual(servidor.ARCHIVO_CLAVE.read_text(encoding="utf-8").strip(), nueva)


class S4RepeticionDeFirma(unittest.TestCase):
    def test_s4_entrada_no_acepta_la_misma_firma_dos_veces(self):
        with EnVivo() as vivo:
            firma = firmas.del_pedido(servidor.clave(), "/entrada")
            primera = vivo.pedir("/entrada", {servidor.CABECERA_FIRMA: firma})[0]
            segunda = vivo.pedir("/entrada", {servidor.CABECERA_FIRMA: firma})[0]
        self.assertEqual((primera, segunda), (200, 403))

    def test_s4_apagar_no_acepta_firma_usada(self):
        firma = firmas.del_pedido(servidor.clave(), "/apagar")
        self.assertTrue(servidor.firma_una_vez("/apagar", firma))
        self.assertFalse(servidor.firma_una_vez("/apagar", firma))
        self.assertTrue(servidor.firma_una_vez("/apagar", firmas.del_pedido(servidor.clave(), "/apagar",
                                                                             time.time() - 1)))


class S7MapaProfundo(unittest.TestCase):
    def test_s7_expresion_larga_no_tumba_el_mapa(self):
        texto = "def antes():\n    pass\n\nx = " + " + ".join(["1"] * 5000) + "\n\nclass Despues:\n    def m(self):\n        pass\n"
        nombres = [(b.tipo, b.nombre) for b in mapa.mapa_py(texto)]
        self.assertIn(("funcion", "antes"), nombres)
        self.assertIn(("clase", "Despues"), nombres)
        self.assertIn(("metodo", "m"), nombres)

    def test_s7_anidados_igual_que_antes(self):
        texto = ("class A:\n    if True:\n        def f(self):\n            def g():\n                pass\n"
                 "try:\n    def h():\n        pass\nexcept Exception:\n    async def k():\n        pass\n")
        nombres = [(b.tipo, b.nombre, b.padre.nombre if b.padre else None) for b in mapa.mapa_py(texto)]
        self.assertEqual(nombres, [("clase", "A", None), ("metodo", "f", "A"), ("funcion", "g", "f"),
                                   ("funcion", "h", None), ("funcion", "k", None)])


class S8MedidorAcotado(unittest.TestCase):
    def test_s8_medidor_olvida_chats_viejos(self):
        medidor = consultas.Medidor()
        t0 = 1_700_000_000
        sesiones = 3000
        for i in range(sesiones):
            t = t0 + i * 288
            s = f"s{i:06d}"
            medidor.anotar({"e": "usuario", "s": s, "t": t})
            medidor.anotar({"e": "aviso", "s": s, "t": t, "fs": ["C:/m/a.md"]})
            medidor.anotar({"e": "recuerda", "s": s, "t": t, "fs": ["C:/m/b.md"]})
            medidor.anotar({"e": "post", "k": "consulta", "s": s, "t": t, "fs": ["C:/m/c.md"]})
        self.assertEqual((medidor.total, medidor.avisos, medidor.recordadas, medidor.con_consulta),
                         (sesiones, sesiones, sesiones, sesiones))
        tope = 2 * consultas.DIA // 288
        for tabla in (medidor.pedido, medidor.de_avisos, medidor.de_recuerdos, medidor.pendientes):
            self.assertLess(len(tabla), tope)

    def test_s8_chat_activo_no_se_olvida(self):
        medidor = consultas.Medidor()
        t0 = 1_700_000_000
        medidor.anotar({"e": "usuario", "s": "viva", "t": t0})
        for i in range(1, 200):
            t = t0 + i * 600
            medidor.anotar({"e": "usuario", "s": f"otra{i}", "t": t})
            medidor.anotar({"e": "post", "k": "leer", "s": "viva", "t": t, "f": "C:/x.py"})
        medidor.anotar({"e": "post", "k": "consulta", "s": "viva", "t": t0 + 200 * 600})
        self.assertEqual(medidor.con_consulta, 1)


class S9TopeDeTiempo(unittest.TestCase):
    def test_s9_manejador_tiene_tope_mayor_al_latido(self):
        self.assertIsNotNone(servidor.Manejador.timeout)
        self.assertGreater(servidor.Manejador.timeout, 15)

    def test_s9_conexion_a_medias_se_corta(self):
        antes = servidor.Manejador.timeout
        servidor.Manejador.timeout = 0.5
        try:
            with EnVivo() as vivo:
                with socket.create_connection(("127.0.0.1", vivo.puerto), timeout=10) as s:
                    s.sendall(b"GET /cerebro.html HTTP/1.1\r\nHost: 127.0.0.1\r\n")
                    inicio = time.monotonic()
                    try:
                        recibido = s.recv(100)
                    except socket.timeout:
                        recibido = None
                    demora = time.monotonic() - inicio
        finally:
            servidor.Manejador.timeout = antes
        self.assertIsNotNone(recibido)
        self.assertLess(demora, 5)


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass
    try:
        programa = unittest.main(exit=False, verbosity=2)
    finally:
        shutil.rmtree(TEMPORAL, ignore_errors=True)
    return 0 if programa.result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main())

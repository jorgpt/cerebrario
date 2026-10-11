# Arquitectura de Cerebrario

Cerebrario es un plugin de Claude Code hecho en Python 3.10+ (solo biblioteca estándar) más una página HTML. No usa
dependencias de npm ni de pip, no tiene `postinstall` y no tiene telemetría. Las únicas conexiones de red son al
servidor propio en `127.0.0.1` y, si la página no encuentra `vendor/`, a jsDelivr con huella SRI.

Este documento sale de la ingeniería inversa de Neuromapa 0.1.5. La lista de lo que cambió está en el
[README](../README.md) y en [AUDITORIA.md](AUDITORIA.md).

## Mapa de piezas

| Pieza | Archivos | Qué hace |
|---|---|---|
| Lanzadores | `scripts/python.sh`, `scripts/python.cmd`, `bin/cerebrario*` | Buscan un Python 3.10+, lo recuerdan y corren cada hook con `-I -S` |
| Hooks | `hooks/hooks.json`, `hook_*.py`, `hooks_comun.py` | Lo que corre solo en cada evento de Claude Code |
| Núcleo | `cerebro.py`, `configuracion.py`, `archivos.py`, `textos.py` | Lee las notas, arma el grafo y la página |
| Visor 3D | `plantilla.html`, `vendor/`, `servidor.py`, `consultas.py`, `mapa.py` | Dibuja el cerebro y lo muestra en vivo |
| Médico | `medico.py`, `vigencia.py`, `parecidas.py`, `entidades.py`, `fichas.py` | Revisa la salud de las notas |
| Pista | `hook_servir.py`, `buscador.py`, `aprender_pista.py` | Contexto antes de cada pedido |
| Ordenar | `ordenar.py`, `dormir.py`, `dormir_claude.py` | Partir y renombrar notas, y la pasada diaria |
| Línea de tiempo | `historial.py`, `hook_guardar.py` | «Qué sabíamos y cuándo» con un git propio |
| Aprender | `aprender*.py`, `charlas.py`, `hook_evento.py`, `registro.py` | Registro en vivo y qué se usa junto |
| Propuestas | `reglas.py`, `recetas.py`, `pendientes.py`, `lecciones.py` | Notas → reglas por carpeta y skills; pendientes |

## Lanzadores y hooks

`hooks.json` usa un truco de dos lenguajes. El comando `/bin/sh python.sh … \; . python.cmd …` corre `python.sh`
cuando hay Git Bash o un sistema tipo Unix; en PowerShell, `/bin/sh` falla y entonces corre `python.cmd`. Cada
lanzador recuerda qué Python encontró en un archivo propio (`python-sh.txt` o `python-cmd.txt`) dentro de la carpeta
de datos del plugin.

| Evento | Script | Modo | Efecto |
|---|---|---|---|
| SessionStart | `hook_inicio.py` | síncrono | Anota la carpeta de datos y da la bienvenida |
| Todos los eventos | `hook_cerebro.py` → `hook_evento.py` | de fondo | Agrega una línea a `en-vivo/eventos.jsonl` |
| UserPromptSubmit | `hook_servir.py` | síncrono, 10 s | Pista y aviso de problemas |
| PreToolUse (Agent/Task/Workflow) | `hook_freno.py` | síncrono | Pide confirmación (`ask`) si los agentes pasan el tope de tokens configurado |
| PostToolUse (Write) | `hook_parecidas.py` | de fondo | Avisa si una memoria nueva repite otra |
| PostToolUse (Edit/Write) | `hook_choques.py` | de fondo | Avisa enlaces rotos y datos viejos en la nota editada |
| Stop / compactación | `hook_guardar.py` | síncrono, corto | Lanza de fondo el guardado del historial y recuerda anotar lo decidido |

Ningún hook escribe en `~/.claude/settings.json`, en `CLAUDE.md` ni en `skills/`. Los hooks escriben solo en la
carpeta de datos del plugin.

## Visor 3D

`cerebro.py` recorre las carpetas configuradas (la memoria de `~/.claude/projects/*/memory/`, los `CLAUDE.md` y las
fuentes extra) y arma un grafo: cada nota es un nodo, y cada enlace, mención, entrada del índice, parecido o uso
conjunto aprendido es una arista. Después escribe `cerebro.html` con base en `plantilla.html`. Mete d3 y marked en
línea desde `vendor/` (con su huella sha384 verificada) y pone los datos como `window.CEREBRO = {…}`, con `<`, `<!--` y
`</` escapados.

El navegador dibuja el grafo con d3-force, agrupado en lóbulos. Todo texto de una nota pasa por `esc()` antes de
llegar a `innerHTML`. El markdown de marked se sanea dentro de un `<template>` inerte y después se filtran sus
enlaces e imágenes.

`servidor.py` le agrega lo «en vivo». Escucha solo en `127.0.0.1` (puertos 8765-8770), valida `Host` contra el DNS
rebinding y acepta solo GET y HEAD sobre caminos fijos: nunca sirve archivos arbitrarios. Para entrar se usa una clave
aleatoria de 192 bits que se cambia por una galleta firmada (`HttpOnly`, `SameSite=Strict`). Los hooks hablan con el
servidor usando una firma HMAC con hora. El servidor sigue `eventos.jsonl` y empuja cada acción al navegador por
Server-Sent Events.

## Médico

`medico.revisar` lee todas las notas en UTF-8 (o cp1252 si no se puede) y les corre unas quince reglas:

- el presupuesto del índice: 200 renglones y 25 KB, lo mismo que Claude Code carga al arrancar;
- el frontmatter;
- rutas y `[[enlaces]]` que no existen;
- notas demasiado grandes para un Read;
- cifras que se contradicen;
- notas huérfanas o que nadie alcanza;
- memorias duplicadas;
- lo que repite un `CLAUDE.md`.

Con proyectos en `config.json` también revisa git:

- commits citados que no existen;
- problemas anotados que un commit posterior quizá resolvió;
- anclas `archivo:línea` que se corrieron.

El médico solo sugiere: nunca toca notas. Nunca toca rutas de red ni rutas absolutas sacadas del texto de una nota.

## Pista

Antes de cada pedido, `hook_servir.py` busca el tema en el índice (`buscador.py`), o en el servidor si está
prendido. Con eso arma un bloque de hasta 2,500 caracteres:

- qué notas leer primero, con su renglón y un pasaje citado;
- las decisiones anotadas;
- los datos viejos;
- el código que esas notas citan.

Ese bloque llega a Claude como `additionalContext`, envuelto en una marca que dice que es texto citado. Antes se le
quitan los caracteres de control e invisibles y las etiquetas `<…>`. La pista viene **apagada**. Apagada, solo agrega
una vez por chat un aviso informativo de problemas nuevos, que no le ordena a Claude arreglar nada.

## Partición de memorias

`--partir NOTA` divide una nota en piezas (títulos, ítems, párrafos) y `--mover 3-17` arma un plan:

- qué renglones se van;
- a qué nota van: una nota nueva `…-historia-N.md`, o una existente de la misma carpeta de memoria;
- qué rastro queda en su lugar;
- qué renglón se agrega a `MEMORY.md`.

Nada se escribe hasta correr `--confirmar <código>`, y ese código está atado a los bytes de las notas. Antes de
escribir respalda todo, comprueba que no se pierda ningún renglón y deshace si algo falla. La partición automática
(`partir_sola`) viene apagada y nunca corre desde un hook.

## Índice MEMORY.md

El índice no se reescribe ni se recorta. El médico mide sus renglones y bytes, dice desde qué renglón Claude ya no lo
ve y marca los ganchos largos o vacíos, las entradas rotas y las memorias que no están listadas. Solo `--partir` y
`--renombrar` lo tocan, y siempre con confirmación.

## Línea de tiempo

`historial.py` guarda un repositorio git aparte por carpeta de memoria, en `datos/historial/`, con solo los `.md`.
Al terminar cada respuesta hace un commit en segundo plano si cambió la firma (tamaños y fechas) de las notas, y no
guarda las versiones que parecen traer un secreto. Las consultas son:

- `--historial "texto"`: cuándo apareció o se borró algo;
- `--cambios NOTA`: qué dato cambió;
- `--sobre tema --al 6/10`: cómo estaba la memoria ese día.

## Propuestas: notas → reglas y skills

- `reglas.py` propone un `.claude/rules/<nota>.md` con `paths:` en la carpeta del proyecto que la nota nombra o con
  la que se usa.
- `recetas.py` detecta los tramos «Cómo se hace…» y propone una skill.

Las dos se escriben solo con `--confirmar`.

## Mapa por proyecto y pendientes

Cada nota toma su proyecto de la fuente o de la carpeta `projects/<proyecto>/memory`. `--pendientes` junta las frases
que dicen que falta algo, con su nota, su renglón y su fecha. Solo lee.

## La pasada diaria («dormir»)

Una vez al día, `dormir.py` busca datos viejos y notas casi llenas y deja las propuestas en `--propuestas`. Si la pista
está apagada, la pasada no se lanza sola. La parte que le pregunta a Claude (`dormir_con_claude`, con tope diario en
dólares) **solo corre a mano** con `cerebrario --dormir`; nunca desde un hook.

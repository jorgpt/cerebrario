# Probar Cerebrario

Gracias por probarlo antes que nadie. Lleva unos 20 minutos. Lo que más sirve es saber **dónde te trabaste** y **si
lo que dice sobre tus notas es cierto**.

## Antes de empezar

- Claude Code instalado y con tu sesión iniciada.
- Python 3.10 o más nuevo. Para ver cuál tenés: `python --version` (en Mac y Linux, `python3 --version`; en Windows
  también sirve `py -3 --version`). Si no tenés, bajalo de [python.org](https://www.python.org/downloads/).
- git, porque Claude Code baja el plugin con git: `git --version` tiene que responder. En Windows viene con
  [Git for Windows](https://git-scm.com/downloads).
- Anotá la hora: queremos saber cuánto tarda alguien que nunca lo vio.

## 1. Instalar

Seguí solo el [README](../README.md), sin ayuda:

```
claude plugin marketplace add jorgpt/cerebrario
claude plugin install cerebrario@cerebrario
```

## 2. Probar

1. Abrí una sesión nueva de Claude Code en un proyecto tuyo.
2. Escribí `/cerebrario:salud`. Anotá **solo los números** del primer renglón (graves, avisos, para revisar) y fijate
   si lo que marca es cierto: ¿esas rutas de verdad ya no existen?, ¿esos datos de verdad quedaron viejos?
3. Escribí `/cerebrario:sobre` y un tema que sepas que está en tus notas. ¿Las notas que dice leer primero eran las
   correctas?
4. Escribí `/cerebrario:abrir`. ¿Se abrió el mapa en el navegador? ¿Se mueve fluido? Probá `?` (ayuda), `A` (nombres
   genéricos) y `C` (modo cine).
5. Trabajá un rato como siempre, con el mapa abierto, y mirá si se ve lo que hace Claude.
6. Si querés, prendé el contexto automático (`/plugin configure cerebrario@cerebrario`) y contá si notás diferencia en
   las respuestas.

Si preferís no usar tus notas, `/cerebrario:abrir --demo` muestra el mapa con notas inventadas.

## 3. Contar

Abrí un issue con la plantilla **«Informe de prueba»**. Pide esto:

- Sistema (Windows, Mac o Linux, y versión), versión de Python, de Claude Code (`claude --version`) y de Cerebrario
  (`claude plugin list`). En Windows, si tenés Git Bash o no.
- Cuánto tardaste en instalarlo y en qué paso te trabaste, si te trabaste.
- Los números de `/cerebrario:salud` y si los avisos eran ciertos.
- Si apareció algún «hook error» en la charla, y en qué momento.
- Qué te sirvió, qué no y qué le falta.

## Lo que nunca hay que mandar

- **`cerebro.html`**: lleva adentro el texto de todas tus notas, aun en modo anónimo.
- Capturas o videos con los nombres de tus notas. Para mostrar el mapa, usá el modo anónimo (`A`) o la copia que
  baja el botón **Sin notas**.
- El contenido de tus notas, la clave del mapa (`en-vivo/clave.txt`) ni una dirección con `clave=`.
- Un problema de seguridad no va en un issue público: mirá [SECURITY.md](../SECURITY.md).

## Actualizar

Cuando salga una versión nueva:

```
claude plugin marketplace update cerebrario
claude plugin update cerebrario@cerebrario
```

Después cerrá y volvé a abrir Claude Code. Si el mapa estaba prendido, abrilo con `/cerebrario:abrir --reiniciar`.

## Desinstalar

```
claude plugin uninstall cerebrario@cerebrario
claude plugin marketplace remove cerebrario
```

Tus notas no se tocan: Cerebrario nunca escribe en la memoria.

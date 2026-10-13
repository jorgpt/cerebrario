# Instalar los hooks de Cerebrario en esta PC (PC1)

Sin hooks, el mapa muestra las notas pero no ve lo que hacen las sesiones de Claude Code (el electro nunca pasa a
«trabajando»). Con estos hooks, cada sesión anota en el registro en vivo qué herramienta usa y qué archivo toca (nunca el
texto de los mensajes ni de los comandos), y el mapa lo muestra al momento.

Solo se instala `hook_cerebro.py`, el que **observa**. No se instalan `hook_servir`, `hook_guardar`, `hook_choques`,
`hook_parecidas` ni `hook_freno`: instalados a mano (sin plugin) prenden solos el contexto automático y le hablarían a
Claude en cada pedido. Así quedan apagados la pista, `dormir_con_claude` y el freno.

## Opción 1: una línea (recomendada)

En PowerShell (no hace falta abrirlo como administrador):

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "C:\Users\jorge\projects\cerebrario\instalar-hooks.ps1"
```

Qué hace `instalar-hooks.ps1`:

1. Copia `%USERPROFILE%\.claude\settings.json` a `settings.json.respaldo-cerebrario-AAAAMMDD-HHMMSS`, al lado.
2. Agrega el hook en 11 eventos al final de los hooks que ya hay (no toca los de ECC ni nada más).
3. Agrega `env.CEREBRO_CONFIG` = `C:\Users\jorge\cerebrario-datos\config.json`, para que los hooks escriban en los
   datos reales y no en la demo.
4. Comprueba que el JSON quede válido. Correrlo dos veces no duplica nada.

Después se abre una sesión nueva de Claude Code y el mapa (http://127.0.0.1:8765/cerebro.html) empieza a ver las
sesiones.

Para quitarlo (deja `settings.json` como estaba, y también hace respaldo antes):

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "C:\Users\jorge\projects\cerebrario\instalar-hooks.ps1" -Quitar
```

## Opción 2: a mano

Agregar a `%USERPROFILE%\.claude\settings.json` (respaldarlo antes). Si un evento ya existe en `hooks`, se suma el
grupo al final de su lista; si `env` ya existe, se suma solo la línea `CEREBRO_CONFIG`.

```json
{
  "env": {
    "CEREBRO_CONFIG": "C:\\Users\\jorge\\cerebrario-datos\\config.json"
  },
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "/bin/sh \"C:/Users/jorge/projects/cerebrario/scripts/python.sh\" -I -S \"C:/Users/jorge/projects/cerebrario/hook_cerebro.py\" \\; . \"C:/Users/jorge/projects/cerebrario/scripts/python.cmd\" hook_cerebro.py",
            "timeout": 5,
            "async": true
          }
        ]
      }
    ],
    "PreToolUse": [
      {
        "matcher": "*",
        "hooks": [
          {
            "type": "command",
            "command": "/bin/sh \"C:/Users/jorge/projects/cerebrario/scripts/python.sh\" -I -S \"C:/Users/jorge/projects/cerebrario/hook_cerebro.py\" \\; . \"C:/Users/jorge/projects/cerebrario/scripts/python.cmd\" hook_cerebro.py",
            "timeout": 5,
            "async": true
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "*",
        "hooks": [
          {
            "type": "command",
            "command": "/bin/sh \"C:/Users/jorge/projects/cerebrario/scripts/python.sh\" -I -S \"C:/Users/jorge/projects/cerebrario/hook_cerebro.py\" \\; . \"C:/Users/jorge/projects/cerebrario/scripts/python.cmd\" hook_cerebro.py",
            "timeout": 5,
            "async": true
          }
        ]
      }
    ],
    "PostToolUseFailure": [
      {
        "matcher": "*",
        "hooks": [
          {
            "type": "command",
            "command": "/bin/sh \"C:/Users/jorge/projects/cerebrario/scripts/python.sh\" -I -S \"C:/Users/jorge/projects/cerebrario/hook_cerebro.py\" \\; . \"C:/Users/jorge/projects/cerebrario/scripts/python.cmd\" hook_cerebro.py",
            "timeout": 5,
            "async": true
          }
        ]
      }
    ],
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "/bin/sh \"C:/Users/jorge/projects/cerebrario/scripts/python.sh\" -I -S \"C:/Users/jorge/projects/cerebrario/hook_cerebro.py\" \\; . \"C:/Users/jorge/projects/cerebrario/scripts/python.cmd\" hook_cerebro.py",
            "timeout": 5,
            "async": true
          }
        ]
      }
    ],
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "/bin/sh \"C:/Users/jorge/projects/cerebrario/scripts/python.sh\" -I -S \"C:/Users/jorge/projects/cerebrario/hook_cerebro.py\" \\; . \"C:/Users/jorge/projects/cerebrario/scripts/python.cmd\" hook_cerebro.py",
            "timeout": 5,
            "async": true
          }
        ]
      }
    ],
    "SubagentStop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "/bin/sh \"C:/Users/jorge/projects/cerebrario/scripts/python.sh\" -I -S \"C:/Users/jorge/projects/cerebrario/hook_cerebro.py\" \\; . \"C:/Users/jorge/projects/cerebrario/scripts/python.cmd\" hook_cerebro.py",
            "timeout": 5,
            "async": true
          }
        ]
      }
    ],
    "Notification": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "/bin/sh \"C:/Users/jorge/projects/cerebrario/scripts/python.sh\" -I -S \"C:/Users/jorge/projects/cerebrario/hook_cerebro.py\" \\; . \"C:/Users/jorge/projects/cerebrario/scripts/python.cmd\" hook_cerebro.py",
            "timeout": 5,
            "async": true
          }
        ]
      }
    ],
    "PreCompact": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "/bin/sh \"C:/Users/jorge/projects/cerebrario/scripts/python.sh\" -I -S \"C:/Users/jorge/projects/cerebrario/hook_cerebro.py\" \\; . \"C:/Users/jorge/projects/cerebrario/scripts/python.cmd\" hook_cerebro.py",
            "timeout": 5,
            "async": true
          }
        ]
      }
    ],
    "InstructionsLoaded": [
      {
        "matcher": "path_glob_match",
        "hooks": [
          {
            "type": "command",
            "command": "/bin/sh \"C:/Users/jorge/projects/cerebrario/scripts/python.sh\" -I -S \"C:/Users/jorge/projects/cerebrario/hook_cerebro.py\" \\; . \"C:/Users/jorge/projects/cerebrario/scripts/python.cmd\" hook_cerebro.py",
            "timeout": 5,
            "async": true
          }
        ]
      }
    ],
    "SessionEnd": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "/bin/sh \"C:/Users/jorge/projects/cerebrario/scripts/python.sh\" -I -S \"C:/Users/jorge/projects/cerebrario/hook_cerebro.py\" \\; . \"C:/Users/jorge/projects/cerebrario/scripts/python.cmd\" hook_cerebro.py",
            "timeout": 5
          }
        ]
      }
    ]
  }
}
```

Cada comando tiene dos mitades a propósito: la primera la corre Git Bash y la segunda PowerShell, según con qué corra
Claude Code los hooks (ver `docs/como-funciona.md`, «Por qué cada comando de hooks/hooks.json tiene dos mitades»).

## Opción 3: como plugin (`/plugin`)

Instala **todos** los hooks del plugin, no solo el que observa. Con el plugin, el contexto automático viene apagado,
pero `hook_servir` igual le avisa a Claude una vez por chat los problemas nuevos de las notas. Si se prefiere así:

1. No correr la opción 1 (si ya se corrió, quitarla con `-Quitar`: dos instalaciones anotan todo dos veces).
2. Dentro de Claude Code: `/plugin marketplace add C:\Users\jorge\projects\cerebrario` y luego
   `/plugin install cerebrario@cerebrario`.
3. En las opciones del plugin: «Carpeta de datos» = `C:\Users\jorge\cerebrario-datos` y «Contexto automático» apagado.

## Cómo comprobar que funciona

1. Abrir una sesión nueva de Claude Code en cualquier carpeta y pedirle algo.
2. En el mapa, abajo a la derecha, el electro pasa de «en calma» a «trabajando» o «pensando», y la sesión aparece en
   «Ahora».
3. O, sin navegador: el archivo `C:\Users\jorge\cerebrario-datos\en-vivo\eventos.jsonl` crece con renglones de esa
   sesión.

## Lo que ya quedó listo (no depende de los hooks)

- Configuración y datos: `C:\Users\jorge\cerebrario-datos` (fuera de OneDrive). No se usó `%LOCALAPPDATA%` porque la
  app de escritorio de Claude lo virtualiza y la tarea programada no lo veía.
- Servidor: tarea programada «Cerebrario en vivo», sin ventana, al iniciar sesión, en http://127.0.0.1:8765/cerebro.html.
- Para abrir el mapa con la clave puesta, sin reiniciar el servidor de la tarea:

  ```powershell
  py -3 C:\Users\jorge\projects\cerebrario\servidor.py --apagar-solo
  ```

  Encuentra los datos reales por `%USERPROFILE%\.claude\plugins\data\cerebrario-local\donde.txt`. Ojo:
  `abrir-cerebro.bat` **reinicia** el servidor dentro de su ventana; al cerrarla, el mapa se apaga hasta el próximo
  inicio de sesión (o hasta volver a correr la tarea «Cerebrario en vivo»).

# Instala (o quita con -Quitar) el hook de Cerebrario que solo observa, en los settings de usuario de Claude Code.
# Antes de tocar nada respalda settings.json al lado, con fecha y hora. Ver INSTALAR_HOOKS.md.
param(
    [switch]$Quitar,
    [string]$Settings = (Join-Path $env:USERPROFILE '.claude\settings.json'),
    [string]$Config = 'C:\Users\jorge\cerebrario-datos\config.json'
)
$ErrorActionPreference = 'Stop'

$repo = ($PSScriptRoot -replace '\\', '/')
$comando = '/bin/sh "' + $repo + '/scripts/python.sh" -I -S "' + $repo + '/hook_cerebro.py" \; . "' + $repo + '/scripts/python.cmd" hook_cerebro.py'
# Evento => matcher ('' = sin matcher). SessionEnd no va de fondo: si no, Claude Code cierra antes de que se anote.
$eventos = [ordered]@{
    SessionStart = ''; PreToolUse = '*'; PostToolUse = '*'; PostToolUseFailure = '*'; UserPromptSubmit = ''
    Stop = ''; SubagentStop = ''; Notification = ''; PreCompact = ''; InstructionsLoaded = 'path_glob_match'; SessionEnd = ''
}

function Es-DeCerebrario($grupo) {
    foreach ($h in @($grupo.hooks)) { if ("$($h.command)" -like '*hook_cerebro.py*') { return $true } }
    return $false
}

function Poner($objeto, $nombre, $valor) {
    if ($objeto.PSObject.Properties[$nombre]) { $objeto.$nombre = $valor }
    else { $objeto | Add-Member -NotePropertyName $nombre -NotePropertyValue $valor }
}

if (-not (Test-Path $Settings)) { '{}' | Set-Content -Path $Settings -Encoding ascii }
if (-not $Quitar -and -not (Test-Path $Config)) { throw "No encuentro la configuración de Cerebrario: $Config" }

$respaldo = "$Settings.respaldo-cerebrario-" + (Get-Date -Format 'yyyyMMdd-HHmmss')
Copy-Item $Settings $respaldo
$texto = [IO.File]::ReadAllText($Settings, [Text.Encoding]::UTF8)
$ajustes = if ($texto.Trim()) { $texto | ConvertFrom-Json } else { New-Object PSObject }
if (-not $ajustes.PSObject.Properties['hooks']) { Poner $ajustes 'hooks' (New-Object PSObject) }
if (-not $ajustes.PSObject.Properties['env']) { Poner $ajustes 'env' (New-Object PSObject) }

$cambios = 0
foreach ($evento in $eventos.Keys) {
    $grupos = @()
    if ($ajustes.hooks.PSObject.Properties[$evento]) { $grupos = @($ajustes.hooks.$evento) }
    $ajenos = @($grupos | Where-Object { -not (Es-DeCerebrario $_) })
    if ($Quitar) {
        if ($ajenos.Count -eq $grupos.Count) { continue }
        if ($ajenos.Count) { Poner $ajustes.hooks $evento ([object[]]$ajenos) } else { $ajustes.hooks.PSObject.Properties.Remove($evento) }
        $cambios++
        continue
    }
    if ($ajenos.Count -ne $grupos.Count) { continue }
    $hook = [ordered]@{ type = 'command'; command = $comando; timeout = 5 }
    if ($evento -ne 'SessionEnd') { $hook.async = $true }
    $grupo = [ordered]@{}
    if ($eventos[$evento]) { $grupo.matcher = $eventos[$evento] }
    $grupo.hooks = [object[]]@([pscustomobject]$hook)
    Poner $ajustes.hooks $evento ([object[]]($grupos + [pscustomobject]$grupo))
    $cambios++
}
if ($Quitar) { $ajustes.env.PSObject.Properties.Remove('CEREBRO_CONFIG') } else { Poner $ajustes.env 'CEREBRO_CONFIG' $Config }

$json = $ajustes | ConvertTo-Json -Depth 30
$null = $json | ConvertFrom-Json
[IO.File]::WriteAllText($Settings, $json, (New-Object Text.UTF8Encoding $false))

$accion = if ($Quitar) { 'quité' } else { 'agregué' }
Write-Output "Listo: $accion el hook de Cerebrario en $cambios eventos de $Settings."
Write-Output "Respaldo de antes: $respaldo"
Write-Output 'Abra una sesión nueva de Claude Code para que lo tome. Mapa: http://127.0.0.1:8765/cerebro.html'

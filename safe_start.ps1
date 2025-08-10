<#
  Script: safe_start.ps1
  Objetivo:
    - Detener procesos activos del frontend (puerto 3000) y backend (puerto 8001) de esta app
    - Mostrar menú para iniciar la aplicación en modo seguro para:
      1) Local (solo equipo)
      2) WiFi (IP local con HTTPS)
      3) Tailscale (IP privada con HTTPS)

  Requisitos:
    - PowerShell 7+
    - Python del entorno virtual en ./venv (o python en PATH)
    - Node.js y npm en PATH
#>

param()

$ErrorActionPreference = 'Stop'

function Write-Info($msg) { Write-Host "[INFO] $msg" -ForegroundColor Cyan }
function Write-Ok($msg)   { Write-Host "[OK]   $msg" -ForegroundColor Green }
function Write-Warn($msg) { Write-Host "[WARN] $msg" -ForegroundColor Yellow }
function Write-Err($msg)  { Write-Host "[ERR]  $msg" -ForegroundColor Red }

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$BackendDir = Join-Path $Root 'backend'
$FrontendDir = Join-Path $Root 'frontend'
$VenvPython = Join-Path $Root 'venv\Scripts\python.exe'

function Resolve-Python() {
  if (Test-Path $VenvPython) { return $VenvPython }
  Write-Warn 'No se encontró venv\\Scripts\\python.exe, se usará "python" del PATH'
  return 'python'
}

function Test-Command($name) {
  try { $null = Get-Command $name -ErrorAction Stop; return $true } catch { return $false }
}

# Inicia un proceso en una nueva ventana estableciendo variables de entorno mediante cmd.exe
function Start-DetachedWithEnv([string]$WorkDir, [hashtable]$EnvMap, [string]$Exe, [string[]]$Args) {
  $setParts = @()
  if ($EnvMap) {
    foreach ($key in $EnvMap.Keys) {
      $val = $EnvMap[$key]
      # Escapar comillas dobles en valor para cmd
      $val = ($val -replace '"', '\"')
      $setParts += "set $key=$val"
    }
  }
  $argsJoined = ($Args -join ' ')
  $exeQuoted = '"' + $Exe + '"'
  $cmdLine = ($setParts + ("$exeQuoted $argsJoined")) -join ' && '
  Start-Process -FilePath 'cmd.exe' -ArgumentList '/c', $cmdLine -WorkingDirectory $WorkDir -WindowStyle Normal | Out-Null
}

# Abre nueva ventana de consola con título, variables de entorno y deja la sesión abierta
function Start-ConsoleWithEnv([string]$WorkDir, [hashtable]$EnvMap, [string]$Title, [string]$Exe, [string[]]$Args) {
  $setParts = @()
  if ($EnvMap) {
    foreach ($key in $EnvMap.Keys) {
      $val = $EnvMap[$key]
      $setParts += "set $key=$val"
    }
  }
  $argsJoined = ($Args -join ' ')
  $exeQuoted = '"' + $Exe + '"'
  $cmd = "$exeQuoted $argsJoined"
  $joined = ($setParts -join ' & ')
  $sep = ''
  if ($setParts.Count -gt 0) { $sep = ' & ' }
  $envAndCmd = ($joined + $sep + $cmd)
  $titleArg = '"' + $Title + '"'
  Start-Process -FilePath 'cmd.exe' -ArgumentList '/c', 'start', $titleArg, 'cmd', '/k', $envAndCmd -WorkingDirectory $WorkDir -WindowStyle Normal | Out-Null
}

# Inicia una nueva ventana (cmd) con título, variables de entorno y deja la consola abierta
function Start-ConsoleWithEnv([string]$WorkDir, [hashtable]$EnvMap, [string]$Title, [string]$Exe, [string[]]$Args) {
  $setParts = @()
  if ($EnvMap) {
    foreach ($key in $EnvMap.Keys) {
      $val = $EnvMap[$key]
      $setParts += "set $key=$val"
    }
  }
  $argsJoined = ($Args -join ' ')
  $exeQuoted = '"' + $Exe + '"'
  $cmd = "$exeQuoted $argsJoined"
  $envAndCmd = (($setParts -join ' & ') + (if ($setParts.Count -gt 0) { ' & ' } else { '' }) + $cmd)
  Start-Process -FilePath 'cmd.exe' -ArgumentList '/c', 'start', $Title, 'cmd', '/k', $envAndCmd -WorkingDirectory $WorkDir -WindowStyle Normal | Out-Null
}

function Get-LocalLanIP() {
  try {
    $candidates = Get-NetIPAddress -AddressFamily IPv4 -PrefixOrigin Manual,Dhcp -AddressState Preferred -ErrorAction Stop |
      Where-Object {
        $_.IPAddress -notlike '127.*' -and
        $_.IPAddress -notlike '169.254.*' -and (
          $_.IPAddress -like '192.168.*' -or
          $_.IPAddress -like '10.*' -or
          ($_.IPAddress -match '^172\.(1[6-9]|2[0-9]|3[0-1])\..*')
        )
      } |
      Sort-Object -Property InterfaceMetric -Descending:$false
    if ($candidates -and $candidates.Count -gt 0) {
      # Preferir explícitamente 192.168.100.6 si está disponible
      $preferred = $candidates | Where-Object { $_.IPAddress -eq '192.168.100.6' } | Select-Object -First 1
      if ($preferred) { return $preferred.IPAddress }
      return $candidates[0].IPAddress
    }
  } catch {}
  try {
    $fallback = (Get-CimInstance Win32_NetworkAdapterConfiguration | Where-Object { $_.IPEnabled }).IPAddress |
      Where-Object { $_ -match '^\d+\.\d+\.\d+\.\d+$' -and $_ -notlike '127.*' } |
      Select-Object -First 1
    if ($fallback) { return $fallback }
  } catch {}
  return '192.168.100.6'
}

function Get-TailscaleIP() {
  try {
    $ts = Get-NetIPAddress -AddressFamily IPv4 -ErrorAction Stop | Where-Object {
      $_.IPAddress -match '^100\.(6[4-9]|[7-9][0-9]|1[0-1][0-9]|12[0-7])\..*'
    } | Select-Object -First 1 -ExpandProperty IPAddress
    if ($ts) { return $ts }
  } catch {}
  return '100.81.201.68'
}

function Stop-PortProcesses([int[]]$Ports) {
  foreach ($port in $Ports) {
    try {
      $connections = Get-NetTCPConnection -State Listen -LocalPort $port -ErrorAction SilentlyContinue
      if ($null -ne $connections) {
        $pids = $connections | Select-Object -ExpandProperty OwningProcess -Unique
        foreach ($pid in $pids) {
          try {
            $proc = Get-Process -Id $pid -ErrorAction SilentlyContinue
            if ($proc) {
              Write-Info "Terminando proceso PID=$pid (" + $proc.ProcessName + ") en puerto $port"
              Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
            }
          } catch {}
        }
      }
    } catch {}
  }
}

function Stop-AppProcesses() {
  Write-Info 'Deteniendo procesos en puertos 3000 (frontend) y 8001 (backend)'
  Stop-PortProcesses -Ports 3000,8001

  # Intento adicional: terminar node.exe o uvicorn del proyecto si persisten
  try {
    Get-Process node -ErrorAction SilentlyContinue | Where-Object { $_.Path -like '*\\node.exe' } | Stop-Process -Force -ErrorAction SilentlyContinue
  } catch {}
  try {
    Get-Process python -ErrorAction SilentlyContinue | Where-Object { $_.Path -like '*\\venv\\Scripts\\python.exe' } | Stop-Process -Force -ErrorAction SilentlyContinue
  } catch {}
}

function Start-Backend([string]$BackendHost, [int]$BackendPort, [bool]$UseSsl, [string]$AllowedOrigins) {
  $python = Resolve-Python
  $venvDir = Join-Path $Root 'venv'
  $venvScripts = Join-Path $venvDir 'Scripts'
  $envMap = @{
    'HOST'           = $BackendHost
    'PORT'           = "$BackendPort"
    'USE_SSL'        = if ($UseSsl) { 'true' } else { 'false' }
    'LOG_LEVEL'      = 'info'
    'RELOAD'         = 'false'
    'ALLOWED_ORIGINS'= $AllowedOrigins
    'VIRTUAL_ENV'    = $venvDir
    'PATH'           = "$venvScripts;$BackendDir;" + $env:PATH
  }
  Write-Info "Iniciando backend (HOST=$BackendHost, PORT=$BackendPort, SSL=$UseSsl) con entorno virtual"
  Start-ConsoleWithEnv -WorkDir $BackendDir -EnvMap $envMap -Title 'Backend (Uvicorn/SSL)' -Exe $python -Args @('start_server.py')
}

function Start-Frontend([string]$ApiBaseUrl, [bool]$BindLan) {
  if (-not (Test-Command 'npm')) { throw 'npm no está disponible en PATH' }
  $envMap = @{}
  if ($ApiBaseUrl) { $envMap['REACT_APP_API_BASE_URL'] = $ApiBaseUrl }
  if ($BindLan)     { $envMap['HOST'] = '0.0.0.0' }

  $args = @('start')
  $apiDisplay = if ($null -ne $ApiBaseUrl -and $ApiBaseUrl -ne '') { $ApiBaseUrl } else { '' }
  $hostDisplay = if ($BindLan) { '0.0.0.0' } else { 'default' }
  Write-Info ("Iniciando frontend (REACT_APP_API_BASE_URL='{0}', HOST={1})" -f $apiDisplay, $hostDisplay)
  Start-ConsoleWithEnv -WorkDir $FrontendDir -EnvMap $envMap -Title 'Frontend (React Dev Server)' -Exe 'npm' -Args $args
}

function Show-Menu() {
  Write-Host ''
  Write-Host '============================================='
  Write-Host ' Biblioteca Inteligente - Inicio Seguro' -ForegroundColor Magenta
  Write-Host '============================================='
  Write-Host ' 1) Local (HTTP, solo este equipo)'
  Write-Host (" 2) WiFi  (HTTPS, IP local {0})" -f $WifiIP)
  Write-Host (" 3) Tailscale (HTTPS, IP {0})" -f $TailIP)
  Write-Host ' 5) Configurar Firewall (crear reglas 3000/8001)'
  Write-Host ' 6) Eliminar Reglas de Firewall creadas'
  Write-Host ' 4) Salir'
  Write-Host ''
}

# Valores por defecto (autodetección)
$WifiIP = Get-LocalLanIP
$TailIP = Get-TailscaleIP
$Port = 8001

function Test-IsAdmin() {
  $wi = [Security.Principal.WindowsIdentity]::GetCurrent()
  $wp = New-Object Security.Principal.WindowsPrincipal($wi)
  return $wp.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Ensure-FirewallRules([string]$WifiIP, [string]$TailCIDR = '100.64.0.0/10') {
  if (-not (Test-IsAdmin)) { throw 'Se requieren privilegios de administrador para modificar el firewall.' }

  $rules = @(
    @{ Name = 'Biblioteca Backend SSL 8001 (Privado)';  Port = 8001; Profile = 'Private,Domain'; Remote='Any' },
    @{ Name = 'Biblioteca Backend SSL 8001 (Tailscale)';Port = 8001; Profile = 'Private,Domain'; Remote=$TailCIDR },
    @{ Name = 'Biblioteca Frontend 3000 (Privado)';     Port = 3000; Profile = 'Private,Domain'; Remote='Any' },
    @{ Name = 'Biblioteca Frontend 3000 (Tailscale)';   Port = 3000; Profile = 'Private,Domain'; Remote=$TailCIDR }
  )

  foreach ($r in $rules) {
    $exists = Get-NetFirewallRule -DisplayName $r.Name -ErrorAction SilentlyContinue
    if ($null -eq $exists) {
      Write-Info "Creando regla de firewall: $($r.Name)"
      if ($r.Remote -eq 'Any') {
        New-NetFirewallRule -DisplayName $r.Name -Direction Inbound -Protocol TCP -LocalPort $r.Port -Action Allow -Profile $r.Profile | Out-Null
      } else {
        New-NetFirewallRule -DisplayName $r.Name -Direction Inbound -Protocol TCP -LocalPort $r.Port -Action Allow -Profile $r.Profile -RemoteAddress $r.Remote | Out-Null
      }
    } else {
      Write-Ok "Regla ya existente: $($r.Name)"
    }
  }
}

function Remove-FirewallRules() {
  if (-not (Test-IsAdmin)) { throw 'Se requieren privilegios de administrador para modificar el firewall.' }
  $names = @(
    'Biblioteca Backend SSL 8001 (Privado)',
    'Biblioteca Backend SSL 8001 (Tailscale)',
    'Biblioteca Frontend 3000 (Privado)',
    'Biblioteca Frontend 3000 (Tailscale)'
  )
  foreach ($n in $names) {
    $rule = Get-NetFirewallRule -DisplayName $n -ErrorAction SilentlyContinue
    if ($rule) {
      Write-Info "Eliminando regla: $n"
      $rule | Remove-NetFirewallRule -ErrorAction SilentlyContinue
    } else {
      Write-Warn "No existe la regla: $n"
    }
  }
}

try {
  Stop-AppProcesses

  do {
    Show-Menu
    $choice = Read-Host 'Selecciona una opción (1-6)'

    switch ($choice) {
      '1' {
        Write-Host ''
        Write-Ok 'Modo Local (HTTP)'
        # Backend HTTP local
        Start-Backend -BackendHost '127.0.0.1' -BackendPort $Port -UseSsl:$false -AllowedOrigins 'http://localhost:3000,https://localhost:3000'
        Start-Sleep -Seconds 2
        # Frontend usando proxy dev
        Start-Frontend -ApiBaseUrl '' -BindLan:$false
        Write-Host ''
        Write-Info 'Abre en tu PC: http://localhost:3000'
        break
      }
      '2' {
        Write-Host ''
        $WifiIP = Get-LocalLanIP
        Write-Ok "Modo WiFi (HTTPS) - IP: $WifiIP"
        try { Ensure-FirewallRules -WifiIP $WifiIP } catch { Write-Warn $_ }
        $api = "https://$($WifiIP):$Port"
        $allowed = "http://$WifiIP:3000,https://$WifiIP:3000,http://localhost:3000,https://localhost:3000"
        Start-Backend -BackendHost '0.0.0.0' -BackendPort $Port -UseSsl:$true -AllowedOrigins $allowed
        Start-Sleep -Seconds 2
        Start-Frontend -ApiBaseUrl $api -BindLan:$true
        Write-Host ''
        Write-Info "Desde el celular (misma WiFi): http://$WifiIP:3000"
        Write-Info "Probar API:  curl -k https://$($WifiIP):$Port/api/drive/status"
        break
      }
      '3' {
        Write-Host ''
        $TailIP = Get-TailscaleIP
        Write-Ok "Modo Tailscale (HTTPS) - IP: $TailIP"
        try { Ensure-FirewallRules -WifiIP $WifiIP } catch { Write-Warn $_ }
        $api = "https://$($TailIP):$Port"
        $allowed = "http://$TailIP:3000,https://$TailIP:3000,http://localhost:3000,https://localhost:3000"
        Start-Backend -BackendHost '0.0.0.0' -BackendPort $Port -UseSsl:$true -AllowedOrigins $allowed
        Start-Sleep -Seconds 2
        Start-Frontend -ApiBaseUrl $api -BindLan:$true
        Write-Host ''
        Write-Info "Desde el celular (Tailscale): http://$TailIP:3000"
        Write-Info "Probar API:  curl -k https://$($TailIP):$Port/api/drive/status"
        break
      }
      '5' {
        try {
          Ensure-FirewallRules -WifiIP $WifiIP
          Write-Ok 'Reglas de firewall creadas/verificadas.'
        } catch { Write-Err $_ }
        continue
      }
      '6' {
        try {
          Remove-FirewallRules
          Write-Ok 'Reglas de firewall eliminadas.'
        } catch { Write-Err $_ }
        continue
      }
      '4' {
        Write-Info 'Saliendo.'
        return
      }
      Default {
        Write-Warn 'Opción inválida.'
      }
    }
  } while ($true)
}
catch {
  Write-Err $_
  exit 1
}

Write-Host ''
Write-Ok 'Procesos iniciados en ventanas separadas.'
Write-Info 'Para detenerlos, cierra las ventanas o vuelve a ejecutar este script (detendrá puertos 3000/8001).'



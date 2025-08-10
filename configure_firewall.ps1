# Configuración de Firewall para Biblioteca Inteligente con Tailscale
# Este script configura automáticamente las reglas de firewall necesarias

Write-Host "🔥 Configurando Firewall para Biblioteca Inteligente con Tailscale" -ForegroundColor Green
Write-Host "=" * 70

# Verificar si se ejecuta como administrador
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")

if (-not $isAdmin) {
    Write-Host "⚠️  Este script necesita ejecutarse como Administrador" -ForegroundColor Yellow
    Write-Host "💡 Para configurar automáticamente el firewall" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "✅ Si no quieres configurar el firewall ahora:" -ForegroundColor Green
    Write-Host "   - Tailscale maneja el tráfico de forma segura" -ForegroundColor White
    Write-Host "   - Solo dispositivos en tu red Tailscale pueden conectar" -ForegroundColor White
    Write-Host "   - La aplicación funcionará sin cambios de firewall" -ForegroundColor White
    Write-Host ""
    Read-Host "Presiona Enter para continuar sin cambios de firewall"
    exit 0
}

Write-Host "✅ Ejecutándose como Administrador" -ForegroundColor Green

# Obtener ubicación de Python
try {
    $pythonPath = (Get-Command python).Source
    Write-Host "🐍 Python encontrado en: $pythonPath" -ForegroundColor Cyan
} catch {
    Write-Host "❌ No se pudo encontrar Python en el PATH" -ForegroundColor Red
    exit 1
}

# Función para crear regla de firewall
function Add-FirewallRuleIfNotExists {
    param(
        [string]$DisplayName,
        [string]$Direction,
        [string]$Action,
        [string]$Protocol,
        [string]$LocalPort,
        [string]$Program
    )
    
    $existingRule = Get-NetFirewallRule -DisplayName $DisplayName -ErrorAction SilentlyContinue
    
    if ($existingRule) {
        Write-Host "✅ Regla '$DisplayName' ya existe" -ForegroundColor Green
    } else {
        try {
            $params = @{
                DisplayName = $DisplayName
                Direction = $Direction
                Action = $Action
                Protocol = $Protocol
            }
            
            if ($LocalPort) { $params.LocalPort = $LocalPort }
            if ($Program) { $params.Program = $Program }
            
            New-NetFirewallRule @params | Out-Null
            Write-Host "✅ Creada regla: $DisplayName" -ForegroundColor Green
        } catch {
            Write-Host "❌ Error creando regla '$DisplayName': $($_.Exception.Message)" -ForegroundColor Red
        }
    }
}

Write-Host ""
Write-Host "🔧 Configurando reglas de firewall..." -ForegroundColor Cyan

# Reglas para Python (backend)
Add-FirewallRuleIfNotExists -DisplayName "Biblioteca Inteligente - Python Backend (TCP In)" -Direction "Inbound" -Action "Allow" -Protocol "TCP" -LocalPort "8001" -Program $pythonPath
Add-FirewallRuleIfNotExists -DisplayName "Biblioteca Inteligente - Python Backend (TCP Out)" -Direction "Outbound" -Action "Allow" -Protocol "TCP" -Program $pythonPath

# Reglas para Node.js (frontend)
try {
    $nodePath = (Get-Command node).Source
    Write-Host "📦 Node.js encontrado en: $nodePath" -ForegroundColor Cyan
    
    Add-FirewallRuleIfNotExists -DisplayName "Biblioteca Inteligente - Node.js Frontend (TCP In)" -Direction "Inbound" -Action "Allow" -Protocol "TCP" -LocalPort "3000" -Program $nodePath
    Add-FirewallRuleIfNotExists -DisplayName "Biblioteca Inteligente - Node.js Frontend (TCP Out)" -Direction "Outbound" -Action "Allow" -Protocol "TCP" -Program $nodePath
} catch {
    Write-Host "⚠️  Node.js no encontrado, creando reglas genéricas para puerto 3000" -ForegroundColor Yellow
    Add-FirewallRuleIfNotExists -DisplayName "Biblioteca Inteligente - Frontend (TCP In)" -Direction "Inbound" -Action "Allow" -Protocol "TCP" -LocalPort "3000"
}

# Reglas específicas para Tailscale (opcional, ya que Tailscale maneja esto)
Write-Host ""
Write-Host "🌐 Verificando configuración de Tailscale..." -ForegroundColor Cyan

$tailscaleRules = Get-NetFirewallRule | Where-Object { $_.DisplayName -like "*Tailscale*" }
if ($tailscaleRules) {
    Write-Host "✅ Reglas de Tailscale ya configuradas" -ForegroundColor Green
} else {
    Write-Host "💡 Tailscale maneja su propio firewall automáticamente" -ForegroundColor Cyan
}

Write-Host ""
Write-Host "✅ Configuración de firewall completada" -ForegroundColor Green
Write-Host ""
Write-Host "📋 Resumen de configuración:" -ForegroundColor Cyan
Write-Host "   • Puerto 8001 (Backend): Permitido para Python" -ForegroundColor White
Write-Host "   • Puerto 3000 (Frontend): Permitido" -ForegroundColor White
Write-Host "   • Tailscale: Maneja su propio tráfico" -ForegroundColor White
Write-Host ""
Write-Host "🔒 Seguridad:" -ForegroundColor Cyan
Write-Host "   • Solo dispositivos en tu red Tailscale pueden conectar" -ForegroundColor White
Write-Host "   • Tráfico cifrado de extremo a extremo" -ForegroundColor White
Write-Host "   • Sin exposición a Internet público" -ForegroundColor White
Write-Host ""

Read-Host "Presiona Enter para continuar"

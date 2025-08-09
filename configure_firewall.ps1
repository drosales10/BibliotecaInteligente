# Script para configurar el firewall de Windows
# Ejecutar como administrador y con PowerShell Set-ExecutionPolicy Unrestricted

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Configuración del Firewall de Windows" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Verificar si se ejecuta como administrador
if (-NOT ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Host "❌ ERROR: Este script debe ejecutarse como Administrador" -ForegroundColor Red
    Write-Host ""
    Write-Host "Por favor:" -ForegroundColor Yellow
    Write-Host "1. Haz clic derecho en este archivo" -ForegroundColor White
    Write-Host "2. Selecciona 'Ejecutar como administrador'" -ForegroundColor White
    Write-Host "3. Ejecuta el script nuevamente" -ForegroundColor White
    Write-Host ""
    Read-Host "Presiona Enter para continuar"
    exit 1
}

Write-Host "✅ Ejecutando como administrador" -ForegroundColor Green
Write-Host ""

Write-Host "🔥 Configurando reglas del firewall..." -ForegroundColor Yellow
Write-Host ""

# Crear regla para el puerto 3000 (Frontend)
Write-Host "Configurando puerto 3000 (Frontend)..." -ForegroundColor Gray
try {
    New-NetFirewallRule -DisplayName "Biblioteca Inteligente - Frontend" -Direction Inbound -Protocol TCP -LocalPort 3000 -Action Allow -Profile Any
    Write-Host "✅ Regla creada para puerto 3000 (Frontend)" -ForegroundColor Green
} catch {
    Write-Host "❌ Error al crear regla para puerto 3000: $($_.Exception.Message)" -ForegroundColor Red
}

# Crear regla para el puerto 8001 (Backend)
Write-Host "Configurando puerto 8001 (Backend)..." -ForegroundColor Gray
try {
    New-NetFirewallRule -DisplayName "Biblioteca Inteligente - Backend" -Direction Inbound -Protocol TCP -LocalPort 8001 -Action Allow -Profile Any
    Write-Host "✅ Regla creada para puerto 8001 (Backend)" -ForegroundColor Green
} catch {
    Write-Host "❌ Error al crear regla para puerto 8001: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""
Write-Host "🔍 Verificando reglas creadas..." -ForegroundColor Yellow
Write-Host ""

# Verificar reglas creadas
Write-Host "Reglas del firewall para Biblioteca Inteligente:" -ForegroundColor Cyan
try {
    Get-NetFirewallRule -DisplayName "Biblioteca Inteligente*" | Format-Table DisplayName, Enabled, Direction, Action, Profile
    Write-Host "✅ Reglas verificadas correctamente" -ForegroundColor Green
} catch {
    Write-Host "❌ Error al verificar reglas: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Configuración Completada" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "✅ Firewall configurado para permitir acceso remoto" -ForegroundColor Green
Write-Host ""
Write-Host "URLs de acceso:" -ForegroundColor Yellow
Write-Host "  Frontend: http://192.168.100.6:3000" -ForegroundColor White
Write-Host "  Backend:  http://192.168.100.6:8001" -ForegroundColor White
Write-Host ""
Write-Host "Ahora otros dispositivos en la misma red WiFi" -ForegroundColor Gray
Write-Host "deberían poder acceder a tu aplicación." -ForegroundColor Gray
Write-Host ""
Read-Host "Presiona Enter para continuar"

# Script para configurar el firewall para acceso móvil con HTTPS
# Ejecutar como administrador

Write-Host "========================================" -ForegroundColor Green
Write-Host "  Configurando Firewall para Móviles" -ForegroundColor Green
Write-Host "  con Soporte HTTPS" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

Write-Host "Configurando reglas del firewall para permitir conexiones desde dispositivos móviles..." -ForegroundColor Yellow
Write-Host ""

try {
    # Verificar si las reglas ya existen
    $existingRule = Get-NetFirewallRule -DisplayName "Biblioteca Inteligente Backend - Entrada" -ErrorAction SilentlyContinue
    
    if ($existingRule) {
        Write-Host "🔄 Reglas del firewall ya existen, actualizando..." -ForegroundColor Yellow
        
        # Actualizar regla existente
        Set-NetFirewallRule -DisplayName "Biblioteca Inteligente Backend - Entrada" -Direction Inbound -Protocol TCP -LocalPort 8001 -Action Allow -Profile Any -Enabled True
        Set-NetFirewallRule -DisplayName "Biblioteca Inteligente Backend - Salida" -Direction Outbound -Protocol TCP -LocalPort 8001 -Action Allow -Profile Any -Enabled True
        
        Write-Host "✅ Reglas del firewall actualizadas exitosamente." -ForegroundColor Green
    } else {
        # Agregar regla para permitir conexiones entrantes al puerto 8001
        New-NetFirewallRule -DisplayName "Biblioteca Inteligente Backend - Entrada" -Direction Inbound -Protocol TCP -LocalPort 8001 -Action Allow -Profile Any
        
        # Agregar regla para permitir conexiones salientes al puerto 8001
        New-NetFirewallRule -DisplayName "Biblioteca Inteligente Backend - Salida" -Direction Outbound -Protocol TCP -LocalPort 8001 -Action Allow -Profile Any
        
        Write-Host "✅ Reglas del firewall configuradas exitosamente." -ForegroundColor Green
    }
    
    Write-Host ""
    Write-Host "🔒 Configuración del firewall completada!" -ForegroundColor Green
    Write-Host ""
    Write-Host "📱 Ahora puedes acceder desde tu celular usando:" -ForegroundColor Cyan
    Write-Host "   HTTP:  http://192.168.100.6:8001" -ForegroundColor White
    Write-Host "   HTTPS: https://192.168.100.6:8001 (recomendado)" -ForegroundColor Green
    Write-Host ""
    Write-Host "💡 Para habilitar HTTPS:" -ForegroundColor Yellow
    Write-Host "   1. Instala OpenSSL desde: https://slproweb.com/products/Win32OpenSSL.html" -ForegroundColor White
    Write-Host "   2. Ejecuta: cd backend && python generate_ssl.py" -ForegroundColor White
    Write-Host "   3. Inicia el servidor con: start_ssl_backend.bat" -ForegroundColor White
    Write-Host ""
    
} catch {
    Write-Host "❌ Error al configurar el firewall: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "💡 Asegúrate de ejecutar PowerShell como administrador" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "🔍 Solución de problemas:" -ForegroundColor Yellow
    Write-Host "   1. Cierra PowerShell y ábrelo como administrador" -ForegroundColor White
    Write-Host "   2. Verifica que el servicio de firewall esté habilitado" -ForegroundColor White
    Write-Host "   3. Ejecuta: Get-Service -Name MpsSvc" -ForegroundColor White
}

Write-Host "Presiona cualquier tecla para continuar..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

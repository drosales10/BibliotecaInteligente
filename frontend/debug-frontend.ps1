# Script de diagnóstico y solución para el frontend
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   Diagnóstico Frontend - Libreria Inteligente" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Verificar Node.js
Write-Host "1. Verificando Node.js..." -ForegroundColor Yellow
try {
    $nodeVersion = node --version
    Write-Host "   ✓ Node.js encontrado: $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "   ✗ Node.js no encontrado" -ForegroundColor Red
    Write-Host "   Instala Node.js desde https://nodejs.org/" -ForegroundColor Red
    exit 1
}

# Verificar npm
Write-Host "2. Verificando npm..." -ForegroundColor Yellow
try {
    $npmVersion = npm --version
    Write-Host "   ✓ npm encontrado: $npmVersion" -ForegroundColor Green
} catch {
    Write-Host "   ✗ npm no encontrado" -ForegroundColor Red
    exit 1
}

# Verificar puertos
Write-Host "3. Verificando puertos..." -ForegroundColor Yellow
$port3000 = Get-NetTCPConnection -LocalPort 3000 -ErrorAction SilentlyContinue
$port8001 = Get-NetTCPConnection -LocalPort 8001 -ErrorAction SilentlyContinue

if ($port3000) {
    Write-Host "   ⚠ Puerto 3000 en uso por PID: $($port3000.OwningProcess)" -ForegroundColor Yellow
} else {
    Write-Host "   ✓ Puerto 3000 disponible" -ForegroundColor Green
}

if ($port8001) {
    Write-Host "   ✓ Backend ejecutándose en puerto 8001" -ForegroundColor Green
} else {
    Write-Host "   ⚠ Backend no encontrado en puerto 8001" -ForegroundColor Yellow
}

# Verificar dependencias
Write-Host "4. Verificando dependencias..." -ForegroundColor Yellow
if (Test-Path "node_modules") {
    Write-Host "   ✓ node_modules encontrado" -ForegroundColor Green
} else {
    Write-Host "   ⚠ node_modules no encontrado, instalando..." -ForegroundColor Yellow
    npm install
}

# Verificar package.json
Write-Host "5. Verificando package.json..." -ForegroundColor Yellow
if (Test-Path "package.json") {
    $packageJson = Get-Content "package.json" | ConvertFrom-Json
    Write-Host "   ✓ package.json válido" -ForegroundColor Green
    Write-Host "   React versión: $($packageJson.dependencies.react)" -ForegroundColor Gray
} else {
    Write-Host "   ✗ package.json no encontrado" -ForegroundColor Red
    exit 1
}

# Limpiar caché
Write-Host "6. Limpiando caché..." -ForegroundColor Yellow
npm cache clean --force
Write-Host "   ✓ Caché limpiado" -ForegroundColor Green

# Intentar diferentes métodos de inicio
Write-Host ""
Write-Host "7. Intentando iniciar servidor..." -ForegroundColor Yellow

# Método 1: React Scripts normal
Write-Host "   Método 1: React Scripts..." -ForegroundColor Gray
try {
    Start-Process -FilePath "npm" -ArgumentList "start" -NoNewWindow -PassThru
    Write-Host "   ✓ Servidor iniciado con React Scripts" -ForegroundColor Green
    exit 0
} catch {
    Write-Host "   ✗ Falló React Scripts" -ForegroundColor Red
}

# Método 2: Puerto alternativo
Write-Host "   Método 2: Puerto alternativo..." -ForegroundColor Gray
try {
    $env:PORT = "3001"
    Start-Process -FilePath "npm" -ArgumentList "start" -NoNewWindow -PassThru
    Write-Host "   ✓ Servidor iniciado en puerto 3001" -ForegroundColor Green
    exit 0
} catch {
    Write-Host "   ✗ Falló puerto alternativo" -ForegroundColor Red
}

# Método 3: Vite (si está disponible)
Write-Host "   Método 3: Vite..." -ForegroundColor Gray
if (Test-Path "vite.config.js") {
    try {
        npm install vite @vitejs/plugin-react
        Start-Process -FilePath "npm" -ArgumentList "run", "dev" -NoNewWindow -PassThru
        Write-Host "   ✓ Servidor iniciado con Vite" -ForegroundColor Green
        exit 0
    } catch {
        Write-Host "   ✗ Falló Vite" -ForegroundColor Red
    }
} else {
    Write-Host "   ⚠ Vite no configurado" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "❌ No se pudo iniciar el servidor con ningún método" -ForegroundColor Red
Write-Host ""
Write-Host "Sugerencias:" -ForegroundColor Yellow
Write-Host "1. Verifica que no haya otros procesos usando el puerto 3000" -ForegroundColor White
Write-Host "2. Revisa los logs de error arriba" -ForegroundColor White
Write-Host "3. Considera usar Vite como alternativa" -ForegroundColor White
Write-Host "4. Reinstala las dependencias: rm -rf node_modules && npm install" -ForegroundColor White

Read-Host "Presiona Enter para continuar" 
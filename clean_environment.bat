@echo off
echo ========================================
echo Limpiando entorno virtual de Python
echo ========================================
echo.

REM Verificar si el entorno virtual existe
if exist "venv" (
    echo ADVERTENCIA: Esto eliminará completamente el entorno virtual actual
    echo y todas las dependencias instaladas.
    echo.
    set /p confirm="¿Estás seguro de que quieres continuar? (s/N): "
    
    if /i "%confirm%"=="s" (
        echo.
        echo Eliminando entorno virtual...
        rmdir /s /q venv
        echo Entorno virtual eliminado
        echo.
        echo Para recrear el entorno virtual, ejecuta:
        echo   setup_environment.bat
    ) else (
        echo Operación cancelada
    )
) else (
    echo No existe ningún entorno virtual para limpiar
    echo.
    echo Para crear un nuevo entorno virtual, ejecuta:
    echo   setup_environment.bat
)

echo.
pause 
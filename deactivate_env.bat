@echo off
echo ========================================
echo Desactivando entorno virtual de Python
echo ========================================
echo.

REM Verificar si el entorno virtual está activado
if defined VIRTUAL_ENV (
    echo Entorno virtual activado: %VIRTUAL_ENV%
    echo.
    
    REM Desactivar el entorno virtual
    call venv\Scripts\deactivate.bat
    
    echo Entorno virtual desactivado exitosamente
    echo Ahora estás usando Python del sistema
) else (
    echo No hay ningún entorno virtual activado
)

echo.
echo Para reactivar el entorno virtual:
echo   venv\Scripts\activate.bat
echo.
pause 
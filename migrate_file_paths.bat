@echo off
echo ========================================
echo Script de Migracion de Rutas de Archivos
echo ========================================
echo.

echo Iniciando migracion...
echo.

cd backend
python migrate_file_paths.py

echo.
echo Presiona cualquier tecla para continuar...
pause >nul

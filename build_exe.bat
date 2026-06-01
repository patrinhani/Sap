@echo off
setlocal
chcp 65001 >nul

cd /d "%~dp0"

set "PYTHON=.venv\Scripts\python.exe"
set "APP_NAME=SapAutomacao"

if not exist "%PYTHON%" (
    echo Python da venv nao encontrado em %PYTHON%.
    exit /b 1
)

"%PYTHON%" icon_utils.py
if errorlevel 1 (
    echo Falha ao preparar o icone do aplicativo.
    exit /b 1
)

"%PYTHON%" -m PyInstaller ^
    --noconfirm ^
    --clean ^
    --onefile ^
    --noupx ^
    --windowed ^
    --name "%APP_NAME%" ^
    --icon "assets\gcb_icone.ico" ^
    --add-data "assets\gcb_icone.ico;assets" ^
    --add-data "GUIA_INTERFACE.html;." ^
    --add-data "MANUAL_DE_USO.html;." ^
    --collect-submodules automations ^
    --hidden-import pythoncom ^
    --hidden-import pywintypes ^
    --hidden-import win32com ^
    --hidden-import win32com.client ^
    --hidden-import win32con ^
    --hidden-import win32gui ^
    --hidden-import win32timezone ^
    main.py

if errorlevel 1 (
    echo Falha ao gerar o executavel.
    exit /b 1
)

copy /Y "MANUAL_DE_USO.html" "dist\MANUAL_DE_USO.html" >nul
copy /Y "ABRIR_MANUAL.bat" "dist\ABRIR_MANUAL.bat" >nul
copy /Y "GUIA_INTERFACE.html" "dist\GUIA_INTERFACE.html" >nul
copy /Y "ABRIR_GUIA_INTERFACE.bat" "dist\ABRIR_GUIA_INTERFACE.bat" >nul

echo Executavel gerado em dist\%APP_NAME%.exe
echo Guia da interface copiado para dist\GUIA_INTERFACE.html

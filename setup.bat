@echo off
setlocal enabledelayedexpansion
title N64 Emu Setup Installer
cd /d "%~dp0"
set "APP_DIR=%CD%"
set "PYTHON=%APP_DIR%\.venv\Scripts\python.exe"

mode con cols=72 lines=28
color 0A

echo.
echo   ========================================================
echo         N64 Emu Setup Installer
echo         Automatic setup - just let it run
echo   ========================================================
echo.
echo   Install folder: %APP_DIR%
echo.

:: ── Step 1: Find Python ──────────────────────────────────────

echo   [1/6] Checking for Python...

python --version >nul 2>&1
if %ERRORLEVEL% EQU 0 goto :create_venv

py --version >nul 2>&1
if %ERRORLEVEL% EQU 0 goto :create_venv

echo   [..]  Python not found. Attempting auto-install...
goto :install_python

:install_python
where winget >nul 2>&1
if errorlevel 1 goto :download_python

echo   [..]  Installing Python via winget...
winget install Python.Python.3.12 --accept-source-agreements --accept-package-agreements --silent >nul 2>&1
if %ERRORLEVEL% EQU 0 goto :create_venv

:download_python
echo   [..]  Downloading Python installer...
powershell -Command "& {[Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12; Invoke-WebRequest 'https://www.python.org/ftp/python/3.12.9/python-3.12.9-amd64.exe' -OutFile '%TEMP%\python-installer.exe' -UseBasicParsing}" >nul 2>&1

if not exist "%TEMP%\python-installer.exe" (
    echo   [FAIL] Could not download Python.
    echo   Install manually: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo   [..]  Installing Python...
start /wait "" "%TEMP%\python-installer.exe" /quiet InstallAllUsers=1 PrependPath=1 Include_test=0
del "%TEMP%\python-installer.exe" 2>nul

for /f "tokens=*" %%a in ('powershell -Command "[Environment]::GetEnvironmentVariable('Path','Machine')"') do set "PATH=%PATH%;%%a"
for /f "tokens=*" %%b in ('powershell -Command "[Environment]::GetEnvironmentVariable('Path','User')"') do set "PATH=%PATH%;%%b"

python --version >nul 2>&1
if errorlevel 1 (
    echo   [FAIL] Python install failed.
    echo   Install manually: https://www.python.org/downloads/
    pause
    exit /b 1
)
echo   [OK]  Python installed

:: ── Step 2: Create Virtual Environment ───────────────────────

:create_venv
echo   [2/6] Creating virtual environment...

if exist "%PYTHON%" (
    echo   [OK]  Virtual environment ready
    goto :install_pillow
)

python -m venv .venv
if errorlevel 1 (
    echo   [FAIL] Could not create virtual environment.
    pause
    exit /b 1
)
echo   [OK]  Virtual environment created

:: ── Step 3: Install Pillow ────────────────────────────────────

:install_pillow
echo   [3/6] Installing Pillow...
"%PYTHON%" -m pip install Pillow --quiet
if errorlevel 1 (
    echo   [WARN] Pillow install had minor issues
)
echo   [OK]  Pillow installed

:: ── Step 4: Generate Desktop Icon ─────────────────────────────

:generate_icon
echo   [4/6] Generating N64 desktop icon...
if not exist "assets\generate_icon.py" goto :create_shortcut

"%PYTHON%" assets\generate_icon.py
if errorlevel 1 (
    echo   [WARN] Icon generation had issues (non-critical)
    goto :create_shortcut
)
echo   [OK]  Icon generated

:: ── Step 5: Create Desktop Shortcut ───────────────────────────

:create_shortcut
echo   [5/6] Creating desktop shortcut...

set "SHORTCUT_FILE=%USERPROFILE%\Desktop\N64 Emu Setup.lnk"
set "VBS=%TEMP%\n64_shortcut.vbs"

echo Set ws = WScript.CreateObject("WScript.Shell") > "%VBS%"
echo Set sc = ws.CreateShortcut("%SHORTCUT_FILE%") >> "%VBS%"
echo sc.TargetPath = "%PYTHON%" >> "%VBS%"
echo sc.Arguments = "%APP_DIR%\n64_emu_setup.py" >> "%VBS%"
echo sc.WorkingDirectory = "%APP_DIR%" >> "%VBS%"
echo sc.Description = "N64 Emu Setup" >> "%VBS%"
if exist "assets\n64_icon.ico" (
    echo sc.IconLocation = "%APP_DIR%\assets\n64_icon.ico, 0" >> "%VBS%"
)
echo sc.Save >> "%VBS%"

cscript //nologo "%VBS%" >nul 2>&1
del "%VBS%" 2>nul

if exist "%SHORTCUT_FILE%" (
    echo   [OK]  Desktop shortcut created
) else (
    echo   [WARN] Could not create shortcut
)

:: ── Step 6: Create ROM Folders ────────────────────────────────

echo   [6/6] Creating ROM folders...

mkdir "roms\n64\zelda_ocarina_of_time" 2>nul
mkdir "roms\n64\super_smash_bros" 2>nul
mkdir "roms\other" 2>nul

if not exist "roms\README.txt" (
    echo N64 Emu Setup - ROMs Folder > "roms\README.txt"
    echo. >> "roms\README.txt"
    echo Where to put your game files: >> "roms\README.txt"
    echo. >> "roms\README.txt"
    echo   Zelda - Ocarina of Time --^> n64\zelda_ocarina_of_time\ >> "roms\README.txt"
    echo   Super Smash Bros. 64 --^> n64\super_smash_bros\ >> "roms\README.txt"
    echo   Other N64 games --^> other\ >> "roms\README.txt"
    echo. >> "roms\README.txt"
    echo Supported formats: .z64, .n64, .v64, .rom >> "roms\README.txt"
)

:: Try to copy Zelda ROM from Downloads
set "ZELDA_ROM=%USERPROFILE%\Downloads\The Legend of Zelda - Ocarina of Time.es.z64"
if exist "%ZELDA_ROM%" (
    echo   [..]  Found Zelda ROM in Downloads. Copying...
    copy "%ZELDA_ROM%" "roms\n64\zelda_ocarina_of_time\" /Y >nul 2>&1
    if errorlevel 1 (
        echo   [WARN] Could not copy ROM
    ) else (
        echo   [OK]  Zelda ROM copied to roms folder
    )
)

echo   [OK]  ROM folders ready

:: ── Done ──────────────────────────────────────────────────────

echo.
echo   ========================================================
echo          INSTALLATION COMPLETE!
echo.
echo          Desktop shortcut: N64 Emu Setup
echo          ROMs folder: %APP_DIR%\roms
echo.
echo          Launching the app now...
echo   ========================================================
echo.

start "" "%PYTHON%" "n64_emu_setup.py"
exit /b 0

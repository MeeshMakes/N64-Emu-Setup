#!/usr/bin/env pwsh
<#
.SYNOPSIS
    N64 Emu Setup - One-command installer for Windows
.DESCRIPTION
    Downloads, installs, and creates a desktop shortcut for the N64 Emu Setup app.
    Run this from CMD with: powershell -ExecutionPolicy Bypass -File setup_windows.ps1
#>

$ErrorActionPreference = "Stop"
$Host.UI.RawUI.WindowTitle = "N64 Emu Setup Installer"

# --- Config -------------------------------------------------------
$RepoUrl     = "https://github.com/MeeshMakes/N64-Emu-Setup"
$Branch      = "master"
$InstallDir  = "$env:USERPROFILE\N64-Emu-Setup"
$DesktopPath = [Environment]::GetFolderPath("Desktop")
$ShortcutPath = "$DesktopPath\N64 Emu Setup.lnk"
$IconIco     = "$InstallDir\assets\n64_icon.ico"
$AppScript   = "$InstallDir\n64_emu_setup.py"
$PythonReq   = "3.8.0"

# --- Helper Functions ---------------------------------------------

function Write-Log($Text, $Color = "Cyan") {
    $ts = Get-Date -Format "HH:mm:ss"
    Write-Host "[$ts] " -NoNewline -ForegroundColor DarkGray
    Write-Host $Text -ForegroundColor $Color
}

function Test-Command($Name) {
    return [bool](Get-Command $Name -ErrorAction SilentlyContinue)
}

function Get-PythonVersion {
    try {
        $v = & python --version 2>&1
        if ($v -match "Python (\d+\.\d+\.\d+)") {
            return [version]$Matches[1]
        }
    } catch {}
    try {
        $v = & python3 --version 2>&1
        if ($v -match "Python (\d+\.\d+\.\d+)") {
            return [version]$Matches[1]
        }
    } catch {}
    return $null
}

function Install-PythonIfMissing {
    $pyVer = Get-PythonVersion
    if ($pyVer -and $pyVer -ge [version]$PythonReq) {
        Write-Log "[OK] Python $pyVer found" Green
        return $true
    }

    $foundVer = if ($pyVer) { $pyVer.ToString() } else { "none" }
    Write-Log "[!!] Python $PythonReq+ required (found: $foundVer)" Yellow
    Write-Log "[..] Attempting to install via winget..." Yellow

    if (-not (Test-Command winget)) {
        Write-Log "[XX] winget not available. Install Python manually from:" Red
        Write-Log "     https://www.python.org/downloads/" Red
        Write-Log "     Make sure to check 'Add Python to PATH'" Red
        return $false
    }

    try {
        $proc = Start-Process -FilePath winget -ArgumentList @(
            "install", "Python.Python.3.14",
            "--accept-source-agreements", "--accept-package-agreements",
            "--silent"
        ) -Wait -PassThru -NoNewWindow
        if ($proc.ExitCode -ne 0) {
            $proc = Start-Process -FilePath winget -ArgumentList @(
                "install", "Python.Python.3.12",
                "--accept-source-agreements", "--accept-package-agreements",
                "--silent"
            ) -Wait -PassThru -NoNewWindow
        }
        # Refresh PATH
        $machinePath = [Environment]::GetEnvironmentVariable("Path", "Machine")
        $userPath = [Environment]::GetEnvironmentVariable("Path", "User")
        $env:Path = $machinePath + ";" + $userPath
        $pyVer = Get-PythonVersion
        if ($pyVer -and $pyVer -ge [version]$PythonReq) {
            Write-Log "[OK] Python $pyVer installed successfully!" Green
            return $true
        }
    } catch {
        Write-Log "[XX] Failed to install Python via winget: $_" Red
    }

    Write-Log "[!!] Could not auto-install Python. Install manually from:" Yellow
    Write-Log "     https://www.python.org/downloads/" Yellow
    return $false
}

# --- Main Installation --------------------------------------------

Clear-Host
Write-Host @"

+----------------------------------------------------+
|           N64 Emu Setup Installer                  |
|     One-click N64 emulator + desktop icon          |
+----------------------------------------------------+

"@ -ForegroundColor Magenta

# Step 1: Python check
Write-Log "[..] Checking Python..."
$hasPython = Install-PythonIfMissing
if (-not $hasPython) {
    Write-Log "[XX] Cannot continue without Python." Red
    Write-Host "`nPress Enter to exit..." -ForegroundColor Gray
    $null = Read-Host
    exit 1
}

# Step 2: Create install directory
Write-Log "[..] Creating install directory: $InstallDir"
$null = New-Item -ItemType Directory -Path $InstallDir -Force

# Step 3: Download the repo (using native PowerShell, no git needed)
Write-Log "[..] Downloading N64 Emu Setup from GitHub..."
try {
    $files = @(
        @{ Path = "n64_emu_setup.py";    Url = "$RepoUrl/raw/$Branch/n64_emu_setup.py" }
        @{ Path = "README.md";           Url = "$RepoUrl/raw/$Branch/README.md" }
        @{ Path = ".gitignore";          Url = "$RepoUrl/raw/$Branch/.gitignore" }
        @{ Path = "assets/generate_icon.py"; Url = "$RepoUrl/raw/$Branch/assets/generate_icon.py" }
    )

    foreach ($f in $files) {
        $dest = Join-Path $InstallDir $f.Path
        $dir = Split-Path $dest -Parent
        $null = New-Item -ItemType Directory -Path $dir -Force
        Write-Log "     Downloading $($f.Path)..." DarkCyan
        Invoke-WebRequest -Uri $f.Url -OutFile $dest -UseBasicParsing -Headers @{
            "User-Agent" = "N64-Emu-Setup-Installer"
        }
    }
    Write-Log "[OK] All files downloaded" Green
} catch {
    Write-Log "[!!] Download failed, trying git clone..." Yellow
    if (Test-Command git) {
        if (Test-Path $InstallDir) { Remove-Item "$InstallDir\*" -Recurse -Force -ErrorAction SilentlyContinue }
        & git clone --depth 1 --branch $Branch $RepoUrl $InstallDir 2>&1 | ForEach-Object { Write-Log "   $_" DarkGray }
    } else {
        Write-Log "[XX] Download failed and git not available." Red
        Write-Log "     Try cloning manually: git clone $RepoUrl" Red
        exit 1
    }
}

# Step 4: Install Pillow (for icon generation)
Write-Log "[..] Installing Pillow (icon generator)..."
try {
    & python -m pip install Pillow --quiet 2>&1 | Out-Null
    Write-Log "[OK] Pillow installed" Green
} catch {
    Write-Log "[!!] Could not install Pillow, icon may be basic" Yellow
}

# Step 5: Generate the desktop icon
Write-Log "[..] Generating N64 desktop icon..."
try {
    Push-Location $InstallDir
    & python assets/generate_icon.py 2>&1
    Pop-Location
    Write-Log "[OK] Icon generated" Green
} catch {
    Write-Log "[!!] Icon generation failed: $_" Yellow
}

# Step 6: Create desktop shortcut with custom icon
Write-Log "[..] Creating desktop shortcut..."
try {
    $wshell = New-Object -ComObject WScript.Shell
    $shortcut = $wshell.CreateShortcut($ShortcutPath)
    $shortcut.TargetPath = "python.exe"
    $shortcut.Arguments = "`"$AppScript`""
    $shortcut.WorkingDirectory = "$InstallDir"
    $shortcut.Description = "N64 Emu Setup - Launch games!"

    if (Test-Path $IconIco) {
        $shortcut.IconLocation = "$IconIco, 0"
    } else {
        $pyExe = (Get-Command python).Source
        $shortcut.IconLocation = "$pyExe, 0"
    }

    $shortcut.Save()
    Write-Log "[OK] Desktop shortcut created: $ShortcutPath" Green
} catch {
    Write-Log "[!!] Could not create desktop shortcut: $_" Yellow
}

# Step 7: Ensure ROM folders exist
Write-Log "[..] Creating ROM folders..."
$romDirs = @(
    "$InstallDir\roms\n64\zelda_ocarina_of_time",
    "$InstallDir\roms\n64\super_smash_bros",
    "$InstallDir\roms\other"
)
foreach ($d in $romDirs) {
    $null = New-Item -ItemType Directory -Path $d -Force
}

# Step 8: Copy user's existing ROM if found in Downloads
$userRom = "$env:USERPROFILE\Downloads\The Legend of Zelda - Ocarina of Time.es.z64"
if (Test-Path $userRom) {
    Write-Log "[OK] Found your Zelda ROM in Downloads!" Green
    $destRom = "$InstallDir\roms\n64\zelda_ocarina_of_time\The Legend of Zelda - Ocarina of Time.es.z64"
    Copy-Item $userRom $destRom -Force
    Write-Log "[OK] Copied to ROMs folder" Green
}

# --- Done! --------------------------------------------------------
Write-Host @"

+----------------------------------------------------+
|           INSTALLATION COMPLETE!                    |
|                                                      |
|  Desktop shortcut: N64 Emu Setup                    |
|  Install folder: $InstallDir
|  ROMs folder: $InstallDir\roms
|                                                      |
|  Double-click the desktop icon to launch!            |
+----------------------------------------------------+

"@ -ForegroundColor Green

# Launch the app
Write-Log "[..] Launching N64 Emu Setup..."
try {
    Start-Process python -ArgumentList "`"$AppScript`"" -WorkingDirectory $InstallDir
    Write-Log "[OK] App launched!" Green
} catch {
    Write-Log "[!!] Could not launch app. Run manually:" Yellow
    Write-Log "     python `"$AppScript`"" Yellow
}

Write-Host "`nPress Enter to close..." -ForegroundColor Gray
$null = Read-Host

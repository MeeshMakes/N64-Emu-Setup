#!/usr/bin/env python3
"""
N64 Emu Setup — One-click N64 emulator installer & launcher
=============================================================
Installs Simple64 (Mupen64Plus), sets up ROM directories, and lets you
launch your N64 games with a clean console log.
"""

import os
import sys
import json
import zipfile
import subprocess
import threading
import shutil
import platform
import webbrowser
from pathlib import Path
from datetime import datetime
from tkinter import (
    Tk, Frame, Label, Button, Text, Scrollbar,
    END, DISABLED, NORMAL, messagebox, ttk, filedialog
)

# ─── Configuration ────────────────────────────────────────────────
APP_NAME = "N64 Emu Setup"
APP_VERSION = "1.0.0"

BASE_DIR = Path(__file__).parent.resolve()
EMULATOR_DIR = BASE_DIR / "emulator"
ROMS_DIR = BASE_DIR / "roms"
SETTINGS_FILE = BASE_DIR / "settings.json"
LOG_FILE = BASE_DIR / "setup.log"
ICON_FILE = BASE_DIR / "assets" / "n64_icon.ico"
ICON_PNG = BASE_DIR / "assets" / "n64_icon.png"

SYSTEM = platform.system().lower()
IS_WINDOWS = SYSTEM == "windows"
IS_MAC = SYSTEM == "darwin"
IS_LINUX = SYSTEM == "linux"

# ─── Helpers ──────────────────────────────────────────────────────

def log(msg):
    """Write a timestamped message to the log file."""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{ts}] {msg}\n")


class RedirectText:
    """Redirect print statements to a tkinter Text widget."""
    def __init__(self, text_widget, console):
        self.text_widget = text_widget
        self.console = console

    def write(self, string):
        if self.text_widget:
            self.text_widget.after(0, lambda: self._append(string))

    def _append(self, string):
        try:
            self.text_widget.insert(END, string)
            self.text_widget.see(END)
            self.text_widget.update_idletasks()
        except Exception:
            pass

    def flush(self):
        pass


# ─── Main Application ─────────────────────────────────────────────

class N64EmuSetupApp:
    def __init__(self, root):
        self.root = root
        self.root.title(f"{APP_NAME} v{APP_VERSION}")
        self.root.geometry("760x620")
        self.root.resizable(True, True)
        self.root.minsize(600, 500)

        # Set the custom N64 icon
        self._set_app_icon()

        self.console_active = True
        self.settings = self.load_settings()

        self._build_ui()
        self._log_initial()
        self.check_emulator_status()

    # ── App Icon ──────────────────────────────────────────────────

    def _set_app_icon(self):
        """Set the window icon from the generated ICO/PNG."""
        try:
            if IS_WINDOWS and ICON_FILE.exists():
                self.root.iconbitmap(default=str(ICON_FILE))
            elif ICON_PNG.exists():
                from PIL import Image, ImageTk
                img = Image.open(ICON_PNG)
                icon = ImageTk.PhotoImage(img)
                self.root.iconphoto(True, icon)
                self.root._icon_image = icon  # prevent GC
        except Exception:
            pass

    # ── UI Build ──────────────────────────────────────────────────

    def _build_ui(self):
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(2, weight=1)

        # ── Header ──
        header = Frame(self.root, bg="#1a1a2e", padx=20, pady=14)
        header.grid(row=0, column=0, sticky="ew")
        header.columnconfigure(0, weight=1)

        title = Label(
            header, text="🎮  N64 Emu Setup",
            font=("Segoe UI", 18, "bold"), fg="#e94560", bg="#1a1a2e"
        )
        title.grid(row=0, column=0, sticky="w")

        subtitle = Label(
            header, text="Simple64 (Mupen64Plus) — Installer & Launcher",
            font=("Segoe UI", 10), fg="#a0a0b0", bg="#1a1a2e"
        )
        subtitle.grid(row=1, column=0, sticky="w")

        # ── Status Bar ──
        status_frame = Frame(self.root, bg="#16213e", padx=14, pady=8)
        status_frame.grid(row=1, column=0, sticky="ew")
        status_frame.columnconfigure(1, weight=1)

        Label(status_frame, text="Status:", font=("Segoe UI", 9, "bold"),
              fg="#e94560", bg="#16213e").grid(row=0, column=0, sticky="w")

        self.status_label = Label(status_frame, text="Initializing...",
                                  font=("Segoe UI", 9), fg="#a0a0b0", bg="#16213e")
        self.status_label.grid(row=0, column=1, sticky="w")

        self.emu_status_label = Label(status_frame, text="⚪ Not installed",
                                      font=("Segoe UI", 9, "bold"), fg="#ff6b6b", bg="#16213e")
        self.emu_status_label.grid(row=0, column=2, sticky="e", padx=(10, 0))

        # ── Console / Log ──
        console_frame = Frame(self.root, bg="#0f0f1a")
        console_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=(4, 6))
        console_frame.columnconfigure(0, weight=1)
        console_frame.rowconfigure(0, weight=1)

        self.console = Text(
            console_frame, wrap="word", state=NORMAL,
            bg="#0a0a14", fg="#00ff88",
            font=("Consolas", 10), relief="flat", borderwidth=0,
            padx=8, pady=6, insertbackground="#00ff88"
        )
        self.console.grid(row=0, column=0, sticky="nsew")

        scrollbar = Scrollbar(console_frame, orient="vertical", command=self.console.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.console.configure(yscrollcommand=scrollbar.set)

        # ── Button Bar ──
        btn_frame = Frame(self.root, bg="#1a1a2e", padx=14, pady=10)
        btn_frame.grid(row=3, column=0, sticky="ew")
        btn_frame.columnconfigure((0, 1, 2, 3, 4, 5), weight=1)

        self.btn_install = self._make_button(
            btn_frame, "⬇  Install Emulator", self.install_emulator_thread, 0
        )
        self.btn_launch = self._make_button(
            btn_frame, "▶  Launch Emulator", self.launch_emulator, 1
        )
        self.btn_select_rom = self._make_button(
            btn_frame, "📁  Select ROM", self.select_rom, 2
        )
        self.btn_open_roms = self._make_button(
            btn_frame, "📂  ROMs Folder", self.open_roms_folder, 3
        )
        self.btn_zip = self._make_button(
            btn_frame, "📦  Select ZIP", self.install_from_zip_thread, 4
        )
        self.btn_clear = self._make_button(
            btn_frame, "🧹  Clear Log", self.clear_log, 5
        )

        # ── Progress Bar ──
        self.progress = ttk.Progressbar(
            self.root, mode="indeterminate", length=760
        )
        self.progress.grid(row=4, column=0, sticky="ew", padx=10, pady=(0, 8))
        self.progress.grid_remove()

        # Redirect stdout/stderr to console
        sys.stdout = RedirectText(self.console, self)
        sys.stderr = RedirectText(self.console, self)

    def _make_button(self, parent, text, command, col):
        btn = Button(
            parent, text=text, command=command,
            bg="#0f3460", fg="white", activebackground="#e94560",
            activeforeground="white", relief="flat", borderwidth=0,
            font=("Segoe UI", 9, "bold"), padx=8, pady=6,
            cursor="hand2"
        )
        btn.grid(row=0, column=col, sticky="ew", padx=4)
        return btn

    def _log_initial(self):
        print(f"{'='*60}")
        print(f"  {APP_NAME} v{APP_VERSION}")
        print(f"  System: {platform.system()} {platform.release()}")
        print(f"  Python: {sys.version.split()[0]}")
        print(f"  Folder: {BASE_DIR}")
        print(f"{'='*60}")
        print("  Ready. Install the emulator to get started.")
        print()

    # ── Settings ──────────────────────────────────────────────────

    def load_settings(self):
        default = {
            "emulator_path": "",
            "roms_directory": str(ROMS_DIR),
            "last_rom": ""
        }
        if SETTINGS_FILE.exists():
            try:
                data = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
                return {**default, **data}
            except Exception:
                pass
        return default

    def save_settings(self):
        SETTINGS_FILE.write_text(
            json.dumps(self.settings, indent=2), encoding="utf-8"
        )

    # ── Status ────────────────────────────────────────────────────

    def set_status(self, text, color="#a0a0b0"):
        self.status_label.configure(text=text, fg=color)
        log(text)

    def show_progress(self):
        self.progress.grid()
        self.progress.start(10)
        self.root.update_idletasks()

    def hide_progress(self):
        self.progress.stop()
        self.progress.grid_remove()
        self.root.update_idletasks()

    def check_emulator_status(self):
        """Check if Simple64 is already installed somewhere."""
        candidates = [
            EMULATOR_DIR / "simple64" / "simple64-gui.exe",
            EMULATOR_DIR / "simple64-gui.exe",
            EMULATOR_DIR / "simple64" / "simple64.exe",
            Path("C:/Program Files/simple64/simple64-gui.exe"),
            Path("C:/Program Files (x86)/simple64/simple64-gui.exe"),
        ]
        if self.settings.get("emulator_path"):
            p = Path(self.settings["emulator_path"])
            if p.exists():
                self.set_emu_installed(p)
                return

        for c in candidates:
            if c.exists():
                self.settings["emulator_path"] = str(c)
                self.save_settings()
                self.set_emu_installed(c)
                return

        self.set_emu_missing()

    def set_emu_installed(self, path):
        self.emu_status_label.configure(text="✅ Installed", fg="#00ff88")
        self.btn_install.configure(text="🔄  Reinstall Emulator")
        self.btn_launch.configure(state=NORMAL)
        self.set_status(f"Emulator found at: {path}", "#00ff88")

    def set_emu_missing(self):
        self.emu_status_label.configure(text="❌ Not installed", fg="#ff6b6b")
        self.btn_install.configure(text="⬇  Install Emulator")
        self.btn_launch.configure(state=DISABLED)
        self.set_status("Emulator not found. Click Install to begin.", "#ff6b6b")

    # ── Install Emulator ──────────────────────────────────────────

    SIMPLE64_ZIP_URL = "https://github.com/simple64/simple64/releases/download/v2024.12.1/simple64-win64-b49e10e.zip"
    SIMPLE64_RELEASES_URL = "https://github.com/simple64/simple64/releases"
    SIMPLE64_ZIP_NAME = "simple64-win64-b49e10e.zip"

    def install_emulator_thread(self):
        thread = threading.Thread(target=self._install_flow, daemon=True)
        thread.start()

    def _install_flow(self):
        """Popup → open browser to download → watch Downloads → move → extract → done."""
        # ── 1. Popup ──
        msg = (
            "Simple64 needs to be downloaded from GitHub.\n\n"
            "I'll open your browser to download the ZIP.\n"
            "Once it finishes downloading, I'll detect it\n"
            "in your Downloads folder, move it here, and\n"
            "extract it automatically."
        )
        answer = messagebox.askyesno(
            title="Download Simple64?",
            message=msg,
            detail="Click Yes to open the download page. Click No to cancel."
        )
        if not answer:
            return

        print("\n── Installing Simple64 ──\n")
        print("  🔗  Opening browser to download ZIP...")
        self.set_status("Opening browser...", "#ffd700")
        webbrowser.open(self.SIMPLE64_ZIP_URL)
        print(f"  📄  File: {self.SIMPLE64_ZIP_NAME} (46 MB)")
        print("  💡  Save it to your Downloads folder when prompted.")

        # ── 2. Wait for the ZIP to appear in Downloads ──
        self.btn_install.configure(state=DISABLED)
        self.set_status("Waiting for download...", "#ffd700")

        download_dir = Path.home() / "Downloads"
        zip_path = download_dir / self.SIMPLE64_ZIP_NAME
        found = False

        print(f"\n  👀  Watching: {download_dir}")
        print(f"  👀  For file: {self.SIMPLE64_ZIP_NAME}")
        print("  ⏳  Waiting for download to complete...")

        # Check up to 5 minutes (30 tries × 10 seconds)
        for attempt in range(30):
            self.root.update()
            if zip_path.exists() and zip_path.stat().st_size > 40000000:
                found = True
                break
            # Also catch partial downloads — check if file exists and size is stable
            if zip_path.exists():
                size1 = zip_path.stat().st_size
                threading.Event().wait(2)
                if zip_path.exists():
                    size2 = zip_path.stat().st_size
                    if size1 == size2 and size1 > 40000000:
                        found = True
                        break
            threading.Event().wait(8)

        if not found:
            print("  ❌  Download not detected after 5 minutes.")
            print("  💡  Use the 'Select ZIP' button to locate it manually.")
            self.set_status("Download not found. Use Select ZIP.", "#ff6b6b")
            self.btn_install.configure(state=NORMAL)
            return

        print(f"  ✅  Found in Downloads!")
        self.set_status("Moving and extracting...", "#ffd700")

        # ── 3. Move the ZIP to emulator folder ──
        try:
            EMULATOR_DIR.mkdir(parents=True, exist_ok=True)
            dest_zip = EMULATOR_DIR / self.SIMPLE64_ZIP_NAME

            print("  📋  Moving ZIP to emulator folder...")
            # Remove old one if exists
            if dest_zip.exists():
                dest_zip.unlink()
            shutil.move(str(zip_path), str(dest_zip))
            print("  ✅  Moved")

            # ── 4. Extract with nesting handling ──
            print("  📦  Extracting...")
            import tempfile
            tmp_dir = EMULATOR_DIR / "_tmp_extract"
            if tmp_dir.exists():
                shutil.rmtree(tmp_dir)
            tmp_dir.mkdir()

            with zipfile.ZipFile(dest_zip, "r") as zf:
                zf.extractall(tmp_dir)

            extract_path = EMULATOR_DIR / "simple64"
            if extract_path.exists():
                shutil.rmtree(extract_path)
            extract_path.mkdir()

            contents = list(tmp_dir.iterdir())
            if len(contents) == 1 and contents[0].is_dir():
                for item in contents[0].iterdir():
                    dest = extract_path / item.name
                    if dest.exists():
                        if dest.is_dir():
                            shutil.rmtree(dest)
                        else:
                            dest.unlink()
                    shutil.move(str(item), str(dest))
            else:
                for item in contents:
                    shutil.move(str(item), str(extract_path / item.name))
            shutil.rmtree(tmp_dir)
            print("  ✅  Extracted")

            # ── 5. Find executable ──
            exe_path = None
            for name in ["simple64-gui.exe", "simple64.exe"]:
                for found in extract_path.rglob(name):
                    exe_path = found
                    break
                if exe_path:
                    break
            if not exe_path:
                for found in extract_path.rglob("*.exe"):
                    fn = found.name.lower()
                    if fn != "7za.exe" and "uninstall" not in fn:
                        exe_path = found
                        break

            if exe_path:
                self.settings["emulator_path"] = str(exe_path)
                self.save_settings()
                self.set_emu_installed(exe_path)
                print(f"  ✅  Found: {exe_path.name}")
            else:
                print(f"  ✅  Files in: {extract_path}")
                self.settings["emulator_path"] = str(extract_path)
                self.save_settings()
                self.set_emu_installed(extract_path)

            self._ensure_roms_dir()
            print(f"\n  ✅  Done! Launch the emulator or pick a ROM.")
            self.set_status("Ready to play!", "#00ff88")

        except Exception as e:
            print(f"\n  ❌  {e}")
            self.set_status(f"Error: {e}", "#ff6b6b")
            log(f"EXCEPTION: {e}")
        finally:
            self.btn_install.configure(state=NORMAL)

    def install_from_zip_thread(self):
        thread = threading.Thread(target=self.install_from_zip, daemon=True)
        thread.start()

    def install_from_zip(self):
        """Browse for a manually-downloaded Simple64 ZIP and install from it."""
        filetypes = [
            ("ZIP files", "*.zip"),
            ("All files", "*.*")
        ]
        filename = filedialog.askopenfilename(
            title="Select Simple64 ZIP file you downloaded",
            initialdir=str(Path.home() / "Downloads"),
            filetypes=filetypes
        )
        if not filename:
            return

        self.show_progress()
        self.btn_install.configure(state=DISABLED)
        try:
            EMULATOR_DIR.mkdir(parents=True, exist_ok=True)
            zip_path = Path(filename)

            print(f"\n── Installing from ZIP: {zip_path.name} ──\n")

            # Copy ZIP to emulator folder
            dest_zip = EMULATOR_DIR / zip_path.name
            if str(zip_path) != str(dest_zip):
                print("  📋  Copying ZIP to emulator folder...")
                shutil.copy2(str(zip_path), str(dest_zip))

            # Extract with nesting handling
            print("  📦  Extracting...")
            self.set_status("Extracting...", "#ffd700")
            import tempfile
            tmp_dir = EMULATOR_DIR / "_tmp_extract"
            if tmp_dir.exists():
                shutil.rmtree(tmp_dir)
            tmp_dir.mkdir()

            with zipfile.ZipFile(str(dest_zip), "r") as zf:
                zf.extractall(str(tmp_dir))

            extract_path = EMULATOR_DIR / "simple64"
            if extract_path.exists():
                shutil.rmtree(extract_path)
            extract_path.mkdir()

            contents = list(tmp_dir.iterdir())
            if len(contents) == 1 and contents[0].is_dir():
                for item in contents[0].iterdir():
                    dest = extract_path / item.name
                    if dest.exists():
                        if dest.is_dir():
                            shutil.rmtree(dest)
                        else:
                            dest.unlink()
                    shutil.move(str(item), str(dest))
            else:
                for item in contents:
                    shutil.move(str(item), str(extract_path / item.name))
            shutil.rmtree(tmp_dir)
            print("  ✅  Extracted")

            # Find executable
            exe_path = None
            for name in ["simple64-gui.exe", "simple64.exe"]:
                for found in extract_path.rglob(name):
                    exe_path = found
                    break
                if exe_path:
                    break
            if not exe_path:
                for found in extract_path.rglob("*.exe"):
                    fn = found.name.lower()
                    if fn != "7za.exe" and "uninstall" not in fn:
                        exe_path = found
                        break

            if exe_path:
                self.settings["emulator_path"] = str(exe_path)
                self.save_settings()
                self.set_emu_installed(exe_path)
                print(f"  ✅  Emulator installed at: {exe_path}")
            else:
                print(f"  ✅  Files extracted to: {extract_path}")
                print("  💡  Look for simple64.exe in there")
                self.settings["emulator_path"] = str(extract_path)
                self.save_settings()
                self.set_emu_installed(extract_path)

            self._ensure_roms_dir()
            print(f"\n  ✅  Installation complete from ZIP!")
            self.set_status("Installation complete! Ready to play.", "#00ff88")

        except Exception as e:
            print(f"\n  ❌  Error: {e}")
            self.set_status(f"Error: {e}", "#ff6b6b")
            log(f"EXCEPTION: {e}")
        finally:
            self.btn_install.configure(state=NORMAL)
            self.hide_progress()
            print()

    def _ensure_roms_dir(self):
        """Create ROM folders with nice structure."""
        ROMS_DIR.mkdir(parents=True, exist_ok=True)
        (ROMS_DIR / "n64").mkdir(exist_ok=True)
        (ROMS_DIR / "n64" / "zelda_ocarina_of_time").mkdir(exist_ok=True)
        (ROMS_DIR / "n64" / "super_smash_bros").mkdir(exist_ok=True)
        (ROMS_DIR / "other").mkdir(exist_ok=True)
        # Create a README in roms folder
        readme = ROMS_DIR / "README.txt"
        if not readme.exists():
            readme.write_text(
                "N64 ROMs Folder\n"
                "===============\n\n"
                "Place your legally obtained N64 ROM files here.\n\n"
                "Folders:\n"
                "  n64/zelda_ocarina_of_time/  — The Legend of Zelda: Ocarina of Time\n"
                "  n64/super_smash_bros/       — Super Smash Bros.\n"
                "  other/                      — Any other N64 games\n\n"
                "Supported formats: .z64, .n64, .v64, .rom\n\n"
                "How to dump your own cartridges:\n"
                "  1. You need a 'Retrode' or 'EverDrive' flash cart\n"
                "  2. Or buy from Wii U Virtual Console and extract\n"
                "  3. See: https://emulation.gametechwiki.com/\n"
            , encoding="utf-8")
        print(f"  📂  ROMs directory ready: {ROMS_DIR}")

    # ── Launch Emulator ───────────────────────────────────────────

    def launch_emulator(self):
        emu_path = self.settings.get("emulator_path", "")
        if not emu_path or not Path(emu_path).exists():
            self.check_emulator_status()
            if not self.settings.get("emulator_path"):
                messagebox.showerror("Error", "Emulator not installed. Install it first.")
                return
            emu_path = self.settings["emulator_path"]

        try:
            print(f"\n  ▶  Launching emulator: {emu_path}")
            if IS_WINDOWS:
                subprocess.Popen([emu_path], cwd=str(Path(emu_path).parent))
            elif IS_MAC:
                subprocess.Popen(["open", emu_path])
            else:
                subprocess.Popen([emu_path], cwd=str(Path(emu_path).parent))
            self.set_status(f"Emulator launched!", "#00ff88")
        except Exception as e:
            print(f"  ❌  Failed to launch: {e}")
            self.set_status(f"Launch failed: {e}", "#ff6b6b")

    # ── Select ROM ────────────────────────────────────────────────

    def select_rom(self):
        filetypes = [
            ("N64 ROMs", "*.z64 *.n64 *.v64 *.rom"),
            ("All files", "*.*")
        ]
        filename = filedialog.askopenfilename(
            title="Select an N64 ROM",
            initialdir=str(self.settings.get("roms_directory", ROMS_DIR)),
            filetypes=filetypes
        )
        if filename:
            self.settings["last_rom"] = filename
            self.save_settings()
            print(f"  📁  Selected ROM: {filename}")
            self.set_status(f"ROM selected: {Path(filename).name}", "#00ff88")

            # Ask if user wants to launch it
            if messagebox.askyesno("Launch ROM", "Launch this ROM with the emulator?"):
                self._launch_rom(filename)

    def _launch_rom(self, rom_path):
        emu_path = self.settings.get("emulator_path", "")
        if not emu_path or not Path(emu_path).exists():
            messagebox.showerror("Error", "Emulator not installed. Install it first.")
            return

        try:
            print(f"  ▶  Launching ROM with emulator...")
            if IS_WINDOWS:
                subprocess.Popen([emu_path, f'"{rom_path}"'],
                                 cwd=str(Path(emu_path).parent))
            else:
                subprocess.Popen([emu_path, rom_path],
                                 cwd=str(Path(emu_path).parent))
            self.set_status(f"Playing: {Path(rom_path).name}", "#00ff88")
        except Exception as e:
            print(f"  ❌  Failed to launch ROM: {e}")

    # ── Folder / Clear ────────────────────────────────────────────

    def open_roms_folder(self):
        self._ensure_roms_dir()
        try:
            if IS_WINDOWS:
                os.startfile(str(ROMS_DIR))
            elif IS_MAC:
                subprocess.Popen(["open", str(ROMS_DIR)])
            else:
                subprocess.Popen(["xdg-open", str(ROMS_DIR)])
        except Exception as e:
            print(f"  ❌  Could not open folder: {e}")

    def clear_log(self):
        self.console.delete("1.0", END)

    # ── Cleanup ───────────────────────────────────────────────────

    def on_close(self):
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__
        log("Application closed.")
        self.root.destroy()


# ─── Entry Point ──────────────────────────────────────────────────

if __name__ == "__main__":
    root = Tk()
    app = N64EmuSetupApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()

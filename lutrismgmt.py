#!/usr/bin/env python3
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os
import subprocess
import shutil
import glob
import re
import json
import tempfile
import threading
import sys
import urllib.request
from tkinter import messagebox

# --- Zentrale Pfade ---
LUTRIS_CONFIG_DIR = os.path.expanduser("~/.config/lutris/games")
LUTRIS_LOCAL_SHARE = os.path.expanduser("~/.local/share/lutris")
CONFIG_FILE = os.path.expanduser("~/.config/andreas_lutris_manager.json")
DEFAULT_BACKUP_DIR = "/home/andreas/LutrisBackups"
PREFIX_DIR = "/home/andreas/GamePrefixes"
APPLICATIONS_DIR = os.path.expanduser("~/.local/share/applications")
script_dir = os.path.dirname(os.path.abspath(__file__))
icon_path = os.path.join(script_dir, "lutris_logo.png")

# --- Design Farben (Dark Mode) ---
BG_COLOR = "#1e1e2e"        # Haupt-Hintergrund
SIDEBAR_COLOR = "#181825"   # Seitenleiste
ACCENT_COLOR = "#89b4fa"    # Akzentfarbe (Hellblau)
TEXT_COLOR = "#cdd6f4"      # Heller Text
BTN_BG = "#313244"          # Button Hintergrund
BTN_HOVER = "#45475a"
SUCCESS_COLOR = "#a6e3a1"   # Grün für wichtige Buttons

# --- Einstellungen ---
def lade_einstellungen():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"backup_dir": DEFAULT_BACKUP_DIR}

def speichere_einstellungen(config_dict):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config_dict, f)
    except Exception:
        pass

app_config = lade_einstellungen()

def github_update_pruefen():
    # --- NUR DIE URL HIER EINTRAGEN ---
    GITHUB_RAW_URL = "https://raw.githubusercontent.com/DukyNuky/-lutris-mgmt/refs/heads/main/lutrismgmt.py"

    try:
        fenster.config(cursor="watch")
        fenster.update()

        req = urllib.request.Request(GITHUB_RAW_URL)
        req.add_header('User-Agent', 'Mozilla/5.0') 

        with urllib.request.urlopen(req) as response:
            neuer_code = response.read().decode('utf-8')

        if "import tkinter" not in neuer_code:
            raise ValueError("Heruntergeladene Datei scheint kein gültiges Skript zu sein.")

        aktuelle_datei = os.path.abspath(__file__)
        with open(aktuelle_datei, 'r', encoding='utf-8') as f:
            aktueller_code = f.read()

        if neuer_code == aktueller_code:
            messagebox.showinfo("Update", "Das Tool ist bereits auf dem neuesten Stand!")
            return

        with open(aktuelle_datei, 'w', encoding='utf-8') as f:
            f.write(neuer_code)

        messagebox.showinfo("Update erfolgreich!", 
                            "Die neueste Version wurde direkt von GitHub geladen!\n\n"
                            "Das Tool startet sich jetzt neu.")
        
        os.execl(sys.executable, sys.executable, *sys.argv)

    except Exception as e:
        messagebox.showerror("Fehler beim Update", f"Konnte nicht aktualisieren.\nPrüfe die URL!\n\nDetails: {e}")
    finally:
        fenster.config(cursor="")

# ==========================================
# FUNKTIONEN FÜR INTEGRATION & IMPORT
# ==========================================
def starter_erstellen():
    script_path = os.path.abspath(sys.argv[0])
    icon_path = os.path.join(os.path.dirname(script_path), "lutris_logo.png")
    desktop_file_path = os.path.join(APPLICATIONS_DIR, "lutris-studio.desktop")
    
    content = f"""[Desktop Entry]
Name=Andreas' Lutris Studio
Comment=Game Importer und Backup-Management
Exec=python3 {script_path}
Icon={icon_path if os.path.exists(icon_path) else ''}
Terminal=false
Type=Application
Categories=Game;Utility;
"""
    try:
        os.makedirs(APPLICATIONS_DIR, exist_ok=True)
        with open(desktop_file_path, "w") as f:
            f.write(content)
        subprocess.run(["chmod", "+x", desktop_file_path])
        messagebox.showinfo("Erfolg", "Der Starter wurde erfolgreich im Startmenü angelegt!")
    except Exception as e:
        messagebox.showerror("Fehler", f"Konnte Starter nicht erstellen: {e}")

def datei_waehlen():
    dateipfad = filedialog.askopenfilename(title="Wähle die .exe Datei des Spiels", filetypes=[("Windows-Spiele", "*.exe"), ("Alle Dateien", "*.*")])
    if dateipfad:
        pfad_eingabe.delete(0, tk.END)
        pfad_eingabe.insert(0, dateipfad)

def skript_erstellen():
    name = name_eingabe.get().strip()
    pfad = pfad_eingabe.get().strip()

    if not name or not pfad:
        messagebox.showwarning("Fehler", "Bitte fülle den Namen und den Dateipfad aus!")
        return

    arbeitsverzeichnis = os.path.dirname(pfad)
    slug = name.lower().replace(" ", "-")

    if eigenes_prefix_var.get():
        ordner_name = name.replace(" ", "_")
        prefix_pfad = os.path.join(PREFIX_DIR, ordner_name)
        os.makedirs(prefix_pfad, exist_ok=True)
        try:
            fenster.update() 
            env = os.environ.copy()
            env["WINEPREFIX"] = prefix_pfad
            subprocess.run(["wineboot", "-u"], env=env, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception as e:
            messagebox.showwarning("Hinweis", f"Präfix erstellt, Auto-Init schlug fehl:\n{e}")
    else:
        prefix_pfad = os.path.join(PREFIX_DIR, "Goldberg")

    yaml_inhalt = f"""name: "{name}"
game_slug: {slug}
version: Andreas Custom Setup
slug: {slug}-andreas
runner: wine

script:
  game:
    exe: "{pfad}"
    working_dir: "{arbeitsverzeichnis}"
    prefix: "{prefix_pfad}"
"""
    temp_dir = tempfile.gettempdir()
    dateiname = os.path.join(temp_dir, f"{slug}_installer.yml")
    try:
        with open(dateiname, "w", encoding="utf-8") as datei:
            datei.write(yaml_inhalt)
        subprocess.Popen(["lutris", "-i", dateiname])
        name_eingabe.delete(0, tk.END)
        pfad_eingabe.delete(0, tk.END)
        eigenes_prefix_var.set(False)
    except Exception as e:
        messagebox.showerror("Fehler", f"Ein Fehler ist aufgetreten:\n{e}")

# ==========================================
# FUNKTIONEN FÜR SUNSHINE
# ==========================================
def sunshine_sync_starten():
    tool_pfad = os.path.join(script_dir, "lutristosunshine")
    
    if not os.path.exists(tool_pfad):
        messagebox.showerror("Fehler", f"Das Tool wurde nicht gefunden:\n{tool_pfad}\n\nBitte stelle sicher, dass es im selben Ordner wie dieses Skript liegt.")
        return
        
    try:
        # Cursor auf Ladesymbol ändern
        fenster.config(cursor="watch")
        fenster.update()
        
        # Tool ausführen
        result = subprocess.run([tool_pfad], capture_output=True, text=True, check=True)
        messagebox.showinfo("Sunshine Sync Erfolgreich", "Die Lutris-Spiele wurden erfolgreich an Sunshine übergeben!")
        
    except subprocess.CalledProcessError as e:
        messagebox.showerror("Fehler beim Ausführen", f"Das Tool 'lutristosunshine' gab einen Fehler zurück.\n\nExit Code: {e.returncode}\nFehler-Ausgabe:\n{e.stderr}")
    except PermissionError:
        messagebox.showerror("Berechtigungsfehler", "Die Datei 'lutristosunshine' darf nicht ausgeführt werden.\nBitte führe 'chmod +x lutristosunshine' im Terminal aus.")
    except Exception as e:
        messagebox.showerror("Unerwarteter Fehler", f"Konnte das Tool nicht starten:\n{e}")
    finally:
        # Cursor zurücksetzen
        fenster.config(cursor="")

# ==========================================
# FUNKTIONEN FÜR BACKUP & RESTORE
# ==========================================
def backup_ordner_aendern():
    aktueller_ordner = aktueller_backup_pfad_var.get()
    neuer_ordner = filedialog.askdirectory(initialdir=aktueller_ordner, title="Wähle den Ordner für Backups")
    if neuer_ordner:
        aktueller_backup_pfad_var.set(neuer_ordner)
        app_config["backup_dir"] = neuer_ordner
        speichere_einstellungen(app_config)

def backup_nur_profile():
    ziel_ordner = os.path.join(aktueller_backup_pfad_var.get(), "Profile_Only")
    os.makedirs(ziel_ordner, exist_ok=True)
    yaml_dateien = glob.glob(os.path.join(LUTRIS_CONFIG_DIR, "*.yml"))
    
    if not yaml_dateien:
        messagebox.showinfo("Backup", "Keine Profile gefunden.")
        return
        
    for datei in yaml_dateien:
        shutil.copy(datei, ziel_ordner)
    messagebox.showinfo("Erfolg", f"Nur Profile gesichert in:\n{ziel_ordner}")

def backup_komplett():
    ziel_ordner = aktueller_backup_pfad_var.get()
    os.makedirs(ziel_ordner, exist_ok=True)
    
    prof_ordner = os.path.join(ziel_ordner, "Lutris_Configs")
    os.makedirs(prof_ordner, exist_ok=True)
    for datei in glob.glob(os.path.join(LUTRIS_CONFIG_DIR, "*.yml")):
        shutil.copy(datei, prof_ordner)
        
    db_pfad = os.path.join(LUTRIS_LOCAL_SHARE, "pga.db")
    if os.path.exists(db_pfad):
        shutil.copy(db_pfad, ziel_ordner)
        
    prefix_archiv_ziel = os.path.join(ziel_ordner, "GamePrefixes_Backup")
    if os.path.exists(PREFIX_DIR):
        messagebox.showinfo("Backup läuft", "Die GamePrefixes werden nun gepackt.\nDas kann je nach Größe einige Minuten dauern!\nDas Fenster friert solange ein.")
        try:
            shutil.make_archive(prefix_archiv_ziel, 'gztar', PREFIX_DIR)
            messagebox.showinfo("Fertig!", f"KOMPLETT-BACKUP ERFOLGREICH!\n\nGespeichert in:\n{ziel_ordner}\n- Profile\n- pga.db\n- GamePrefixes.tar.gz")
        except Exception as e:
            messagebox.showerror("Fehler", f"Fehler beim Packen:\n{e}")
    else:
        messagebox.showwarning("Hinweis", f"Präfix-Ordner {PREFIX_DIR} nicht gefunden. Rest wurde gesichert.")

def yml_pfad_anpassen_und_installieren(yml_pfad):
    spielname_fallback = os.path.basename(yml_pfad).replace(".yml", "")
    
    try:
        with open(yml_pfad, 'r', encoding='utf-8') as f:
            inhalt = f.read()
            
        name_match = re.search(r'(?m)^name:\s*"?([^"\n]+)"?', inhalt)
        spielname = name_match.group(1).strip() if name_match else spielname_fallback
        
        prefix_match = re.search(r'(?m)^[ \t]*prefix:\s*"?([^"\n]+)"?', inhalt)
        altes_prefix = prefix_match.group(1).strip() if prefix_match else os.path.join(PREFIX_DIR, "Goldberg")
        
        runner_match = re.search(r'(?m)^runner:\s*"?([^"\n]+)"?', inhalt)
        runner = runner_match.group(1).strip() if runner_match else "wine"

    except Exception as e:
        messagebox.showerror("Fehler", f"Konnte Backup {spielname_fallback} nicht lesen:\n{e}")
        return False

    messagebox.showinfo("Pfad anpassen", f"Wo liegt nun die .exe für das Spiel:\n'{spielname}'?")
    
    neue_exe = filedialog.askopenfilename(title=f"Neue .exe für {spielname}", filetypes=[("Windows-Spiele", "*.exe"), ("Alle Dateien", "*.*")])
    if not neue_exe:
        return False 
        
    neues_working_dir = os.path.dirname(neue_exe)
    slug = spielname.lower().replace(" ", "-")
    
    yaml_inhalt = f"""name: "{spielname}"
game_slug: {slug}
version: Andreas Restore
slug: {slug}-restore
runner: {runner}

script:
  game:
    exe: "{neue_exe}"
    working_dir: "{neues_working_dir}"
    prefix: "{altes_prefix}"
"""
    
    temp_dir = tempfile.gettempdir()
    temp_yml = os.path.join(temp_dir, f"restore_{slug}.yml")
    
    try:
        with open(temp_yml, 'w', encoding='utf-8') as f:
            f.write(yaml_inhalt)
        subprocess.Popen(["lutris", "-i", temp_yml])
        return True
    except Exception as e:
        messagebox.showerror("Fehler", f"Fehler beim Installieren von {spielname}:\n{e}")
        return False

def hole_restore_ordner():
    backup_dir = aktueller_backup_pfad_var.get()
    if not os.path.exists(backup_dir):
        return None
    
    prof_ordner = os.path.join(backup_dir, "Lutris_Configs")
    prof_only = os.path.join(backup_dir, "Profile_Only")
    
    if os.path.exists(prof_ordner):
        return prof_ordner
    elif os.path.exists(prof_only):
        return prof_only
    return backup_dir

def restore_einzeln():
    such_ordner = hole_restore_ordner()
    if not such_ordner:
        messagebox.showwarning("Fehler", "Backup-Ordner existiert nicht.")
        return
        
    yml_pfad = filedialog.askopenfilename(initialdir=such_ordner, title="Wähle das Profil (.yml)", filetypes=[("Lutris Config", "*.yml")])
    if yml_pfad:
        yml_pfad_anpassen_und_installieren(yml_pfad)

def restore_bulk():
    such_ordner = hole_restore_ordner()
    if not such_ordner:
        messagebox.showwarning("Fehler", "Backup-Ordner existiert nicht.")
        return
        
    yaml_dateien = glob.glob(os.path.join(such_ordner, "*.yml"))
    if not yaml_dateien:
        messagebox.showinfo("Info", "Keine Backups (.yml) gefunden.")
        return
        
    antwort = messagebox.askyesno("Bulk Restore", f"Es wurden {len(yaml_dateien)} Backups gefunden.\nDas Skript wird dich nun für JEDES Spiel nach der neuen .exe fragen.\n\nMöchtest du fortfahren?")
    if antwort:
        erfolgreich = 0
        for datei in yaml_dateien:
            if yml_pfad_anpassen_und_installieren(datei):
                erfolgreich += 1
        messagebox.showinfo("Fertig", f"Bulk Restore abgeschlossen.\n{erfolgreich} Spiele wurden an Lutris übergeben.")


# ==========================================
# GUI AUFBAU (CUSTOM

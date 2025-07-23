import os
import sys
import requests
import zipfile
import shutil
import time
from pathlib import Path
import subprocess
import threading
import tkinter as tk
from tkinter import ttk

# Paramètres
GITHUB_USER = "GGNatio"
GITHUB_REPO = "GendALF"
API_URL = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/releases/latest"

class UpdateWindow:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Mise à jour GendALF")
        self.root.geometry("650x320")
        self.root.resizable(False, False)
        self.label = tk.Label(self.root, text="", font=("Helvetica", 14))
        self.label.pack(pady=12)
        self.progress = ttk.Progressbar(self.root, orient="horizontal", length=580, mode="determinate")
        self.progress.pack(pady=12)
        self.status = tk.Label(self.root, text="", font=("Helvetica", 11), fg="#1976D2", wraplength=580, justify="left")
        self.status.pack(pady=8)
        # Boutons
        btn_frame = tk.Frame(self.root)
        btn_frame.pack(pady=10)
        self.pause_btn = tk.Button(btn_frame, text="Pause", width=12, command=self.pause)
        self.resume_btn = tk.Button(btn_frame, text="Reprendre", width=12, command=self.resume, state="disabled")
        self.stop_btn = tk.Button(btn_frame, text="Arrêter", width=12, command=self.stop)
        self.continue_btn = tk.Button(btn_frame, text="Continuer", width=12, command=self.close, state="disabled")
        self.pause_btn.grid(row=0, column=0, padx=8)
        self.resume_btn.grid(row=0, column=1, padx=8)
        self.stop_btn.grid(row=0, column=2, padx=8)
        self.continue_btn.grid(row=0, column=3, padx=8)
        self._pause_event = threading.Event()
        self._pause_event.set()  # autorisé à avancer
        self._stop_flag = False
        self.root.update()

    def pause(self):
        self._pause_event.clear()
        self.pause_btn.config(state="disabled")
        self.resume_btn.config(state="normal")
        self.set_status("Mise à jour en pause...")

    def resume(self):
        self._pause_event.set()
        self.pause_btn.config(state="normal")
        self.resume_btn.config(state="disabled")
        self.set_status("Mise à jour reprise.")

    def stop(self):
        self._stop_flag = True
        self.set_status("Arrêt demandé. La mise à jour va s'interrompre.")
        self.pause_btn.config(state="disabled")
        self.resume_btn.config(state="disabled")
        self.stop_btn.config(state="disabled")

    def check_pause_stop(self):
        while True:
            if self._stop_flag:
                raise Exception("Arrêt utilisateur")
            if self._pause_event.is_set():
                break
            time.sleep(0.1)

    def set_message(self, msg):
        self.label.config(text=msg)
        self.root.update()
    def set_status(self, msg):
        self.status.config(text=msg)
        self.root.update()
    def set_progress(self, value, maxval=100):
        self.progress.config(max=maxval)
        self.progress['value'] = value
        self.root.update()
    def enable_continue(self):
        self.continue_btn.config(state="normal")
        self.pause_btn.config(state="disabled")
        self.resume_btn.config(state="disabled")
        self.stop_btn.config(state="disabled")
        self.root.update()
    def close(self):
        self.root.destroy()
def get_log_file():
    logs_dir = INSTALL_DIR / "logs"
    logs_dir.mkdir(exist_ok=True)
    log_file = logs_dir / f"update_{time.strftime('%Y%m%d_%H%M%S')}.log"
    return log_file
def get_log_file():
    logs_dir = INSTALL_DIR / "logs"
    try:
        logs_dir.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        # Si le dossier ne peut pas être créé, fallback dans le dossier courant
        logs_dir = Path.cwd() / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)
    log_file = logs_dir / f"update_{time.strftime('%Y%m%d_%H%M%S')}.log"
    return log_file

def log_message(log_file, msg):
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}\n")

    def pause(self):
        self._pause_event.clear()
        self.pause_btn.config(state="disabled")
        self.resume_btn.config(state="normal")
        self.set_status("Mise à jour en pause...")

    def resume(self):
        self._pause_event.set()
        self.pause_btn.config(state="normal")
        self.resume_btn.config(state="disabled")
        self.set_status("Mise à jour reprise.")

    def stop(self):
        self._stop_flag = True
        self.set_status("Arrêt demandé. La mise à jour va s'interrompre.")
        self.pause_btn.config(state="disabled")
        self.resume_btn.config(state="disabled")
        self.stop_btn.config(state="disabled")

    def check_pause_stop(self):
        while not self._pause_event.is_set():
            time.sleep(0.1)
        if self._stop_flag:
            raise Exception("Arrêt utilisateur")

    def set_message(self, msg):
        self.label.config(text=msg)
        self.root.update()
    def set_status(self, msg):
        self.status.config(text=msg)
        self.root.update()
    def set_progress(self, value, maxval=100):
        self.progress.config(max=maxval)
        self.progress['value'] = value
        self.root.update()
    def close(self):
        self.root.destroy()
    def set_message(self, msg):
        self.label.config(text=msg)
        self.root.update()
    def set_status(self, msg):
        self.status.config(text=msg)
        self.root.update()
    def set_progress(self, value, maxval=100):
        self.progress.config(max=maxval)
        self.progress['value'] = value
        self.root.update()
    def close(self):
        self.root.destroy()


def get_install_dir():
    # Toujours prendre le dossier parent du fichier exécuté (update.exe ou .py)
    return Path(os.path.dirname(os.path.abspath(sys.argv[0])))

INSTALL_DIR = get_install_dir()


def get_latest_zip_url_and_version():
    print("Recherche de la dernière release...")
    r = requests.get(API_URL, timeout=10)
    r.raise_for_status()
    data = r.json()
    version = data.get("tag_name") or data.get("name") or "?"
    for asset in data.get("assets", []):
        if asset["name"].lower().endswith(".zip"):
            print(f"Dernier zip trouvé : {asset['browser_download_url']}")
            return asset["browser_download_url"], version
    raise Exception("Aucun zip trouvé dans la dernière release.")


def download_update(zip_url, zip_path, win):
    win.set_message("Téléchargement de la mise à jour...")
    log_file = win.log_file
    log_message(log_file, "Début du téléchargement de la mise à jour.")
    r = requests.get(zip_url, stream=True)
    r.raise_for_status()
    total = int(r.headers.get('content-length', 0))
    downloaded = 0
    chunk_size = 8192
    with open(zip_path, "wb") as f:
        for chunk in r.iter_content(chunk_size=chunk_size):
            win.check_pause_stop()
            f.write(chunk)
            downloaded += len(chunk)
            percent = int(downloaded * 100 / total) if total else 0
            win.set_progress(percent)
            win.set_status(f"{downloaded//1024} Ko / {total//1024 if total else '?'} Ko")
    win.set_progress(100)
    win.set_status("Téléchargement terminé.")
    log_message(log_file, "Téléchargement terminé.")


def extract_update(zip_path, target_dir, win):
    win.set_message("Extraction des fichiers...")
    log_file = win.log_file
    log_message(log_file, "Début de l'extraction des fichiers.")
    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        members = [m for m in zip_ref.namelist() if m.startswith("GendALF/") and not m.endswith("/")]
        total = len(members)
        if total == 0:
            win.set_message("Erreur : Aucun fichier à extraire depuis le zip !")
            log_message(log_file, "Erreur : Aucun fichier à extraire depuis le zip !")
            win.enable_continue()
            return False
        exclusions_extract = {"update.exe", "update.py"}
        extracted_count = 0
        for i, member in enumerate(members):
            win.check_pause_stop()
            rel_path = Path(member[len("GendALF/"):])
            if rel_path.name == "":
                continue
            if rel_path.name in exclusions_extract:
                log_message(log_file, f"Fichier ignoré à l'extraction : {rel_path}")
                continue
            target_path = target_dir / rel_path
            target_path.parent.mkdir(parents=True, exist_ok=True)
            try:
                with zip_ref.open(member) as source, open(target_path, "wb") as target:
                    shutil.copyfileobj(source, target)
            except Exception as e:
                msg = f"Erreur lors de l'extraction de {rel_path}: {e}\n\nFermez GendALF et tout programme qui utilise ce fichier, puis relancez la mise à jour."
                win.set_message(msg)
                log_message(log_file, msg)
                win.enable_continue()
                return False
            extracted_count += 1
            win.set_progress(extracted_count, total)
            win.set_status(f"{extracted_count}/{total} fichiers extraits")
            log_message(log_file, f"Fichier extrait : {rel_path}")
    win.set_status("Extraction terminée.")
    log_message(log_file, "Extraction terminée.")
    return True



from tkinter import filedialog, messagebox

def show_choice_window():
    root = tk.Tk()
    root.title("Choix de la mise à jour")
    root.geometry("400x180")
    root.resizable(False, False)
    label = tk.Label(root, text="Choisissez le mode de mise à jour :", font=("Helvetica", 14))
    label.pack(pady=18)
    btn_frame = tk.Frame(root)
    btn_frame.pack(pady=10)
    result = {'choice': None}
    def online():
        result['choice'] = 'online'
        root.destroy()
    def local():
        result['choice'] = 'local'
        root.destroy()
    online_btn = tk.Button(btn_frame, text="Mise à jour en ligne", width=18, command=online)
    local_btn = tk.Button(btn_frame, text="Mise à jour locale (ZIP)", width=18, command=local)
    online_btn.grid(row=0, column=0, padx=12)
    local_btn.grid(row=0, column=1, padx=12)
    root.mainloop()
    return result['choice']

def download_update_with_eta(zip_url, zip_path, win):
    win.set_message("Téléchargement de la mise à jour...")
    log_file = win.log_file
    log_message(log_file, "Début du téléchargement de la mise à jour.")
    r = requests.get(zip_url, stream=True)
    r.raise_for_status()
    total = int(r.headers.get('content-length', 0))
    downloaded = 0
    chunk_size = 8192
    start_time = time.time()
    with open(zip_path, "wb") as f:
        for chunk in r.iter_content(chunk_size=chunk_size):
            win.check_pause_stop()
            f.write(chunk)
            downloaded += len(chunk)
            percent = int(downloaded * 100 / total) if total else 0
            elapsed = time.time() - start_time
            speed = downloaded / elapsed if elapsed > 0 else 0
            eta = (total - downloaded) / speed if speed > 0 else 0
            eta_str = time.strftime('%M:%S', time.gmtime(eta)) if eta > 0 else "--:--"
            win.set_progress(percent)
            win.set_status(f"{downloaded//1024} Ko / {total//1024 if total else '?'} Ko  |  {percent}%  |  Temps restant estimé : {eta_str}")
    win.set_progress(100)
    win.set_status("Téléchargement terminé.")
    log_message(log_file, "Téléchargement terminé.")

def extract_update_with_eta(zip_path, target_dir, win):
    win.set_message("Extraction des fichiers...")
    log_file = win.log_file
    log_message(log_file, "Début de l'extraction des fichiers.")
    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        members = [m for m in zip_ref.namelist() if m.startswith("GendALF/") and not m.endswith("/")]
        total = len(members)
        if total == 0:
            win.set_message("Erreur : Aucun fichier à extraire depuis le zip !")
            log_message(log_file, "Erreur : Aucun fichier à extraire depuis le zip !")
            win.enable_continue()
            return False
        exclusions_extract = {"update.exe", "update.py"}
        extracted_count = 0
        start_time = time.time()
        for i, member in enumerate(members):
            win.check_pause_stop()
            rel_path = Path(member[len("GendALF/" ):])
            if rel_path.name == "":
                continue
            if rel_path.name in exclusions_extract:
                log_message(log_file, f"Fichier ignoré à l'extraction : {rel_path}")
                continue
            target_path = target_dir / rel_path
            target_path.parent.mkdir(parents=True, exist_ok=True)
            try:
                with zip_ref.open(member) as source, open(target_path, "wb") as target:
                    shutil.copyfileobj(source, target)
            except Exception as e:
                msg = f"Erreur lors de l'extraction de {rel_path}: {e}\n\nFermez GendALF et tout programme qui utilise ce fichier, puis relancez la mise à jour."
                win.set_message(msg)
                log_message(log_file, msg)
                win.enable_continue()
                return False
            extracted_count += 1
            percent = int(extracted_count * 100 / total)
            elapsed = time.time() - start_time
            speed = extracted_count / elapsed if elapsed > 0 else 0
            eta = (total - extracted_count) / speed if speed > 0 else 0
            eta_str = time.strftime('%M:%S', time.gmtime(eta)) if eta > 0 else "--:--"
            win.set_progress(extracted_count, total)
            win.set_status(f"{extracted_count}/{total} fichiers extraits  |  {percent}%  |  Temps restant estimé : {eta_str}")
            log_message(log_file, f"Fichier extrait : {rel_path}")
    win.set_status("Extraction terminée.")
    log_message(log_file, "Extraction terminée.")
    return True

def main():
    # Demander les droits admin si nécessaire
    if os.name == "nt":
        import ctypes
        try:
            is_admin = ctypes.windll.shell32.IsUserAnAdmin()
        except Exception:
            is_admin = False
        if not is_admin:
            params = ' '.join([f'"{arg}"' for arg in sys.argv])
            ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, params, None, 1)
            sys.exit(0)

    choice = show_choice_window()
    if not choice:
        return

    win = UpdateWindow()
    win.log_file = get_log_file()
    log_message(win.log_file, "--- Démarrage de la mise à jour ---")

    def update_process():
        try:
            zip_path = INSTALL_DIR / "update.zip"
            backup_dir = INSTALL_DIR / "backup_update"
            backup_dir.mkdir(exist_ok=True)
            exclusions = {
                "update.exe",
                "asset/preference.json",
                "asset/icons/",
                "asset/lang/",
                "asset/recent",
                "logs/",
                "backup_update/",
            }
            win.set_message("Sauvegarde des fichiers existants...")
            log_message(win.log_file, "Début de la sauvegarde des fichiers existants.")
            for item in INSTALL_DIR.iterdir():
                rel_path = str(item.relative_to(INSTALL_DIR)).replace("\\", "/")
                if rel_path in exclusions or any(rel_path.startswith(excl.rstrip("/")) for excl in exclusions if excl.endswith("/")):
                    continue
                try:
                    shutil.move(str(item), str(backup_dir / item.name))
                    log_message(win.log_file, f"Fichier sauvegardé : {item}")
                except Exception as e:
                    log_message(win.log_file, f"Erreur sauvegarde {item}: {e}")
            win.set_status("Fichiers sauvegardés.")

            if choice == 'online':
                win.set_message("Recherche de la dernière release...")
                zip_url, version = get_latest_zip_url_and_version()
                win.set_status(f"Version : {version}\nURL : {zip_url}")
                log_message(win.log_file, f"Release trouvée : {version} - {zip_url}")
                win.set_message(f"Téléchargement de la version {version}...")
                download_update_with_eta(zip_url, zip_path, win)
                # Vérification que le fichier est bien un zip
                is_zip = False
                try:
                    with open(zip_path, "rb") as f:
                        sig = f.read(4)
                        is_zip = sig == b'PK\x03\x04'
                except Exception as e:
                    log_message(win.log_file, f"Erreur lors de la lecture du zip téléchargé : {e}")
                if not is_zip:
                    msg = "Le fichier téléchargé n'est pas un zip valide.\nVérifiez votre connexion ou l'intégrité de la release."
                    win.set_message(msg)
                    try:
                        with open(zip_path, "rb") as f:
                            preview = f.read(256)
                        log_message(win.log_file, f"Contenu du fichier (256 premiers octets) : {preview}")
                    except Exception as e:
                        log_message(win.log_file, f"Impossible de lire le contenu du zip : {e}")
                    win.enable_continue()
                    return
                win.set_message("Attente de la fermeture de l'application...")
                time.sleep(2)
                win.set_message(f"Extraction de la version {version}...")
                extracted = extract_update_with_eta(zip_path, INSTALL_DIR, win)
            else:
                # Locale : demander le zip
                win.set_message("Sélectionnez le fichier ZIP de mise à jour...")
                zip_file = filedialog.askopenfilename(
                    title="Sélectionnez le fichier ZIP de mise à jour",
                    filetypes=[("Fichiers ZIP", "*.zip")],
                )
                if not zip_file:
                    win.set_message("Aucun fichier sélectionné. Annulation.")
                    win.enable_continue()
                    return
                if "GendALF" not in os.path.basename(zip_file):
                    win.set_message("Le fichier ZIP doit contenir 'GendALF' dans son nom.")
                    win.enable_continue()
                    return
                # Copie le zip local dans update.zip pour réutiliser la logique
                shutil.copy(zip_file, zip_path)
                version = os.path.basename(zip_file)
                win.set_message(f"Extraction de la version locale : {version}...")
                extracted = extract_update_with_eta(zip_path, INSTALL_DIR, win)

            if not extracted:
                win.set_message("Aucun fichier extrait, restauration du backup...")
                log_message(win.log_file, "Aucun fichier extrait, restauration du backup...")
                for item in backup_dir.iterdir():
                    try:
                        shutil.move(str(item), str(INSTALL_DIR / item.name))
                        log_message(win.log_file, f"Fichier restauré : {item}")
                    except Exception as e:
                        log_message(win.log_file, f"Erreur restauration {item}: {e}")
                shutil.rmtree(backup_dir)
                win.set_message("Mise à jour échouée, backup restauré.")
                win.enable_continue()
                return
            new_files = [f for f in INSTALL_DIR.iterdir() if f.name not in exclusions and f.name != "backup_update"]
            if new_files:
                shutil.rmtree(backup_dir)
                win.set_message(f"Mise à jour terminée ! Version installée : {version}")
                log_message(win.log_file, f"Mise à jour terminée ! Version installée : {version}")
            else:
                win.set_message("Aucun fichier mis à jour, restauration du backup...")
                log_message(win.log_file, "Aucun fichier mis à jour, restauration du backup...")
                for item in backup_dir.iterdir():
                    try:
                        shutil.move(str(item), str(INSTALL_DIR / item.name))
                        log_message(win.log_file, f"Fichier restauré : {item}")
                    except Exception as e:
                        log_message(win.log_file, f"Erreur restauration {item}: {e}")
                shutil.rmtree(backup_dir)
                win.set_message("Mise à jour échouée, backup restauré.")
                win.enable_continue()
        except Exception as e:
            win.set_message(f"Erreur : {e}")
            log_message(win.log_file, f"Erreur générale : {e}")
            try:
                for item in (INSTALL_DIR / "backup_update").iterdir():
                    try:
                        shutil.move(str(item), str(INSTALL_DIR / item.name))
                        log_message(win.log_file, f"Fichier restauré : {item}")
                    except Exception as e2:
                        log_message(win.log_file, f"Erreur restauration {item}: {e2}")
                shutil.rmtree(INSTALL_DIR / "backup_update")
            except Exception as e3:
                log_message(win.log_file, f"Erreur suppression backup_update: {e3}")
            win.set_message("Mise à jour échouée, backup restauré.")
            win.enable_continue()
        finally:
            try:
                os.remove(INSTALL_DIR / "update.zip")
                log_message(win.log_file, "update.zip supprimé.")
            except Exception as e:
                log_message(win.log_file, f"Erreur suppression update.zip: {e}")
            exe_path = INSTALL_DIR / "GendALF.exe"
            # Ne pas redémarrer automatiquement si erreur, seulement si tout OK
            if exe_path.exists() and not win.continue_btn['state'] == "normal":
                win.set_message("Redémarrage de l'application...")
                log_message(win.log_file, "Redémarrage de l'application...")
                subprocess.Popen([str(exe_path)])
                time.sleep(2)
                win.close()
    threading.Thread(target=update_process, daemon=True).start()
    win.root.mainloop()

if __name__ == "__main__":
    main()

import os
import sys
import json
import requests
import subprocess
import threading
import time
from pathlib import Path
from packaging import version
import tkinter as tk
from tkinter import messagebox

class RXviewerAutoUpdater:
    def __init__(self, app):
        self.app = app
        self.github_user = "GGNatio"
        self.github_repo = "GendALF"
        self.github_api_url = f"https://api.github.com/repos/{self.github_user}/{self.github_repo}/releases/latest"
        self.current_version = self._get_current_version()

    def _get_current_version(self):
        try:
            data_path = Path(__file__).parent.parent / "asset" / "data.json"
            with open(data_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data.get("app_info", {}).get("version", "1.0.0")
        except Exception:
            return "1.0.0"

    def check_for_updates(self, manual_check=False):
        def check_update_thread():
            try:
                response = requests.get(self.github_api_url, timeout=10)
                if response.status_code != 200:
                    if manual_check:
                        messagebox.showerror("Erreur", "Impossible d'accéder à GitHub.")
                    return
                release_data = response.json()
                latest_version = release_data.get("tag_name", "").lstrip("v")
                if not latest_version:
                    if manual_check:
                        messagebox.showinfo("Mise à jour", "Impossible de récupérer la version en ligne.")
                    return
                if version.parse(latest_version) > version.parse(self.current_version):
                    self._show_update_dialog(latest_version)
                else:
                    if manual_check:
                        messagebox.showinfo("Mise à jour", f"Vous avez déjà la dernière version ({self.current_version}).")
            except Exception as e:
                if manual_check:
                    messagebox.showerror("Erreur", f"Erreur lors de la vérification des mises à jour:\n{e}")
        threading.Thread(target=check_update_thread, daemon=True).start()

    def _show_update_dialog(self, latest_version):
        def show_dialog():
            win = tk.Toplevel(self.app.app if hasattr(self.app, 'app') else None)
            win.title("Mise à jour disponible")
            win.geometry("400x200")
            win.resizable(False, False)
            tk.Label(win, text=f"Nouvelle version disponible : {latest_version}", font=("Helvetica", 14, "bold"), fg="green").pack(pady=10)
            tk.Label(win, text=f"Version actuelle : {self.current_version}", font=("Helvetica", 10)).pack(pady=5)
            tk.Label(win, text="Voulez-vous installer la mise à jour maintenant ?", font=("Helvetica", 10)).pack(pady=10)
            def update_and_quit():
                win.destroy()
                self._run_updater()
            tk.Button(win, text="Mettre à jour", command=update_and_quit, bg="green", fg="white", font=("Helvetica", 10, "bold")).pack(side='left', padx=30, pady=20)
            tk.Button(win, text="Plus tard", command=win.destroy, font=("Helvetica", 10)).pack(side='right', padx=30, pady=20)
            win.grab_set()
        if hasattr(self.app, 'app'):
            self.app.app.after(0, show_dialog)
        else:
            show_dialog()

    def _run_updater(self):
        import sys
        import os
        from pathlib import Path
        exe_dir = Path(os.path.dirname(os.path.abspath(sys.argv[0])))
        updater_path = exe_dir / "update.exe"
        if updater_path.exists():
            subprocess.Popen([str(updater_path)])
        else:
            messagebox.showerror("Erreur", f"update.exe est introuvable dans le dossier : {exe_dir}")
        if hasattr(self.app, 'app'):
            self.app.app.quit()

class RXviewerBackupManager:
    def __init__(self, app):
        self.app = app

    def create_backup(self, project_path, backup_name=None):
        try:
            project_path = Path(project_path)
            if not project_path.exists():
                raise Exception(f"Le projet {project_path} n'existe pas")
            backup_dir = Path.home() / "Documents" / "RXViewer" / "backups"
            backup_dir.mkdir(parents=True, exist_ok=True)
            if not backup_name:
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                backup_name = f"{project_path.name}_{timestamp}"
            backup_path = backup_dir / f"{backup_name}.zip"
            import zipfile
            with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(project_path):
                    for file in files:
                        file_path = Path(root) / file
                        arcname = file_path.relative_to(project_path)
                        zipf.write(file_path, arcname)
            return backup_path
        except Exception as e:
            raise Exception(f"Erreur lors de la création de la sauvegarde: {str(e)}")

    def restore_backup(self, backup_path, restore_location=None):
        try:
            backup_path = Path(backup_path)
            if not backup_path.exists():
                raise Exception(f"La sauvegarde {backup_path} n'existe pas")
            if not restore_location:
                restore_location = Path.home() / "Documents" / "RXViewer" / "projects"
            restore_location = Path(restore_location)
            restore_location.mkdir(parents=True, exist_ok=True)
            import zipfile
            with zipfile.ZipFile(backup_path, 'r') as zipf:
                zipf.extractall(restore_location)
            return restore_location
        except Exception as e:
            raise Exception(f"Erreur lors de la restauration: {str(e)}")

    def list_backups(self):
        try:
            backup_dir = Path.home() / "Documents" / "RXViewer" / "backups"
            if not backup_dir.exists():
                return []
            backups = []
            for backup_file in backup_dir.glob("*.zip"):
                stat = backup_file.stat()
                backups.append({
                    'name': backup_file.stem,
                    'path': backup_file,
                    'size': stat.st_size,
                    'date': time.ctime(stat.st_mtime)
                })
            return sorted(backups, key=lambda x: x['date'], reverse=True)
        except Exception as e:
            print(f"Erreur lors de la liste des sauvegardes: {e}")
            return []

class RXviewerSaveManager:
    def __init__(self, app):
        self.app = app
        self.updater = RXviewerAutoUpdater(app)
        self.backup_manager = RXviewerBackupManager(app)

    def check_updates_on_startup(self):
        def delayed_check():
            time.sleep(3)
            self.updater.check_for_updates(manual_check=False)
        threading.Thread(target=delayed_check, daemon=True).start()

    def manual_update_check(self):
        self.updater.check_for_updates(manual_check=True)

    def backup_current_project(self):
        if not hasattr(self.app, 'current_project') or not self.app.current_project:
            messagebox.showwarning("Aucun projet", "Aucun projet ouvert à sauvegarder")
            return
        try:
            backup_path = self.backup_manager.create_backup(self.app.current_project)
            messagebox.showinfo("Sauvegarde réussie", f"Projet sauvegardé avec succès :\n{backup_path}")
        except Exception as e:
            messagebox.showerror("Erreur de sauvegarde", str(e))

    def show_backup_manager(self):
        backups = self.backup_manager.list_backups()
        if not backups:
            messagebox.showinfo("Sauvegardes", "Aucune sauvegarde trouvée")
            return
        backup_list = "\n".join([f"• {b['name']} ({b['date']})" for b in backups[:10]])
        messagebox.showinfo("Sauvegardes disponibles", f"Dernières sauvegardes:\n\n{backup_list}")

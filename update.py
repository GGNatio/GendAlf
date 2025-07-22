import os
import sys
import requests
import zipfile
import shutil
import time
from pathlib import Path
import subprocess

# Paramètres
GITHUB_USER = "GGNatio"
GITHUB_REPO = "GendALF"
ZIP_URL = f"https://github.com/{GITHUB_USER}/{GITHUB_REPO}/archive/refs/heads/main.zip"
def get_install_dir():
    # Toujours prendre le dossier parent du fichier exécuté (update.exe ou .py)
    return Path(os.path.dirname(os.path.abspath(sys.argv[0])))

INSTALL_DIR = get_install_dir()

def download_update(zip_path):
    print("Téléchargement de la mise à jour...")
    r = requests.get(ZIP_URL, stream=True)
    with open(zip_path, "wb") as f:
        for chunk in r.iter_content(chunk_size=8192):
            f.write(chunk)

def extract_update(zip_path, target_dir):
    print("Extraction des fichiers...")
    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        for member in zip_ref.namelist():
            if member.startswith(f"{GITHUB_REPO}-main/"):
                rel_path = member[len(f"{GITHUB_REPO}-main/"):]
                if rel_path:
                    target_path = target_dir / rel_path
                    if member.endswith("/"):
                        target_path.mkdir(parents=True, exist_ok=True)
                    else:
                        with zip_ref.open(member) as source, open(target_path, "wb") as target:
                            shutil.copyfileobj(source, target)

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

    zip_path = INSTALL_DIR / "update.zip"
    backup_dir = INSTALL_DIR / "backup_update"
    backup_dir.mkdir(exist_ok=True)

    # Liste des fichiers/dossiers à NE PAS toucher
    exclusions = {
        "update.exe",
        "asset/preference.json",
        "asset/icons/",  # Garde tout le dossier icons
        "asset/lang/",   # Garde les langues
        "asset/recent",  # Historique récent
    }

    # Déplacer tous les fichiers/dossiers sauf exclusions dans le backup
    for item in INSTALL_DIR.iterdir():
        rel_path = str(item.relative_to(INSTALL_DIR)).replace("\\", "/")
        if rel_path in exclusions or any(rel_path.startswith(excl.rstrip("/")) for excl in exclusions if excl.endswith("/")):
            continue
        try:
            shutil.move(str(item), str(backup_dir / item.name))
        except Exception:
            print(f"Impossible de déplacer {item} dans le backup.")

    print("Téléchargement de la mise à jour...")
    download_update(zip_path)
    print("Attente de la fermeture de l'application...")
    time.sleep(2)

    # Extraction et vérification
    try:
        extract_update(zip_path, INSTALL_DIR)
        # Vérifier qu'au moins un nouveau fichier a été ajouté (hors exclusions)
        new_files = [f for f in INSTALL_DIR.iterdir() if f.name not in exclusions and f.name != "backup_update"]
        if new_files:
            # Suppression du backup si tout est ok
            shutil.rmtree(backup_dir)
            print("Mise à jour terminée.")
        else:
            # Restauration du backup
            print("Aucun fichier mis à jour, restauration du backup...")
            for item in backup_dir.iterdir():
                try:
                    shutil.move(str(item), str(INSTALL_DIR / item.name))
                except Exception:
                    print(f"Impossible de restaurer {item}")
            shutil.rmtree(backup_dir)
            print("Mise à jour échouée, backup restauré.")
    except Exception as e:
        print(f"Erreur lors de l'extraction: {e}\nRestauration du backup...")
        for item in backup_dir.iterdir():
            try:
                shutil.move(str(item), str(INSTALL_DIR / item.name))
            except Exception:
                print(f"Impossible de restaurer {item}")
        shutil.rmtree(backup_dir)
        print("Mise à jour échouée, backup restauré.")

    os.remove(zip_path)
    exe_path = INSTALL_DIR / "GendALF.exe"
    if exe_path.exists():
        subprocess.Popen([str(exe_path)])
    else:
        print("Impossible de relancer l'application.")

if __name__ == "__main__":
    main()

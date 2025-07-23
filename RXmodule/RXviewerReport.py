import tkinter as tk
from tkinter import messagebox
import socket

class RXviewerReport:
    def __init__(self, parent=None):
        self.parent = parent
        if not self.check_internet():
            messagebox.showerror("Connexion requise", "Aucune connexion internet détectée.\nVeuillez vous connecter à internet ou faire le rapport sur une machine connectée.")
            return
        self.open_report_window()

    def check_internet(self, host="8.8.8.8", port=53, timeout=3):
        """Vérifie la connexion internet en tentant de joindre un serveur DNS public."""
        try:
            socket.setdefaulttimeout(timeout)
            socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
            return True
        except Exception:
            return False

    def open_report_window(self):
        import platform
        import json
        import requests
        from tkinter import filedialog, messagebox
        from pathlib import Path
        import os

        win = tk.Toplevel(self.parent) if self.parent else tk.Tk()
        win.title("Signaler un bug")
        win.geometry("520x540")
        win.grab_set()

        tk.Label(win, text="Décrivez le problème rencontré :", font=("Helvetica", 11, "bold")).pack(pady=(10, 2))

        # Problèmes courants
        common_issues = [
            "Crash au démarrage",
            "Problème d'affichage",
            "Erreur lors de l'ouverture d'un projet",
            "Problème de sauvegarde",
            "Autre (voir description)"
        ]
        self.issue_vars = []
        frame_issues = tk.Frame(win)
        frame_issues.pack(pady=2)
        for issue in common_issues:
            var = tk.BooleanVar()
            cb = tk.Checkbutton(frame_issues, text=issue, variable=var)
            cb.pack(anchor='w')
            self.issue_vars.append((issue, var))

        # Zone de texte pour description
        tk.Label(win, text="Description détaillée :").pack(pady=(10, 2))
        self.text_desc = tk.Text(win, height=7, width=60)
        self.text_desc.pack(pady=2)


        # Champ de contact optionnel
        contact_frame = tk.Frame(win)
        contact_frame.pack(pady=(10, 2))
        tk.Label(contact_frame, text="Moyen de contact pour plus de demande (optionnel) :").pack(side='left')
        self.contact_var = tk.StringVar()
        tk.Entry(contact_frame, textvariable=self.contact_var, width=35).pack(side='left', padx=(5,0))

        # Checkbox pour ajouter le contenu du dernier log
        self.add_log_var = tk.BooleanVar()
        def update_log_label():
            if self.add_log_var.get():
                log_label.config(fg="#1976D2")
            else:
                log_label.config(fg="black")
        log_frame = tk.Frame(win)
        log_frame.pack(pady=(10, 2))
        self.last_log_path = None
        logs_dir = Path(__file__).resolve().parent.parent / "logs"
        last_log_name = "aucun log trouvé"
        if logs_dir.exists():
            logs = sorted(logs_dir.glob("*.log"), key=os.path.getmtime, reverse=True)
            if logs:
                self.last_log_path = logs[0]
                last_log_name = self.last_log_path.name
        log_label = tk.Label(log_frame, text=f"Inclure le contenu du dernier log : {last_log_name}")
        log_label.pack(side='left')
        tk.Checkbutton(log_frame, variable=self.add_log_var, command=update_log_label).pack(side='left', padx=(5,0))

        # Bouton Envoyer

        def send_report():
            issues = [issue for issue, var in self.issue_vars if var.get()]
            desc = self.text_desc.get("1.0", 'end').strip()
            contact = self.contact_var.get().strip()
            sysinfo = f"\n\n---\nVersion: à compléter\nOS: {platform.system()} {platform.release()}"
            logs_content = ""
            if self.add_log_var.get() and self.last_log_path:
                try:
                    with open(self.last_log_path, 'r', encoding='utf-8', errors='replace') as logf:
                        content = logf.read(1024*1024)
                    logs_content = f"\n\n---\nContenu du dernier log ({self.last_log_path.name}) :\n\n" + content + "\n"
                except Exception as e:
                    logs_content = f"\n\nImpossible de lire le log {self.last_log_path} : {e}\n"
            contact_info = f"\n\nMoyen de contact : {contact}" if contact else ""
            body = "**Problèmes cochés :**\n" + '\n'.join(f"- {i}" for i in issues) + "\n\n**Description :**\n" + desc + sysinfo + contact_info + logs_content

            # Récupérer le token depuis asset/token.json
            try:
                data_path = Path(__file__).resolve().parent.parent / "asset" / "token.json"
                with open(data_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                token = data.get("github_token", "")
            except Exception as e:
                messagebox.showerror("Erreur", f"Impossible de lire le token GitHub dans asset/token.json : {e}")
                return
            if not token:
                messagebox.showerror("Erreur", "Aucun token GitHub trouvé dans asset/token.json (clé 'github_token').")
                return

            # Envoi de l'issue via l'API GitHub
            url = "https://api.github.com/repos/GGNatio/GendAlf/issues"
            headers = {
                "Authorization": f"token {token}",
                "Accept": "application/vnd.github+json"
            }
            title = desc.split('\n')[0][:60] if desc else "Bug GendAlf"
            payload = {"title": title, "body": body}
            try:
                resp = requests.post(url, headers=headers, json=payload, timeout=10)
                if resp.status_code == 201:
                    messagebox.showinfo("Succès", "Le rapport de bug a été envoyé avec succès sur GitHub !")
                    win.destroy()
                else:
                    messagebox.showerror("Erreur", f"Erreur lors de l'envoi : {resp.status_code}\n{resp.text}")
            except Exception as e:
                messagebox.showerror("Erreur", f"Erreur lors de l'envoi : {e}")

        tk.Button(win, text="Envoyer le rapport", command=send_report, bg="#1976D2", fg="white", font=("Helvetica", 11, "bold")).pack(pady=18)

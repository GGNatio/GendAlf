import tkinter as tk
from tkinter import messagebox
from pathlib import Path
import cv2
from PIL import Image, ImageTk
import json

from RXmodule.RXviewerRaws import RXviewerRaws
from RXmodule.RXviewerLabels import RXviewerLabels
from RXmodule.RXviewerToolsBox import RXviewerToolsBox
class ViewerAdapter:
    def __init__(self, project_view):
        self.app = project_view.app  # le Toplevel transmis à ProjectView
        self.raw = project_view.raw
        self.can = project_view.canvas
        self.displayImage = project_view.showImage
        self.labels = project_view.labels
        self.project_file = {}
        self.labels_canvas = None
        self.lang = {
            "tools_box": "Boîte à Outils",
            "tools": "Outils",
            "color": "Couleur",
            "settings": "Paramètres",
            "thickness": "Épaisseur",
            "tolerance": "Tolérance",
            "color_switch": "Changer la couleur",
            "change_contrast": "Contraste",
            "apply_all": "Appliquer à toutes"
        }

class ProjectView:
    def __init__(self, parent, bgColor, app):
        self.app = app
        self.project_path = None
        self.raw = RXviewerRaws(app)
        self.labels = RXviewerLabels(app)
        
        


        self.raw_id = 0
        self.tk_image = None
        self.raw.raw_coords = [0, 0]

        

        self.container = tk.Frame(parent, bg=bgColor)
        self.container.pack(side="left", expand=True, fill="both")

        self.canvas = tk.Canvas(self.container, bg=bgColor)
        self.canvas.pack(expand=True, fill="both")

        self.button_bar = tk.Frame(self.container)
        self.button_bar.pack(side="bottom", fill="x")
        self.adapter = ViewerAdapter(self)
        self.toolsBox = RXviewerToolsBox(self.adapter)
        self.toolsBox_visible = False
        self._setupButtons()
        self._bindTools()
        

    def loadImagesFromPath(self, project_path):
        self.project_path = project_path
        self.raw.loadImagesFromPath(project_path)
        with open(project_path / "project.json", 'r', encoding='utf-8') as file:
            project_file = json.load(file)
        self.labels.addLabels(project_file['labels'])
        self.showImage()

    def showImage(self):
        
        if not self.raw.raw:
            return
        image = self.raw.raw[self.raw_id].raw
        image_pil = Image.fromarray(image)
        self.tk_image = ImageTk.PhotoImage(image_pil)
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.tk_image)
        self.counter_label.config(text=f"{self.raw_id+1}/{len(self.raw.raw)}")
        self.labels.moveLabels((image.shape[1], image.shape[0]), self.raw.raw_coords)

    def scroll(self, delta):
        if not self.raw.raw:
            return
        step = 1 if delta < 0 else -1
        new_id = self.raw_id + step
        if 0 <= new_id < len(self.raw.raw):
            self.raw_id = new_id
            self.showImage()

    def reset(self):
        '''Recharge l’image originale depuis le fichier raw'''
        if not self.raw.raw:
            messagebox.showwarning("⚠️", "Aucun projet n'est ouvert.")
            return

        try:
            # Récupère le nom du fichier en cours
            filename = self.raw.raw[self.raw_id].filename
            raw_path = self.project_path / "raw" / filename

            if raw_path.exists():
                raw_image = cv2.imread(str(raw_path), cv2.IMREAD_UNCHANGED)
                self.raw.raw[self.raw_id].raw = raw_image
                self.raw.raw_coords = [0, 0]
                self.toolsBox.raw_zoom = 1.0
                self.toolsBox.raw_rotation = -1
                self.toolsBox.raw_flip = -2
                self.showImage()
            else:
                messagebox.showerror("Erreur", f"Image introuvable : {raw_path}")
        except Exception as e:
            messagebox.showerror("Erreur", f"Échec de la réinitialisation de l'image.\n\n{e}")


    def _setupButtons(self):
        tk.Button(self.button_bar, text='<<', command=lambda: self._navig(-self.raw_id)).pack(side='left')
        tk.Button(self.button_bar, text='<', command=lambda: self._navig(-1)).pack(side='left')
        tk.Button(self.button_bar, text='♦', command=self.reset).pack(side='left')
        tk.Button(self.button_bar, text='>', command=lambda: self._navig(1)).pack(side='left')
        tk.Button(self.button_bar, text='>>', command=lambda: self._navig(len(self.raw.raw) - 1 - self.raw_id)).pack(side='left')
        tk.Button(self.button_bar, text='reset', command=self.reset).pack(side='left')
        tk.Button(self.button_bar, text='🧰', command=self.toolsBox.toolsBox).pack(side='left', padx=5)

        self.counter_label = tk.Label(self.button_bar, text='0/0')
        self.counter_label.pack(side='left', padx=5)

    def _navig(self, direction):
        if not self.raw.raw:
            return
        new_id = self.raw_id + direction
        if 0 <= new_id < len(self.raw.raw):
            self.raw_id = new_id
            self.showImage()

    def _bindTools(self):
        self.canvas.bind("<Button-3>", self.toolsBox._startMove)
        self.canvas.bind("<B3-Motion>", self.toolsBox._doMove)
        self.canvas.bind("<Control-MouseWheel>", self.toolsBox.do_zoom)
        self.app.bind_all("<Control-z>", lambda e: self.toolsBox.draw.undo())
        self.app.bind_all("<Control-y>", lambda e: self.toolsBox.draw.redo())

    def _openToolbox(self):
        if not self.toolsBox_visible:
            self.adapter.can = self.canvas
            self.adapter.raw = self.raw
            self.adapter.displayImage = self.showImage
            self.toolsBox.canvas = self.canvas
            if hasattr(self.toolsBox, 'draw'):
                self.toolsBox.draw.canvas = self.canvas
            self.toolsBox.toolsBox()
            self.toolsBox_visible = True
        else:
            if hasattr(self.toolsBox, '_child_window_toolsBox') and self.toolsBox._child_window_toolsBox.winfo_exists():
                self.toolsBox._child_window_toolsBox.destroy()
            self.toolsBox_visible = False




class RXviewerSecondary:
    def __init__(self, app, path1: Path, path2: Path):
        self.window = app

        self.window.title("RXviewer - Double Projet")
        self.window.geometry("1920x1080")
        self.window.configure(bg="#333333")

        self.project_left = ProjectView(self.window, bgColor="#222222", app=self.window)
        self.project_right = ProjectView(self.window, bgColor="#222222", app=self.window)

        self.project_left.loadImagesFromPath(path1)
        self.project_right.loadImagesFromPath(path2)

        self.project_left.canvas.bind("<Enter>", lambda e: self._setActive('left'))
        self.project_right.canvas.bind("<Enter>", lambda e: self._setActive('right'))
        
        self.active_view = 'left'
        self.window.bind("<MouseWheel>", self._onScroll)
        self.window.bind("<Button-4>", self._onScroll)
        self.window.bind("<Button-5>", self._onScroll)

    def _setActive(self, side):
        self.active_view = side

    def _onScroll(self, event):
        delta = event.delta if hasattr(event, 'delta') else (120 if event.num == 4 else -120)
        if self.active_view == 'left':
            self.project_left.scroll(delta)
        elif self.active_view == 'right':
            self.project_right.scroll(delta)

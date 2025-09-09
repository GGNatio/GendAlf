import tkinter as tk
from tkinter import colorchooser
from PIL import Image, ImageTk, ImageDraw
from pathlib import Path
import cv2
import numpy as np

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent)) 


class RXviewer: ...


class RXviewerToolsBox:
    def __init__(self, app: RXviewer) -> None:
        print('RXviewerToolsBox')
        self.app = app
        
        self.contrast = RXviewerContrast(self.app)
        self.draw = RXviewerDraw(app)
        # Suppression de l'instance redondante de pathTracking
        self.path_tolerance = 10  
        self.draw_color = '#%02x%02x%02x' % (255, 0, 0)
        self.intercouche_var = tk.BooleanVar(value=False)
        ICON_DIR = Path(__file__).resolve().parents[1] / "asset/icons/toolsBox"
        self.toolsIcon = {i.stem: tk.PhotoImage(file=i) for i in ICON_DIR.glob("*.png")}

        

        self.resetImage()
    
    def resetImage(self) -> None:
        '''Initialise les modifieurs (zoom, rotation et flip)'''
        print('resetImage')
        self.raw_zoom = 1.0
        self.raw_rotation = -1
        self.raw_flip = -2
    
    def toolsBox(self) -> None:
        '''Fenêtre qui sert de toolsbox avec tous les outils'''
        print('toolsBox')
        # Détruire proprement la fenêtre toolbox si elle existe
        if hasattr(self, '_child_window_toolsBox') and self._child_window_toolsBox is not None:
            try:
                if tk.Toplevel.winfo_exists(self._child_window_toolsBox):
                    self._child_window_toolsBox.destroy()
            except Exception:
                pass
            self._child_window_toolsBox = None

        # Réinitialiser tous les widgets et états
        self._toolsBoxTools = None
        self._setting_scale = None
        self._intercouche_checkbox = None

        # Créer la nouvelle fenêtre toolbox
        self._child_window_toolsBox = tk.Toplevel(self.app.app)
        self._child_window_toolsBox.title(self.app.lang['tools_box'])
        self._child_window_toolsBox.transient(self.app.app)
        self._child_window_toolsBox.geometry(f'+{self.app.app.winfo_x()}+{self.app.app.winfo_y()+55}')

        # Recréer tous les widgets et boutons
        tk.Label(self._child_window_toolsBox, text=self.app.lang['tools'] + ' :').pack(anchor='nw', padx=5, pady=(2, 0))
        self._toolsBoxTools = tk.Frame(self._child_window_toolsBox, borderwidth=2, relief='sunken', bg='white', border=0.5)
        self._toolsBoxTools.pack(padx=5, pady=(0, 5))

        # Création des boutons et widgets comme dans la version de base
        tk.Label(self._child_window_toolsBox, text=self.app.lang['tools'] + ' :').pack(anchor='nw', padx=5, pady=(2, 0))
        self._toolsBoxTools = tk.Frame(self._child_window_toolsBox, borderwidth=2, relief='sunken', bg='white', border=0.5)
        self._toolsBoxTools.pack(padx=5, pady=(0, 5))

        tk.Button(self._toolsBoxTools, command=self.draw.undo, image=self.toolsIcon['undo-history'], width=25, height=25).grid(row=0, column=1, padx=1, pady=1)
        tk.Button(self._toolsBoxTools, command=self.draw.redo, image=self.toolsIcon['redo-history'], width=25, height=25).grid(row=0, column=2, padx=1, pady=1)
        tk.Button(self._toolsBoxTools, command=lambda: self.toolsBox_switch('default'), text='○', font=('Arial', 6)).grid(row=0, column=0, padx=1, pady=1, sticky='nsew')
        tk.Button(self._toolsBoxTools, command=lambda: self.toolsBox_switch('move'), image=self.toolsIcon['move'], width=25, height=25).grid(row=1, column=0, padx=1, pady=1)
        tk.Button(self._toolsBoxTools, command=lambda: self.toolsBox_switch('pencil'), image=self.toolsIcon['pencil'], width=25, height=25).grid(row=1, column=1, padx=1, pady=1)
        tk.Button(self._toolsBoxTools, command=lambda: self.toolsBox_switch('fuzzySelect'), image=self.toolsIcon['fuzzy-select'], width=25, height=25).grid(row=1, column=2, padx=1, pady=1)
        tk.Button(self._toolsBoxTools, command=lambda: self.toolsBox_switch('text'), image=self.toolsIcon['text'], width=25, height=25).grid(row=1, column=3, padx=1, pady=1)
        tk.Button(self._toolsBoxTools, command=lambda: self.toolsBox_switch('bucketFill'), image=self.toolsIcon['bucket-fill'], width=25, height=25).grid(row=2, column=0, padx=1, pady=1)
        tk.Button(self._toolsBoxTools, command=lambda: self.toolsBox_switch('colorPicker'), image=self.toolsIcon['color-picker'], width=25, height=25).grid(row=2, column=1, padx=1, pady=1)
        tk.Button(self._toolsBoxTools, command=None, image=self.toolsIcon['display-filter-contrast'], width=25, height=25).grid(row=2, column=2, padx=1, pady=1)
        tk.Button(self._toolsBoxTools, command=self.toolsBox_hueSaturation, image=self.toolsIcon['hue-saturation'], width=25, height=25).grid(row=2, column=3, padx=1, pady=1)
        tk.Button(self._toolsBoxTools, command=lambda: self.toolsBox_flip(1), image=self.toolsIcon['flip-horizontal'], width=25, height=25).grid(row=3, column=0, padx=1, pady=1)
        tk.Button(self._toolsBoxTools, command=lambda: self.toolsBox_flip(0), image=self.toolsIcon['flip-vertical'], width=25, height=25).grid(row=3, column=1, padx=1, pady=1)
        tk.Button(self._toolsBoxTools, command=lambda: self.do_rotation(90), image=self.toolsIcon['rotate-right'], width=25, height=25).grid(row=3, column=3, padx=1, pady=1)
        tk.Button(self._toolsBoxTools, command=lambda: self.do_rotation(-90), image=self.toolsIcon['rotate-left'], width=25, height=25).grid(row=3, column=2, padx=1, pady=1)

        tk.Label(self._child_window_toolsBox, text=self.app.lang['color'] + ' :').pack(anchor='nw', padx=5, pady=(2, 0))
        self._toolsBoxCan_color = tk.Canvas(self._child_window_toolsBox, background=self.draw_color, width=27, height=27, relief='solid', borderwidth=1)
        self._toolsBoxCan_color.pack()
        self._toolsBoxCan_color.bind('<Button-1>', self.choose_color)

        tk.Label(self._child_window_toolsBox, text=self.app.lang['settings'] + ' :').pack(anchor='nw', padx=5, pady=(2, 0))
        toolsBoxSettings = tk.Frame(self._child_window_toolsBox, borderwidth=2, relief='sunken', bg='white', border=0.5)
        toolsBoxSettings.pack(padx=5, pady=(0, 5))
        self._setting_scale = tk.Scale(toolsBoxSettings, from_=1, to=10, orient='horizontal', length=200, width=10, bg='white', label=self.app.lang['thickness'] + ' :', command=self._settingScale)
        self._setting_scale.pack()
        # Rebind tous les outils par défaut
        self.toolsBox_switch('default')

        # Couleur
        tk.Label(self._child_window_toolsBox, text=self.app.lang['color'] + ' :').pack(anchor='nw', padx=5, pady=(2, 0))
        self._toolsBoxCan_color = tk.Canvas(self._child_window_toolsBox, background=self.draw_color, width=27, height=27, relief='solid', borderwidth=1)
        self._toolsBoxCan_color.pack()
        self._toolsBoxCan_color.bind('<Button-1>', self.choose_color)

        # Paramètres
        tk.Label(self._child_window_toolsBox, text=self.app.lang['settings'] + ' :').pack(anchor='nw', padx=5, pady=(2, 0))
        toolsBoxSettings = tk.Frame(self._child_window_toolsBox, borderwidth=2, relief='sunken', bg='white', border=0.5)
        toolsBoxSettings.pack(padx=5, pady=(0, 5))
        self._setting_scale = tk.Scale(toolsBoxSettings, from_=1, to=10, orient='horizontal', length=200, width=10, bg='white', label=self.app.lang['thickness'] + ' :', command=self._settingScale)
        self._setting_scale.pack()

        # Rebind tous les outils par défaut
        self.toolsBox_switch('default')
    
    def toolsBox_switch(self, tool: str) -> None:
        '''Gère quels outils sont utilisés'''
        if tool not in ['colorPicker', 'move', 'pencil', 'bucketFill', 'text', 'fuzzySelect', 'track', 'default']: return
        self.app.can.unbind('<Button-1>')
        self.app.can.unbind('<B1-Motion>')
        self.app.can.unbind('<ButtonRelease-1>')
        self.app.can.unbind('<Button-3>')
        self.app.can.config(cursor='left_ptr')
        # Réinitialise le relief de tous les boutons toolbox
        # Réinitialise le relief de tous les boutons toolbox
        for i in self._toolsBoxTools.winfo_children():
            i.config(relief='raised')
            i.config(state='normal')

        # Associe le bon bouton à l'outil actif
        tool_map = {
            'default': 2,
            'move': 0,
            'pencil': 1,
            'fuzzySelect': 2,
            'text': 3,
            'bucketFill': 0,
            'colorPicker': 1,
        }
        # Pour la grille, l'ordre est :
        # row 1: move(0), pencil(1), fuzzySelect(2), text(3)
        # row 2: bucketFill(0), colorPicker(1), ...
        # On utilise l'index du bouton dans la ligne correspondante
        # Mais pour la simplicité, on va retrouver le bouton par son commande
        # On va griser le bouton sélectionné
        for btn in self._toolsBoxTools.winfo_children():
            if hasattr(btn, 'cget') and btn.cget('relief') == 'sunken':
                btn.config(relief='raised')
        # Trouver le bouton actif
        if tool == 'move':
            self._toolsBoxTools.grid_slaves(row=1, column=0)[0].config(relief='sunken')
        elif tool == 'pencil':
            self._toolsBoxTools.grid_slaves(row=1, column=1)[0].config(relief='sunken')
        elif tool == 'fuzzySelect':
            self._toolsBoxTools.grid_slaves(row=1, column=2)[0].config(relief='sunken')
        elif tool == 'text':
            self._toolsBoxTools.grid_slaves(row=1, column=3)[0].config(relief='sunken')
        elif tool == 'bucketFill':
            self._toolsBoxTools.grid_slaves(row=2, column=0)[0].config(relief='sunken')
        elif tool == 'colorPicker':
            self._toolsBoxTools.grid_slaves(row=2, column=1)[0].config(relief='sunken')
        elif tool == 'default':
            self._toolsBoxTools.grid_slaves(row=0, column=0)[0].config(relief='sunken')

        # Affichage dynamique des paramètres
        # Afficher tolérance pour fuzzySelect/track, épaisseur pour pencil
        if tool in ['fuzzySelect', 'track']:
            self._setting_scale.config(label=f"{self.app.lang.get('tolerance', 'Tolérance')} : ", from_=1, to=100)
            self._setting_scale.set(self.path_tolerance)
            # Afficher la checkbox pathtracking
            if not hasattr(self, '_intercouche_checkbox') or self._intercouche_checkbox is None:
                self._intercouche_checkbox = tk.Checkbutton(
                    self._child_window_toolsBox,
                    text=self.app.lang.get("auto_path_tracking", "Path tracking automatique"),
                    variable=self.intercouche_var,
                    onvalue=True,
                    offvalue=False
                )
            self._intercouche_checkbox.pack(anchor='nw', padx=5, pady=(2, 0))
        else:
            self._setting_scale.config(label=self.app.lang['thickness'] + ' :', from_=1, to=10)
            self._setting_scale.set(3)
            # Cacher la checkbox pathtracking si elle existe
            if hasattr(self, '_intercouche_checkbox') and self._intercouche_checkbox:
                self._intercouche_checkbox.pack_forget()
        # Rebind label move si curseur de base ou mode label
        if tool in ["move", "cursor", "default"]:
            if hasattr(self.app, "rebindLabelMove"):
                self.app.rebindLabelMove()
        # Mode label (curseur croix) : bind déplacement labels
        if tool == "label":
            self.app.can.config(cursor='crosshair')
            if hasattr(self.app, "rebindLabelMove"):
                self.app.rebindLabelMove()
        
        # Cache la checkbox path tracking pour tous les outils sauf fuzzySelect et track
        if hasattr(self, '_intercouche_checkbox') and tool not in ['fuzzySelect', 'track']:
            self._intercouche_checkbox.pack_forget()
            
        if tool == 'default':
            # Curseur de base - pas d'actions spéciales
            self.app.can.config(cursor='left_ptr')
            toolActif = self._toolsBoxTools.winfo_children()[2]  # Le bouton default
        elif tool == 'colorPicker':
            self.app.can.bind('<Button-1>', self._toolsBox_colorPicker)
            self.app.can.config(cursor='target')
            toolActif = self._toolsBoxTools.winfo_children()[8]
        elif tool == 'pencil':
            self.app.can.bind('<Button-1>', self.draw.startDraw)
            self.app.can.bind('<ButtonRelease-1>', self.draw.finishDraw)
            self.app.can.bind('<B1-Motion>', self.draw.paint)
            self.app.can.config(cursor='dotbox')
            toolActif = self._toolsBoxTools.winfo_children()[4]
            self._setting_scale.config(label=self.app.lang['thickness'] + ' :', from_=1, to=10)
            self._setting_scale.set(3)
        elif tool == 'text':
            self.app.can.bind('<Button-1>', self.toolsBox_text)
            self.app.can.config(cursor='plus')
            toolActif = self._toolsBoxTools.winfo_children()[6]
        elif tool == 'move':
            self.app.can.bind("<Button-1>", self._startMove)
            self.app.can.bind("<B1-Motion>", self._doMove)
            self.app.can.config(cursor='fleur')
            toolActif = self._toolsBoxTools.winfo_children()[3]
        elif tool == 'bucketFill':
            self.app.can.bind("<Button-1>", self.draw.fill)
            toolActif = self._toolsBoxTools.winfo_children()[7]
            self.app.can.config(cursor='sizing')
            self._setting_scale.config(label=self.app.lang['tolerance'] + ' :', from_=0, to=255)
            self._setting_scale.set(10)
        elif tool == 'fuzzySelect':
            # Path tracking manuel 
            if hasattr(self.app, 'via_path_tracking'):
                self.app.can.bind("<Button-1>", self.app.via_path_tracking.pathTracking)
                if hasattr(self.app.via_path_tracking, 'on_right_click'):
                    self.app.can.bind("<Button-3>", self.app.via_path_tracking.on_right_click)
            toolActif = self._toolsBoxTools.winfo_children()[5]
            self.app.can.config(cursor='center_ptr')
            # Affiche le slider tolérance et la checkbox (seulement si elle n'existe pas déjà)
            if not hasattr(self, '_intercouche_checkbox'):
                self._intercouche_checkbox = tk.Checkbutton(
                    self._child_window_toolsBox,
                    text=self.app.lang.get("auto_path_tracking", "Path tracking automatique"),
                    variable=self.intercouche_var,
                    onvalue=True,
                    offvalue=False
                )
            self._intercouche_checkbox.pack(anchor='nw', padx=5, pady=(2, 0))
            self._setting_scale.config(label=f"{self.app.lang.get('tolerance', 'Tolérance')} : ", from_=1, to=100)
            self._setting_scale.set(self.path_tolerance)
        elif tool == 'track':
            # Path tracking automatique
            if hasattr(self.app, 'via_path_tracking'):
                self.app.can.bind("<Button-1>", self.app.via_path_tracking.pathTracking)
                if hasattr(self.app.via_path_tracking, 'on_right_click'):
                    self.app.can.bind("<Button-3>", self.app.via_path_tracking.on_right_click)
            self.app.can.config(cursor='crosshair')
            # Pas de bouton spécifique dans la grille pour track pour l'instant
            toolActif = self._toolsBoxTools.winfo_children()[5]  # Utilise le même que fuzzySelect temporairement
            # Affiche la checkbox pour le path tracking automatique aussi
            if not hasattr(self, '_intercouche_checkbox'):
                self._intercouche_checkbox = tk.Checkbutton(
                    self._child_window_toolsBox,
                    text=self.app.lang.get("auto_path_tracking", "Path tracking automatique"),
                    variable=self.intercouche_var,
                    onvalue=True,
                    offvalue=False
                )
            self._intercouche_checkbox.pack(anchor='nw', padx=5, pady=(2, 0))
            self._setting_scale.config(label=f"{self.app.lang.get('tolerance', 'Tolérance')} : ", from_=1, to=100)
            self._setting_scale.set(self.path_tolerance)
        

        toolActif.config(relief='sunken')
        toolActif.config(stat='disable')
    
    def _settingScale(self, event: tk.Event):
        '''Récupère la valeur de l'épaisseur ou de la tolérance'''
        label = self._setting_scale.cget("label").lower()
        
        # Vérifier si c'est la tolérance (avec faute d'orthographe possible)
        if any(word in label for word in ["tolérance", "tolerance", "tolérence", "tolerence"]):
            self.path_tolerance = self._setting_scale.get()
        else:
            self.draw.draw_line_width = self._setting_scale.get()

    def _startMove(self, event: tk.Event) -> None:
        '''Point de départ du déplacement'''
        self._temp_coords = event.x, event.y
    
    def _doMove(self, event: tk.Event) -> None:
        '''Effectue le déplacement'''
        if self.app.raw.raw and hasattr(self, '_temp_coords'):
            dx = event.x - self._temp_coords[0]
            dy = event.y - self._temp_coords[1]
            self.app.raw.raw_coords[0] += dx
            self.app.raw.raw_coords[1] += dy
            self._temp_coords = event.x, event.y
            self.app.displayImage()
    def _doMoveRight(self, event: tk.Event) -> None:
        self.app.raw.raw_coords[0]+= 10
        self.app.displayImage()
        
    def do_zoom(self, event: tk.Event) -> None:
        '''Zoom sur l'image par rapport à la souris'''
        if self.app.raw.raw:
            factor = 1.1 if event.delta > 0 else 0.9
            self.raw_zoom *= factor
            self.app.raw.raw_coords = [(self.app.raw.raw_coords[0] - event.x) * factor + event.x, (self.app.raw.raw_coords[1] - event.y) * factor + event.y]
            self.app.displayImage()
    
    def do_rotation(self, angle: int) -> None:
        '''Roatate l'image'''
        print('do_rotation')
        if self.app.raw.raw:
            rotations = [cv2.ROTATE_90_CLOCKWISE, cv2.ROTATE_180, cv2.ROTATE_90_COUNTERCLOCKWISE, -1]
            current_index = rotations.index(self.raw_rotation)
            step = 1 if angle > 0 else -1
            self.raw_rotation = rotations[(current_index + step) % len(rotations)]
            self.app.displayImage()

    def _toolsBox_colorPicker(self, event: tk.Event) -> None:
        '''Récupère les coordonnées pour pouvoir récupérer la couleur du clic'''
        print('toolsBox_colorPicker')
        if self.app.raw.raw:
            x = event.x - self.app.can.bbox('raw')[0]
            y = event.y - self.app.can.bbox('raw')[1]
            if 0 <= x < self.app.current_image_fromarray.width and 0 <= y < self.app.current_image_fromarray.height:
                self.choose_color(self.app.current_image_fromarray.getpixel((x, y)))

    def toolsBox_flip(self, flip_code: int) -> None:
        '''Flip l'image'''
        print('toolsBox_flip')
        if not self.app.raw.raw:
            return
        self.raw_flip = {-2: flip_code, 0: -2 if flip_code == 0 else -1, 1: -2 if flip_code == 1 else -1, -1: 1 if flip_code == 0 else 0}[self.raw_flip]
        self.app.displayImage()

    def toolsBox_hueSaturation(self):
        '''Ouvre l'image actuelle en brut, et l'envoie pour modifier son contraste'''
        print('toolsBox_hueSaturation')
        if self.app.raw.raw:
            self.contrast.rawContrast(cv2.cvtColor(cv2.imread(self.app.current_project / 'raw' / self.app.raw.raw[self.app.raw_id].filename), cv2.COLOR_BGR2GRAY))

    def relativeClick(self, x, y):
        '''Calcul les coordonnées par rapport à l'image initiale (sans: rotation et flip)'''
        size = self.app.raw.raw[self.app.raw_id].raw.shape[1] * self.raw_zoom, self.app.raw.raw[self.app.raw_id].raw.shape[0] * self.raw_zoom
        if self.raw_rotation == 1:
            x, y = size[0] - x, size[1] - y
        elif self.raw_rotation == 0:
            x, y = y, size[1] - x
        elif self.raw_rotation == 2:
            x, y = size[0] - y, x
        if self.raw_flip == 1 or self.raw_flip == -1:
            x = size[0] - x
        if self.raw_flip == 0 or self.raw_flip == -1:
            y = size[1] - y
        return x, y, size

    def toolsBox_text(self, event: tk.Event) -> None:
        '''Créer un marqueur'''
        print('toolsBox_text')
        if self.app.raw.raw:
            self.app.labels_canvas.config(width=225)
            x, y, size = self.relativeClick((event.x - self.app.raw.raw_coords[0]), (event.y - self.app.raw.raw_coords[1]))
            x = x / size[0]
            y = y / size[1]
            uuid = self.app.project_file['label_id']
            self.app.project_file['labels'][str(uuid)] = {"name": f'Marker_{uuid}', "coords": [x, y], "color": self.draw_color}
            self.app.project_file['label_id'] += 1
            self.app.labels.newLabel(x, y, uuid, f'Marker_{uuid}', self.draw_color, self.app.labels_frame)
    
    def choose_color(self, event: tk.Event | tuple):
        '''Changement de la couleur de dessin, marqueur, ...'''
        print('choose_color')
        if type(event) == tk.Event:
            color = colorchooser.askcolor(title=self.app.lang['color_switch'])[1]
            if color:
                self.draw_color = color
                self._toolsBoxCan_color.config(background=color)
        else:
            if type(event) == int: event = (event, event, event)
            self.draw_color = '#%02x%02x%02x' % event
            self._toolsBoxCan_color.config(background='#%02x%02x%02x' % event)


class RXviewerDraw:
    def __init__(self, app: RXviewer) -> None:
        self.app = app
        self.draw_line_width = 1
    
    def newDraw(self):
        '''Lorsque l'on switch entre les images'''
        self._draw_image = Image.new("RGBA", (self.app.raw.raw[self.app.raw_id].raw.shape[1], self.app.raw.raw[self.app.raw_id].raw.shape[0]), (0, 0, 0, 0))
        self._drawing_image = ImageDraw.Draw(self._draw_image)
        self._modif = False
        self._resetHistory()
    
    def _resetHistory(self) -> None:
        '''Historique pour le undo et le redo'''
        self._history = [(self.app.raw.raw[self.app.raw_id].raw.copy(), self.app.raw.raw[self.app.raw_id].draw.copy(), self._draw_image.copy())]
        self._history_undo = []

    def startDraw(self, event: tk.Event):
        '''Point de départ du dessin'''
        self._draw_current_line = event.x, event.y
        self._draw_current_line_relative = [int(i / self.app.toolsBox.raw_zoom) for i in self.app.toolsBox.relativeClick(event.x - self.app.raw.raw_coords[0], event.y - self.app.raw.raw_coords[1])[:2]]
    
    def fill(self, event: tk.Event) -> None:
        '''Remplissage'''
        if not self.app.raw.raw:
            return
        x, y = self.app.toolsBox.relativeClick(event.x - self.app.raw.raw_coords[0], event.y - self.app.raw.raw_coords[1])[:2]
        x, y = int(x / self.app.toolsBox.raw_zoom), int(y / self.app.toolsBox.raw_zoom)
        if 0 < x < self.app.raw.raw[self.app.raw_id].raw.shape[1] and 0 < y < self.app.raw.raw[self.app.raw_id].raw.shape[0]:
            mask = np.zeros((self.app.raw.raw[self.app.raw_id].raw.shape[0] + 2, self.app.raw.raw[self.app.raw_id].raw.shape[1] + 2), np.uint8)
            cv2.floodFill(self.app.raw.raw[self.app.raw_id].raw, mask, (x, y), 
                        tuple(int(self.app.toolsBox.draw_color.lstrip('#')[i:i+2], 16) for i in (0, 2, 4)), (self.draw_line_width,)*3, (self.draw_line_width,)*3, cv2.FLOODFILL_FIXED_RANGE)
            self._history.append((self.app.raw.raw[self.app.raw_id].raw.copy(), self.app.raw.raw[self.app.raw_id].draw.copy(), self._draw_image.copy()))
            self.app.displayImage()

    def paint(self, event: tk.Event):
        '''Dessin en utilisant des traits'''
        if not self.app.raw.raw:
            return
        x1, y1 = self._draw_current_line
        x1_, y1_ = self._draw_current_line_relative
        self._draw_current_line = event.x, event.y
        self._draw_current_line_relative = [int(i / self.app.toolsBox.raw_zoom) for i in self.app.toolsBox.relativeClick(event.x - self.app.raw.raw_coords[0], event.y - self.app.raw.raw_coords[1])[:2]]
        if 0 < self._draw_current_line_relative[0] < self.app.raw.raw[self.app.raw_id].raw.shape[1] and 0 < self._draw_current_line_relative[1] < self.app.raw.raw[self.app.raw_id].raw.shape[0]:
            self.app.can.create_line(x1, y1, self._draw_current_line[0], self._draw_current_line[1], fill=self.app.toolsBox.draw_color, width=self.draw_line_width*self.app.toolsBox.raw_zoom, tags=['line', 'can'])
            self._drawing_image.line((x1_, y1_, self._draw_current_line_relative[0], self._draw_current_line_relative[1]), 
                                fill=self.app.toolsBox.draw_color, width=self.draw_line_width)

    def undo(self, event: tk.Event | None = None) -> None:
        '''Restaure l'historique'''
        if len(self._history) > 1:
            self._history_undo.append(self._history.pop())
            self._do()

    def redo(self, event: tk.Event | None = None) -> None:
        '''Redo l'action annulée'''
        if self._history_undo:
            self._history.append(self._history_undo.pop())
            self._do()
    
    def _do(self) -> None:
        '''Restaure la bonne image après un undo ou redo'''
        self.app.raw.raw[self.app.raw_id].draw = self._history[-1][1].copy()
        self.app.raw.raw[self.app.raw_id].raw = self._history[-1][0].copy()
        self._draw_image = self._history[-1][2].copy()
        self._drawing_image = ImageDraw.Draw(self._draw_image)
        self.app.displayImage()
    
    def imageOverlay(self, raw, rgba=False, raw2=None):
        '''Fusionne deux images ensemble'''
        if type(raw2) == type(None):
            raw2 = np.array(self._draw_image)
        b_b, g_b, r_b, alpha_b = cv2.split(raw2)
        if not rgba:
            b_a, g_a, r_a = cv2.split(raw)
        else:
            b_a, g_a, r_a, alpha_a = cv2.split(raw)
            alpha_a = alpha_a / 255.0
        alpha_b = alpha_b / 255.0
        combined = (alpha_b * b_b + (1 - alpha_b) * b_a).astype(np.uint8), (alpha_b * g_b + (1 - alpha_b) * g_a).astype(np.uint8), (alpha_b * r_b + (1 - alpha_b) * r_a).astype(np.uint8)
        if rgba:
            combined += ((alpha_b * 255 + (1 - alpha_b) * alpha_a * 255).astype(np.uint8),)
        return cv2.merge(combined)

    def save(self) -> None:
        '''Sauvegarde s'il y a eu des dessins'''
        if self._modif:
            self.app.raw.raw[self.app.raw_id].draw = self.imageOverlay(self.app.raw.raw[self.app.raw_id].draw, True)
            self.app.raw.raw[self.app.raw_id].raw = self.imageOverlay(self.app.raw.raw[self.app.raw_id].raw)

    def finishDraw(self, event: tk.Event | None = None) -> None:
        '''Lorsqu'un trait est terminé'''
        if not self.app.raw.raw:
            return
        self._modif = True
        self.save()
        self._history_undo.clear()
        self._history.append((self.app.raw.raw[self.app.raw_id].raw.copy(), self.app.raw.raw[self.app.raw_id].draw.copy(), self._draw_image.copy()))


class RXviewerContrast:
    def __init__(self, app: RXviewer) -> None:
        self.app = app

    def rawContrast(self, raw: cv2.typing.MatLike) -> None:
        '''Fenêtre pour la preview et modification du contraste'''
        print('rawContrast')
        if "_child_window_rawContrast" in self.__dict__:
            if self._child_window_rawContrast is not None and tk.Toplevel.winfo_exists(self._child_window_rawContrast):
                return
        self._raw = raw
        self._min = int(np.min(self._raw))
        self._max = int(np.max(self._raw))

        self._child_window_rawContrast = tk.Toplevel(self.app.app)
        self._child_window_rawContrast.title(self.app.lang['change_contrast'])
        self._child_window_rawContrast.transient(self.app.app)
        self._child_window_rawContrast.grab_set()
        self._child_window_rawContrast.focus()
        self._child_window_rawContrast.geometry("700x600")

        self._zoom = 1.0
        self._offset = [0, 0]
        self._drag = None

        self._can = tk.Canvas(self._child_window_rawContrast, width=650, height=450, bg="black")
        self._can.pack(fill="both", expand=False)
        self._can.bind("<Button-1>", self._startMove)
        self._can.bind("<B1-Motion>", self._doMove)
        self._can.bind("<MouseWheel>", self._zoomImage)
        self._can.bind("<Button-4>", self._zoomImage)  
        self._can.bind("<Button-5>", self._zoomImage)  

        self._rawContrastScale = tk.Frame(self._child_window_rawContrast)
        self._rawContrastScale.pack(fill="x", side="bottom", pady=8)

        self._min_var = tk.IntVar(value=self._min)
        self._max_var = tk.IntVar(value=self._max)
        min_scale = tk.Scale(self._rawContrastScale, from_=0, to=self._max, orient='horizontal', length=200, width=10, label='Min :', variable=self._min_var, command=self._rawContrastPreview)
        max_scale = tk.Scale(self._rawContrastScale, from_=self._min, to=255, orient='horizontal', length=200, width=10, label='Max :', variable=self._max_var, command=self._rawContrastPreview)
        min_scale.pack(side='left', padx=5)
        max_scale.pack(side='left', padx=5)

        tk.Button(self._rawContrastScale, text="Appliquer à cette image", command=self._apply_one).pack(side='left', padx=10)
        tk.Button(self._rawContrastScale, text=self.app.lang['apply_all'], command=self._apply_all).pack(side='left', padx=10)

        self._rawContrastPreview()

    def _startMove(self, event: tk.Event) -> None:
        self._drag = (event.x, event.y)

    def _doMove(self, event: tk.Event) -> None:
        if self._drag:
            dx = event.x - self._drag[0]
            dy = event.y - self._drag[1]
            self._offset[0] += dx
            self._offset[1] += dy
            self._drag = (event.x, event.y)
            self._rawContrastPreview()

    def _zoomImage(self, event: tk.Event) -> None:
        if hasattr(event, 'delta'):
            factor = 1.1 if event.delta > 0 else 0.9
        else:
            factor = 1.1 if event.num == 4 else 0.9
        old_zoom = self._zoom
        self._zoom *= factor
        mouse_x, mouse_y = event.x, event.y
        self._offset[0] = int(mouse_x - (mouse_x - self._offset[0]) * (self._zoom / old_zoom))
        self._offset[1] = int(mouse_y - (mouse_y - self._offset[1]) * (self._zoom / old_zoom))
        self._rawContrastPreview()

    def _apply_one(self):
        '''Applique le contraste uniquement à l'image courante'''
        print('apply_one')
        new_min, new_max = self._min_var.get(), self._max_var.get()
        self._child_window_rawContrast.destroy()
        self.app.raw.saveEditRawOne(new_min, new_max)

    def _apply_all(self):
        '''Applique le contraste à toutes les images'''
        print('apply_all')
        new_min, new_max = self._min_var.get(), self._max_var.get()
        self._child_window_rawContrast.destroy()
        self.app.raw.saveEditRaws(new_min, new_max)

    def _rawContrastPreview(self, event: tk.Event | None = None) -> None:
        '''Update de l'image de preview'''
        min_val = self._min_var.get()
        max_val = self._max_var.get()
        img = self.editContrast(self._raw, min_val, max_val)
        h, w = img.shape
        zoomed = cv2.resize(img, (int(w * self._zoom), int(h * self._zoom)), interpolation=cv2.INTER_LINEAR)
        canvas_w = int(self._can['width'])
        canvas_h = int(self._can['height'])
        display = np.zeros((canvas_h, canvas_w), dtype=np.uint8)
        x0 = self._offset[0]
        y0 = self._offset[1]
        x1 = x0 + zoomed.shape[1]
        y1 = y0 + zoomed.shape[0]
        x0_img = max(0, -x0)
        y0_img = max(0, -y0)
        x0_can = max(0, x0)
        y0_can = max(0, y0)
        x1_can = min(canvas_w, x1)
        y1_can = min(canvas_h, y1)
        x1_img = x0_img + (x1_can - x0_can)
        y1_img = y0_img + (y1_can - y0_can)
        if x1_can > x0_can and y1_can > y0_can:
            display[y0_can:y1_can, x0_can:x1_can] = zoomed[y0_img:y1_img, x0_img:x1_img]
        self.curent_image = ImageTk.PhotoImage(Image.fromarray(display))
        self._can.delete('all')
        self._can.create_image(0, 0, anchor=tk.NW, image=self.curent_image, tags='raw')

    def editContrast(self, raw: cv2.typing.MatLike, new_min: int, new_max: int):
        '''Modification du contraste de l'image'''
        old_min = np.min(raw)
        old_max = np.max(raw)
        # Si les valeurs sont identiques, retourne l'image d'origine
        if new_min == old_min and new_max == old_max:
            return raw.astype(np.uint8)
        if old_max == old_min:
            return np.clip(raw, new_min, new_max).astype(np.uint8)
        return np.clip((raw - old_min) * ((new_max - new_min) / (old_max - old_min)) + new_min, new_min, new_max).astype(np.uint8)
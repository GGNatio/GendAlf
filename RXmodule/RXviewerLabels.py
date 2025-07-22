import tkinter as tk

class RXviewer: ...


class RXviewerLabel:
    def __init__(self, app, frame: tk.Frame, coords: list, uid: str, name: str, color: str) -> None:
        self.visible = 1
        self.app = app
        self.frame = frame
        self.coords = coords
        self.id = uid
        self.name = name
        self.color = color
        self.setup()

    def __str__(self) -> str:
        return self.name

    def setup(self) -> None:
        self.label_checkBox = tk.IntVar()
        self.label_checkBox.set(1)
        tk.Checkbutton(self.frame, command=self.onoff, onvalue=1, offvalue=0, variable=self.label_checkBox, bg='white').pack(side='left', padx=(2,0))
        self.label_name = tk.Entry(self.frame, bg='white', font=("Helvetica", 13), relief='flat', borderwidth=2, width=18)
        self.label_name.pack(side='left', fill='x', expand=True)
        tk.Button(self.frame, text='X', width=2, bg='white', command=self.remove).pack(side='left')
        self.label_name.insert(0, self.name)
        self.label_name.bind('<KeyRelease>', self.editName)

    def remove(self) -> None:
        '''Supprime le marqueur du projet'''
        self.delete()
        if hasattr(self.app, "project_file") and 'labels' in self.app.project_file and str(self.id) in self.app.project_file['labels']:
            del self.app.project_file['labels'][str(self.id)]
        if self in self.app.labels.markers:
            self.app.labels.markers.remove(self)
        
        # Masque la bande blanche s'il n'y a plus de marqueurs
        if len(self.app.labels.markers) == 0:
            self.app.labels._hide_labels_panel()
        
        self.app.displayImage()

    def delete(self) -> None:
        if self.frame and self.frame.winfo_exists():
            self.frame.destroy()

    def onoff(self) -> None:
        '''Rends ou non visible le marqueur'''
        self.visible = self.label_checkBox.get()
        if not self.visible:
            self.app.can.delete(f'label_{self.id}')
        else:
            self.place()

    def editName(self, event=None) -> None:
        self.name = self.label_name.get()
        if hasattr(self.app.labels, "labels") and str(self.id) in self.app.labels.labels:
            self.app.labels.labels[str(self.id)]['name'] = self.name
        self.app.can.itemconfig(f'label_{self.id}_text', text=self.name)

    def placeMarker(self, size: tuple, raw_coords: tuple) -> None:
        self.temp_coords = [size[0] * self.coords[0], size[1] * self.coords[1]]
        if getattr(self.app.toolsBox, "raw_flip", -2) == 1 or getattr(self.app.toolsBox, "raw_flip", -2) == -1:
            self.temp_coords[0] = size[0] - self.temp_coords[0]
        if getattr(self.app.toolsBox, "raw_flip", -2) == 0 or getattr(self.app.toolsBox, "raw_flip", -2) == -1:
            self.temp_coords[1] = size[1] - self.temp_coords[1]
        rot = getattr(self.app.toolsBox, "raw_rotation", -1)
        if rot == 1:  # 180°
            self.temp_coords[0], self.temp_coords[1] = size[0] - self.temp_coords[0], size[1] - self.temp_coords[1]
        elif rot == 0:  # 90°
            self.temp_coords[0], self.temp_coords[1] = (size[1] - self.temp_coords[1]) * size[0]/size[1], (self.temp_coords[0]) * size[1]/size[0]
        elif rot == 2:  # -90°
            self.temp_coords[0], self.temp_coords[1] = (self.temp_coords[1]) * size[0]/size[1], (size[0] - self.temp_coords[0]) * size[1]/size[0]
        self.temp_coords = [raw_coords[0] + self.temp_coords[0],  raw_coords[1] + self.temp_coords[1]]
        if self.visible:
            self.app.can.delete(f'label_{self.id}')
            self.place()

    def place(self) -> None:
        self.app.can.create_oval(self.temp_coords[0] - 5, self.temp_coords[1] - 5, self.temp_coords[0] + 5, self.temp_coords[1] + 5,
                                tags=['can', 'label', f'label_{self.id}', 'label_marker'], fill=self.color)
        self.app.can.create_text(self.temp_coords[0], self.temp_coords[1] - 15, 
                                text=self.name, anchor='center', justify='center', tags=['can', 'label', f'label_{self.id}', 'label_text', f'label_{self.id}_text'], fill=self.color)

class RXviewerLabels:
    def __init__(self, app) -> None:
        self.app = app
        self.markers = []
        self.labels = {}
        self.frame = None
        self.parent_frame = None  # Référence au parent_frame
        self.app.can.bind('<Control-Shift-Button-1>', self._start_move_marker)
        self.app.can.bind('<B1-Motion>', self._move_marker)
        self.app.can.bind('<ButtonRelease-1>', self._end_move_marker)

    def _start_move_marker(self, event):
        x, y = event.x, event.y
        found = None
        for marker in self.markers:
            mx, my = marker.temp_coords if hasattr(marker, 'temp_coords') else (0, 0)
            if abs(mx - x) < 10 and abs(my - y) < 10:
                found = marker
                break
        if found:
            self._moving_marker = found
            self._moving_marker_offset = (0, 0)
        else:
            self._moving_marker = None

    def _move_marker(self, event):
        if hasattr(self, '_moving_marker') and self._moving_marker:
            can = self.app.can
            raw_coords = self.app.raw.raw_coords
            zoom = getattr(self.app.toolsBox, "raw_zoom", 1.0)
            flip = getattr(self.app.toolsBox, "raw_flip", -2)
            rot = getattr(self.app.toolsBox, "raw_rotation", -1)
            img = self.app.raw.raw[self.app.raw_id].raw
            h, w = img.shape[:2]
            size = (int(w * zoom), int(h * zoom))
            px = event.x - raw_coords[0]
            py = event.y - raw_coords[1]
            if flip == 1 or flip == -1:
                px = size[0] - px
            if flip == 0 or flip == -1:
                py = size[1] - py
            if rot == 1:
                px, py = size[0] - px, size[1] - py
            elif rot == 0:
                px, py = py, size[0] - px
            elif rot == 2:
                px, py = size[1] - py, px
            norm_x = px / size[0]
            norm_y = py / size[1]
            self._moving_marker.coords = [norm_x, norm_y]
            self.app.displayImage()

    def _end_move_marker(self, event):
        if hasattr(self, '_moving_marker'):
            self._moving_marker = None

    def _hide_labels_panel(self):
        '''Masque la bande blanche des labels'''
        if self.frame and self.frame.winfo_exists():
            self.frame.destroy()
            self.frame = None
        # Utilise la méthode de la classe principale pour masquer la bande blanche
        if hasattr(self.app, 'hideLabelsPanel'):
            self.app.hideLabelsPanel()
        elif self.parent_frame and self.parent_frame.winfo_ismapped():
            self.parent_frame.pack_forget()

    def addLabels(self, labels: dict) -> None:
        '''Ajoute une liste de marqueurs'''
        self.labels = labels

    def setupLabels(self, parent_frame: tk.Frame) -> None:
        '''Supprime les marqueurs actuels et affiche les nouveaux'''
        self.parent_frame = parent_frame  # Stocke la référence
        # Supprime tous les marqueurs existants
        while self.markers:
            marker = self.markers.pop()
            if hasattr(marker, "frame") and marker.frame.winfo_exists():
                marker.frame.destroy()
        # Détruit le frame parent s'il existe
        if self.frame and self.frame.winfo_exists():
            self.frame.destroy()
            self.frame = None
        # Si plus de labels, masque le parent_frame (bande blanche)
        if not self.labels or len(self.labels) == 0:
            if hasattr(self.app, 'hideLabelsPanel'):
                self.app.hideLabelsPanel()
            elif parent_frame.winfo_ismapped():
                parent_frame.pack_forget()
            return
        # Sinon, affiche la bande blanche et les labels
        if hasattr(self.app, 'showLabelsPanel'):
            self.app.showLabelsPanel()
        if not parent_frame.winfo_ismapped():
            parent_frame.pack(side='right', fill='y')
        self.frame = tk.Frame(parent_frame, borderwidth=2)
        self.frame.pack(side='right', fill='y')
        for key in self.labels.keys():
            new_frame = tk.Frame(self.frame, borderwidth=2)
            new_frame.pack(pady=2)
            label = self.labels[key]
            self.markers.append(RXviewerLabel(self.app, new_frame, label['coords'], key, label['name'], label['color']))

    def newLabel(self, x: float, y: float, uuid: str, name: str, color: str, parent_frame: tk.Frame):
        self.parent_frame = parent_frame  # Stocke la référence
        # Réaffiche le conteneur principal si nécessaire
        if hasattr(self.app, 'showLabelsPanel'):
            self.app.showLabelsPanel()
        # Réaffiche le parent_frame si besoin
        if not parent_frame.winfo_ismapped():
            parent_frame.pack(side='right', fill='y')
        if not self.frame or not self.frame.winfo_exists():
            self.frame = tk.Frame(parent_frame, borderwidth=2)
            self.frame.pack(side='right', fill='y')
        new_frame = tk.Frame(self.frame, borderwidth=2)
        new_frame.pack(pady=2)
        self.markers.append(RXviewerLabel(self.app, new_frame, [x, y], uuid, name, color))
        self.app.displayImage()

    def moveLabels(self, size: tuple, raw_coords: tuple):
        for i in self.markers:
            i.placeMarker(size, raw_coords)
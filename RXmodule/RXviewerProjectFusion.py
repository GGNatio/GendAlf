import tkinter as tk
from tkinter import messagebox, filedialog
from PIL import Image, ImageTk
from pathlib import Path
import threading
import cv2
import numpy as np
from skimage.metrics import structural_similarity as ssim
from RXmodule.RXviewerToolsBox import RXviewerToolsBox
class RXviewer: ...


class RXviewerProjectFusion:
    def __init__(self, app: RXviewer) -> None:
        self.app = app
        self.fusion_path = None  # <-- Ajoute cette ligne
        self.colors = (
            "red", "green", "blue", "yellow", "orange", "purple", "cyan", "magenta",
            "lime", "pink", "teal", "lavender", "brown", "beige", "maroon", "navy",
            "gold", "coral", "turquoise", "indigo", "violet", "salmon", "olive", "chocolate"
        )
        self.raw_way = tk.IntVar(value=0)
        # Pour le crop interactif
        self._crop_vars = {}

    def window(self):
        self.window_projectFuseion = tk.Toplevel(self.app.app)
        self.window_projectFuseion.geometry('1200x750')
        self.window_projectFuseion.title(self.app.lang['merge_project'])
        self.window_projectFuseion.grab_set()
        self.window_projectFuseion.focus()
        tk.Label(self.window_projectFuseion, text=self.app.lang['merge_project'], font=("Helvetica", 15, "bold")).pack(anchor='nw', padx=1, pady=1)
        self.frame = tk.Frame(self.window_projectFuseion, borderwidth=1, relief='solid')
        self.frame.pack(fill='both', expand=True, side='left', padx=1, pady=1)
        self.window_projectFuseion.protocol("WM_DELETE_WINDOW", self.app.fusionProjectClose)
        self.phase1()

    def phase1(self):
        frame_label = tk.Frame(self.frame)
        frame_label.pack(side='top', padx=5, pady=5)
        frame_project_name = tk.Frame(frame_label)
        frame_project_name.pack(side="top", anchor='nw')
        tk.Label(frame_project_name, text=self.app.lang["new_project_name"], font=('Helvetica', 10, 'bold')).pack(side='left', anchor='w')
        self.project_name = tk.Entry(frame_project_name, width=30)
        self.project_name.insert(0, self.app.lang['entry_new_project_name'])
        self.project_name.pack(side='left')
        self.project_name.bind('<FocusIn>', lambda event: self._p1_onEntry(self.project_name, 'entry_new_project_name'))
        self.project_name.bind('<FocusOut>', lambda event: self._p1_offEntry(self.project_name, 'entry_new_project_name'))

        frame_folder = tk.Frame(frame_label)
        frame_folder.pack(anchor='w')
        tk.Button(frame_folder, text=self.app.lang['edit_registration_file'], command=self.p1_changeSaveFolder).pack(side='bottom')
        tk.Label(frame_folder, text=f"{self.app.lang['registration_file']} :", font=('Helvetica', 10, 'bold')).pack(side='left')
        self.savefolder = Path.home() / "Documents/RXViwer/project/"
        self.folder_label = tk.Label(frame_folder, text=self.savefolder)
        self.folder_label.pack(side='left', fill='x')

        frame_radio = tk.Frame(frame_label)
        frame_radio.pack(anchor='w', pady=(10,0))
        tk.Label(frame_radio, text=self.app.lang["original_modified"] + ' 1:', font=('Helvetica', 10, 'bold')).pack(anchor='w', side='left')
        project1_raw1 = tk.StringVar()
        project1_raw1.set('raw')
        tk.Radiobutton(frame_radio, text=self.app.lang["original"], variable=project1_raw1, value='raw', command=None).pack(side='left')
        tk.Radiobutton(frame_radio, text=self.app.lang["modified"], variable=project1_raw1, value='edit', command=None).pack(side='left')

        frame_radio = tk.Frame(frame_label)
        frame_radio.pack(anchor='w')
        tk.Label(frame_radio, text=self.app.lang["original_modified"] + ' 2:', font=('Helvetica', 10, 'bold')).pack(anchor='w', side='left')
        project1_raw2 = tk.StringVar()
        project1_raw2.set('raw')
        tk.Radiobutton(frame_radio, text=self.app.lang["original"], variable=project1_raw2, value='raw', command=None).pack(side='left')
        tk.Radiobutton(frame_radio, text=self.app.lang["modified"], variable=project1_raw2, value='edit', command=None).pack(side='left')

        frame_way = tk.Frame(frame_label)
        frame_way.pack(anchor="w", padx=5, pady=5)
        tk.Label(frame_way, text=self.app.lang.get("choose_way_of_fusion", "Orientation de la fusion :")).pack(side="left")
        tk.Radiobutton(frame_way, text=self.app.lang.get("vertical", "Verticale"), variable=self.raw_way, value=0).pack(side="left", padx=5)
        tk.Radiobutton(frame_way, text=self.app.lang.get("horizontal", "Horizontale"), variable=self.raw_way, value=1).pack(side="left", padx=5)

        frame_cans = tk.Frame(self.frame)
        frame_cans.pack(side='top', fill='x', expand=True, anchor='s')
        frame_can1 = tk.Frame(frame_cans)
        frame_can1.pack(side='left', padx=20)
        tk.Button(frame_can1, text=self.app.lang['open_project'], command=lambda: self.p1_openProject(1, project1_raw1.get())).pack(side='bottom', anchor='center')
        self.index1_label = tk.Label(frame_can1, text='0/0')
        self.index1_label.pack(side='bottom', anchor='ne')
        tk.Label(frame_can1, text=self.app.lang['project'] + ' 1').pack()
        self._p1_button(frame_can1, 'left')
        self.can1 = tk.Canvas(frame_can1, width=400, height=400, bg='white', highlightthickness=1, highlightbackground='black')
        self.can1.pack()
        self.can1.bind("<MouseWheel>", lambda event: self.p1_wheelNext(1, event))

        frame_can2 = tk.Frame(frame_cans)
        frame_can2.pack(side='right', padx=20)
        tk.Button(frame_can2, text=self.app.lang['open_project'], command=lambda: self.p1_openProject(2, project1_raw2.get())).pack(side='bottom', anchor='center')
        self.index2_label = tk.Label(frame_can2, text='0/0')
        self.index2_label.pack(side='bottom', anchor='nw')
        tk.Label(frame_can2, text=self.app.lang['project'] + ' 2').pack()
        self._p1_button(frame_can2, 'right')
        self.can2 = tk.Canvas(frame_can2, width=400, height=400, bg='white', highlightthickness=1, highlightbackground='black')
        self.can2.pack(side="left")
        self.can2.bind("<MouseWheel>", lambda event: self.p1_wheelNext(2, event))

        tk.Button(frame_cans, text='← ' + self.app.lang['link'] + ' →', command=self.p1_link, font=("Helvetica", 12)).pack(anchor='center', pady=200)
        tk.Button(self.frame, text=self.app.lang['create_new_projet'], command=self.phase2).pack(pady=(0, 5))

    def _p1_button(self, frame: tk.Frame, side: str):
        frame_b = tk.Frame(frame)
        frame_b.pack(side=side)
        tk.Button(frame_b, text=self.app.lang['crop_button'], command=lambda: self._start_crop(side)).grid(padx=1, pady=1)

    # ----------- FENÊTRE DE CROP INTERACTIVE -----------
    def _start_crop(self, side):
        raws = getattr(self, f'raws1' if side == 'left' else 'raws2', None)
        raw_id = getattr(self, f'raws1_id' if side == 'left' else 'raws2_id', 0)
        if not raws or not len(raws):
            project_num = 1 if side == 'left' else 2
            messagebox.showwarning("⚠️", self.app.lang['no_image_to_crop'].format(project_num=project_num))
            return

        crop_win = tk.Toplevel(self.app.app)
        crop_side = self.app.lang.get('left', 'left') if side == 'left' else self.app.lang.get('right', 'right')
        crop_win.title(self.app.lang['crop_window_title'].format(side=crop_side))
        crop_win.geometry("900x900")
        crop_win.transient(self.app.app)
        crop_win.grab_set()

        crop_vars = {
            "zoom": 1.0,
            "offset": [0, 0],
            "drag": None,
            "box": None,
            "box_start": None,
            "side": side,
            "raws": raws,
            "raw_id": raw_id,
            "canvas": None,
            "img_disp": None,
            "img": None,
        }
        self._crop_vars = crop_vars

        crop_canvas = tk.Canvas(crop_win, bg='white', width=800, height=800)
        crop_canvas.pack(fill='both', expand=True)
        crop_vars["canvas"] = crop_canvas

        crop_vars["img"] = crop_vars["raws"][crop_vars["raw_id"]].copy()
        self._draw_crop_image()

        # Clic gauche = cropping, clic droit = déplacement
        crop_canvas.bind("<ButtonPress-1>", self._crop_start_box)
        crop_canvas.bind("<B1-Motion>", self._crop_draw_box)
        crop_canvas.bind("<ButtonRelease-1>", self._crop_end_box)
        crop_canvas.bind("<ButtonPress-3>", self._crop_start_drag)
        crop_canvas.bind("<B3-Motion>", self._crop_drag_move)
        crop_canvas.bind("<ButtonRelease-3>", self._crop_end_drag)
        crop_canvas.bind("<MouseWheel>", self._crop_zoom_event)
        crop_canvas.bind("<Button-4>", self._crop_zoom_event)  # Linux
        crop_canvas.bind("<Button-5>", self._crop_zoom_event)  # Linux

        nav_frame = tk.Frame(crop_win)
        nav_frame.pack()
        tk.Button(nav_frame, text="<<", command=lambda: self._crop_navigate(-crop_vars["raw_id"])).pack(side='left')
        tk.Button(nav_frame, text="<", command=lambda: self._crop_navigate(-1)).pack(side='left')
        tk.Button(nav_frame, text=">", command=lambda: self._crop_navigate(1)).pack(side='left')
        tk.Button(nav_frame, text=">>", command=lambda: self._crop_navigate(len(crop_vars["raws"])-1-crop_vars["raw_id"])).pack(side='left')
        tk.Label(nav_frame, textvariable=tk.StringVar(value=f"{crop_vars['raw_id']+1}/{len(crop_vars['raws'])}")).pack(side='left')

        tk.Button(crop_win, text=self.app.lang['apply_crop_all_button'], command=lambda: self._apply_crop_all(crop_win)).pack(pady=10)

    def _draw_crop_image(self):
        crop_vars = self._crop_vars
        img = crop_vars["img"]
        zoom = crop_vars["zoom"]
        offset = crop_vars["offset"]
        h, w = img.shape[:2]
        disp_img = cv2.resize(img, (int(w*zoom), int(h*zoom)), interpolation=cv2.INTER_AREA)
        disp_img = ImageTk.PhotoImage(Image.fromarray(disp_img))
        crop_vars["img_disp"] = disp_img
        crop_vars["canvas"].delete("all")
        crop_vars["canvas"].create_image(offset[0], offset[1], anchor='nw', image=disp_img, tags="img")
        if crop_vars["box"]:
            x0, y0, x1, y1 = crop_vars["box"]
            crop_vars["canvas"].create_rectangle(x0, y0, x1, y1, outline='red', width=2, tags="crop_rect")

    # Clic gauche = cropping
    def _crop_start_box(self, event):
        self._crop_vars["box_start"] = (event.x, event.y)
        self._crop_vars["box"] = (event.x, event.y, event.x, event.y)
        self._draw_crop_image()

    def _crop_draw_box(self, event):
        x0, y0 = self._crop_vars["box_start"]
        x1, y1 = event.x, event.y
        self._crop_vars["box"] = (x0, y0, x1, y1)
        self._draw_crop_image()

    def _crop_end_box(self, event):
        x0, y0 = self._crop_vars["box_start"]
        x1, y1 = event.x, event.y
        self._crop_vars["box"] = (min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1))
        self._draw_crop_image()
        # Confirmation
        if messagebox.askyesno(self.app.lang['crop_confirm_title'], self.app.lang['crop_confirm_msg']):
            self._apply_crop_remove_zone()
    def _apply_crop_remove_zone(self):
        crop_vars = self._crop_vars
        x0, y0, x1, y1 = [int(v) for v in crop_vars["box"]]
        zoom = crop_vars["zoom"]
        offset = crop_vars["offset"]
        for i in range(len(crop_vars["raws"])):
            img = crop_vars["raws"][i]
            h, w = img.shape[:2]
            # Calcul des coordonnées dans l'image, tronquées aux bords
            x0_img = max(0, min(w, int((min(x0, x1) - offset[0]) / zoom)))
            x1_img = max(0, min(w, int((max(x0, x1) - offset[0]) / zoom)))
            y0_img = max(0, min(h, int((min(y0, y1) - offset[1]) / zoom)))
            y1_img = max(0, min(h, int((max(y0, y1) - offset[1]) / zoom)))
            # On retire la zone (recollage si toute la largeur ou hauteur, sinon on remplit en noir)
            if x0_img == 0 and x1_img == w:
                img_new = np.concatenate([img[:y0_img, :], img[y1_img:, :]], axis=0)
            elif y0_img == 0 and y1_img == h:
                img_new = np.concatenate([img[:, :x0_img], img[:, x1_img:]], axis=1)
            else:
                img_new = img.copy()
                if img.ndim == 3:
                    img_new[y0_img:y1_img, x0_img:x1_img, :] = 0
                else:
                    img_new[y0_img:y1_img, x0_img:x1_img] = 0
            crop_vars["raws"][i] = img_new

        messagebox.showinfo("✅", self.app.lang['crop_zone_removed_msg'])
        crop_vars["canvas"].master.destroy()
    # Clic droit = déplacement
    def _crop_start_drag(self, event):
        self._crop_vars["drag"] = (event.x, event.y)

    def _crop_drag_move(self, event):
        if self._crop_vars["drag"]:
            dx = event.x - self._crop_vars["drag"][0]
            dy = event.y - self._crop_vars["drag"][1]
            self._crop_vars["offset"][0] += dx
            self._crop_vars["offset"][1] += dy
            self._crop_vars["drag"] = (event.x, event.y)
            self._draw_crop_image()

    def _crop_end_drag(self, event):
        self._crop_vars["drag"] = None

    def _crop_zoom_event(self, event):
        if hasattr(event, 'delta'):
            factor = 1.1 if event.delta > 0 else 0.9
        else:
            factor = 1.1 if event.num == 4 else 0.9
        self._crop_vars["zoom"] *= factor
        self._draw_crop_image()

    def _crop_navigate(self, direction):
        crop_vars = self._crop_vars
        new_id = crop_vars["raw_id"] + direction
        if 0 <= new_id < len(crop_vars["raws"]):
            crop_vars["raw_id"] = new_id
            crop_vars["img"] = crop_vars["raws"][crop_vars["raw_id"]].copy()
            self._draw_crop_image()

    def _apply_crop_all(self, crop_win):
        crop_vars = self._crop_vars
        if not crop_vars["box"]:
            messagebox.showwarning("⚠️", self.app.lang['select_crop_zone_warning'])
            return
        x0, y0, x1, y1 = [int(v) for v in crop_vars["box"]]
        zoom = crop_vars["zoom"]
        offset = crop_vars["offset"]
        x0_img = int((x0 - offset[0]) / zoom)
        y0_img = int((y0 - offset[1]) / zoom)
        x1_img = int((x1 - offset[0]) / zoom)
        y1_img = int((y1 - offset[1]) / zoom)
        x0_img, x1_img = sorted([max(0, x0_img), max(0, x1_img)])
        y0_img, y1_img = sorted([max(0, y0_img), max(0, y1_img)])
        for i in range(len(crop_vars["raws"])):
            img = crop_vars["raws"][i]
            crop_vars["raws"][i] = img[y0_img:y1_img, x0_img:x1_img]
        crop_win.destroy()
        messagebox.showinfo("✅", self.app.lang['crop_applied_all_msg'])



    def _p1_onEntry(self, entry: tk.Entry, text: str) -> None:
        '''Retirer le texte de la zone du nom du projet lorsque l'on clic dedans'''
        if entry.get() == self.app.lang[text]:
            entry.delete(0, 'end')

    def _p1_offEntry(self, entry: tk.Entry, text: str) -> None:
        '''Remettre le texte de la zone du nom du projet lorsque l'Entry perd le focus'''
        if entry.get() == '':
            entry.insert(0, self.app.lang[text])
    
    def p1_changeSaveFolder(self) -> None:
        '''Changer l'emplacement de sauvegarde'''
        folder_selected = filedialog.askdirectory(initialdir=Path.home() / "Documents/RXViwer/project/")
        if folder_selected:
            self.savefolder = Path(folder_selected)
            self.folder_label.config(text=self.savefolder)
    
    def p1_openProject(self, project: int, raw: str) -> None:
        '''Ouvrir un projet pour l'afficher dans un des canvas'''
        path = Path(filedialog.askdirectory(initialdir=Path.home() / 'Documents/RXViwer/project/'))
        if (path / 'project.json').is_file():
            self.p1_setupRawInCan(project, self.p1_loadImages(path / raw))
        elif path == Path('.'):
            return
        else:
            messagebox.showerror(self.app.lang['err'], self.app.lang['err7'])
    
    def p1_loadImages(self, project: Path) -> list:
        '''Charge les images du projet dans la mémoire'''
        if project.is_dir():
            folders = list(project.glob('*.png'))
            if len(folders) == 0:
                messagebox.showerror(self.app.lang['err'], self.app.lang['err8'])
                return []
            raws = [None] * len(folders)  
            thread = []
            self.app.loadingBar(0)
            for i in range(len(folders)):
                thread.append(threading.Thread(target=self._p1_loadImage, args=(folders[i], raws, i)))
                thread[-1].start()
                self.app.loadingBar(int(i/len(folders) * 100))
            for i in thread:i.join()
            self.app.resetLoadingBar()
            return raws
    
    def _p1_loadImage(self, filename: Path, raws: list, index: int) -> None:
        '''Charge une image'''
        if filename.is_file():
            raws[index] =  cv2.imread(filename)
    
    def p1_setupRawInCan(self, project: int, raws: list) -> None:
        '''Setup les variables raw, raw_id, raw_rotation et raw_flip pour chaque projet'''
        if not raws:
            return
        raw_attr = f'raws{project}'
        raw_id_attr = f'raws{project}_id'
        rotation_attr = f'raw{project}_rotation'
        flip_attr = f'raw{project}_flip'
        setattr(self, raw_attr, raws)
        setattr(self, raw_id_attr, 1)
        setattr(self, rotation_attr, -1)
        setattr(self, flip_attr, -2)
        if hasattr(self, 'raws1') and hasattr(self, 'raws2'):
            self.links = LinkSystem(self.raws1, self.raws2)
            self.p1_linkPreview()
        raw = self._p1_resizeRaw(getattr(self, raw_attr)[getattr(self, raw_id_attr)], getattr(self, rotation_attr), getattr(self, flip_attr))
        self.p1_displayRaw(project, raw)
        getattr(self, f'index{project}_label').config(text=f'2/{len(raws)}')

    def p1_displayRaw(self, lr: int, raw: cv2.typing.MatLike) -> None:
        '''Affiche les images dans les canvas de preview'''
        canvas = getattr(self, f'can{lr}')
        canvas.delete('all')
        new_id = getattr(self, f'raws{lr}_id')
        if 0 == new_id or new_id ==  len(getattr(self, f'raws{lr}')) - 1:
            self.p1_displayBlankRaw(lr)
        current_raw_attr = f'current_raw{lr}'
        setattr(self, current_raw_attr, ImageTk.PhotoImage(Image.fromarray(raw)))
        canvas.create_image(200, 200, image=getattr(self, current_raw_attr), anchor='center')
        if hasattr(self, 'links'):
            color = getattr(self.links, f'l{lr}')[getattr(self, f'raws{lr}_id')]
            if color is not None:
                canvas.create_rectangle(3, 3, 397, 397, width=5, outline=self.colors[int(color)%len(self.colors)], tag='link')
    
    def p1_displayBlankRaw(self, lr: int):
        '''Affichage de l'image vide dans les canvas de preview pour la première et la dernière image'''
        canvas = getattr(self, f'can{lr}')
        canvas.create_text(200, 200, anchor='center', text=self.app.lang['blank_raw'], font=("Helvetica", 12))
        if hasattr(self, 'links'):
            color = getattr(self.links, f'l{lr}')[getattr(self, f'raws{lr}_id')]
            if color is not None:
                canvas.create_rectangle(3, 3, 397, 397, width=5, outline=self.colors[int(color)%len(self.colors)], tag='link')
    
    def _p1_resizeRaw(self, raw: cv2.typing.MatLike, rotation: int, flip: int, size: int = 400) -> None:
        '''Redimensionner le raw pour le faire rentrer dans le canvas de preview'''
        current_image = raw.copy()
        size = (size, int(size / current_image.shape[1] * current_image.shape[0])) if current_image.shape[1] > current_image.shape[0] else (int(size / current_image.shape[0] * current_image.shape[1]), size)
        current_image = cv2.resize(current_image, size)
        if flip != -2:
                current_image = cv2.flip(current_image, flip)
        if rotation != -1:
            current_image = cv2.rotate(current_image, rotation)
        return current_image

    def _p1_navigRaw(self, project: int, direction: int) -> None:
        '''Naviguer entre les raws'''
        raw_attr = f'raws{project}'
        raw_id_attr = f'raws{project}_id'
        if not hasattr(self, raw_attr) or not getattr(self, raw_attr):
            return
        new_id = getattr(self, raw_id_attr) + direction
        if 0 <= new_id < len(getattr(self, raw_attr)):
            setattr(self, raw_id_attr, new_id)
            getattr(self, f'index{project}_label').config(text=f'{new_id + 1}/{len(getattr(self, raw_attr))}')
            self.p1_displayRaw(project, self._p1_resizeRaw(getattr(self, raw_attr)[new_id], getattr(self, f'raw{project}_rotation'), getattr(self, f'raw{project}_flip')))

    def p1_wheelNext(self, project: int, event: tk.Event) -> None:
        '''Défilement des raws avec la molette '''
        if not (event.state & 0x0004):
            self._p1_navigRaw(project, -1 if event.delta < 0 else 1)
    
    def p1_doRotation(self, project: int, angle: int) -> None:
        '''Effectuer les rotations'''
        raw_attr = f'raws{project}'
        if not hasattr(self, raw_attr) or not getattr(self, raw_attr):
            return
        rotation_attr = f'raw{project}_rotation'

        current_rotation = getattr(self, rotation_attr)
        rotations = [cv2.ROTATE_90_CLOCKWISE, cv2.ROTATE_180, cv2.ROTATE_90_COUNTERCLOCKWISE, -1]
        current_index = rotations.index(current_rotation)
        step = 1 if angle > 0 else -1
        new_rotation = rotations[(current_index + step) % len(rotations)]
        setattr(self, rotation_attr, new_rotation)
        self.p1_displayRaw(project, self._p1_resizeRaw(getattr(self, raw_attr)[getattr(self, f'raws{project}_id')], new_rotation, getattr(self, f'raw{project}_flip')))
    
    def p1_doFlip(self, project: int, flip_code: int) -> None:
        '''Effectuer les filps'''
        raw_attr = f'raws{project}'
        flip_attr = f'raw{project}_flip'
        if not hasattr(self, raw_attr) or not getattr(self, raw_attr):
            return
        new_flip = {-2: flip_code, 0: -2 if flip_code == 0 else -1, 1: -2 if flip_code == 1 else -1, -1: 1 if flip_code == 0 else 0}[getattr(self, flip_attr)]
        setattr(self, flip_attr, new_flip)
        self.p1_displayRaw(project, self._p1_resizeRaw(getattr(self, raw_attr)[getattr(self, f'raws{project}_id')], getattr(self, f'raw{project}_rotation'), new_flip))
    
    def _p1_chooseWindows(self, args, choose: tuple):
        '''Lors de la suppression d'un link demande à l'utilisateur ceux à supprimer dans une nouvelle fenêtre'''
        self.window_projectFuseion_choose = tk.Toplevel(self.window_projectFuseion)
        self.window_projectFuseion_choose.title(self.app.lang['merge_project'])
        self.window_projectFuseion_choose.grab_set()
        self.window_projectFuseion_choose.focus()
        self.window_projectFuseion_choose.transient(self.window_projectFuseion)

        self.choose_select = tk.StringVar()
        self.choose_select.set('1')
        if len(choose) == 2:
            text = (self.app.lang['del_all'], self.app.lang['del_one'])
        else:
            text = (self.app.lang['del_all'], self.app.lang['del_born'] + ' ' + str(choose[1]), self.app.lang['del_born'] + ' ' + str(choose[2]))
        for i in range(len(choose)):
            tk.Radiobutton(self.window_projectFuseion_choose, text=text[i], variable=self.choose_select, value=str(i+1)).pack(padx=5, pady=5)
        tk.Button(self.window_projectFuseion_choose, text=self.app.lang['validate'], command=lambda: self._p1_choose(args, i, choose)).pack(pady=10)
        self.window_projectFuseion_choose.wait_visibility()
        x = self.window_projectFuseion.winfo_x() + self.window_projectFuseion.winfo_width()//2 - self.window_projectFuseion_choose.winfo_width()//2
        y = self.window_projectFuseion.winfo_y() + self.window_projectFuseion.winfo_height()//2 - self.window_projectFuseion_choose.winfo_height()//2
        self.window_projectFuseion_choose.geometry(f"+{x}+{y}")
    
    def _p1_choose(self, args, i, select):
        '''Récupération de la selection de l'utilisation pour la suppresion des links'''
        if i == 1:
            self.links.chose_to_remove(*args, self.choose_select.get())
        else:
            self.links.choose_midpoint(*args, self.choose_select.get(), select[1:])
        self.window_projectFuseion_choose.destroy()
        self._p1_linkValid()
    
    def p1_link(self):
        '''Lorsque le bouton de link est appuyé'''
        if not hasattr(self, 'raws1') or not hasattr(self, 'raws2'):
            return
        link = self.links.add_link(self.raws1_id, self.raws2_id)
        if link is None:
            self._p1_linkValid()
        else:
            self._p1_chooseWindows(link[:-1], link[-1])

    def _p1_linkValid(self):
        '''Link si LinkSystem à validé le link'''
        color = self.links.l1[self.raws1_id]
        if color is not None:
            self.can1.create_rectangle(3, 3, 397, 397, width=5, outline=self.colors[int(color)%len(self.colors)], tags='link')
        else:
            self.can1.delete('link')
        color = self.links.l2[self.raws2_id]
        if color is not None:
            self.can2.create_rectangle(3, 3, 397, 397, width=5, outline=self.colors[int(color)%len(self.colors)], tags='link')
        else:
            self.can2.delete('link')
        self.p1_placeLinks()
    
    def p1_linkPreview(self):
        '''Création d'une fenêtre pour afficher les links effectuée avec les couleurs'''
        if hasattr(self, 'window_projectFusion_links'):
            self.window_projectFusion_links.destroy()
        self.window_projectFusion_links = tk.Toplevel(self.window_projectFuseion)
        self.window_projectFusion_links.transient(self.window_projectFuseion)
        self.window_projectFusion_links.protocol("WM_DELETE_WINDOW", lambda: None)
        self.window_projectFusion_links.geometry(f'+{self.window_projectFuseion.winfo_x() + self.window_projectFuseion.winfo_width() - 150}+{self.window_projectFuseion.winfo_y()+30}')

        self.links_can_start = [0, 0]
        self.links_can1 = tk.Canvas(self.window_projectFusion_links, width=70, height=200)
        self.links_can1.pack(side='left', expand=True, fill='y')
        self.links_can2 = tk.Canvas(self.window_projectFusion_links, width=70, height=200)
        self.links_can2.pack(side='right', expand=True, fill='y')
        self.links_can1.bind("<MouseWheel>", self._p1_linksPreviewScroll)
        self.links_can2.bind("<MouseWheel>",  self._p1_linksPreviewScroll)
        self.p1_placeLinks()
    
    def p1_placeLinks(self):
        '''Affiche les links effectués avec les couleurs dans la fenêtre window_projectFuseion_links'''
        self.links_can1.delete('all')
        self.links_can2.delete('all')
        for i, color in enumerate(self.links.l1):
            self.links_can1.create_text(15, self.links_can_start[0] + i*20, text=f'Raw {i+1}', fill='black' if color is None else self.colors[int(color)%len(self.colors)], font=("Helvetica", 12), anchor='nw')
        for i, color in enumerate(self.links.l2):
            self.links_can2.create_text(15, self.links_can_start[1] + i*20, text=f'Raw {i+1}', fill='black' if color is None else self.colors[int(color)%len(self.colors)], font=("Helvetica", 12), anchor='nw')
    
    def _p1_linksPreviewScroll(self, event: tk.Event):
        '''Permet de faire défiler la preview des links dans la fenêtre window_projectFuseion_links'''
        project = event.widget == self.links_can1
        if event.delta < 0:
            if event.widget.coords('all')[1] > -(len(self.links.l1 if project else self.links.l2) - 10) * 20:
                self.links_can_start[0 if project else 1] -= 100
                event.widget.move('all', 0, -100)
        else:
            if event.widget.coords('all')[1] < 0:
                self.links_can_start[0 if project else 1] += 100
                event.widget.move('all', 0, 100)


    def phase2(self):
        '''Phase 2: placement des images'''
        if not hasattr(self, 'raws1') or not hasattr(self, 'raws2'):
            return
        self.project_name = self.project_name.get()
        self.frame.destroy()
        self.window_projectFusion_links.destroy()
        if self.links.l1[0] is None:
            self.links.l1.pop(0)
            self.raws1.pop(0)
        if self.links.l1[-1] is None: 
            self.links.l1.pop()
            self.raws1.pop()
        self.links.complete()
        self._p2_setup()
    
    def _p2_setup(self):
        '''PLace les élements de la phase 2'''
        self.raws_id = self.links.raws_id()
        self.raw_id = 0
        self.can = tk.Canvas(self.window_projectFuseion, bg='white')
        self.can.pack(fill='both', expand=True, side='top')
        
        frame = tk.Frame(self.window_projectFuseion)
        frame.pack(side='bottom')
        self.raw_ontop = tk.StringVar()
        self.raw_ontop.set('raw1')
        tk.Label(frame, text=f"{self.app.lang['foreground']} :").pack(side='left')

        frame_radiobutton = tk.Frame(frame)
        frame_radiobutton.pack(side='left')
        tk.Radiobutton(frame_radiobutton, text=f"{self.app.lang['project']}1", variable=self.raw_ontop, value='raw1', command=lambda: self.can.tag_raise('raw1')).pack(side='top')
        tk.Radiobutton(frame_radiobutton, text=f"{self.app.lang['project']} 2", variable=self.raw_ontop, value='raw2', command=lambda: self.can.tag_raise('raw2')).pack(side='bottom')
        
        tk.Button(frame, text=self.app.lang['create_new_projet'], command=self.p2_compileRaws).pack(side='right', padx=(20, 0))

        self.selectRaw = None
        self.can.update()
        self._p2_placeRaws()
    
    def _p2_placeRaws(self):
        '''Setup les coordonnées, les bind, ...'''
        img1 = self.raws1[self.raws_id[self.raw_id][0]]
        img2 = self.raws2[self.raws_id[self.raw_id][1]]
        can_w = self.can.winfo_width()
        can_h = self.can.winfo_height()

        self.raw1_zoom = self._p2_calculateResize(img1, self.can)
        self.raw2_zoom = self._p2_calculateResize(img2, self.can)

        img1_w = int(img1.shape[1] * self.raw1_zoom)
        img1_h = int(img1.shape[0] * self.raw1_zoom)
        img2_w = int(img2.shape[1] * self.raw2_zoom)
        img2_h = int(img2.shape[0] * self.raw2_zoom)

        self.raw1_coords = [
            (can_w // 4) - (img1_w // 2),
            (can_h // 2) - (img1_h // 2)
        ]
        self.raw2_coords = [
            (3 * can_w // 4) - (img2_w // 2),
            (can_h // 2) - (img2_h // 2)
        ]

        self.can.create_text(self.can.winfo_width() - 5, self.can.winfo_height() - 5, text=f'{self.raw_id + 1}/{len(self.raws_id)}', tags='raw_id', anchor='se', font=("Helvetica", 12))

        self.window_projectFuseion.bind("<MouseWheel>", self._p2_wheelNext)
        self.can.bind('<Button-1>', self._p2_selectRaw)
        self.can.bind('<Button-3>', self._p2_unSelectRaw)
        self.can.bind('<B1-Motion>', self._p2_moveDoSelectedRaw)
        self.can.bind('<B3-Motion>', self._p2_moveDoSelectedRaw)
        self.can.bind('<Control-MouseWheel>', self._p2_zoomDoSelectedRaw)
        self.can.tag_bind('raw', '<Double-Button-1>', self._p2_editRaw)
        self.p2_displayRaws()

    def _p2_calculateResize(self, raw: cv2.typing.MatLike, can: tk.Canvas) -> float:
        '''Return le facteur de proportionnalité pour que les deux projets rentrent dans le canvas'''
        max_width = can.winfo_width() / 2
        max_height = can.winfo_height()
        width_ratio1 = max_width / raw.shape[1]
        height_ratio1 = max_height / raw.shape[0]
        multiplier1 = min(width_ratio1, height_ratio1)
        return multiplier1
    
    def p2_displayRaws(self):
        '''Gère l'affichage des projets ainsi que leur superposition'''
        self.p2_displayRaws1()
        self.p2_displayRaws2()
        self._p2_selectIndicator()
        self.can.tag_raise(self.raw_ontop.get())
        self.can.tag_raise('select')
        self.can.tag_raise('raw_id')
    
    def p2_displayRaws1(self):
        '''Affiche le projet 1'''
        self.can.delete('raw1')
        self.image1_relative_coods = self.raw1_coords
        self.current_image1 = self.raws1[self.raws_id[self.raw_id][0]].copy()
        if self.raw1_flip != -2:
            self.current_image1 = cv2.flip(self.current_image1, self.raw1_flip)
        if self.raw1_rotation != -1:
            self.current_image1 = cv2.rotate(self.current_image1, self.raw1_rotation)
        if self.raw1_zoom != 1.0:
            image_size = self.current_image1.shape[1] * self.raw1_zoom, self.current_image1.shape[0] * self.raw1_zoom
            x1 = min(max(0, -self.image1_relative_coods[0] * self.current_image1.shape[1] / image_size[0]), self.current_image1.shape[1])
            y1 = min(max(0, -self.image1_relative_coods[1] * self.current_image1.shape[0] / image_size[1]), self.current_image1.shape[0])
            x2 = min(max(0, (self.can.winfo_width() - self.image1_relative_coods[0]) * self.current_image1.shape[1] / image_size[0]), self.current_image1.shape[1])
            y2 = min(max(0, (self.can.winfo_height() - self.image1_relative_coods[1]) * self.current_image1.shape[0] / image_size[1]), self.current_image1.shape[0])

            new_raw = self.current_image1[int(y1):int(y2), int(x1):int(x2)]
            if new_raw.size and int((x2 - x1) * self.raw1_zoom) > 0 and int((y2 - y1) * self.raw1_zoom) > 0:
                self.current_image1 = cv2.resize(new_raw, (int((x2 - x1) * self.raw1_zoom), int((y2 - y1) * self.raw1_zoom)))
                self.image1_relative_coods = [int(self.image1_relative_coods[0] + x1 * self.raw1_zoom), int(self.image1_relative_coods[1] + y1 * self.raw1_zoom)]
                self.current_image1 = ImageTk.PhotoImage(Image.fromarray(self.current_image1))
                self.can.create_image(self.image1_relative_coods, anchor='nw', image=self.current_image1, tags=('raw1', 'raw'))

    def p2_displayRaws2(self):
        '''Affiche le projet 2'''
        self.can.delete('raw2')
        self.image2_relative_coods = self.raw2_coords
        self.current_image2 = self.raws2[self.raws_id[self.raw_id][1]].copy()
        if self.raw2_flip != -2:
            self.current_image2 = cv2.flip(self.current_image2, self.raw2_flip)
        if self.raw2_rotation != -1:
            self.current_image2 = cv2.rotate(self.current_image2, self.raw2_rotation)
        if self.raw2_zoom != 1.0:
            image_size = self.current_image2.shape[1] * self.raw2_zoom, self.current_image2.shape[0] * self.raw2_zoom
            x1 = min(max(0, -self.image2_relative_coods[0] * self.current_image2.shape[1] / image_size[0]), self.current_image2.shape[1])
            y1 = min(max(0, -self.image2_relative_coods[1] * self.current_image2.shape[0] / image_size[1]), self.current_image2.shape[0])
            x2 = min(max(0, (self.can.winfo_width() - self.image2_relative_coods[0]) * self.current_image2.shape[1] / image_size[0]), self.current_image2.shape[1])
            y2 = min(max(0, (self.can.winfo_height() - self.image2_relative_coods[1]) * self.current_image2.shape[0] / image_size[1]), self.current_image2.shape[0])

            new_raw = self.current_image2[int(y1):int(y2), int(x1):int(x2)]
            if new_raw.size and int((x2 - x1) * self.raw2_zoom) > 0 and int((y2 - y1) * self.raw2_zoom) > 0:
                self.current_image2 = cv2.resize(new_raw, (int((x2 - x1) * self.raw2_zoom), int((y2 - y1) * self.raw2_zoom)))
                self.image2_relative_coods = [int(self.image2_relative_coods[0] + x1 * self.raw2_zoom), int(self.image2_relative_coods[1] + y1 * self.raw2_zoom)]
                self.current_image2 = ImageTk.PhotoImage(Image.fromarray(self.current_image2))
                self.can.create_image(self.image2_relative_coods, anchor='nw', image=self.current_image2, tags=('raw2', 'raw'))

    def _p2_selectRaw(self, event: tk.Event):
        '''Sélectionne le projet sur lequel on clic'''
        self._xy = event.x, event.y
        rawSelected = event.widget.gettags(event.widget.find_withtag("current"))
        self.selectRaw = None if rawSelected == () else rawSelected[0][-1:]
        self._p2_selectIndicator()
    
    def _p2_unSelectRaw(self, event: tk.Event):
        '''Désélectionne le projet sélectionné'''
        self._xy = event.x, event.y
        self.selectRaw = None
        self._p2_selectIndicator()
    
    def _p2_selectIndicator(self):
        '''Entour en pointillés le projet sélectionné'''
        self.can.delete('select')
        if self.selectRaw == '1':
            coords = (self.image1_relative_coods[0], self.image1_relative_coods[1],
                    self.image1_relative_coods[0] + self.current_image1.width() - 1, self.image1_relative_coods[1] + self.current_image1.height() - 1)
        elif self.selectRaw == '2':
            coords = (self.image2_relative_coods[0], self.image2_relative_coods[1], 
                    self.image2_relative_coods[0] + self.current_image2.width() - 1, self.image2_relative_coods[1] + self.current_image2.height() - 1)
        else:
            return
        self.can.create_rectangle(coords, outline='yellow', width=3, dash=(5, 20), tags='select')
    
    def _p2_moveDoSelectedRaw(self, event: tk.Event):
        '''Déplace le projet sélectionné'''
        if event.state & 0x100 and self.selectRaw is None:
            return
        dx = event.x - self._xy[0]
        dy = event.y - self._xy[1]
        if self.selectRaw is None or self.selectRaw == '1':
            self.raw1_coords[0] += dx
            self.raw1_coords[1] += dy
        if self.selectRaw is None or self.selectRaw == '2':
            self.raw2_coords[0] += dx
            self.raw2_coords[1] += dy
        self._xy = event.x, event.y
        self.p2_displayRaws()

    def _p2_zoomDoSelectedRaw(self, event: tk.Event) -> None:
        '''
        Update le facteur de zoom
        Si aucun projet n'est sélectionné cela zoom sur les deux
        '''
        factor = 1.1 if event.delta > 0 else 0.9
        if self.selectRaw is None or self.selectRaw == '1':
            self.raw1_zoom *= factor
            self.raw1_coords = [int((self.raw1_coords[0] - event.x) * factor + event.x), int((self.raw1_coords[1] - event.y) * factor + event.y)]
        if self.selectRaw is None or self.selectRaw == '2':
            self.raw2_zoom *= factor
            self.raw2_coords = [int((self.raw2_coords[0] - event.x) * factor + event.x), int((self.raw2_coords[1] - event.y) * factor + event.y)]
        self.p2_displayRaws()
    
    def p2_navigRaw(self, direction: int) -> None:
        '''Fais défiler les images des deux projets en prenant en compte les links'''
        if 0 <= self.raw_id + direction < len(self.raws_id):
            self.raw_id += direction
            self.can.delete('raw_id')
            self.can.create_text(self.can.winfo_width() - 5, self.can.winfo_height() - 5, text=f'{self.raw_id + 1}/{len(self.raws_id)}', tags='raw_id', anchor='se', font=("Helvetica", 12))
            self.p2_displayRaws()

    def _p2_wheelNext(self, event: tk.Event) -> None:
        '''Lors du scroll sans appuyer sur Ctrl'''
        if not (event.state & 0x0004):
            self.p2_navigRaw(-1 if event.delta < 0 else 1)
    
    def _p2_editRaw(self, event: tk.Event):
        '''Permets d'édit les coordonnées, le zoom, les rotations et les filps de chaque projet manuellement'''
        self.window_projectFuseion_edit = tk.Toplevel(self.window_projectFuseion)
        self.window_projectFuseion_edit.title(f"{self.app.lang['editor']} - {self.app.lang['project']}{self.selectRaw}")
        self.window_projectFuseion_edit.grab_set()
        self.window_projectFuseion_edit.focus()
        self.window_projectFuseion_edit.transient(self.window_projectFuseion)
        self.window_projectFuseion_edit.geometry(f"+{self.window_projectFuseion.winfo_x() + self.window_projectFuseion.winfo_width()//2 - 97}+{self.window_projectFuseion.winfo_y() + self.window_projectFuseion.winfo_height()//2 - 145}")

        tk.Label(self.window_projectFuseion_edit, text=f"{self.app.lang['position']} :").pack(pady=(10, 5))
        position = tk.Frame(self.window_projectFuseion_edit)
        position.pack()
        tk.Label(position, text='x :').pack(side='left')
        x = tk.Entry(position)
        x.pack(side='left')
        x.insert(0, str(self.raw1_coords[0] if self.selectRaw == '1' else self.raw2_coords[0]))
        position = tk.Frame(self.window_projectFuseion_edit)
        position.pack()
        tk.Label(position, text='y :').pack(side='left')
        y = tk.Entry(position)
        y.pack(side='left')
        y.insert(0, str(self.raw1_coords[1] if self.selectRaw == '1' else self.raw2_coords[1]))

        tk.Label(self.window_projectFuseion_edit, text=f"{self.app.lang['zoom']} :").pack(pady=(10, 5))
        z = tk.Entry(self.window_projectFuseion_edit)
        z.pack()
        z.insert(0, str(self.raw1_zoom if self.selectRaw == '1' else self.raw2_zoom))

        tk.Label(self.window_projectFuseion_edit, text=f"{self.app.lang['rotation']} :").pack(pady=(10, 5))
        rotation = tk.Frame(self.window_projectFuseion_edit)
        rotation.pack(padx=5)
        rotation_value = tk.IntVar(value=self.raw1_rotation if self.selectRaw == '1' else self.raw2_rotation)
        for i in (('90°', cv2.ROTATE_90_CLOCKWISE), ('180°', cv2.ROTATE_180), ('-90°', cv2.ROTATE_90_COUNTERCLOCKWISE), ('0°', -1)):
            tk.Radiobutton(rotation, variable=rotation_value, text=i[0], value=i[1]).pack(side='left')

        tk.Label(self.window_projectFuseion_edit, text=f"{self.app.lang['flip']} :").pack(pady=(10, 5))
        flip = tk.Frame(self.window_projectFuseion_edit)
        flip.pack()
        flip_value = self.raw1_flip if self.selectRaw == '1' else self.raw2_flip
        v_filp = tk.IntVar(value=0 if flip_value == -2 or flip_value == 1 else 1)
        tk.Checkbutton(flip, text=self.app.lang['vertical'], onvalue=1, offvalue=0, variable=v_filp).pack(side='left')
        h_filp = tk.IntVar(value=0 if flip_value == -2 or flip_value == 0 else 1)
        tk.Checkbutton(flip, text=self.app.lang['horizontal'], onvalue=1, offvalue=0, variable=h_filp).pack(side='left')

        tk.Button(self.window_projectFuseion_edit, text=self.app.lang['validate'], command=lambda: self._p2_edit(x.get(), y.get(), z.get(), rotation_value.get(), v_filp.get(), h_filp.get())).pack(pady=5)
    
    def _p2_edit(self, x: str, y: str, z: str, r: int, v: int, h: int):
        '''Update les coordonnées, le zoom, les rotations et les filps lors de la modification manuelle'''
        attr_coords = f'raw{self.selectRaw}_coords'
        if not x.isdigit():
            x = getattr(self, attr_coords)[0]
        if not y.isdigit():
            y = getattr(self, attr_coords)[1]
        setattr(self, attr_coords, [int(x), int(y)])
        if not z.replace('.','',1).isdigit():
            z = getattr(self, f'raw{self.selectRaw}_zoom')[0]
        setattr(self, f'raw{self.selectRaw}_zoom', float(z))
        setattr(self, f'raw{self.selectRaw}_rotation', int(r))
        if v == h == 0:
            f = -2
        elif v == h == 1:
            f = -1
        elif v == 1:
            f = 0
        else:
            f = 1
        setattr(self, f'raw{self.selectRaw}_flip', f)
        self.window_projectFuseion_edit.destroy()
        self.p2_displayRaws()
    
    def p2_compileRaws(self):
        self.app.createProject(self.project_name, self.savefolder)
        self.fusion_path = self.savefolder  # <-- Ajoute cette ligne
        self.app.raw.importRawAutoFusion()
        self.window_projectFuseion.destroy()
        


class LinkSystem:
    def __init__(self, list1: list, list2: list):
        self.l1 = [None] * len(list1)
        self.l2 = [None] * len(list2)
        self.links = {}
        self.current_color = 0

    def __str__(self):
        return f"Links: {self.links}\n{self.l1}\n{self.l2}"
    
    def add_link(self, i1: int, i2: int):
        if self.l1[i1] and self.l2[i2]:
            return self.remove_link(i1, i2)
        elif self.l1[i1]:
            self._handle_single_link(self.l1, self.l2, i1, i2, 0)
        elif self.l2[i2]:
            self._handle_single_link(self.l2, self.l1, i2, i1, 1)
        else:
            if not self._crosses(self.l1, self.l2, i1, i2):
                self._create_link(i1, i2)
    
    def _crosses(self, l1: list, l2: list, i1: int, i2: int) -> bool:
        return bool(set(filter(None, l1[:i1])).intersection(l2[i2+1:])) or bool(set(filter(None, l2[:i2])).intersection(l1[i1+1:]))

    def _create_link(self, i1: int, i2: int):
        color = str(self.current_color)
        self._link(self.l1, i1, color, 0)
        self._link(self.l2, i2, color, 1)
        self.current_color += 1

    def _handle_single_link(self, l_from, l_to, i_from, i_to, index):
        color = l_from[i_from]
        if not self._link_between(l_to, i_to, self.links[color][not index][0]):
            if len(self.links[color][index]) == 1 and not self._crosses(l_from, l_to, i_from, i_to):
                self._link_range(l_to, i_to, self.links[color][not index][0], color, not index)
    
    def _link_range(self, l: list, start: int, end: int, color: str, index: int):
        for i in range(min(start, end), max(start, end) + 1):
            if i not in self.links[color][index]:
                l[i] = color
                self.links[color][index].append(i)

    def _link(self, l: list, i: int, color: str, index: int):
        l[i] = color
        if color not in self.links:
            self.links[color] = [[], []]
        self.links[color][index].append(i)
    
    def remove_link(self, i1: int, i2: int):
        if self.l1[i1] == self.l2[i2]:
            return self._unlink_both(i1, i2)
        else:
            self._unlink_different_colors(i1, i2)
    
    def _unlink_both(self, i1: int, i2: int):
        if self._is_isolated(self.l1, i1) and self._is_isolated(self.l2, i2):
            self._remove_both(i1, i2, self.l1[i1])
        elif self._is_isolated(self.l1, i1):
            return self._remove_single(1, i1, i2)
        elif self._is_isolated(self.l2, i2):
            return self._remove_single(0, i1, i2)
    
    def _unlink_different_colors(self, i1: int, i2: int):
        pass
    
    def _remove_both(self, i1: int, i2: int, color: str):
        self.links[color][0].remove(i1)
        self.links[color][1].remove(i2)
        if not self.links[color][0] and not self.links[color][1]:
            del self.links[color]
        self.l1[i1] = None
        self.l2[i2] = None

    def _remove_single(self, index: int, i1: int, i2: int):
        end = self._is_end(self.l1 if index == 0 else self.l2, i1 if index == 0 else i2)
        if end:
            return self._choose_to_remove(index, i1, i2)
        else:
            return self._choose_midpoint(index, i1, i2)

    def _choose_to_remove(self, index: int, i1: int, i2: int):
        return index, i1, i2, (sorted(self.links[self.l1[i1]][index]), i1 if index == 0 else i2)
    
    def chose_to_remove(self, index: int, i1: int, i2: int, choice: str):
        if choice == '1':
            self._remove_all_links(i1)
        elif choice == '2':
            self.links[self.l1[i1]][index].remove(i1 if index == 0 else i2)
            (self.l1 if index == 0 else self.l2)[i1 if index == 0 else i2] = None

    def _choose_midpoint(self, index: int, i1: int, i2: int):
        positions = sorted(self.links[self.l1[i1]][index])
        first_half = positions[:positions.index(i1 if index == 0 else i2) + 1]
        second_half = positions[positions.index(i1 if index == 0 else i2):]
        return index, i1, i2, (positions, first_half, second_half)
    
    def choose_midpoint(self, index: int, i1: int, i2: int, choice: str, select: tuple):
        if choice == '1':
            self._remove_all_links(i1)
        elif choice == '2':
            self._remove_selected_links(index, select[0], self.l1[i1])
        elif choice == '3':
            self._remove_selected_links(index, select[1], self.l1[i1])

    def _remove_all_links(self, i: int):
        color = self.l1[i]
        link = self.links.pop(color)
        for j in link[0]:
            self.l1[j] = None
        for j in link[1]:
            self.l2[j] = None

    def _remove_selected_links(self, index: int, positions: list, color: str):
        for i in positions:
            self.links[color][index].remove(i)
            (self.l1 if index == 0 else self.l2)[i] = None

    def _is_isolated(self, l: list, i: int) -> bool:
        return (i == 0 or l[i] != l[i - 1]) and (i == len(l) - 1 or l[i] != l[i + 1])

    def _is_end(self, l: list, i: int) -> bool:
        return (i == 0 or l[i] != l[i - 1]) or (i == len(l) - 1 or l[i] != l[i + 1])

    def _link_between(self, l: list, i1: int, i2: int) -> bool:
        segment = set(l[min(i1, i2):max(i1, i2)])
        segment.discard(None)
        return len(segment) > 1
    
    def complete(self, i1: int = 0, i2: int = 0):
        last = False
        if i1 >= len(self.l1) and i2 >= len(self.l2):
            return
        elif i1 >= len(self.l1):
            last = True
            i1 -= 1
        elif i2 >= len(self.l2):
            last = True
            i2 -= 1
        l1 = self.l1[i1:]
        l2 = self.l2[i2:]
        if not l1[0] and not l2[0]:
            range1 = self._find_motif_range(l1, None)
            range2 = self._find_motif_range(l2, None)
            r1 = range1[1] - range1[0] + 1
            r2 = range2[1] - range2[0] + 1
            if r1 == r2:
                for i in range(r1):
                    color = str(self.current_color)
                    self.current_color += 1
                    self.links[color] = [[i1 + i], [i2 + i]]
                i1 += r1
                i2 += r2
            elif r1 < r2:
                x = self._distribute_proportionally(r2, r1)
                for i in x:
                    color = str(self.current_color)
                    self.current_color += 1
                    self.links[color] = [[], []]
                    self.links[color][0].append(i1)
                    for _ in range(i):
                        self.links[color][1].append(i2)
                        i2 += 1
                    i1 += 1
            elif r1 > r2:
                x = self._distribute_proportionally(r1, r2)
                for i in x:
                    color = str(self.current_color)
                    self.current_color += 1
                    self.links[color] = [[], []]
                    self.links[color][1].append(i2)
                    for _ in range(i):
                        self.links[color][0].append(i1)
                        i1 += 1
                    i2 += 1
        elif not l1[0] and l2[0]:
            range1 = self._find_motif_range(l1, None)
            r1 = range1[1] - range1[0] + 1
            if r1 > 1 and i2 > 0 and not last:
                x = self._distribute_proportionally(r1, 2)
                color = str(self.current_color)
                self.current_color += 1
                self.links[color] = [[i1 + i for i in range(x[0])], [i2 - 1]]
                color = str(self.current_color)
                self.current_color += 1
                self.links[color] = [[i1 + i + x[0] for i in range(x[1])], [i2]]
            else:
                color = str(self.current_color)
                self.current_color += 1
                self.links[color] = [[i1 + i for i in range(r1)], [i2]]
            i1 += r1
            i2 += self._find_motif_range(l2, l2[0])[1] + 1
            if r1 < len(l1) and l1[r1] == l2[0] and not last:
                i1 += self._find_motif_range(l1[r1:], l2[0])[1] + 1
        elif l1[0] and not l2[0]:
            range1 = self._find_motif_range(l2, None)
            r1 = range1[1] - range1[0] + 1
            if r1 > 1 and i1 > 0 and not last:
                x = self._distribute_proportionally(r1, 2)
                color = str(self.current_color)
                self.current_color += 1
                self.links[color] = [[i1 - 1], [i2 + i for i in range(x[0])]]
                color = str(self.current_color)
                self.current_color += 1
                self.links[color] = [[i1], [i2 + i + x[0] for i in range(x[1])]]
            else:
                color = str(self.current_color)
                self.current_color += 1
                self.links[color] = [[i1], [i2 + i for i in range(r1)]]
            i1 += self._find_motif_range(l1, l1[0])[1] + 1
            i2 += r1
            if r1 < len(l2) and l2[r1] == l1[0] and not last:
                i2 += self._find_motif_range(l2[r1:], l1[0])[1] + 1
        else:
            i1 += self._find_motif_range(l1, l1[0])[1] + 1
            i2 += self._find_motif_range(l2, l2[0])[1] + 1
        self.complete(i1, i2)

    def _distribute_proportionally(self, y: int, x: int) -> list:
        return [y // x + (1 if i < y % x else 0) for i in range(x)]

    def _find_motif_range(self, lst: list, motif) -> tuple:
        return (0, next((i for i, v in enumerate(lst) if v is not motif), len(lst)) - 1)
    
    def raws_id(self) -> list:
        result = []
        for _, (raws1, raws2) in self.links.items():
            for img1 in raws1:
                for img2 in raws2:
                    result.append((img1, img2))
        result.sort()
        return result

import tkinter as tk
from tkinter import messagebox, filedialog
from PIL import Image
from pathlib import Path
import threading
import cv2
import numpy as np
from PIL import Image as PILImage, ImageTk



class RXviewer:...


class RXviewerRaw:
    def newRaw(self, image_path: Path, project_folder: Path):
        '''Ajoute une image au projet'''
        self.filename = image_path.stem + '.png'
        if (image_path).is_file():
            gray = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
            blurred = cv2.GaussianBlur(gray, (3, 3), 0)
            edges = cv2.Laplacian(blurred, cv2.CV_64F)
            edges = np.uint8(np.absolute(edges))

            
            enhanced = cv2.addWeighted(gray, 0.8, edges, 0.5, 0)

            
            self.raw = cv2.cvtColor(enhanced, cv2.COLOR_GRAY2BGR)


            self.importRawInProjectFolder(project_folder)
    
    def importRaw(self, project_folder: Path, raw: cv2.typing.MatLike, name: str):
        '''Ajoute une image lors de la fusion de deux projets'''
        self.raw = raw
        self.filename = f'slice{name.zfill(5)}.png'
        self.importRawInProjectFolder(project_folder)
    
    def importRawInProjectFolder(self, project_folder: Path):
        '''Ajoute une images'''
        cv2.imwrite(project_folder / 'raw' / self.filename, self.raw)
        cv2.imwrite(project_folder / 'edit' / self.filename, self.raw)
        self.draw = np.array(Image.new("RGBA", (self.raw.shape[1], self.raw.shape[0]), (0, 0, 0, 0)))
        cv2.imwrite(project_folder / 'draw' / self.filename, self.draw)
        # Créer l'image pathtracking (même format que draw)
        self.pathtracking = np.array(Image.new("RGBA", (self.raw.shape[1], self.raw.shape[0]), (0, 0, 0, 0)))
        cv2.imwrite(project_folder / 'pathtracking' / self.filename, self.pathtracking)

    def loadRaw(self, project_folder: Path, filename: str):
        '''Charge les images dans le RAM'''
        self.filename = filename
        
        # Charger l'image edit
        if (project_folder / 'edit' / filename).is_file():
            self.raw = cv2.imread(str(project_folder / 'edit' / filename), cv2.IMREAD_UNCHANGED)
        else:
            # Fallback vers raw si edit n'existe pas
            if (project_folder / 'raw' / filename).is_file():
                self.raw = cv2.imread(str(project_folder / 'raw' / filename), cv2.IMREAD_UNCHANGED)
            else:
                print(f"Erreur: Impossible de charger l'image {filename}")
                return
        
        # Charger l'image draw ou l'initialiser
        if (project_folder / 'draw' / filename).is_file():
            self.draw = cv2.imread(str(project_folder / 'draw' / filename), cv2.IMREAD_UNCHANGED)
        else:
            # Créer une image draw vide si elle n'existe pas
            if hasattr(self, 'raw') and self.raw is not None:
                self.draw = np.array(Image.new("RGBA", (self.raw.shape[1], self.raw.shape[0]), (0, 0, 0, 0)))
                # Sauvegarder l'image draw vide pour la prochaine fois
                cv2.imwrite(str(project_folder / 'draw' / filename), self.draw)
            else:
                print(f"Erreur: Impossible d'initialiser l'image draw pour {filename}")
                return
    
    def saveRaw(self, project_folder: Path):
        '''Sauvegarde les images'''
        cv2.imwrite(project_folder / 'draw' / self.filename, self.draw)
        cv2.imwrite(project_folder / 'edit' / self.filename, self.raw)
    

class RXviewerRaws:
    def __init__(self, app: RXviewer):
        self.app = app
        self.raw = []
        self.raw_coords = [0, 0]

    def _updatePreviews(self):
        '''Affiche les images min et max dans les labels'''
        

        def get_image(index):
            try:
                path = self._tif_files[index]
                img = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
                if img is None:
                    return None
                img = cv2.resize(img, (256, 256), interpolation=cv2.INTER_AREA)
                return ImageTk.PhotoImage(PILImage.fromarray(img))
            except Exception as e:
                print(f"[Preview Error] {e}")
                return None

        i_min = self._child_window_valid_born_m0.get()
        i_max = self._child_window_valid_born_m1.get()

        img_min = get_image(i_min)
        img_max = get_image(i_max)

        if img_min:
            self._preview_min_label.config(image=img_min)
            self._preview_min_label.image = img_min
        else:
            self._preview_min_label.config(text="❌")

        if img_max:
            self._preview_max_label.config(image=img_max)
            self._preview_max_label.image = img_max
        else:
            self._preview_max_label.config(text="❌")
    def loadImagesFromPath(self, project_path: Path):
        self.raw = []
        raw_folder = project_path / 'raw'
        for file in sorted((project_path / 'edit').glob("*.png")):
            image = cv2.imread(str(file), cv2.IMREAD_UNCHANGED)
            if image is not None:
                self.raw.append(type('Raw', (), {'raw': image, 'filename': file.name})())

    def importRawAutoValidBorn(self, mi: int, ma: int, leng: int) -> None:
        '''Fenêtre de sélection des bornes avec double preview visuel dynamique'''
        print('importRawAutoValidBorn')
        if "_child_window_valid_born" in self.__dict__:
            if self._child_window_valid_born is not None and tk.Toplevel.winfo_exists(self._child_window_valid_born):
                return

        self._child_window_valid_born = tk.Toplevel(self.app.app)
        self._child_window_valid_born.title(self.app.lang["valid_born"])
        self._child_window_valid_born.transient(self.app.app)
        self._child_window_valid_born.grab_set()
        self._child_window_valid_born.focus()
        self._child_window_valid_born.geometry(f"+{self.app.app.winfo_x() + self.app.app.winfo_width()//2 - 250}+{self.app.app.winfo_y() + self.app.app.winfo_height()//2 - 200}")

        tk.Label(self._child_window_valid_born, text=eval(self.app.lang['selected_raw']), font=("Helvetica", 14)).pack(padx=5, pady=5)

        frame_controls = tk.Frame(self._child_window_valid_born)
        frame_controls.pack(padx=10, pady=5)

        self._child_window_valid_born_m0 = tk.Scale(frame_controls, from_=0, to=leng, orient='horizontal', length=300, width=10, label=f'{self.app.lang.get("min_label", "Min")} :')
        self._child_window_valid_born_m0.grid(row=0, column=0, padx=5)
        self._child_window_valid_born_m0.set(mi)
        self._child_window_valid_born_m0.bind("<B1-Motion>", lambda e: self._updatePreviews())
        self._child_window_valid_born_m0.bind("<ButtonRelease-1>", lambda e: self._updatePreviews())

        self._child_window_valid_born_m1 = tk.Scale(frame_controls, from_=0, to=leng, orient='horizontal', length=300, width=10, label=f'{self.app.lang.get("max_label", "Max")} :')
        self._child_window_valid_born_m1.grid(row=0, column=1, padx=5)
        self._child_window_valid_born_m1.set(ma)
        self._child_window_valid_born_m1.bind("<B1-Motion>", lambda e: self._updatePreviews())
        self._child_window_valid_born_m1.bind("<ButtonRelease-1>", lambda e: self._updatePreviews())

        preview_frame = tk.Frame(self._child_window_valid_born)
        preview_frame.pack(pady=10)

        self._preview_min_label = tk.Label(preview_frame)
        self._preview_min_label.pack(side='left', padx=10)

        self._preview_max_label = tk.Label(preview_frame)
        self._preview_max_label.pack(side='right', padx=10)

        self._child_window_valid_born_err = tk.Label(self._child_window_valid_born, fg='red')
        self._child_window_valid_born_err.pack()

        tk.Button(self._child_window_valid_born, text=self.app.lang.get("ok_button", "OK"), command=self._importRawAutoValid, width=20).pack(padx=5, pady=5)
        self._child_window_valid_born.bind('<Return>', self._importRawAutoValid)

        self._updatePreviews()


    
    def _importRawAutoValid(self, event: tk.Event | None = None) -> None:
        '''Vérifie les bornes'''
        print('importRawAutoValid')
        if self._child_window_valid_born_m0.get() >= self._child_window_valid_born_m1.get():
            self._child_window_valid_born_err.config(text=self.app.lang['err4'])
            return
        m0, m1 = int(self._child_window_valid_born_m0.get()), int(self._child_window_valid_born_m1.get())
        self._child_window_valid_born.destroy()
        self._importRawAutoSave(self._tif_files[m0:m1])
        del self._tif_files, self._child_window_valid_born
    
    def saveRaws(self):
        '''Sauvegarde les images du projet'''
        thread = []
        for i in self.raw:
            thread.append(threading.Thread(target=i.saveRaw, args=(self.app.current_project,)))
            thread[-1].start()
        for i in thread:i.join()

    def _import_tif(self, image_path: Path, index: int) -> None:
        '''Importe les images dans le projet'''
        self.raw[index] = RXviewerRaw()
        self.raw[index].newRaw(image_path, self.app.current_project)
    
    def _isExploitable(self, image_path: Path, sensi: int = 80) -> bool:
        '''Renvoie si une image est exploitable'''
        _, img_binary = cv2.threshold(cv2.cvtColor(cv2.imread(str(image_path)), cv2.COLOR_BGR2GRAY) , sensi, 255, cv2.THRESH_BINARY)
        outlines, _ = cv2.findContours(cv2.bitwise_not(img_binary), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        return len(outlines) > 0
    
    def importRawManual(self, event: tk.Event | None = None) -> None:
        '''Laisse l'utilisateur importer des images manuellement'''
        print('importRawManual')
        if self.app.current_project:
            tif_files = filedialog.askopenfilenames(title=self.app.lang['select_file'], filetypes=[("TIFF Files", "*.tif")], multiple=True)
            if tif_files:
                self.app.app.title('GendALF - ' + str(self.app.current_project) + ' - Loading raw...')
                thread = []
                self.app.loadingBar(0)
                self.raw = [None] * len(tif_files)
                for i, tif_path in enumerate(tif_files):
                    thread.append(threading.Thread(target=self._import_tif, args=(Path(tif_path), i)))
                    thread[-1].start()
                    self.app.loadingBar(int(i/len(tif_files) * 100))
                for i in thread: i.join()
                self.app.resetLoadingBar()
                self.app.app.title('GendALF - ' + str(self.app.current_project))
                self._displayImages()
        else:
            messagebox.showerror(self.app.lang['err'], f"{self.app.lang['err2']}")
    
    def importRawAuto(self, event: tk.Event | None = None):
        '''Import des images depuis un dossier'''
        print('importRawAuto')
        if self.app.current_project:
            folder_selected = Path(filedialog.askdirectory())
            if folder_selected.exists() and str(folder_selected) != '.':
                self.app.app.title('GendALF - ' + str(self.app.current_project) + ' - Importing raw...')
                self._tif_files = list(folder_selected.glob('*.tif'))
                if not self._tif_files:
                    messagebox.showerror(self.app.lang['err'], f"{self.app.lang['err5']}")
                    return
                self.app.loadingBar(10)
                self._min_index, self._max_index = 0, len(self._tif_files) - 1
                thread_min = threading.Thread(target=self._importRawAutoMin, args=(self._tif_files,))
                thread_max = threading.Thread(target=self._importRawAutoMax, args=(self._tif_files,))
                self.app.loadingBar(25)
                thread_min.start()
                thread_max.start()
                thread_min.join()
                self.app.loadingBar(50)
                thread_max.join()
                if self._max_index - self._min_index > 500:
                    self._min_index, self._max_index = 0, len(self._tif_files) - 1
                    thread_min = threading.Thread(target=self._importRawAutoMin, args=(self._tif_files, 65))
                    thread_max = threading.Thread(target=self._importRawAutoMax, args=(self._tif_files, 65))
                    self.app.loadingBar(65)
                    thread_min.start()
                    thread_max.start()
                    thread_min.join()
                    self.app.loadingBar(75)
                    thread_max.join()
                self.app.loadingBar(100)
                if self._min_index > self._max_index:
                    messagebox.showerror(self.app.lang['err'], f"{self.app.lang['err6']}")
                    return
                self.app.app.title('GendALF - ' + str(self.app.current_project))
                self.app.resetLoadingBar()
                self.importRawAutoValidBorn(self._min_index, self._max_index, len(self._tif_files) - 1)
                del self._min_index, self._max_index
        else:
            messagebox.showerror(self.app.lang['err'], f"{self.app.lang['err2']}")
    
    def _importRawAutoMin(self, tif_files: list, sensi: int = 80) -> None:
        '''Cherche la borne min des images exploitable'''
        print('importRawAutoMin')
        for i in range(0, len(tif_files), 10):
            valid = self._isExploitable(tif_files[i], sensi)
            if valid:
                self._min_index = i
                return

    def _importRawAutoMax(self, tif_files: list, sensi: int = 80) -> None:
        '''Cherche la borne max des images exploitable'''
        print('importRawAutoMax')
        for i in range(len(tif_files) - 1, -1, -10):
            valid = self._isExploitable(tif_files[i], sensi)
            if valid:
                self._max_index = i
                return
    
    def importRawAutoFusion(self):
        '''Import les images lors de la fusion de deux projets'''
        self._fusion_zomm = self.app.project_fusion.raw1_zoom, self.app.project_fusion.raw2_zoom
        self._onTop = self.app.project_fusion.raw_ontop.get()
        self._way = self.app.project_fusion.raw_way.get()  

        self.raw = [None] * len(self.app.project_fusion.raws_id)
        thread = []
        self.app.loadingBar(0)
        self.app.app.title('GendALF - ' + str(self.app.current_project) + ' - Importing raw...')
        for i, raws in enumerate(self.app.project_fusion.raws_id):
            thread.append(threading.Thread(target=self._complileRaw, args=(self.app.project_fusion.raws1[raws[0]], self.app.project_fusion.raws2[raws[1]], i, self.app.project_fusion.raw_way.get())))
            print("Fonctionne")
            thread[-1].start()
            self.app.loadingBar(int(i/len(self.app.project_fusion.raws_id) * 100))
        for i in thread: i.join()
        self.app.resetLoadingBar()
        self.app.app.title('GendALF - ' + str(self.app.current_project))
        del self.app.project_fusion, self._fusion_zomm, self._onTop, self._way
    
    def _addAphaChannel(self, raw: cv2.typing.MatLike):
        '''Créer un canal alpha'''
        if raw.shape[2] == 3:
            raw = cv2.cvtColor(raw, cv2.COLOR_BGR2BGRA)
        return raw

    def _complileRaw(self, raw1: cv2.typing.MatLike, raw2: cv2.typing.MatLike, index: int, way: int = 0):
        print("Fusionne")

        x1, y1 = [int(i) for i in self.app.project_fusion.raw1_coords]
        x2, y2 = [int(i) for i in self.app.project_fusion.raw2_coords]

        if self.app.project_fusion.raw1_flip != -2:
            raw1 = cv2.flip(raw1, self.app.project_fusion.raw1_flip)
        if self.app.project_fusion.raw1_rotation != -1:
            raw1 = cv2.rotate(raw1, self.app.project_fusion.raw1_rotation)
        if self._fusion_zomm[0] != 1:
            raw1 = cv2.resize(raw1, (int(raw1.shape[1] * self._fusion_zomm[0]), int(raw1.shape[0] * self._fusion_zomm[0])))

        if self.app.project_fusion.raw2_flip != -2:
            raw2 = cv2.flip(raw2, self.app.project_fusion.raw2_flip)
        if self.app.project_fusion.raw2_rotation != -1:
            raw2 = cv2.rotate(raw2, self.app.project_fusion.raw2_rotation)
        if self._fusion_zomm[1] != 1:
            raw2 = cv2.resize(raw2, (int(raw2.shape[1] * self._fusion_zomm[1]), int(raw2.shape[0] * self._fusion_zomm[1])))

        raw1 = self._addAphaChannel(raw1)
        raw2 = self._addAphaChannel(raw2)

        h1, w1 = raw1.shape[:2]
        h2, w2 = raw2.shape[:2]

        if way == 0:  
            final_width = max(w1, w2)
            final_height = h1 + h2
            final_image = np.zeros((final_height, final_width, 4), dtype=np.uint8)
            final_image[0:h1, 0:w1] = raw1
            final_image[h1:h1+h2, 0:w2] = raw2
        else:  
            final_width = w1 + w2
            final_height = max(h1, h2)
            final_image = np.zeros((final_height, final_width, 4), dtype=np.uint8)
            final_image[0:h1, 0:w1] = raw1
            final_image[0:h2, w1:w1+w2] = raw2

        
        self.raw[index] = RXviewerRaw()
        self.raw[index].importRaw(self.app.current_project, cv2.cvtColor(final_image, cv2.COLOR_BGRA2BGR), str(index))
    
    def _importRawAutoSave(self, tif_files: list) -> None:
        '''Import des images depuis une liste'''
        print('importRawAutoSave')
        thread = []
        self.app.loadingBar(0)
        self.raw = [None] * len(tif_files)
        for i, tif_path in enumerate(tif_files):
            thread.append(threading.Thread(target=self._import_tif, args=(tif_path, i)))
            thread[-1].start()
            self.app.loadingBar(int(i/len(tif_files) * 100))
        for i in thread: i.join()
        self.app.loadingBar(100)
        self.app.resetLoadingBar()
        self._displayImages()

    def loadImages(self) -> None:
        '''Charge les images dans la RAN'''
        print('loadImages')
        if (self.app.current_project / 'edit').is_dir():
            # Valider l'intégrité du projet avant le chargement
            if not self.validateProjectIntegrity():
                messagebox.showerror(self.app.lang.get("error_label", "Erreur"), self.app.lang.get("project_integrity_error", "Impossible de valider l'intégrité du projet"))
                return
            
            self.app.app.title('GendALF - ' + str(self.app.current_project) + ' - Loading raw...')
            folders = list((self.app.current_project / 'edit').glob('*.png'))
            
            if not folders:
                print("Aucune image trouvée dans le projet")
                self.app.app.title('GendALF - ' + str(self.app.current_project))
                return
                
            self.raw = [None] * len(folders)
            thread = []
            self.app.loadingBar(0)
            for i, filename in enumerate(folders):
                thread.append(threading.Thread(target=self._loadImage, args=(filename, i)))
                thread[-1].start()
                self.app.loadingBar(int(i/len(folders) * 100))
            for i in thread: i.join()
            
            # Vérifier que toutes les images ont été chargées correctement
            valid_images = [img for img in self.raw if img is not None and hasattr(img, 'raw') and img.raw is not None]
            if len(valid_images) != len(folders):
                print(f"Attention: {len(folders) - len(valid_images)} images n'ont pas pu être chargées")
            
            self.app.resetLoadingBar()
            self.app.app.title('GendALF - ' + str(self.app.current_project))
            self._displayImages()
        else:
            messagebox.showerror(self.app.lang.get("error_label", "Erreur"), f"{self.app.lang.get('edit_folder_missing', 'Le dossier edit n existe pas dans le projet')} {self.app.current_project}")
    
    def _loadImage(self, filename: Path, index: int) -> None:
        '''Charge une image dans la ram'''
        self.raw[index] = RXviewerRaw()
        self.raw[index].loadRaw(self.app.current_project, filename.name)
        
        # Vérification que l'image a été chargée correctement
        if not hasattr(self.raw[index], 'raw') or self.raw[index].raw is None:
            print(f"Erreur: Image raw non chargée pour {filename.name}")
            return
            
        if not hasattr(self.raw[index], 'draw') or self.raw[index].draw is None:
            print(f"Attention: Image draw non chargée pour {filename.name}, initialisation...")
            # Initialiser l'image draw si elle n'existe pas
            self.raw[index].draw = np.array(Image.new("RGBA", (self.raw[index].raw.shape[1], self.raw[index].raw.shape[0]), (0, 0, 0, 0)))
            # Sauvegarder l'image draw vide
            cv2.imwrite(str(self.app.current_project / 'draw' / filename.name), self.raw[index].draw)
    
    def _displayImages(self):
        '''Setup l'affichage d'une image dans le canvas'''
        if self.raw and len(self.raw) > 0:
            # Trouver la première image valide
            valid_image = None
            for img in self.raw:
                if img is not None and hasattr(img, 'raw') and img.raw is not None:
                    valid_image = img
                    break
            
            if valid_image is None:
                print("Erreur: Aucune image valide trouvée")
                messagebox.showerror(self.app.lang.get("error_label", "Erreur"), self.app.lang.get("no_valid_image_in_project", "Aucune image valide trouvée dans le projet"))
                return
            
            # Calculer les coordonnées de centrage
            self.raw_coords = [
                self.app.can.winfo_width() // 2 - valid_image.raw.shape[1] // 2, 
                self.app.can.winfo_height() // 2 - valid_image.raw.shape[0] // 2
            ]
            
            # Initialiser le système de dessin
            try:
                self.app.toolsBox.draw.newDraw()
            except AttributeError as e:
                print(f"Erreur lors de l'initialisation du dessin : {e}")
                # Continuer sans le système de dessin
            
            # Afficher l'image
            self.app.displayImage()
        else:
            print("Aucune image à afficher")
            messagebox.showwarning("Attention", "Aucune image disponible dans le projet")
    
    def saveEditRaws(self, new_min: int, new_max: int) -> None:
        '''Applique le contraste sur toutes les images'''
        print('saveEditRaws')
        thread = []
        self.app.loadingBar(0)
        for i, raw in enumerate(self.raw):
            thread.append(threading.Thread(target=self._saveEditRaw, args=(raw, new_min, new_max)))
            thread[-1].start()
            self.app.loadingBar(int(i/len(self.raw) * 100))
        for i in thread: i.join()
        self.app.loadingBar(100)
        self.app.resetLoadingBar()
        self.loadImages()

    def _saveEditRaw(self, raw: RXviewerRaw, new_min: int, new_max: int) -> None:
        """Applique le contraste et enregistre l'image avec gestion d'erreurs robuste"""
        try:
            # Essayer de charger l'image depuis le dossier raw d'abord
            raw_path = self.app.current_project / 'raw' / raw.filename
            original_image = None
            
            if raw_path.exists():
                original_image = cv2.imread(str(raw_path))
                if original_image is not None and original_image.size > 0:
                    print(f"Image chargée depuis raw: {raw_path}")
                else:
                    print(f"Erreur: Impossible de lire l'image raw {raw_path}")
                    original_image = None
            
            # Si l'image raw n'est pas disponible, essayer depuis edit
            if original_image is None:
                edit_path = self.app.current_project / 'edit' / raw.filename
                if edit_path.exists():
                    original_image = cv2.imread(str(edit_path))
                    if original_image is not None and original_image.size > 0:
                        print(f"Image chargée depuis edit: {edit_path}")
                    else:
                        print(f"Erreur: Impossible de lire l'image edit {edit_path}")
                        original_image = None
                else:
                    print(f"Erreur: Fichier edit non trouvé {edit_path}")
            
            # Si aucune image n'est disponible, utiliser l'image en mémoire
            if original_image is None:
                if hasattr(raw, 'raw') and raw.raw is not None:
                    original_image = raw.raw.copy()
                    print(f"Utilisation de l'image en mémoire pour {raw.filename}")
                else:
                    print(f"Erreur: Aucune image disponible pour {raw.filename}")
                    return
            
            # Vérifications finales avant traitement OpenCV
            if original_image is None:
                print(f"Erreur: Image None pour {raw.filename}")
                return
                
            if original_image.size == 0:
                print(f"Erreur: Image vide pour {raw.filename}")
                return
                
            if len(original_image.shape) != 3 or original_image.shape[2] != 3:
                print(f"Erreur: Format d'image invalide pour {raw.filename}: {original_image.shape}")
                return
            
            # Appliquer le contraste
            gray_image = cv2.cvtColor(original_image, cv2.COLOR_BGR2GRAY)
            contrast_image = self.app.toolsBox.contrast.editContrast(gray_image, new_min, new_max)
            color_image = cv2.cvtColor(contrast_image, cv2.COLOR_GRAY2BGR)
            
            # Appliquer l'overlay si disponible
            if hasattr(raw, 'draw') and raw.draw is not None:
                final_image = self.app.toolsBox.draw.imageOverlay(color_image, raw2=raw.draw)
            else:
                final_image = color_image
            
            # Sauvegarder le résultat
            edit_output_path = self.app.current_project / 'edit' / raw.filename
            cv2.imwrite(str(edit_output_path), final_image)
            print(f"Image avec contraste sauvegardée : {edit_output_path}")
            
        except Exception as e:
            print(f"Erreur lors de l'application du contraste pour {raw.filename}: {e}")
            # En cas d'erreur, essayer de sauvegarder l'image actuelle si disponible
            if hasattr(raw, 'raw') and raw.raw is not None:
                try:
                    fallback_path = self.app.current_project / 'edit' / raw.filename
                    if raw.raw is not None and raw.raw.size > 0:
                        cv2.imwrite(str(fallback_path), raw.raw)
                        print(f"Image de fallback sauvegardée : {fallback_path}")
                    else:
                        print(f"Image de fallback invalide pour {raw.filename}")
                except Exception as e2:
                    print(f"Erreur lors de la sauvegarde de fallback : {e2}")
    
    def saveEditRawOne(self, new_min: int, new_max: int) -> None:
        '''Applique le contraste sur l'image courante seulement'''
        print('saveEditRawOne')
        if self.raw and self.app.raw_id is not None and self.app.raw_id < len(self.raw):
            current_raw = self.raw[self.app.raw_id]
            self._saveEditRaw(current_raw, new_min, new_max)
            # Recharger l'image courante pour afficher les modifications
            current_raw.loadRaw(self.app.current_project, current_raw.filename)
            self.app.displayImage()
            print(f'Contraste appliqué et sauvegardé pour l\'image {current_raw.filename}')
        else:
            print('Erreur: Aucune image courante à traiter')
    
    def saveCurrentImageState(self):
        '''Sauvegarde l'état actuel de l'image courante dans le dossier edit'''
        print('saveCurrentImageState')
        if self.raw and self.app.raw_id is not None and self.app.raw_id < len(self.raw):
            current_raw = self.raw[self.app.raw_id]
            try:
                # Sauvegarder l'image courante avec toutes ses modifications
                edit_path = self.app.current_project / 'edit' / current_raw.filename
                cv2.imwrite(str(edit_path), current_raw.raw)
                print(f'État de l\'image sauvegardé : {edit_path}')
            except Exception as e:
                print(f'Erreur lors de la sauvegarde de l\'état de l\'image : {e}')
        else:
            print('Erreur: Aucune image courante à sauvegarder')
    
    def saveCurrentImageStateIfModified(self):
        '''Sauvegarde l'état de l'image courante seulement si elle diffère du fichier edit'''
        print('saveCurrentImageStateIfModified')
        if self.raw and self.app.raw_id is not None and self.app.raw_id < len(self.raw):
            current_raw = self.raw[self.app.raw_id]
            try:
                edit_path = self.app.current_project / 'edit' / current_raw.filename
                
                # Vérifier si le fichier edit existe
                if edit_path.exists():
                    # Charger l'image actuelle du fichier edit
                    edit_img = cv2.imread(str(edit_path), cv2.IMREAD_UNCHANGED)
                    
                    # Comparer avec l'image en mémoire
                    if edit_img is not None:
                        # Calculer la différence
                        if edit_img.shape == current_raw.raw.shape:
                            diff = cv2.absdiff(edit_img, current_raw.raw)
                            total_diff = np.sum(diff)
                            
                            # Si l'image a été modifiée, la sauvegarder
                            if total_diff > 0:
                                cv2.imwrite(str(edit_path), current_raw.raw)
                                print(f'Image modifiée sauvegardée : {edit_path} (différence: {total_diff})')
                            else:
                                print(f'Image inchangée, pas de sauvegarde nécessaire : {edit_path}')
                        else:
                            # Tailles différentes, sauvegarder
                            cv2.imwrite(str(edit_path), current_raw.raw)
                            print(f'Image redimensionnée sauvegardée : {edit_path}')
                    else:
                        # Impossible de charger l'image edit, sauvegarder
                        cv2.imwrite(str(edit_path), current_raw.raw)
                        print(f'Image edit corrompue, sauvegardée : {edit_path}')
                else:
                    # Fichier edit n'existe pas, le créer
                    cv2.imwrite(str(edit_path), current_raw.raw)
                    print(f'Nouvel fichier edit créé : {edit_path}')
                    
            except Exception as e:
                print(f'Erreur lors de la sauvegarde conditionnelle : {e}')
        else:
            print('Erreur: Aucune image courante à sauvegarder')
    
    def checkAndFixProjectImages(self):
        '''Vérifie et corrige les images manquantes dans le projet'''
        print('checkAndFixProjectImages')
        if not self.app.current_project:
            return
        
        edit_folder = self.app.current_project / 'edit'
        draw_folder = self.app.current_project / 'draw'
        raw_folder = self.app.current_project / 'raw'
        
        # Créer les dossiers s'ils n'existent pas
        draw_folder.mkdir(exist_ok=True)
        
        # Vérifier chaque image dans edit
        for edit_file in edit_folder.glob('*.png'):
            draw_file = draw_folder / edit_file.name
            
            # Si l'image draw n'existe pas, la créer
            if not draw_file.exists():
                print(f"Création de l'image draw manquante : {edit_file.name}")
                # Charger l'image edit pour connaître ses dimensions
                img = cv2.imread(str(edit_file), cv2.IMREAD_UNCHANGED)
                if img is not None:
                    # Créer une image draw vide transparente
                    draw_img = np.array(Image.new("RGBA", (img.shape[1], img.shape[0]), (0, 0, 0, 0)))
                    cv2.imwrite(str(draw_file), draw_img)
                    print(f"Image draw créée : {draw_file}")
                else:
                    print(f"Erreur: Impossible de lire l'image {edit_file}")
        
        print("Vérification et correction terminée")
        
    def validateProjectIntegrity(self):
        '''Valide l'intégrité du projet et corrige les problèmes'''
        print('validateProjectIntegrity')
        if not self.app.current_project:
            return False
        
        try:
            # Vérifier et corriger les images manquantes
            self.checkAndFixProjectImages()
            
            # Vérifier que tous les dossiers existent
            required_folders = ['raw', 'edit', 'draw']
            for folder_name in required_folders:
                folder_path = self.app.current_project / folder_name
                if not folder_path.exists():
                    print(f"Création du dossier manquant : {folder_name}")
                    folder_path.mkdir(parents=True, exist_ok=True)
            
            return True
            
        except Exception as e:
            print(f"Erreur lors de la validation de l'intégrité du projet : {e}")
            return False
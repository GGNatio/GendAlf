import tkinter as tk
from tkinter import messagebox, colorchooser, filedialog
from PIL import Image, ImageTk
from pathlib import Path
import cv2
import json
import shutil
from datetime import datetime   
import os


from RXmodule.RXviewerLabels import RXviewerLabels
from RXmodule.RXviewerToolsBox import RXviewerToolsBox
from RXmodule.RXviewerRaws import RXviewerRaws
from RXmodule.RXviewerProjectFusion import RXviewerProjectFusion
from RXmodule.RXviewerSecondary import RXviewerSecondary
from RXmodule.RXviewerSync import RXviewerSync  
from RXmodule.RXviewerVia import RXviewerVia
from RXmodule.RXviewerPathTracking import RXviewerPathTracking
from RXmodule.RXviewerSave import RXviewerSaveManager  
from RXmodule.RXviewerReport import RXviewerReport
class ProjectView:
    def __init__(self, parent: tk.Frame, bgColor: str):
        self.container = tk.Frame(parent)
        self.container.pack(side='left', expand=True, fill='both')

        self.frame = tk.Frame(self.container)
        self.frame.pack(side='top', expand=True, fill='both')

        self.canvas = tk.Canvas(self.frame, bg=bgColor)
        self.canvas.pack(expand=True, fill='both', side='left')

        self.label_frame = tk.Frame(self.frame, width=200, bg='white')
        self.label_frame.pack(side='right', fill='y')

        
        self.button_bar = tk.Frame(self.container)
        self.button_bar.pack(side='bottom', pady=5)

        self.raw = None
        self.labels = None
        self.project_path = None
        self.raw_id = 0
        self.tk_image = None  
        self._cached_pathtracking_image = None
        self._cached_pathtracking_id = None
        self.canvas.bind("<Enter>", lambda e: self._setActive(True))
        self.canvas.bind("<Leave>", lambda e: self._setActive(False))
        self.canvas.bind_all("<MouseWheel>", self._onScroll)  
        self.canvas.bind_all("<Button-4>", self._onScroll)    
        self.canvas.bind_all("<Button-5>", self._onScroll)   

        self._active = False
        self._scrolling = False  # Flag pour éviter les scrolls multiples
    def _setActive(self, value: bool):
        self._active = value

    def _onScroll(self, event):
        if not self._active or self._scrolling:
            return
        self._scrolling = True
        try:
            delta = 0
            if hasattr(event, 'delta'):  
                delta = event.delta
            elif event.num == 4:  
                delta = 120
            elif event.num == 5:  
                delta = -120

            if hasattr(self, 'scroll_callback'):
                self.scroll_callback(self, delta)
        finally:
            self._scrolling = False




class RXviewer:
    def __init__(self) -> None:
        self.app = tk.Tk()
        self.app.protocol("WM_DELETE_WINDOW", self.on_close)

        # Rediriger stdout/stderr vers un buffer pour capturer tout le terminal
        import io, sys
        self._stdout_buffer = io.StringIO()
        sys.stdout = self._stdout_buffer
        sys.stderr = self._stdout_buffer

        # Créer le dossier de logs au premier lancement si besoin (compatible PyInstaller)
        if hasattr(sys, '_MEIPASS'):
            base_dir = Path(sys._MEIPASS)
        else:
            base_dir = Path(__file__).resolve().parent
        logs_dir = base_dir / "logs"
        try:
            logs_dir.mkdir(parents=True, exist_ok=True)
        except Exception:
            # Fallback dans le dossier courant si besoin
            logs_dir = Path.cwd() / "logs"
            logs_dir.mkdir(parents=True, exist_ok=True)

        self.app.state("zoomed")
        self.app.title('GendALF')
        self.app.geometry('1200x800')
        (Path.home() / "Documents/RXViwer/project").mkdir(parents=True, exist_ok=True)
        self.option = self.openPreference()
        self.lang = self.openLang(self.option['language'])

        
        self.can_and_labels = tk.Frame(self.app)
        self.can_and_labels.pack(fill='both', expand=True, side='top')

        
        self.can = tk.Canvas(self.can_and_labels)
        self.can.config(background=(self.option['bgColor']))
        self.can.pack(fill='both', expand=True, side='left')

        self._variable()
        self._setupMenu()
        self._setupLabels()
        self._setupPathtrackingPanel()
        self._setupLoadingBar()
        self._setupButtons()
        
        # Vérifier automatiquement les mises à jour au démarrage
        if hasattr(self, 'save_manager'):
            self.save_manager.check_updates_on_startup()

        self.app.mainloop()
        
        # Sauvegarder le projet avant de fermer (sans appeler updateMenuStates)
        if self.current_project:
            self.saveProjectFile(self.current_project)
        
        PREF_PATH = Path(__file__).resolve().parent / "asset" / "preference.json"
        try:
            with open(PREF_PATH, 'r', encoding='utf-8') as file:
                prefs = json.load(file)
        except Exception:
            prefs = {}
        prefs['bgColor'] = self.option.get('bgColor', prefs.get('bgColor', '#454545'))
        prefs['language'] = self.option.get('language', prefs.get('language', 'francais'))
        with open(PREF_PATH, 'w', encoding='utf-8') as file:
            json.dump(prefs, file, indent=2, ensure_ascii=False)
    

    def openDoubleProjectEmbedded(self):
        '''Permet de charger deux projets dans la même fenêtre, en les affichant côte à côte'''
        win = tk.Toplevel(self.app)
        win.title(self.lang.get("open_two_projects", "Ouvrir deux projets"))
        win.geometry("500x240")
        win.grab_set()

        path1_var = tk.StringVar()
        path2_var = tk.StringVar()

        def browse(var):
            path = filedialog.askdirectory(initialdir=Path.home() / 'Documents/RXViwer/project/')
            if path:
                var.set(path)

        def load_both():
            p1 = Path(path1_var.get())
            p2 = Path(path2_var.get())
            if not (p1 / 'project.json').is_file() or not (p2 / 'project.json').is_file():
                messagebox.showerror(self.lang.get("error_label", "Erreur"), self.lang.get("two_projects_must_be_valid", "Les deux projets doivent être valides."))
                return

            win.destroy()
            self.loadDoubleProject(p1, p2)

        tk.Label(win, text=self.lang.get("project1", "Projet 1")).pack(pady=(10, 0))
        tk.Entry(win, textvariable=path1_var, width=60).pack()
        tk.Button(win, text=self.lang.get("browse", "Parcourir"), command=lambda: browse(path1_var)).pack(pady=5)

        tk.Label(win, text=self.lang.get("project2", "Projet 2")).pack(pady=(10, 0))
        tk.Entry(win, textvariable=path2_var, width=60).pack()
        tk.Button(win, text=self.lang.get("browse", "Parcourir"), command=lambda: browse(path2_var)).pack(pady=5)

        tk.Button(win, text=self.lang.get("open_both", "Ouvrir les deux"), command=load_both).pack(pady=15)
    
    def loadDoubleProject(self, path1: Path, path2: Path):
        '''Charge les deux projets dans des frames côte à côte avec scroll centralisé'''

        for widget in self.can_and_labels.winfo_children():
            widget.destroy()

        self.project_left = ProjectView(self.can_and_labels, self.option["bgColor"])
        self.project_right = ProjectView(self.can_and_labels, self.option["bgColor"])

        self.loadProjectInView(self.project_left, path1)
        self.loadProjectInView(self.project_right, path2)

        
        self.app.bind_all("<MouseWheel>", self.globalScrollHandler)

    def globalScrollHandler(self, event):
        widget = event.widget.winfo_containing(event.x_root, event.y_root)
        if self.project_left.canvas == widget or self.project_left.canvas.winfo_containing(event.x_root, event.y_root):
            self.scrollInView(self.project_left, event.delta if hasattr(event, 'delta') else (120 if event.num == 4 else -120))
        elif self.project_right.canvas == widget or self.project_right.canvas.winfo_containing(event.x_root, event.y_root):
            self.scrollInView(self.project_right, event.delta if hasattr(event, 'delta') else (120 if event.num == 4 else -120))



    def setupProjectButtons(self, view: ProjectView):
        def updateLabel():
            total = len(view.raw.raw) if view.raw.raw else 0
            view.counter_label.config(text=f"{view.raw_id + 1}/{total}" if total else "0/0")

        def navig(direction):
            if not view.raw.raw:
                return
            
            # Sauvegarder l'image actuelle avant de changer de couche
            if hasattr(view, 'raw') and hasattr(view.raw, 'saveCurrentImageStateIfModified'):
                view.raw.saveCurrentImageStateIfModified()
            
            new_id = view.raw_id + direction
            if 0 <= new_id < len(view.raw.raw):
                view.raw_id = new_id
                self.displayImageInView(view)
                updateLabel()

        def reset():
            if view.raw.raw:
                view.raw.raw_coords = [
                    view.canvas.winfo_width() // 2 - view.raw.raw[view.raw_id].raw.shape[1] // 2,
                    view.canvas.winfo_height() // 2 - view.raw.raw[view.raw_id].raw.shape[0] // 2
                ]
                self.displayImageInView(view)
                updateLabel()  # Mise à jour du compteur après reset

        bar = view.button_bar
        tk.Button(bar, text='<<', command=lambda: navig(-view.raw_id)).pack(side='left', padx=2)
        tk.Button(bar, text='<', command=lambda: navig(-1)).pack(side='left', padx=2)
        tk.Button(bar, text='♦', command=reset).pack(side='left', padx=2)
        tk.Button(bar, text='>', command=lambda: navig(1)).pack(side='left', padx=2)
        tk.Button(bar, text='>>', command=lambda: navig(len(view.raw.raw) - 1 - view.raw_id)).pack(side='left', padx=2)

        tk.Button(bar, text=self.lang.get("reset", "reset"), command=reset).pack(side='left', padx=2)
        view.counter_label = tk.Label(bar, text="0/0")
        view.counter_label.pack(side='left', padx=5)

        updateLabel()

    def loadProjectInView(self, view, path: Path):
        with open(path / 'project.json', 'r', encoding='utf-8') as file:
            project_file = json.load(file)

        view.raw = RXviewerRaws(self)
        view.labels = RXviewerLabels(self)
        view.project_path = path
        view.raw.loadImagesFromPath(path)
        view.raw_id = 0

        if not view.raw.raw:
            messagebox.showwarning("⚠️", f"{self.lang.get('no_image_found_project', 'Aucune image trouvée dans le projet')} : {path.name}")
            return

        
        view.raw.raw_coords = [
            view.canvas.winfo_width() // 2 - view.raw.raw[view.raw_id].raw.shape[1] // 2,
            view.canvas.winfo_height() // 2 - view.raw.raw[view.raw_id].raw.shape[0] // 2
        ]

        view.labels.addLabels(project_file['labels'])
        view.labels.setupLabels(view.label_frame)
        self.displayImageInView(view)
        self.setupProjectButtons(view)

    def scrollInView(self, view: 'ProjectView', delta: int):
        if not view.raw.raw:
            return

        # Sauvegarder l'image actuelle avant de changer de couche
        if hasattr(view, 'raw') and hasattr(view.raw, 'saveCurrentImageStateIfModified'):
            view.raw.saveCurrentImageStateIfModified()

        new_id = view.raw_id + (1 if delta < 0 else -1)
        if 0 <= new_id < len(view.raw.raw):
            view.raw_id = new_id
            # Optimisation : ne pas recharger l'image si l'id n'a pas changé
            self._updateImageAndCounter(view)

    def _updateImageAndCounter(self, view):
        # Affiche l'image et met à jour le compteur, en optimisant l'affichage des pathtrackings
        if not view.raw or not view.raw.raw:
            return
        image = view.raw.raw[view.raw_id].raw
        use_pathtracking = hasattr(self, 'via_path_tracking') and hasattr(self.via_path_tracking, 'pathtrackings') and self.via_path_tracking.pathtrackings
        # Utiliser le cache si possible
        if use_pathtracking:
            if view._cached_pathtracking_id == view.raw_id and view._cached_pathtracking_image is not None:
                image_to_show = view._cached_pathtracking_image
            else:
                try:
                    image_to_show = self.drawPathtrackingsFromLayer(image, view.raw_id)
                    view._cached_pathtracking_image = image_to_show
                    view._cached_pathtracking_id = view.raw_id
                except Exception:
                    image_to_show = image
        else:
            image_to_show = image
            view._cached_pathtracking_image = None
            view._cached_pathtracking_id = None
        image_pil = Image.fromarray(image_to_show)
        view.tk_image = ImageTk.PhotoImage(image_pil)
        view.canvas.delete('all')
        view.canvas.create_image(0, 0, anchor=tk.NW, image=view.tk_image)
        if hasattr(view, 'labels') and hasattr(view.labels, 'moveLabels'):
            view.labels.moveLabels((image.shape[1], image.shape[0]), view.raw.raw_coords)
        total = len(view.raw.raw) if view.raw.raw else 0
        if hasattr(view, 'counter_label'):
            view.counter_label.config(text=f"{view.raw_id + 1}/{total}" if total else "0/0")

    def displayImageInView(self, view):
        self._updateImageAndCounter(view)
        



    
    def hideLabelsPanel(self):
        '''Masque la bande blanche des labels'''
        if hasattr(self, 'labels_frame_container') and self.labels_frame_container.winfo_ismapped():
            self.labels_frame_container.pack_forget()

    def showLabelsPanel(self):
        '''Affiche la bande blanche des labels'''
        if hasattr(self, 'labels_frame_container') and not self.labels_frame_container.winfo_ismapped():
            self.labels_frame_container.pack(side='right', fill='y')

    def hidePathtrackingPanel(self):
        '''Masque le panneau des pathtrackings'''
        if hasattr(self, 'pathtracking_frame_container') and self.pathtracking_frame_container.winfo_ismapped():
            self.pathtracking_frame_container.pack_forget()

    def showPathtrackingPanel(self):
        '''Affiche le panneau des pathtrackings'''
        if hasattr(self, 'pathtracking_frame_container') and not self.pathtracking_frame_container.winfo_ismapped():
            self.pathtracking_frame_container.pack(side='left', fill='y', before=self.can)

    def _setupLabels(self) -> None:
        '''Préparation de la zone pour accueillir les marqueurs'''
        self.labels_frame_container = tk.Frame(self.can_and_labels, bg='white')
        self.labels_frame_container.pack(side='right', fill='y')
        self.labels_canvas = tk.Canvas(self.labels_frame_container, bg='white', width=0)
        self.labels_canvas.pack(side='left', fill='y')
        
        scrollbar = tk.Scrollbar(self.labels_frame_container, orient="vertical", command=self.labels_canvas.yview)
        scrollbar.pack(side='right', fill='y')
        self.labels_canvas.configure(yscrollcommand=scrollbar.set)
        self.labels_frame = tk.Frame(self.labels_canvas, bg='white')
        self.labels_canvas.create_window((0, 0), window=self.labels_frame, anchor='nw')
        self.labels_frame.bind("<Configure>", self.onFrameConfigure)

    def _setupPathtrackingPanel(self) -> None:
        '''Préparation de la zone pour accueillir les pathtrackings'''
        self.pathtracking_frame_container = tk.Frame(self.can_and_labels, bg='#f0f0f0', width=250)
        self.pathtracking_frame_container.pack_propagate(False)  # Garder la largeur fixe
        
        # Titre du panneau
        title_frame = tk.Frame(self.pathtracking_frame_container, bg='#e0e0e0', height=30)
        title_frame.pack(fill='x')
        title_frame.pack_propagate(False)
        
        tk.Label(title_frame, text="Pathtrackings", font=("Arial", 12, "bold"), 
                bg='#e0e0e0').pack(pady=5)
        
        # Canvas avec scrollbar pour le contenu
        self.pathtracking_canvas = tk.Canvas(self.pathtracking_frame_container, bg='#f0f0f0')
        self.pathtracking_canvas.pack(side='left', fill='both', expand=True)
        
        pathtracking_scrollbar = tk.Scrollbar(self.pathtracking_frame_container, orient="vertical", 
                                            command=self.pathtracking_canvas.yview)
        pathtracking_scrollbar.pack(side='right', fill='y')
        self.pathtracking_canvas.configure(yscrollcommand=pathtracking_scrollbar.set)
        
        self.pathtracking_frame = tk.Frame(self.pathtracking_canvas, bg='#f0f0f0')
        self.pathtracking_canvas.create_window((0, 0), window=self.pathtracking_frame, anchor='nw')
        self.pathtracking_frame.bind("<Configure>", self.onPathtrackingFrameConfigure)
        
        # Masquer le panneau par défaut
        self.pathtracking_frame_container.pack_forget()

    def onPathtrackingFrameConfigure(self, event: tk.Event):
        '''Met à jour la zone de défilement du panneau pathtracking'''
        self.pathtracking_canvas.configure(scrollregion=self.pathtracking_canvas.bbox("all"))
    
    def onFrameConfigure(self, event: tk.Event):
        self.labels_canvas.configure(scrollregion=self.labels_canvas.bbox("all"))
    def rebindLabelMove(self):
        """(Ré)applique les binds pour déplacer les labels sur le canvas, peu importe l'outil/curseur actif."""
        # On suppose que self.labels est une instance de RXviewerLabels
        # et que les méthodes _start_move_marker, _move_marker, _end_move_marker existent
        self.can.bind("<Control-Shift-Button-1>", self.labels._start_move_marker)
        self.can.bind("<B1-Motion>", self.labels._move_marker)
        self.can.bind("<ButtonRelease-1>", self.labels._end_move_marker)
    def _variable(self) -> None:
       
        self.current_project = None
       
        self.raw = RXviewerRaws(self)
       
        self.labels = RXviewerLabels(self)
        
       
        self.toolsBox = RXviewerToolsBox(self)
        self.via_calibration = RXviewerVia(self)
        self.via_path_tracking = RXviewerPathTracking(self)
        self.second_viewer = None
        
        # Initialiser la liste des vias du projet
        self.project_vias = []
        
        # Initialiser le gestionnaire de sauvegarde et mise à jour
        self.save_manager = RXviewerSaveManager(self)

    def openLang(self, lang: str = "francais") -> dict:
        '''Ouvre le fichier de langue'''
        try:
            CURRENT_DIR = Path(__file__).resolve().parent
            LANG_DIR = CURRENT_DIR / "asset" / "lang"
            with open(LANG_DIR / f"{lang}.json", 'r', encoding='utf-8') as file:
                return json.load(file)
        except Exception as e:
            # Utiliser un message d'erreur générique si self.lang n'est pas encore initialisé
            try:
                messagebox.showerror(self.lang.get("error_label", "Error"), f"{self.lang.get('unable_to_read_language_file', 'Unable to read language file')} {lang}.\nError: {e}")
                return {"err": "Error", "err2": self.lang.get("please_open_or_create_project", "Please open or create a project")}
            except Exception:
                messagebox.showerror("Erreur", f"Impossible de lire le fichier de langue {lang}.json.\nError: {e}")
                return {"err": "Error", "err2": "Veuillez ouvrir ou créer un projet"}
    
    def openPreference(self) -> dict:
        '''Ouvre le fichier de préférence avec la langue et la couleur de bg'''
        CURRENT_DIR = Path(__file__).resolve().parent
        PREF_DIR = CURRENT_DIR / "asset"
        try:
            with open(PREF_DIR / "preference.json", 'r', encoding='utf-8') as file:
                return json.load(file)
        except Exception as e:
            # Utiliser un message d'erreur générique si self.lang n'est pas encore initialisé
            try:
                messagebox.showerror(self.lang.get("error_label", "Error"), f"{self.lang.get('unable_to_read_preference_file', 'Unable to read file preference.json')}.\nError: {e}")
            except Exception:
                messagebox.showerror("Erreur", f"Impossible de lire le fichier preference.json.\nError: {e}")
            return {"bgColor": "#454545", "language": "francais"}

    def _setupMenu(self) -> None:
        '''Menu déroulant'''
        menu_bar = tk.Menu(self.app)

        
        self.projet_menu = tk.Menu(menu_bar, tearoff=0)
        self.projet_menu.add_command(label=self.lang['new_project'], accelerator="Ctrl+N", command=self.newProject)
        self.projet_menu.add_command(label=self.lang['open_project'], accelerator="Ctrl+O", command=self.searchProject)
        
        recent_menu = tk.Menu(self.projet_menu, tearoff=0)
        self._openRecent(recent_menu)
        self.projet_menu.add_cascade(label=self.lang['open_recent'], menu=recent_menu)
        self.projet_menu.add_separator()
        
        # Ajouter le bouton de suppression de projet (toujours activé)
        self.delete_project_menu_index = self.projet_menu.index('end') + 1
        self.projet_menu.add_command(label=self.lang.get('delete_project', 'Supprimer un projet'), 
                                   command=self.deleteProject, 
                                   state='normal')
        self.projet_menu.add_separator()
        self.projet_menu.add_command(label=self.lang['project_fusion'], command=self.fusionProject)
        self.projet_menu.add_command(label=self.lang['double_project'], command=self.doubleProject)
        self.projet_menu.add_command(label=self.lang['synchro_project'], command=self.synchroProject)

        self.projet_menu.add_separator()
        self.projet_menu.add_command(label=self.lang['import_raw_auto'], accelerator="Ctrl+I", command=self.raw.importRawAuto)
        self.projet_menu.add_command(label=self.lang['import_raw_manual'], accelerator="Ctrl+M", command=self.raw.importRawManual)
        self.projet_menu.add_separator()
        # Ajouter le bouton d'étalonnage des vias
        self.projet_menu.add_command(label=self.lang['calibrate_vias'], command=self.calibrateVias, state='disabled')
        self.calibrate_vias_menu_index = self.projet_menu.index('end')
        
        # Ajouter le bouton pour afficher/masquer les vias
        self.show_vias_var = tk.BooleanVar(value=False)
        self.projet_menu.add_checkbutton(label=self.lang.get('show_vias', 'Afficher les vias'), 
                                       variable=self.show_vias_var, 
                                       command=self.toggleShowVias, 
                                       state='disabled')
        self.show_vias_menu_index = self.projet_menu.index('end')
        self.projet_menu.add_separator()
        self.projet_menu.add_command(label=self.lang['quit'], command=self.app.quit)
        menu_bar.add_cascade(label=self.lang['project'], menu=self.projet_menu)

        
        toolsBox_menu = tk.Menu(menu_bar, tearoff=0)
        toolsBox_menu.add_command(label=self.lang['open_toolsbox'], command=self.toolsBox.toolsBox)
        menu_bar.add_cascade(label=self.lang['tools_box'], menu=toolsBox_menu)

        
        settings_menu = tk.Menu(menu_bar, tearoff=0)
        settings_menu.add_command(label=self.lang['background_color'], command=self.backgroundColor)
        settings_menu.add_command(label=self.lang['language'], command=self.language)
        menu_bar.add_cascade(label=self.lang['settings'], menu=settings_menu)

        
        help_menu = tk.Menu(menu_bar, tearoff=0)
        help_menu.add_command(label=f"❔ {self.lang.get('help_title', 'Raccourcis clavier')} (F1)", command=self.showShortcutsHelp)
        help_menu.add_separator()
        help_menu.add_command(label="Documentation", command=self.showDocumentation)

        menu_bar.add_cascade(label=self.lang.get("help_menu", "Aide"), menu=help_menu)

        
        about_menu = tk.Menu(menu_bar, tearoff=0)
        about_menu.add_command(label=self.lang.get('check_updates', 'Rechercher les mises à jour'), command=self.checkForUpdates)
        about_menu.add_command(label="Mise à jour automatique", command=self.run_update_online)
        about_menu.add_command(label="Mise à jour locale (ZIP)", command=self.run_update_local)
        about_menu.add_separator()
        
        about_menu.add_command(label="Signaler un bug", command=lambda: RXviewerReport(self.app))
        about_menu.add_separator()
        about_menu.add_command(label=self.lang.get('about_info', 'Informations'), command=self.showAboutInfo)
        


        menu_bar.add_cascade(label=self.lang.get("about_menu", "À propos"), menu=about_menu)

        self.app.bind("<Control-n>",self.newProject)
        self.app.bind("<Control-o>",self.searchProject)
        self.app.bind("<Control-i>",self.raw.importRawAuto)
        self.app.bind("<Control-m>",self.raw.importRawManual)
        self.app.bind("<Home>", lambda e: self.firstRaw())
        self.app.bind("<End>", lambda e: self.lastRaw())
        self.app.bind("<F1>", lambda e: self.showShortcutsHelp())

        

        
        self.app.bind("<Control-Shift-O>", lambda e: self.doubleProject())
        self.app.bind("<Control-f>", lambda e: self.fusionProject())
        self.app.bind("<Control-s>", lambda e: self.saveProjectFile(self.current_project) if self.current_project else None)
        self.app.bind("<Control-q>", lambda e: self.app.quit())

      
        self.app.bind("<Control-b>", lambda e: self.backgroundColor())
        self.app.bind("<Control-l>", lambda e: self.language())
        self.app.bind("t", lambda e: self.toolsBox.toolsBox())
        
        

        self.app.config(menu=menu_bar)
    def run_update_online(self):
        """Lance update.exe en mode online (forcé)"""
        import subprocess
        import sys
        import os
        from pathlib import Path
        exe_dir = Path(os.path.dirname(os.path.abspath(sys.argv[0])))
        exe_path = exe_dir / "update.exe"
        if not exe_path.exists():
            from tkinter import messagebox
            messagebox.showerror("Erreur", f"update.exe introuvable dans le dossier : {exe_dir}")
            return
        try:
            subprocess.Popen([str(exe_path), "--online"])
        except Exception as e:
            from tkinter import messagebox
            messagebox.showerror("Erreur", f"Impossible de lancer la mise à jour automatique : {e}")

    def run_update_local(self):
        """Lance update.exe en mode local (forcé)"""
        import subprocess
        import sys
        import os
        from pathlib import Path
        exe_dir = Path(os.path.dirname(os.path.abspath(sys.argv[0])))
        exe_path = exe_dir / "update.exe"
        if not exe_path.exists():
            from tkinter import messagebox
            messagebox.showerror("Erreur", f"update.exe introuvable dans le dossier : {exe_dir}")
            return
        try:
            subprocess.Popen([str(exe_path), "--local"])
        except Exception as e:
            from tkinter import messagebox
            messagebox.showerror("Erreur", f"Impossible de lancer la mise à jour locale : {e}")
        
        
        # Initialiser l'état des menus
        self.updateMenuStates()
    
    def _openRecent(self, menu: tk.Menu) -> None:
        '''Ouvre le fichier qui contient les projets ouverts récemment'''
        if Path("asset/recent").is_file():
           
            with open("asset/recent", 'r') as file:
                self.recent = file.read().split('\n')
            if self.recent != ['']:
                
                for path in self.recent:
                    
                    if Path(path).exists():
                       
                        menu.add_command(label=path.replace(str(Path.home() / "Documents/RXViwer/project") + '\\', ''), command=lambda p=path: self.openProject(Path(p)))
                    else:
                       
                        self.recent.remove(path)
                return
        self.recent = []
        
        menu.add_command(label=self.lang['no_recent_project'], activebackground="SystemButtonFace", activeforeground="SystemButtonText")
    
    def _setupLoadingBar(self) -> None:
        '''Barre de chargement'''
        self._loading_bar = tk.Frame(self.app)
        self._loading_bar.pack(fill='x')
        
        
        tk.Label(self._loading_bar, text='', width=10).pack(side='left', padx=5)
        
        tk.Label(self._loading_bar).pack(side='left', padx=(0, 5))
    
    def _setupButtons(self) -> None:
        '''Place les boutons de navigation'''
        self._buttons_frame = tk.Frame(self.app)
        self._buttons_frame.pack(side='bottom', pady=(5, 5), padx=10, fill='x')

       
        self._buttons_frame.columnconfigure(0, weight=1)
        self._buttons_frame.columnconfigure(1, weight=1)
        self._buttons_frame.columnconfigure(2, weight=1)
        self._buttons_frame.columnconfigure(3, weight=1)
        self._buttons_frame.columnconfigure(4, weight=1)

        tk.Button(self._buttons_frame, text='<<', command=self.firstRaw, font=("Helvetica", 16), height=1, width=10).grid(column=0, row=0, padx=2, sticky='ew')
        tk.Button(self._buttons_frame, text='<', command=lambda: self.navigRaw(-1), font=("Helvetica", 16), height=1, width=10).grid(column=1, row=0, padx=2, sticky='ew')
        tk.Button(self._buttons_frame, text='♦', command=self.resetRaw, font=("Helvetica", 16), height=1, width=10).grid(column=2, row=0, padx=2, sticky='ew')
       
        tk.Button(self._buttons_frame, text='>', command=lambda: self.navigRaw(1), font=("Helvetica", 16), height=1, width=10).grid(column=3, row=0, padx=2, sticky='ew')
        tk.Button(self._buttons_frame, text='>>', command=self.lastRaw, font=("Helvetica", 16), height=1, width=10).grid(column=4, row=0, padx=2, sticky='ew')
        tk.Button(self._buttons_frame, text='reset', command=lambda: self.restoreRaw(), font=("Helvetica", 16), height=1, width=10).grid(column=5, row=0, padx=2, sticky='ew')

        self.counter_label = tk.Label(self._buttons_frame, text='0/0', font=("Helvetica", 16), height=1, width=10)
        self.counter_label.grid(column=6, row=0, padx=2, sticky='ew')
    
    def addRecent(self, path: str):
        self.recent.insert(0, path)
        self.recent = list(dict.fromkeys(self.recent))  
        recent_path = Path("asset/recent")

        
        recent_path.parent.mkdir(parents=True, exist_ok=True)

        
        recent_path.write_text('\n'.join(self.recent), encoding='utf-8')

    def restoreRaw(self) -> None:
        '''Recharge l’image originale depuis le fichier disque'''

        if not self.current_project or not self.project_file:
            messagebox.showwarning("⚠️", self.lang.get("no_project_open", "Aucun projet n'est ouvert."))
            return

        try:
            
            filename = self.raw.raw[self.raw_id].filename  
            raw_path = self.current_project / "raw" / filename

            if raw_path.exists():
                raw_image = cv2.imread(str(raw_path), cv2.IMREAD_UNCHANGED)
                self.raw.raw[self.raw_id].raw = raw_image
                self.resetRaw()
            else:
                messagebox.showerror(self.lang.get("error_label", "Erreur"), f"{self.lang.get('image_not_found', 'Image introuvable')} : {raw_path}")
        except Exception as e:
            error_msg = self.lang.get('image_restore_failed', 'Échec de la réinitialisation de l\'image')
            messagebox.showerror(self.lang.get("error_label", "Erreur"), f"{error_msg}.\n\n{e}")


    def _setupBind(self) -> None:
        '''Setup les binds'''

        self.can.bind("<Button-3>", self.toolsBox._startMove)
        self.can.bind("<B3-Motion>", self.toolsBox._doMove)
        self.app.bind("<Control-Up>", lambda e: self.moveImageWithArrow(0, -20))
        self.app.bind("<Control-Down>", lambda e: self.moveImageWithArrow(0, 20))
        self.app.bind("<Control-Left>", lambda e: self.moveImageWithArrow(-20, 0))
        self.app.bind("<Control-Right>", lambda e: self.moveImageWithArrow(20, 0))

        self.can.bind("<Control-MouseWheel>", self.toolsBox.do_zoom)
        self.app.bind("<MouseWheel>", self._wheelNext)
        self.app.bind('<Left>', lambda event: self.navigRaw(-1))
        self.app.bind('<Right>', lambda event: self.navigRaw(1))
        self.app.bind("<Control-Shift-r>", lambda e: self.resetRaw())
        self.app.bind("<Control-r>", lambda e: self.restoreRaw())
        self.app.bind("z", lambda e: self.toolsBox.toolsBox_switch('colorPicker'))
        self.app.bind("m", lambda e: self.toolsBox.toolsBox_switch('move'))
        self.app.bind("p", lambda e: self.toolsBox.toolsBox_switch('pencil'))
        self.app.bind("b", lambda e: self.toolsBox.toolsBox_switch('bucketFill'))
        self.app.bind("t", lambda e: self.toolsBox.toolsBox_switch('text'))
        self.app.bind("f", lambda e: self.toolsBox.toolsBox_switch('fuzzySelect'))
        self.app.bind("r", lambda e: self.toolsBox.toolsBox_switch('track'))
        
        self.app.bind("<Control-z>", lambda e: self.smart_undo())
        self.app.bind_all("<Control-y>", self.toolsBox.draw.redo)
        self.app.bind("<Alt-z>", lambda e: self.undo_pathtracking() if hasattr(self, 'via_path_tracking') else None)

        # (Ré)appliquer les binds pour le déplacement des labels
        self.rebindLabelMove()
        
    def moveImageWithArrow(self, dx: int, dy: int):
        '''Déplace l’image zoomée dans le canvas'''
        if not self.raw.raw:
            return
        self.raw.raw_coords[0] += dx
        self.raw.raw_coords[1] += dy
        self.displayImage()

    def showShortcutsHelp(self):
        help_win = tk.Toplevel(self.app)
        help_win.title(self.lang.get("help_title", "Aide - Raccourcis clavier"))
        help_win.geometry("600x400")
        help_win.grab_set()

        shortcuts = [
            (self.lang.get("help_image_navigation", "🖼️ Navigation d'image"), ""),
            ("← / →", self.lang.get("help_prev_next_image", "Image précédente / suivante")),
            ("Home", self.lang.get("help_first_image", "Première image")),
            ("End", self.lang.get("help_last_image", "Dernière image")),
            ("Ctrl + R", self.lang.get("help_reset_image", "Réinitialiser l'image")),
            ("Ctrl + Maj + R", self.lang.get("help_restore_from_disk", "Restaurer depuis le disque")),
            ("Ctrl + + / -", self.lang.get("help_zoom", "Zoom avant / arrière (via molette)")),
            ("Ctrl + ↑ / ↓ / ← / →", self.lang.get("help_move_zoomed_image", "Déplacer l'image zoomée")),

            
            (self.lang.get("help_project_section", "📁 Projet"), ""),
            ("Ctrl + N", self.lang.get("help_new_project", "Nouveau projet")),
            ("Ctrl + O", self.lang.get("help_open_project", "Ouvrir un projet")),
            ("Ctrl + Maj + O", self.lang.get("help_open_two_projects", "Ouvrir deux projets")),
            ("Ctrl + F", self.lang.get("help_merge_projects", "Fusionner deux projets")),
            ("Ctrl + S", self.lang.get("help_save_project", "Sauvegarder le projet")),
            ("Ctrl + Q", self.lang.get("help_quit", "Quitter")),

            (self.lang.get("help_preferences", "⚙️ Préférences"), ""),
            ("Ctrl + B", self.lang.get("help_change_bg_color", "Changer la couleur de fond")),
            ("Ctrl + L", self.lang.get("help_change_language", "Changer de langue")),

            (self.lang.get("help_tools", "🛠️ Outils (Toolbox)"), ""),
            ("C", self.lang.get("help_color_picker", "Pipette (colorPicker)")),
            ("M", self.lang.get("help_move_tool", "Déplacement (move)")),
            ("P", self.lang.get("help_brush", "Pinceau (pencil)")),
            ("B", self.lang.get("help_bucket_fill", "Pot de peinture (bucketFill)")),
            ("T", self.lang.get("help_text", "Texte (text)")),
            ("F", self.lang.get("help_fuzzy_select", "Sélection floue (fuzzySelect)")),
            ("R", self.lang.get("help_tracking", "Tracking (track)")),
            ("Alt + T", self.lang.get("help_show_hide_toolbox", "Afficher/Masquer la boîte à outils")),

            (self.lang.get("help_history", "🔁 Historique"), ""),
            ("Ctrl + Z", self.lang.get("help_undo", "Annuler")),
            ("Ctrl + Y", self.lang.get("help_redo", "Rétablir"))
        ]

        text_area = tk.Text(help_win, wrap='none', font=('Helvetica', 11), bg="#f8f8f8")
        text_area.pack(fill='both', expand=True, padx=10, pady=10)

        for key, action in shortcuts:
            line = f"{key:<15}  {action}\n"
            text_area.insert('end', line)

        text_area.config(state='disabled')  
    
    def _openProjectSetup(self, path: Path) -> None:
        '''Après l'ouverture d'un projet setup l'interface'''

        
        self.raw_id = 0
        if not self.current_project:
            
            self._setupBind()
        
        self.can.delete('all')
        self.current_project = path
        
        self.toolsBox.resetImage()
        
        self.app.title('GendALF - ' + str(self.current_project))
        
        self.addRecent(str(self.current_project))
        
        self.labels.addLabels(self.project_file['labels'])
        self.labels.setupLabels(self.labels_frame)
        
        self.raw.loadImages()
        
        # Ne naviguer que s'il y a des images
        if self.raw.raw and len(self.raw.raw) > 0:
            self.navigRaw(0)
            # Le compteur est déjà mis à jour dans navigRaw
        else:
            # Pas d'images, mettre le compteur à 0/0
            self.updateCounter()
        
        if self.labels.labels.keys():
            self.labels_canvas.config(width=225)
        else:
            self.labels_canvas.config(width=0)
        self.toolsBox.toolsBox()
        
        # Charger les vias du projet
        self.loadProjectVias()
        
        # S'assurer que le compteur est correctement affiché
        self.updateCounter()
        
        # Charger les pathtrackings du projet et configurer les bindings
        if hasattr(self, 'via_path_tracking'):
            # Vérifier si la méthode existe avant de l'appeler
            if hasattr(self.via_path_tracking, 'load_pathtrackings_from_project'):
                self.via_path_tracking.load_pathtrackings_from_project()
            
            # Configurer le binding du clic droit pour supprimer les pathtrackings
            if hasattr(self.via_path_tracking, 'setup_right_click_binding'):
                self.via_path_tracking.setup_right_click_binding()
        
        # Mettre à jour l'état des menus
        self.updateMenuStates()
        
        # Forcer une seconde mise à jour avec délai pour s'assurer que les menus vias sont activés
        self.app.after(100, self.updateMenuStates)
    
    
    def openProject(self, path: Path, new: bool = False) -> None:
        print(f"[LOG] Tentative d'ouverture du projet : {path}")
        print(f"[LOG] Projet ouvert : {path}")
        print(f"[LOG] Projet ajouté à preference.json : {path}")
        '''Ouvre un projet'''

  
        if (path / 'project.json').is_file():
            if not new:
                self.closeProject()
                with open(path / 'project.json', 'r', encoding='utf-8') as file:
                    self.project_file = json.load(file)

            # Vérifier et ajouter le projet dans preference.json si absent
            try:
                pref_file = Path(__file__).resolve().parent / "asset" / "preference.json"
                if pref_file.exists():
                    with open(pref_file, 'r', encoding='utf-8') as f:
                        prefs = json.load(f)
                else:
                    prefs = {"bgColor": "#454545", "language": "francais", "projects": []}
                if "projects" not in prefs or not isinstance(prefs["projects"], list):
                    prefs["projects"] = []
                # Vérifier si le projet est déjà enregistré
                project_path_str = str(path)
                if not any(p.get('path') == project_path_str for p in prefs["projects"]):
                    # Utiliser le nom du dossier comme nom de projet si pas dans project_file
                    project_name = self.project_file.get('file_name', path.name) if hasattr(self, 'project_file') else path.name
                    prefs["projects"].append({'name': project_name, 'path': project_path_str})
                    with open(pref_file, 'w', encoding='utf-8') as f:
                        json.dump(prefs, f, indent=2, ensure_ascii=False)
            except Exception as e:
                print(f"[DEBUG] Impossible d'ajouter le projet ouvert manuellement à asset/preference.json : {e}")

            self._openProjectSetup(path)
        elif path == Path('.'):
            return
        else:
            messagebox.showerror(self.lang['err'], self.lang['err7'])

    def closeProject(self):
        print(f"[LOG] Fermeture du projet : {self.current_project}")

        if self.current_project:
            self.saveProjectFile(self.current_project)
            self.current_project = None
            if hasattr(self.raw, 'raw'):
                self.raw.raw.clear()
            if hasattr(self.labels, 'labels'):
                self.labels.labels.clear()
            if hasattr(self, 'project_file'):
                del self.project_file
            if hasattr(self.raw, 'raw_coords'):
                del self.raw.raw_coords
            if hasattr(self.toolsBox.draw, '_history'):
                del self.toolsBox.draw._history, self.toolsBox.draw._history_undo
            
            # Mettre à jour l'état des menus
            self.updateMenuStates()


    def newProject(self, event: tk.Event | None = None) -> None:
        '''Fenêtre pour créer un nouveau projet'''

        if "_child_window" in self.__dict__:
            if self._child_window is not None and tk.Toplevel.winfo_exists(self._child_window):
                
                return

        self._child_window = tk.Toplevel(self.app)
        self._child_window.title(self.lang["new_project"])
        self._child_window.transient(self.app)
        self._child_window.grab_set()
        self._child_window.focus()

        tk.Label(self._child_window, text=self.lang["new_project_name"]).pack(pady=5)
        entry = tk.Entry(self._child_window, width=40)
        entry.insert(0, self.lang['entry_new_project_name'])
        entry.pack(fill='x', padx=10, pady=(0, 10))
        entry.bind('<FocusIn>', lambda event: self._onEntry(entry))
        entry.bind('<FocusOut>', lambda event: self._offEntry(entry))

        folder_label = tk.Label(self._child_window, text=f"{self.lang['registration_file']} : \n{Path.home() / 'Documents/RXViwer/project/'}")

        folder_label.pack(pady=(0, 5))
        self._child_window.geometry(f"{folder_label.winfo_reqwidth()}x180+{self.app.winfo_x() + self.app.winfo_width()//2 - 120}+{self.app.winfo_y() + self.app.winfo_height()//2 - 90}")
        tk.Button(self._child_window, text=self.lang['edit_registration_file'], command=lambda: self.changeSaveFolder(folder_label)).pack(pady=(0, 5))

        tk.Button(self._child_window, text=self.lang['create_new_projet'], command=lambda: self.createProject(entry.get(), folder_label.cget('text').replace(f"{self.lang['registration_file']} : \n", ""))).pack(pady=10)
        self._child_window.bind('<Return>', lambda event: self.createProject(entry.get(), folder_label.cget('text').replace(f"{self.lang['registration_file']} : \n", "")))
    
    def loadingBar(self, percentage: int) -> None:
        '''Update la barre de chargement'''
        bar = self._loading_bar.winfo_children()
        bar[0].config(text=f'{percentage}%')
        bar[0].update_idletasks()
        bar[1].place(x=bar[0].winfo_width() + 5, width=int((self.app.winfo_width() - bar[0].winfo_width() - 15)/100*percentage))
        bar[1].config(background='green')
        bar[1].update_idletasks()
    
    def resetLoadingBar(self) -> None:
        '''Reset la barre de chargement'''

        bar = self._loading_bar.winfo_children()
        bar[0].config(text='')
        bar[1].config(background='#F0F0F0')
        bar[1].place(x=bar[0].winfo_width() + 5, width=0)

    def _onEntry(self, entry: tk.Entry) -> None:
        '''Retirer le texte de la zone du nom du projet lorsque l'on clic dedans'''

        if entry.get() == self.lang['entry_new_project_name']:
            entry.delete(0, 'end')

    def _offEntry(self, entry: tk.Entry) -> None:
        '''Remettre le texte de la zone du nom du projet lorsque l'Entry perd le focus'''

        if entry.get() == '':
            entry.insert(0, self.lang['entry_new_project_name'])

    def changeSaveFolder(self, label: tk.Label) -> None:
        '''Changer l'emplacement de sauvegarde'''

        folder_selected = filedialog.askdirectory(initialdir=Path.home() / "Documents/RXViwer/project/")
        if folder_selected:
            label.config(text=f"{self.lang['registration_file']} : \n{folder_selected}")
            self._child_window.geometry(str(label.winfo_reqwidth() if label.winfo_reqwidth() > 260 else 260) + "x180")
    def doubleProject(self):
        '''Fenêtre pour sélectionner deux projets à ouvrir en parallèle dans une nouvelle fenêtre.'''
        win = tk.Toplevel(self.app)
        win.title(self.lang.get("choose_two_projects", "Choisir deux projets"))
        win.geometry("500x240")
        win.grab_set()

        path1_var = tk.StringVar()
        path2_var = tk.StringVar()

        def browse(var):
            path = filedialog.askdirectory(initialdir=Path.home() / 'Documents/RXViwer/project/')
            if path:
                var.set(path)

        def launchProjects():
            p1, p2 = Path(path1_var.get()), Path(path2_var.get())
            if not (p1 / 'project.json').is_file() or not (p2 / 'project.json').is_file():
                messagebox.showerror(self.lang["err"], self.lang.get("invalid_folder", "Les dossiers ne sont pas valides."))
                return
            RXviewerSecondary(tk.Toplevel(self.app), p1, p2)
            win.destroy()

        tk.Label(win, text=self.lang.get("project1", "Projet 1")).pack(pady=(10, 0))
        tk.Entry(win, textvariable=path1_var, width=60).pack()
        tk.Button(win, text=self.lang.get("browse", "Parcourir"), command=lambda: browse(path1_var)).pack(pady=5)

        tk.Label(win, text=self.lang.get("project2", "Projet 2")).pack(pady=(10, 0))
        tk.Entry(win, textvariable=path2_var, width=60).pack()
        tk.Button(win, text=self.lang.get("browse", "Parcourir"), command=lambda: browse(path2_var)).pack(pady=5)

        tk.Button(win, text=self.lang.get("open_both", "Ouvrir les deux projets"), command=launchProjects).pack(pady=15)
    
    def synchroProject(self):
        win = tk.Toplevel(self.app)
        win.title(self.lang.get("sync_two_projects", "Synchroniser deux projets"))
        win.geometry("500x300")
        win.configure(bg="#2f2f2f")
        win.grab_set() 
        win.focus_set() 

        path1_var = tk.StringVar()
        path2_var = tk.StringVar()

        def browse(var):
            folder = tk.filedialog.askdirectory(parent=win)  
            if folder:
                var.set(folder)

        def launchSync():
            p1 = Path(path1_var.get())
            p2 = Path(path2_var.get())

            if not (p1 / 'project.json').is_file() or not (p2 / 'project.json').is_file():
                messagebox.showerror(
                    self.lang["err"], 
                    self.lang.get("invalid_folder", "Les dossiers ne sont pas valides."),
                    parent=win  
                )
                return

            from RXmodule.RXviewerSync import RXviewerSync
            RXviewerSync(self.app, p1, p2)
            win.destroy()

        tk.Label(win, text=self.lang.get("project1", "Projet 1"), bg="#2f2f2f", fg="white").pack(pady=(10, 0))
        tk.Entry(win, textvariable=path1_var, width=60).pack()
        tk.Button(win, text=self.lang.get("browse", "Parcourir"), command=lambda: browse(path1_var)).pack(pady=5)

        tk.Label(win, text=self.lang.get("project2", "Projet 2"), bg="#2f2f2f", fg="white").pack(pady=(10, 0))
        tk.Entry(win, textvariable=path2_var, width=60).pack()
        tk.Button(win, text=self.lang.get("browse", "Parcourir"), command=lambda: browse(path2_var)).pack(pady=5)

        tk.Button(win, text=self.lang.get("open_both", "Synchroniser les projets"), command=launchSync).pack(pady=20)


    def fusionProject(self):
        '''Ouvre la fenêtre de fusion de projet'''

        self.can.delete('all')
        self.closeProject()
        self.project_fusion = RXviewerProjectFusion(self)
        self.project_fusion.window()
    
    def fusionProjectClose(self):
        '''Lors de la fermeture de la fenêtre de fusion de projet clear la mémoire'''

        fusion_path = self.project_fusion.fusion_path  
        self.project_fusion.window_projectFuseion.destroy()
        del self.project_fusion

        if fusion_path:
            self.openProject(fusion_path)
    
    def calibrateVias(self):
        '''Fonction d'étalonnage des vias'''

        if not self.current_project:
            messagebox.showwarning(self.lang.get("err", "Erreur"), self.lang.get("err2", "Veuillez ouvrir ou créer un nouveau projet."))
            return
        
        # Ouvrir la fenêtre d'étalonnage des vias
        self.via_calibration.open_via_calibration_window()
    
    def toggleShowVias(self):
        '''Active/désactive l'affichage des vias sur l'image principale'''
        if self.show_vias_var.get():
            # Charger les vias du projet s'ils ne sont pas déjà chargés
            self.loadProjectVias()
        
        # Rafraîchir l'affichage
        if self.current_project and self.raw.raw:
            self.displayImage()
    
    def loadProjectVias(self):
        '''Charge les vias du projet depuis le fichier project.json'''
        if not self.current_project:
            return
            
        try:
            project_path = self.current_project / 'project.json'

            
            with open(project_path, 'r', encoding='utf-8') as file:
                project_data = json.load(file)
                
            if 'vias' in project_data and project_data['vias']:
                self.project_vias = project_data['vias']


            else:
                self.project_vias = []

                
        except Exception as e:
            self.project_vias = []

    def updateMenuStates(self):
        '''Met à jour l'état des éléments du menu selon l'état du projet'''
        try:
            if hasattr(self, 'projet_menu'):
                
                # États des menus selon le projet
                project_is_open = self.current_project is not None
                vias_menu_state = 'normal' if project_is_open else 'disabled'
                

                
                # Parcourir tous les éléments du menu
                menu_end = self.projet_menu.index('end')
 
                
                for i in range(menu_end + 1):
                    try:
                        item_type = self.projet_menu.type(i)
                        if item_type in ['command', 'checkbutton']:
                            label = self.projet_menu.entrycget(i, 'label')

                            
                            # SEULS les menus vias doivent être activés/désactivés selon l'état du projet
                            if ('vias' in label.lower() or 
                                'étalonnage' in label.lower() or 
                                'etalonnage' in label.lower() or
                                'calibrate' in label.lower() or
                                'afficher les vias' in label.lower() or
                                'afficher vias' in label.lower() or
                                'show vias' in label.lower()):
                                
                                old_state = self.projet_menu.entrycget(i, 'state')
                                self.projet_menu.entryconfig(i, state=vias_menu_state)

                            
                            # Les autres menus (fusion, sync, import, etc.) restent TOUJOURS activés
                            elif any(keyword in label.lower() for keyword in [
                                'fusio', 'synchron', 'import'
                            ]):
                                # S'assurer qu'ils restent activés
                                old_state = self.projet_menu.entrycget(i, 'state')
                                self.projet_menu.entryconfig(i, state='normal')

                            
                            # Seuls quelques menus spécifiques sont désactivés sans projet
                            elif any(keyword in label.lower() for keyword in [
                                'sauvegard', 'ferm'
                            ]):
                                old_state = self.projet_menu.entrycget(i, 'state')
                                project_menu_state = 'normal' if project_is_open else 'disabled'
                                self.projet_menu.entryconfig(i, state=project_menu_state)

                                
                    except tk.TclError as e:

                        continue
                

                        
        except Exception:
            pass

    def createProject(self, projectName: str, folder: str) -> None:
        print(f"[LOG] Création d'un nouveau projet : {projectName} dans {folder}")
        '''Créer un nouveau projet'''
        # ...existing code...
        # L'initialisation du dict se fait plus bas, inutile ici

        self.closeProject()
        directory = Path(folder)
        if projectName and projectName != self.lang['entry_new_project_name']:
            if (directory / projectName).exists():
                messagebox.showerror(self.lang['err'], f"{self.lang['err1']} \n'{directory / projectName}'")
                return
            rep = directory / projectName
            (rep / 'raw').mkdir(parents=True)
            (rep / 'edit').mkdir()
            (rep / 'draw').mkdir()
            (rep / 'pathtracking').mkdir()
            self.project_file = dict(
                file_name=projectName,
                creation_date=datetime.now().isoformat(),
                project_path=str(rep),
                labels={},
                label_id=0
            )
        else:
            i = 1
            while f'New_Project{i}' in [f.name for f in directory.iterdir() if f.is_dir()]:
                i += 1
            rep = directory / f'New_Project{i}'
            (rep / 'raw').mkdir(parents=True)
            (rep / 'edit').mkdir()
            (rep / 'draw').mkdir()
            (rep / 'pathtracking').mkdir()
            self.project_file = dict(
                file_name=f'New_Project{i}',
                creation_date=datetime.now().isoformat(),
                project_path=str(rep),
                labels={},
                label_id=0
            )

        # Ajouter le projet à asset/preference.json (liste des projets connus)
        try:
            asset_dir = Path(__file__).resolve().parent / "asset"
            asset_dir.mkdir(parents=True, exist_ok=True)
            pref_file = asset_dir / "preference.json"
            import json
            if pref_file.exists():
                with open(pref_file, 'r', encoding='utf-8') as f:
                    prefs = json.load(f)
            else:
                prefs = {"bgColor": "#454545", "language": "francais", "projects": []}
            # S'assurer que la clé 'projects' existe et est une liste
            if "projects" not in prefs or not isinstance(prefs["projects"], list):
                prefs["projects"] = []
            # Ajouter le projet si pas déjà présent (par chemin)
            if not any(p.get('path') == str(rep) for p in prefs["projects"]):
                prefs["projects"].append({'name': self.project_file['file_name'], 'path': str(rep)})
                with open(pref_file, 'w', encoding='utf-8') as f:
                    json.dump(prefs, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[DEBUG] Impossible d'ajouter le projet à asset/preference.json : {e}")

        if "_child_window" in self.__dict__:
            self._child_window.destroy()
        self.saveProjectFile(rep)
        self.openProject(rep, True)

    def saveProjectFile(self, path: Path):
        print(f"[LOG] Sauvegarde du projet : {path}")
        '''Sauvegarde le fichier projet'''

        self.raw.saveRaws()
        self.project_file['lest_modified_date'] = datetime.now().isoformat()
        
        # Lire le fichier existant pour préserver les vias
        project_json_path = path / 'project.json'
        existing_vias = []
        if project_json_path.exists():
            try:
                with open(project_json_path, 'r', encoding='utf-8') as file:
                    existing_data = json.load(file)
                    existing_vias = existing_data.get('vias', [])
            except Exception:
                pass
        
        # Préserver les vias dans le fichier à sauvegarder
        self.project_file['vias'] = existing_vias
        
        with open(project_json_path, 'w', encoding='utf-8') as file:
            json.dump(self.project_file, file, indent=4, ensure_ascii=False)
        


    def searchProject(self, event: tk.Event | None = None) -> None:
        '''Ouvrir un projet existant'''

        project_selected = Path(filedialog.askdirectory(initialdir=Path.home() / 'Documents/RXViwer/project/'))
        if project_selected and project_selected.is_dir():
            self.openProject(project_selected)
        
    def backgroundColor(self) -> None:
        '''Modifier la couleur d'arrière plan'''

        color = colorchooser.askcolor(title=self.lang['switch_color_background'])[1]
        if color:
            self.option['bgColor'] = color
            self.can.config(background=color)
    
    def language(self) -> None:
        '''Permets de changer la langue de l'interface'''

        if "_child_window" in self.__dict__:
            if self._child_window is not None and tk.Toplevel.winfo_exists(self._child_window):
                
                return

        self._child_window = tk.Toplevel(self.app)
        self._child_window.title(self.lang["language"])
        self._child_window.transient(self.app)
        self._child_window.grab_set()

        # Utiliser le chemin absolu vers les fichiers de langue
        CURRENT_DIR = Path(__file__).resolve().parent
        LANG_DIR = CURRENT_DIR / "asset" / "lang"
        
        # Récupérer tous les fichiers JSON dans le dossier lang
        lang_files = list(LANG_DIR.glob('*.json'))
        self._langs = [lang_file.stem for lang_file in lang_files]
        

        
        tk.Label(self._child_window, text=self.lang['choose_language'] + ' :', font=("Helvetica", 10)).pack(side='top')
        var = tk.Variable(value=self._langs)
        listbox = tk.Listbox(self._child_window, listvariable=var, height=6, font=("Helvetica", 10))
        listbox.pack(expand=True, fill='both', side='left')
        scrollbar = tk.Scrollbar(self._child_window, orient=tk.VERTICAL, command=listbox.yview)
        listbox['yscrollcommand'] = scrollbar.set
        scrollbar.pack(side='left', expand=True, fill='y')
        listbox.bind('<<ListboxSelect>>', lambda event: self._languageC(listbox))
        self._child_window.geometry(f"+{self.app.winfo_x() + self.app.winfo_width()//2 - 50}+{self.app.winfo_y() + self.app.winfo_height()//2 - 50}")

    def _languageC(self, lang: tk.Listbox) -> None:
        '''Enregistre la langue sélectionnée et met à jour l'interface immédiatement'''

        selection = lang.curselection()
        if selection:  # Vérifier qu'il y a une sélection
            selected_lang = self._langs[selection[0]]

            self.option['language'] = selected_lang
            
            # Charger la nouvelle langue
            self.lang = self.openLang(selected_lang)
            
            # Fermer la fenêtre de sélection
            self._child_window.destroy()
            
            # Mettre à jour l'interface immédiatement
            self.refreshLanguage()
            
            if hasattr(self, '_langs'):
                del self._langs
                
            messagebox.showinfo(title=self.lang['info'], message=self.lang.get('language_applied', 'Langue appliquée avec succès.'))

    def refreshLanguage(self):
        print(f"[LOG] Changement de langue : {self.option.get('language')}")
        '''Met à jour tous les textes de l'interface avec la nouvelle langue'''

        
        # Mettre à jour le titre de la fenêtre principale
        if self.current_project:
            self.app.title('GendALF - ' + str(self.current_project))
        else:
            self.app.title('GendALF')
        
        # Recréer complètement la barre de menu avec la nouvelle langue
        self.app.config(menu='')  # Supprimer l'ancien menu
        self._setupMenu()  # Recréer le menu avec les nouvelles traductions

        # Réactiver les boutons calibrate/show vias si un projet est ouvert
        if hasattr(self, 'current_project') and self.current_project:
            try:
                # Rechercher les index des boutons calibrate/show vias
                for i in range(self.projet_menu.index('end') + 1):
                    label = self.projet_menu.entrycget(i, 'label').lower()
                    if ('vias' in label or 'calibrate' in label or 'étalonnage' in label or 'etalonnage' in label or 'afficher' in label or 'show' in label):
                        self.projet_menu.entryconfig(i, state='normal')
            except Exception:
                pass

        # Mettre à jour les fenêtres enfants si elles existent
        if hasattr(self, '_child_window_toolsBox') and hasattr(self._child_window_toolsBox, 'winfo_exists') and self._child_window_toolsBox.winfo_exists():
            self._child_window_toolsBox.title(self.lang['tools_box'])

        # Mettre à jour les fenêtres secondaires si elles existent
        if hasattr(self, '_child_window_secondary') and hasattr(self._child_window_secondary, 'winfo_exists') and self._child_window_secondary.winfo_exists():
            self._child_window_secondary.title(self.lang.get('project', 'Projet'))

        # Mettre à jour les fenêtres de labels si elles existent
        if hasattr(self, '_child_window_labels') and hasattr(self._child_window_labels, 'winfo_exists') and self._child_window_labels.winfo_exists():
            self._child_window_labels.title(self.lang.get('labels', 'Marqueurs'))

        # Mettre à jour les fenêtres de fusion si elles existent
        if hasattr(self, '_child_window_fusion') and hasattr(self._child_window_fusion, 'winfo_exists') and self._child_window_fusion.winfo_exists():
            self._child_window_fusion.title(self.lang.get('project_fusion', 'Fusionner deux projets'))

        # Rafraîchir l'affichage si nécessaire
        if hasattr(self, 'raw') and self.raw.raw:
            self.displayImage()

        # Sauvegarder les préférences
        PREF_PATH = Path(__file__).resolve().parent / "asset" / "preference.json"
        try:
            with open(PREF_PATH, 'r', encoding='utf-8') as file:
                prefs = json.load(file)
        except Exception:
            prefs = {}
        prefs['bgColor'] = self.option.get('bgColor', prefs.get('bgColor', '#454545'))
        prefs['language'] = self.option.get('language', prefs.get('language', 'francais'))
        with open(PREF_PATH, 'w', encoding='utf-8') as file:
            json.dump(prefs, file, indent=2, ensure_ascii=False)

    def displayImage(self) -> None:
        '''Modifie l'image et l'affiche dans le canvas'''
        self.can.delete('all')
        if self.raw.raw:
            image_coords = self.raw.raw_coords[0], self.raw.raw_coords[1]
            self._current_image = self.raw.raw[self.raw_id].raw.copy()
            # Afficher les vias si l'option est activée
            if (hasattr(self, 'show_vias_var') and self.show_vias_var.get() and 
                hasattr(self, 'project_vias') and self.project_vias):
                self._current_image = self.drawViasOnImage(self._current_image)
            # Afficher les pathtrackings visibles uniquement
            if hasattr(self, 'via_path_tracking') and self.via_path_tracking.pathtrackings:
                visibles = self.via_path_tracking.get_visible_pathtrackings() if hasattr(self.via_path_tracking, 'get_visible_pathtrackings') else None
                self._current_image = self.drawPathtrackingsFromLayer(self._current_image, self.raw_id, visibles=visibles)
            if self.toolsBox.raw_flip != -2:
                self._current_image = cv2.flip(self._current_image, self.toolsBox.raw_flip)
            if self.toolsBox.raw_rotation != -1:
                self._current_image = cv2.rotate(self._current_image, self.toolsBox.raw_rotation)
            image_size = self._current_image.shape[1] * self.toolsBox.raw_zoom, self._current_image.shape[0] * self.toolsBox.raw_zoom
            if self.toolsBox.raw_zoom != 1.0:
                x1 = min(max(0, -self.raw.raw_coords[0] * self._current_image.shape[1] / image_size[0]), self._current_image.shape[1])
                y1 = min(max(0, -self.raw.raw_coords[1] * self._current_image.shape[0] / image_size[1]), self._current_image.shape[0])
                x2 = min(max(0, (self.can.winfo_width() - self.raw.raw_coords[0]) * self._current_image.shape[1] / image_size[0]), self._current_image.shape[1])
                y2 = min(max(0, (self.can.winfo_height() - self.raw.raw_coords[1]) * self._current_image.shape[0] / image_size[1]), self._current_image.shape[0])
                new_raw = self._current_image[int(y1):int(y2), int(x1):int(x2)]
                if new_raw.size and int((x2 - x1) * self.toolsBox.raw_zoom) > 0 and int((y2 - y1) * self.toolsBox.raw_zoom) > 0:
                    self._current_image = cv2.resize(new_raw, (int((x2 - x1) * self.toolsBox.raw_zoom), int((y2 - y1) * self.toolsBox.raw_zoom)))
                    image_coords = self.raw.raw_coords[0] + x1 * self.toolsBox.raw_zoom, self.raw.raw_coords[1] + y1 * self.toolsBox.raw_zoom
                else:
                    return
            self.current_image_fromarray = Image.fromarray(self._current_image)
            self._current_image = ImageTk.PhotoImage(self.current_image_fromarray)
            self.can.create_image(image_coords, anchor=tk.NW, image=self._current_image, tags=['raw', 'can'])
            self.labels.moveLabels(image_size, self.raw.raw_coords)
    
    def drawViasOnImage(self, image):
        '''Dessine les vias sur l'image'''
        if not self.project_vias:
            return image
            
        image_copy = image.copy()
        via_colors = [(255, 255, 0), (255, 0, 255), (0, 255, 255), (0, 255, 0), (255, 0, 0)]  # BGR colors
        
        for i, via in enumerate(self.project_vias):
            color = via_colors[i % len(via_colors)]
            center = tuple(via['center'])
            radius = via.get('radius', 5)
            
            # Couleur spéciale pour le via sélectionné
            if (hasattr(self, 'via_path_tracking') and 
                hasattr(self.via_path_tracking, 'selected_via_id') and 
                self.via_path_tracking.selected_via_id == i):
                color = (0, 255, 255)  # Jaune pour le via sélectionné
                thickness = 3
            else:
                thickness = 2
            
            # Dessiner le cercle du via
            cv2.circle(image_copy, center, radius, color, thickness)
            
            # Ajouter le numéro du via
            cv2.putText(image_copy, str(i+1), (center[0]-10, center[1]-15), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
        
        return image_copy

    def drawPathtrackingsFromLayer(self, image, raw_id, visibles=None):
        """Superpose le calque pathtracking sur l'image courante."""
        try:
            # Construire le chemin vers l'image pathtracking correspondante
            if hasattr(self.raw.raw[raw_id], 'filename'):
                pathtracking_filename = self.raw.raw[raw_id].filename
            else:
                pathtracking_filename = f"slice{raw_id:05d}.png"
            
            pathtracking_path = os.path.join(self.current_project, "pathtracking", pathtracking_filename)
            
            # Charger l'image pathtracking si elle existe
            if os.path.exists(pathtracking_path):
                pathtracking_layer = cv2.imread(pathtracking_path, cv2.IMREAD_UNCHANGED)
                
                if pathtracking_layer is not None:
                    # S'assurer que l'image de base est en couleur
                    if len(image.shape) == 2:
                        image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
                    
                    # Redimensionner le calque pathtracking si nécessaire
                    if pathtracking_layer.shape[:2] != image.shape[:2]:
                        pathtracking_layer = cv2.resize(pathtracking_layer, (image.shape[1], image.shape[0]))
                    
                    # Si on reçoit la liste des pathtrackings visibles, on ne dessine que ceux-ci
                    # (Ici, on suppose que chaque pathtracking a un calque séparé ou on peut filtrer autrement)
                    # Si besoin, adapter ici pour ne dessiner que les visibles
                    # (Si chaque pathtracking a son propre calque, il faudrait les charger un par un)
                    # Pour l'instant, on affiche le calque global si au moins un pathtracking est visible
                    if visibles is not None and len(visibles) == 0:
                        return image  # Aucun à afficher
                    # --- code d'origine ---
                    if len(pathtracking_layer.shape) == 3 and pathtracking_layer.shape[2] == 4:
                        alpha = pathtracking_layer[:, :, 3] / 255.0
                        for c in range(3):
                            image[:, :, c] = image[:, :, c] * (1 - alpha) + pathtracking_layer[:, :, c] * alpha
                    elif len(pathtracking_layer.shape) == 3 and pathtracking_layer.shape[2] == 3:
                        mask = cv2.cvtColor(pathtracking_layer, cv2.COLOR_BGR2GRAY) > 0
                        image[mask] = pathtracking_layer[mask]
                    else:
                        mask = pathtracking_layer > 0
                        if len(image.shape) == 3:
                            pathtracking_bgr = cv2.cvtColor(pathtracking_layer, cv2.COLOR_GRAY2BGR)
                            image[mask] = pathtracking_bgr[mask]
                        else:
                            image[mask] = pathtracking_layer[mask]
            return image
        except Exception as e:
            print(f"Erreur lors de la superposition du calque pathtracking : {e}")
            return image

    def updateCounter(self) -> None:
        '''Met à jour le compteur d'images'''
        if hasattr(self, 'counter_label'):
            if self.raw.raw and hasattr(self, 'raw_id'):
                # Vérifier que raw_id est dans la plage valide
                if 0 <= self.raw_id < len(self.raw.raw):
                    self.counter_label.config(text=f'{self.raw_id + 1}/{len(self.raw.raw)}')
                else:
                    # raw_id hors limites, corriger et afficher
                    self.raw_id = max(0, min(self.raw_id, len(self.raw.raw) - 1))
                    self.counter_label.config(text=f'{self.raw_id + 1}/{len(self.raw.raw)}')
            else:
                self.counter_label.config(text='0/0')

    def resetRaw(self) -> None:
        '''Reset les paramètres de l'image (zoom, flip, rotation, coordonnées)'''

        if self.raw.raw:
            self.raw.raw_coords = [self.can.winfo_width() // 2 - self.raw.raw[self.raw_id].raw.shape[1] // 2, self.can.winfo_height() // 2 - self.raw.raw[self.raw_id].raw.shape[0] // 2]
            self.toolsBox.raw_zoom = 1.0
            self.toolsBox.raw_rotation = -1
            self.toolsBox.raw_flip = -2
            self.updateCounter()
            self.displayImage()

    def navigRaw(self, direction: int) -> None:
        '''Permets de défiler entre les images'''
        if self.raw.raw:
            new_id = self.raw_id + direction
            if 0 <= new_id < len(self.raw.raw):
                self.raw_id = new_id
                self.toolsBox.draw.newDraw()
                self.updateCounter()
                self.displayImage()

    def _wheelNext(self, event: tk.Event) -> None:
        '''Détermine le sens du défilement de l'image avec la molette'''
        if not (event.state & 0x0004):
            self.navigRaw(-1 if event.delta < 0 else 1)
    
    def firstRaw(self) -> None:
        '''Va à la première image'''
        if self.raw.raw:
            self.raw_id = 0
            self.updateCounter()
            self.displayImage() 

    def lastRaw(self) -> None:
        '''Va à la dernière image'''
        if self.raw.raw:
            self.raw_id = len(self.raw.raw) - 1
            self.updateCounter()
            self.displayImage()


    def deleteProject(self) -> None:
        '''Supprime un projet en utilisant asset/preference.json comme source de vérité.'''
        import json
        from tkinter import messagebox
        from pathlib import Path
        import tkinter as tk
        # Charger la liste des projets connus
        asset_dir = Path(__file__).resolve().parent / "asset"
        projects_file = asset_dir / "preference.json"
        if not projects_file.exists():
            messagebox.showinfo("Info", "Aucun projet à supprimer (preference.json introuvable).")
            return
        try:
            with open(projects_file, 'r', encoding='utf-8') as f:
                prefs = json.load(f)
            projects_list = prefs.get('projects', []) if isinstance(prefs, dict) else []
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de lire asset/preference.json : {e}")
            return
        if not projects_list:
            messagebox.showinfo("Info", "Aucun projet à supprimer.")
            return
        # Ouvre une fenêtre pour sélectionner et supprimer un projet (affiche uniquement ceux du preference.json)
        if "_child_window" in self.__dict__:
            if self._child_window is not None and tk.Toplevel.winfo_exists(self._child_window):
                return
        self._child_window = tk.Toplevel(self.app)
        self._child_window.title(self.lang.get('delete_project', 'Supprimer un projet'))
        self._child_window.transient(self.app)
        self._child_window.grab_set()
        self._child_window.focus()
        self._child_window.geometry(f"500x400+{self.app.winfo_x() + self.app.winfo_width()//2 - 250}+{self.app.winfo_y() + self.app.winfo_height()//2 - 200}")

        # Titre d'avertissement
        warning_label = tk.Label(
            self._child_window, 
            text=self.lang.get("delete_project_warning", "⚠️ SUPPRESSION DÉFINITIVE DE PROJET ⚠️"),
            font=("Helvetica", 14, "bold"),
            fg="red"
        )
        warning_label.pack(pady=(10, 5))

        # Instruction
        instruction_label = tk.Label(
            self._child_window, 
            text=self.lang.get('select_project_to_delete', 'Sélectionnez le projet à supprimer dans la liste ci-dessous :'),
            font=("Helvetica", 10),
            justify="center"
        )
        instruction_label.pack(pady=(5, 10))

        # Frame pour la liste des projets
        list_frame = tk.Frame(self._child_window)
        list_frame.pack(fill='both', expand=True, padx=20, pady=5)

        # Liste des projets avec scrollbar
        project_listbox = tk.Listbox(list_frame, font=("Helvetica", 10))
        scrollbar = tk.Scrollbar(list_frame, orient=tk.VERTICAL, command=project_listbox.yview)
        project_listbox.configure(yscrollcommand=scrollbar.set)
        project_listbox.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        # Remplir la liste avec les projets du preference.json (nom + chemin)
        for project in projects_list:
            name = project.get('name', '')
            path = project.get('path', '')
            display = f"{name:<25}  {path}"
            project_listbox.insert(tk.END, display)

        selected_index = [None]

        def on_project_select(event):
            selection = project_listbox.curselection()
            if selection:
                selected_index[0] = selection[0]
                confirm_button.config(state='normal')
            else:
                selected_index[0] = None
                confirm_button.config(state='disabled')

        project_listbox.bind('<<ListboxSelect>>', on_project_select)

        confirm_frame = tk.Frame(self._child_window)  
        confirm_frame.pack(pady=10)
        tk.Label(confirm_frame, 
                text=self.lang.get("type_project_name_to_confirm", "Tapez le nom exact du projet pour confirmer :"),
                font=("Helvetica", 10)).pack()
        entry = tk.Entry(confirm_frame, width=40, font=("Helvetica", 10))
        entry.pack(pady=5)
        error_label = tk.Label(self._child_window, text="", fg="red", font=("Helvetica", 9))
        error_label.pack(pady=2)
        button_frame = tk.Frame(self._child_window)
        button_frame.pack(pady=10)

        def confirm_deletion():
            if selected_index[0] is None:
                error_label.config(text=self.lang.get("no_project_selected", "Veuillez sélectionner un projet !"))
                return
            entered_name = entry.get().strip()
            project = projects_list[selected_index[0]]
            if entered_name == project.get('name', ''):
                proj_path = project.get('path', '')
                try:
                    proj_dir = Path(proj_path)
                    if proj_dir.exists() and proj_dir.is_dir():
                        import shutil
                        shutil.rmtree(proj_dir)
                except Exception as e:
                    messagebox.showerror("Erreur", f"Impossible de supprimer le dossier du projet : {e}", parent=self._child_window)
                del projects_list[selected_index[0]]
                try:
                    with open(projects_file, 'w', encoding='utf-8') as f:
                        json.dump(projects_list, f, indent=2, ensure_ascii=False)
                except Exception as e:
                    messagebox.showerror("Erreur", f"Impossible de mettre à jour asset/preference.json : {e}", parent=self._child_window)
                    self._child_window.destroy()
                    return
                if hasattr(self, 'recent') and self.recent:
                    project_path_str = str(proj_path)
                    self.recent = [path for path in self.recent if path != project_path_str]
                    recent_path = Path("asset/recent")
                    recent_path.parent.mkdir(parents=True, exist_ok=True)
                    recent_path.write_text('\n'.join(self.recent), encoding='utf-8')
                self._child_window.destroy()
                success_msg = self.lang.get('project_deleted_successfully_msg', 'a été supprimé définitivement.\n\nTous les fichiers et dossiers associés ont été supprimés.')
                messagebox.showinfo(
                    self.lang.get("deletion_successful", "Suppression réussie"),
                    f"{self.lang.get('project_deleted_successfully', 'Le projet')} '{entered_name}' {success_msg}"
                )
            else:
                error_label.config(text=self.lang.get("name_does_not_match", "Le nom saisi ne correspond pas au nom du projet sélectionné !"))
                entry.delete(0, 'end')
                entry.focus()

        def cancel_deletion():
            self._child_window.destroy()

        confirm_button = tk.Button(
            button_frame, 
            text=self.lang.get("delete_permanently", "SUPPRIMER DÉFINITIVEMENT"), 
            command=confirm_deletion,
            font=("Helvetica", 10, "bold"),
            fg="white",
            bg="red",
            width=25,
            state='disabled'
        )
        confirm_button.pack(side='left', padx=5)

        tk.Button(
            button_frame, 
            text=self.lang.get("cancel", "Annuler"), 
            command=cancel_deletion,
            font=("Helvetica", 10),
            width=15
        ).pack(side='right', padx=5)

        self._child_window.bind('<Return>', lambda event: confirm_deletion())
        self._child_window.bind('<Escape>', lambda event: cancel_deletion())

    def _performProjectDeletion(self, project_to_delete: Path) -> None:
        '''Effectue la suppression complète du projet spécifié'''

        if not project_to_delete or not project_to_delete.exists():
            return

        project_name = project_to_delete.name

        try:
            # Si le projet à supprimer est le projet actuellement ouvert, le fermer d'abord
            if self.current_project and self.current_project == project_to_delete:
                self.closeProject()

            # Supprimer complètement le dossier du projet
            shutil.rmtree(project_to_delete)
            
            # Supprimer le projet de la liste des projets récents
            if hasattr(self, 'recent') and self.recent:
                # Convertir project_to_delete en string pour la comparaison
                project_to_delete_str = str(project_to_delete)
                self.recent = [path for path in self.recent if path != project_to_delete_str]
                recent_path = Path("asset/recent")
                recent_path.parent.mkdir(parents=True, exist_ok=True)
                recent_path .write_text('\n'.join(self.recent), encoding='utf-8')


            # Message de confirmation
            success_msg = self.lang.get('project_deleted_successfully_msg', 'a été supprimé définitivement.\n\nTous les fichiers et dossiers associés ont été supprimés.')
            messagebox.showinfo(
                self.lang.get("deletion_successful", "Suppression réussie"),
                f"{self.lang.get('project_deleted_successfully', 'Le projet')} '{project_name}' {success_msg}"
            )
            


        except Exception as e:
            messagebox.showerror(
                self.lang.get("err", "Erreur"),
                f"{self.lang.get('deletion_error', 'Erreur lors de la suppression du projet')} :\n\n{str(e)}"
            )


    def checkForUpdates(self):
        '''Recherche les mises à jour disponibles'''
        if hasattr(self, 'save_manager'):
            self.save_manager.manual_update_check()
        else:
            messagebox.showerror(
                self.lang.get("error", "Erreur"),
                "Le gestionnaire de mise à jour n'est pas disponible."
            )

    def showAboutInfo(self):
        '''Affiche les informations sur l'application'''

        
        # Charger les données de l'application
        try:
            CURRENT_DIR = Path(__file__).resolve().parent
            DATA_PATH = CURRENT_DIR / "asset" / "data.json"
            with open(DATA_PATH, 'r', encoding='utf-8') as file:
                app_data = json.load(file)
        except Exception as e:

            app_data = {
                "app_info": {"name": "GendALF", "version": "1.0.0", "description": "Visualiseur d'images"},
                "developer": {"name": "Développeur", "email": "contact@example.com"}
            }

        # Créer la fenêtre À propos
        if hasattr(self, '_about_window') and self._about_window and tk.Toplevel.winfo_exists(self._about_window):
            self._about_window.lift()
            return

        self._about_window = tk.Toplevel(self.app)
        self._about_window.title(self.lang.get('about_title', 'À propos de GendALF'))
        self._about_window.transient(self.app)
        self._about_window.grab_set()
        self._about_window.focus()
        self._about_window.geometry(f"520x600+{self.app.winfo_x() + self.app.winfo_width()//2 - 260}+{self.app.winfo_y() + self.app.winfo_height()//2 - 300}")
        self._about_window.resizable(True, True)
        self._about_window.minsize(400, 500)

        # Canvas pour permettre le défilement sans scrollbar visible
        canvas = tk.Canvas(self._about_window, bg='white', highlightthickness=0)
        scrollable_frame = tk.Frame(canvas, bg='white')

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

        canvas.pack(fill="both", expand=True, padx=20, pady=20)

        # Support de la molette de souris
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        canvas.bind("<MouseWheel>", _on_mousewheel)
        self._about_window.bind("<MouseWheel>", _on_mousewheel)

        # Frame principal avec padding dans le frame scrollable
        main_frame = tk.Frame(scrollable_frame, bg='white', padx=20, pady=20)
        main_frame.pack(fill='both', expand=True)

        # Titre de l'application
        app_title = tk.Label(
            main_frame,
            text=app_data["app_info"]["name"],
            font=("Helvetica", 20, "bold"),
            bg='white',
            fg='#2E7D32'
        )
        app_title.pack(pady=(0, 5))

        # Version
        version_label = tk.Label(
            main_frame,
            text=f"{self.lang.get('version', 'Version')} {app_data['app_info']['version']}",
            font=("Helvetica", 12),
            bg='white',
            fg='#666666'
        )
        version_label.pack(pady=(0, 10))

        # Description
        desc_label = tk.Label(
            main_frame,
            text=app_data["app_info"]["description"],
            font=("Helvetica", 10),
            bg='white',
            wraplength=450,
            justify='center'
        )
        desc_label.pack(pady=(0, 15))

        # Séparateur
        separator = tk.Frame(main_frame, height=1, bg='#CCCCCC')
        separator.pack(fill='x', pady=(0, 15))

        # Informations développeur
        dev_frame = tk.Frame(main_frame, bg='white')
        dev_frame.pack(fill='x', pady=(0, 10))

        tk.Label(
            dev_frame,
            text=f"{self.lang.get('developer', 'Développeur')} :",
            font=("Helvetica", 10, "bold"),
            bg='white'
        ).pack()

        tk.Label(
            dev_frame,
            text=app_data["developer"]["name"],
            font=("Helvetica", 10),
            bg='white'
        ).pack()

        tk.Label(
            dev_frame,
            text=app_data["developer"]["email"],
            font=("Helvetica", 10),
            bg='white',
            fg='#1976D2'
        ).pack()

        # Ajouter un bouton pour contacter le développeur (ouvrir le repo GitHub)
        def open_github():
            import webbrowser
            webbrowser.open_new('https://github.com/GGNatio/GendAlf')

        contact_btn = tk.Button(
            dev_frame,
            text="Contact / Repo GitHub",
            font=("Helvetica", 10, "bold"),
            bg="#1976D2",
            fg="white",
            cursor="hand2",
            command=open_github
        )
        contact_btn.pack(pady=(8, 0))

        # Informations techniques
        tech_frame = tk.Frame(main_frame, bg='white')
        tech_frame.pack(fill='x', pady=(10, 15))

        tk.Label(
            tech_frame,
            text=f"{self.lang.get('technical_info', 'Informations techniques')} :",
            font=("Helvetica", 10, "bold"),
            bg='white'
        ).pack()

        tech_info = f"• Python {app_data['technical']['python_version']}\n"
        tech_info += f"• {app_data['technical']['platform']} {app_data['technical']['architecture']}\n"
        tech_info += f"• Build: {app_data['app_info']['build']}"

        tk.Label( 
            tech_frame,
            text=tech_info,
            font=("Helvetica", 9),
            bg='white',
            justify='center'
        ).pack()

        # Fonctionnalités principales
        features_frame = tk.Frame(main_frame, bg='white')
        features_frame.pack(fill='x', pady=(0, 15))

        tk.Label(
            features_frame,
            text=f"{self.lang.get('main_features', 'Fonctionnalités principales')} :",
            font=("Helvetica", 10, "bold"),
            bg='white'
        ).pack()

        features_text = "\n".join([f"• {feature}" for feature in app_data["features"]])
        tk.Label(
            features_frame,
            text=features_text,
            font=("Helvetica", 9),
            bg='white',
            justify='center'
        ).pack()

        # Bind Escape pour fermer et focus sur la fenêtre
        self._about_window.bind('<Escape>', lambda e: self._about_window.destroy())
        self._about_window.focus_set()

    def smart_undo(self):
        """Fonction intelligente d'undo qui annule soit un pathtracking soit un dessin."""
        # Vérifier s'il y a des pathtrackings à annuler
        if hasattr(self, 'via_path_tracking') and self.via_path_tracking.pathtrackings:
            # Vérifier s'il y a un pathtracking récent sur la couche actuelle
            current_layer_pathtrackings = [p for p in self.via_path_tracking.pathtrackings if p['raw_id'] == self.raw_id]
            
            if current_layer_pathtrackings:
                # Demander à l'utilisateur ce qu'il veut annuler
                result = tk.messagebox.askyesnocancel(
                    "Annuler", 
                    "Que voulez-vous annuler ?\n\n"
                    "• Oui : Annuler le dernier pathtracking de cette couche\n"
                    "• Non : Annuler le dernier dessin\n"
                    "• Annuler : Ne rien faire"
                )
                
                if result is True:  # Oui - annuler pathtracking
                    self.via_path_tracking.undo_last_pathtracking_on_current_layer()
                    return
                elif result is False:  # Non - annuler dessin
                    self.toolsBox.draw.undo()
                    return
                # Si Annuler (None), ne rien faire
                return
        
        # Si pas de pathtracking sur la couche actuelle, annuler le dessin directement
        self.toolsBox.draw.undo()
    
    def showDocumentation(self):
        """Affiche la documentation du logiciel dans une fenêtre dédiée."""
        from pathlib import Path
        import tkinter as tk
        from tkinter import messagebox
        doc_path = Path(__file__).resolve().parent / "documentation.md"
        if not doc_path.exists():
            messagebox.showerror("Erreur", "Le fichier de documentation est introuvable.")
            return
        doc_win = tk.Toplevel(self.app)
        doc_win.title("Documentation GendALF")
        doc_win.geometry("800x700")
        doc_win.grab_set()
        doc_win.focus()
        text = tk.Text(doc_win, wrap='word', font=('Helvetica', 11), bg="#f8f8f8")
        text.pack(fill='both', expand=True)
        with open(doc_path, 'r', encoding='utf-8') as f:
            doc_content = f.read()
        text.insert('end', doc_content)
        text.config(state='disabled')
        scrollbar = tk.Scrollbar(doc_win, command=text.yview)
        text['yscrollcommand'] = scrollbar.set
        scrollbar.pack(side='right', fill='y')
        doc_win.bind('<Escape>', lambda e: doc_win.destroy())

    def create_log_on_exit(self):
        """Crée un fichier de log avec le contenu du terminal lors de la fermeture."""
        import datetime
        now = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        try:
            base_dir = Path(__file__).resolve().parent
            logs_dir = base_dir / "logs"
            logs_dir.mkdir(parents=True, exist_ok=True)
        except Exception:
            logs_dir = Path.cwd() / "logs"
            logs_dir.mkdir(parents=True, exist_ok=True)
        log_path = logs_dir / f"session_{now}.log"
        try:
            if hasattr(self, '_stdout_buffer'):
                log_content = self._stdout_buffer.getvalue()
            else:
                log_content = "[stdout non redirigé, impossible de capturer le terminal]"
            with open(log_path, 'w', encoding='utf-8') as f:
                f.write(log_content)
        except Exception:
            pass

    def on_close(self):
        """Handler appelé juste avant la fermeture de l'application."""
        # ... ta gestion de projet et préférences ici ...
        print("Fermeture de l'application. Merci d'avoir utilisé GendALF !")
        self.create_log_on_exit()
        
        self.app.destroy()
        
if __name__ == "__main__":
    # Créer et lancer l'interface RXViewer
    app = RXviewer()
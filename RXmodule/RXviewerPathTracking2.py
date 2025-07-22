import tkinter as tk
from tkinter import messagebox
import cv2
import numpy as np
import os
import json
import uuid

class RXviewer: ...

class RXviewerPathTracking2:
    def delete_pathtracking_like_right_click(self, pt):
        """
        Supprime un pathtracking (ou groupe intercouche) avec confirmation, comme le clic droit, mais en ciblant directement le pathtracking passé en argument.
        """
        from tkinter import messagebox
        if pt.get('is_intercouche', False):
            link_id = pt.get('link_id')
            linked_layer = pt.get('linked_layer')
            if messagebox.askyesno("Supprimer pathtracking intercouche",
                f"Ce pathtracking est lié à la couche {linked_layer + 1 if linked_layer is not None else '?'}."\
                f"\nSupprimer TOUS les pathtrackings liés ?"):
                # Supprimer tous les pathtrackings avec le même link_id
                self.pathtrackings = [p for p in self.pathtrackings if p.get('link_id') != link_id]
                self.save_pathtrackings_to_project()
                # Redessiner les calques des couches affectées
                affected_layers = set()
                for p in self.pathtrackings:
                    if p.get('link_id') == link_id:
                        affected_layers.add(p['raw_id'])
                affected_layers.add(self.app.raw_id)
                if linked_layer is not None:
                    affected_layers.add(linked_layer)
                for layer_id in affected_layers:
                    self.redraw_all_pathtrackings_on_layer(layer_id)
                self.app.displayImage()
                self._check_panel_visibility()
        else:
            if messagebox.askyesno("Supprimer pathtracking", "Supprimer ce pathtracking ?"):
                # Trouver l'index du pathtracking dans la liste (pour cohérence avec on_right_click)
                try:
                    idx = self.pathtrackings.index(pt)
                except ValueError:
                    idx = -1
                if idx != -1:
                    del self.pathtrackings[idx]
                    self.save_pathtrackings_to_project()
                    self.redraw_all_pathtrackings_on_layer(self.app.raw_id)
                    self.app.displayImage()
                    self._check_panel_visibility()
    def __init__(self, app: 'RXviewer') -> None:
        self.app = app
        self.pathtrackings = []
        self.layer_frames = {}  # Dictionnaire pour stocker les frames par couche
        self.expanded_layers = set()  # Set des couches expandées
        self._pt_visibility_vars = {}  # id(pt): tk.BooleanVar

    def update_pathtracking_panel(self):
        """Met à jour dynamiquement le panneau intégré avec la liste des pathtrackings."""
        frame = self.app.pathtracking_frame
        # Nettoyer le contenu
        for widget in frame.winfo_children():
            widget.destroy()

        if not self.pathtrackings:
            tk.Label(frame, text="Aucun pathtracking", bg="#f0f0f0", fg="#888").pack(pady=10)
            # Fermer le panneau si plus de pathtrackings
            if hasattr(self.app, 'hidePathtrackingPanel'):
                self.app.hidePathtrackingPanel()
            return

        # Grouper par photo/couche
        layers = {}
        for pt in self.pathtrackings:
            raw_id = pt.get('raw_id')
            layer = pt.get('layer', None)
            if raw_id is not None:
                key = f"Photo {raw_id+1}"
            elif layer is not None:
                key = f"Couche {layer}"
            else:
                key = "Inconnu"
            if key not in layers:
                layers[key] = []
            layers[key].append(pt)

        for key, pts in sorted(layers.items()):
            lf = tk.LabelFrame(frame, text=key, bg="#f0f0f0", fg="#333", font=("Arial", 10, "bold"))
            lf.pack(fill='x', padx=5, pady=5, anchor='n')
            # Ajout du bouton oeil pour la couche
            layer_raw_id = None
            # Extraire le raw_id de la couche (clé: "Photo X")
            if key.startswith("Photo "):
                try:
                    layer_raw_id = int(key.split(" ")[1]) - 1
                except Exception:
                    layer_raw_id = None
            # Variable de visibilité par couche
            if not hasattr(self, '_layer_visibility_vars'):
                self._layer_visibility_vars = {}
            if layer_raw_id is not None:
                if layer_raw_id not in self._layer_visibility_vars:
                    self._layer_visibility_vars[layer_raw_id] = tk.BooleanVar(value=True)
                layer_var = self._layer_visibility_vars[layer_raw_id]
                def on_layer_toggle(var=layer_var, raw_id=layer_raw_id):
                    # Toggle la visibilité du calque pathtracking pour cette couche
                    self._layer_visibility_vars[raw_id].set(var.get())
                    if hasattr(self.app, 'displayImage'):
                        self.app.displayImage()
                # Eye icon: open/closed
                eye_icon = '\U0001F441' if layer_var.get() else '\U0001F441\u200D\U0001F5E8'
                eye_btn = tk.Button(lf, text=eye_icon, width=2, font=("Arial", 12), relief='flat',
                                   bg="#f0f0f0", fg="#1976D2" if layer_var.get() else "#888")
                eye_btn.pack(side='left', padx=(0, 4), pady=2)
                def toggle_and_update(var=layer_var, raw_id=layer_raw_id, btn=eye_btn):
                    var.set(not var.get())
                    btn.config(text=('\U0001F441' if var.get() else '\U0001F441\u200D\U0001F5E8'), fg=("#1976D2" if var.get() else "#888"))
                    if hasattr(self.app, 'displayImage'):
                        self.app.displayImage()
                eye_btn.config(command=lambda v=layer_var, r=layer_raw_id, b=eye_btn: toggle_and_update(v, r, b))
            # Affichage des pathtrackings de la couche
            for pt in pts:
                row = tk.Frame(lf, bg="#f0f0f0")
                row.pack(fill='x', padx=5, pady=2)
                # Navigation button: click to go to image and center on start via
                nav_btn = tk.Button(row, text="Pathtracking", anchor='w', relief='flat', bg='#f8f8f8',
                                   font=("Arial", 9, "bold"),
                                   command=lambda p=pt: self.navigate_to_pathtracking(p, center_on_via=True))
                nav_btn.pack(side='left', fill='x', expand=True)
                # Info button
                info_btn = tk.Button(row, text="I", width=2, font=("Arial", 9, "bold"), fg="#1976D2", bg="#e0e0e0",
                                    command=lambda p=pt: self.show_pathtracking_info(p))
                info_btn.pack(side='right', padx=2)
                # Trash button
                trash_btn = tk.Button(row, text="🗑", width=2, font=("Arial", 10), fg="#B71C1C", bg="#f0f0f0",
                                      command=lambda p=pt: self.delete_pathtracking_like_right_click(p))
                trash_btn.pack(side='right', padx=2)
    def get_visible_pathtrackings(self):
        """Retourne la liste des pathtrackings visibles pour la couche courante (selon l'oeil de la couche)."""
        raw_id = self.app.raw_id if hasattr(self.app, 'raw_id') else None
        if not hasattr(self, '_layer_visibility_vars') or raw_id is None:
            return [pt for pt in self.pathtrackings if pt.get('raw_id', None) == raw_id]
        if self._layer_visibility_vars.get(raw_id, tk.BooleanVar(value=True)).get():
            return [pt for pt in self.pathtrackings if pt.get('raw_id', None) == raw_id]
        else:
            return []

    def show_pathtracking_info(self, pt):
        """Ouvre une fenêtre avec toutes les infos du pathtracking, image plus grande, toutes les infos bien notées."""
        import PIL.Image, PIL.ImageTk
        info = tk.Toplevel(self.app.app)
        info.title("Infos Pathtracking")
        info.geometry("440x540")
        info.resizable(True, True)
        info.grab_set()

        # --- Zone scrollable ---
        canvas = tk.Canvas(info, borderwidth=0, background="#f8f8f8", width=420, height=500)
        vscroll = tk.Scrollbar(info, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=vscroll.set)
        vscroll.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        scroll_frame = tk.Frame(canvas, background="#f8f8f8")
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")

        def _on_frame_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
        scroll_frame.bind("<Configure>", _on_frame_configure)

        # Titre
        tk.Label(scroll_frame, text=f"Pathtracking sur Photo {pt.get('raw_id', '?')}", font=("Arial", 13, "bold"), pady=4, bg="#f8f8f8").pack()

        # Affichage miniature image (plus petit)
        img_frame = tk.Frame(scroll_frame, bg="#f8f8f8")
        img_frame.pack(pady=2)
        raw_id = pt.get('raw_id')
        img_label = tk.Label(img_frame, bg="#f8f8f8")
        img_label.pack()
        if raw_id is not None and hasattr(self.app, 'raw') and self.app.raw.raw and 0 <= raw_id < len(self.app.raw.raw):
            arr = self.app.raw.raw[raw_id].raw
            try:
                img = PIL.Image.fromarray(arr)
                img.thumbnail((180, 180))
                img_tk = PIL.ImageTk.PhotoImage(img)
                img_label.configure(image=img_tk)
                img_label.image = img_tk
            except Exception as e:
                img_label.configure(text=f"Erreur image: {e}")
        else:
            img_label.configure(text="Image non trouvée")

        # Infos détaillées (compact)
        details = tk.Frame(scroll_frame, bg="#f8f8f8")
        details.pack(pady=4, fill='x')
        def add_row(label, value):
            f = tk.Frame(details, bg="#f8f8f8")
            f.pack(fill='x', pady=0, padx=6)
            tk.Label(f, text=label, width=18, anchor='w', font=("Arial", 10, "bold"), bg="#f8f8f8").pack(side='left')
            tk.Label(f, text=str(value), anchor='w', font=("Arial", 10), bg="#f8f8f8").pack(side='left')

        add_row("Photo (raw_id)", pt.get('raw_id', ''))
        add_row("Couche", pt.get('layer', ''))
        add_row("Départ (x, y)", pt.get('start', ''))
        add_row("Arrivée (x, y)", pt.get('end', ''))
        add_row("Taille (px)", pt.get('length', ''))
        add_row("Couleur", pt.get('color', ''))
        # Vias traversés
        traversed = pt.get('traversed_vias', [])
        add_row("Nb vias traversés", len(traversed))
        if traversed:
            for i, via in enumerate(traversed):
                add_row(f"  Via {i+1} (id)", via.get('id', '?'))
                add_row(f"    Centre", via.get('center', ''))
                add_row(f"    Rayon", via.get('radius', ''))
        # Via de départ/arrivée
        if 'start_via' in pt:
            sv = pt['start_via']
            add_row("Via départ (id)", sv.get('id', ''))
            add_row("  Centre", sv.get('center', ''))
            add_row("  Rayon", sv.get('radius', ''))
        if 'end_via' in pt:
            ev = pt['end_via']
            add_row("Via arrivée (id)", ev.get('id', ''))
            add_row("  Centre", ev.get('center', ''))
            add_row("  Rayon", ev.get('radius', ''))
        # Divers
        if 'is_intercouche' in pt:
            add_row("Intercouche", pt['is_intercouche'])
        if 'link_id' in pt:
            add_row("Link ID", pt['link_id'])
        if 'linked_layer' in pt:
            add_row("Linked Layer", pt['linked_layer'])
        if 'has_end_via' in pt:
            add_row("A une via d'arrivée", pt['has_end_via'])
        # Points et autres
        if 'points' in pt:
            add_row("Nb points", len(pt['points']))
        if 'created_at' in pt:
            add_row("Créé le", pt['created_at'])
        if 'author' in pt:
            add_row("Auteur", pt['author'])

        # Zone brute JSON (plus compacte)
        import json
        from tkinter.scrolledtext import ScrolledText
        tk.Label(scroll_frame, text="Données brutes :", font=("Arial", 8, "bold"), fg="#888", bg="#f8f8f8").pack(pady=(4,0))
        st = ScrolledText(scroll_frame, height=5, width=48, font=("Consolas", 7))
        st.pack(padx=6)
        st.insert('end', json.dumps(pt, indent=2, ensure_ascii=False))
        st.config(state='disabled')

        tk.Button(scroll_frame, text="Fermer", command=info.destroy).pack(pady=6)

        # Support molette pour le scroll
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)

    def navigate_to_pathtracking(self, pt, center_on_via=False):
        """Navigue vers l'image concernée par le pathtracking et centre sur le via de départ si demandé."""
        raw_id = pt.get('raw_id')
        if raw_id is not None:
            self.app.raw_id = raw_id
            # Center on start via if requested
            if center_on_via and 'start_via' in pt and pt['start_via'] and 'center' in pt['start_via']:
                via_x, via_y = pt['start_via']['center']
                # Center the image on the via (adjust raw_coords)
                if hasattr(self.app, 'raw') and hasattr(self.app.raw, 'raw') and self.app.raw.raw:
                    img = self.app.raw.raw[raw_id].raw
                    can_w, can_h = self.app.can.winfo_width(), self.app.can.winfo_height()
                    img_h, img_w = img.shape[0], img.shape[1]
                    # Center the via in the canvas
                    new_x = can_w // 2 - via_x
                    new_y = can_h // 2 - via_y
                    self.app.raw.raw_coords = [new_x, new_y]
            self.app.displayImage()
    def confirm_delete_pathtracking(self, pt):
        """Demande confirmation avant suppression du pathtracking."""
        from tkinter import messagebox
        if messagebox.askyesno("Supprimer le pathtracking", "Voulez-vous vraiment supprimer ce pathtracking ?"):
            self.delete_pathtracking(pt)

    def delete_pathtracking(self, pt):
        """Supprime un pathtracking du panneau et met à jour l'affichage."""
        if pt in self.pathtrackings:
            self.pathtrackings.remove(pt)
            pt_id = id(pt)
            if pt_id in self._pt_visibility_vars:
                del self._pt_visibility_vars[pt_id]
            self.update_pathtracking_panel()
            if hasattr(self.app, 'displayImage'):
                self.app.displayImage()

    def show_panel(self):
        """Affiche le panneau intégré à gauche."""
        self.app.showPathtrackingPanel()
        self.update_pathtracking_panel()

    def hide_panel(self):
        self.app.hidePathtrackingPanel()

    def add_pathtracking(self, pt):
        self.pathtrackings.append(pt)
        self.update_pathtracking_panel()

    def clear_pathtrackings(self):
        self.pathtrackings.clear()
        self.update_pathtracking_panel()

    def pathTracking(self, event: tk.Event):
        if not self.app.raw.raw:
            return

        # --- Vérification de l'étalonnage des vias ---
        if not self._check_vias_calibrated():
            tk.messagebox.showerror(
                "Vias non étalonnés",
                "Les vias ne sont pas étalonnés !\n\n"
                "Avant de faire du pathtracking, vous devez :\n"
                "1. Aller dans le menu 'Projet' puis 'Étalonnage des vias'\n"
                "2. Étalonner les vias en cliquant sur les vias de votre circuit, ou en les détectants manuellement\n"
                "3. Sauvegarder l'étalonnage\n\n"
                "Le pathtracking utilise les vias pour déterminer les points de départ et d'arrivée optimaux."
            )
            return

        # --- Gestion multicouche ---
        if getattr(self.app.toolsBox, "intercouche_var", None) and self.app.toolsBox.intercouche_var.get():
            self._pathTracking_intercouche(event.x, event.y)
            return

        # --- PathTracking de base ---
        self._pathTracking_internal_with_link(event.x, event.y)

    def _pathTracking_internal(self, x, y):
        # Récupérer la tolérance depuis la toolbox
        tolerance_direct = self.app.toolsBox.path_tolerance
        
        # Forcer une mise à jour de la tolérance depuis le scale si il existe
        if hasattr(self.app.toolsBox, '_setting_scale'):
            scale_value = self.app.toolsBox._setting_scale.get()
            scale_label = self.app.toolsBox._setting_scale.cget("label").lower()
            if any(word in scale_label for word in ["tolérance", "tolerance", "tolérence", "tolerence"]):
                self.app.toolsBox.path_tolerance = scale_value
        
        tolerance = self.app.toolsBox.path_tolerance
        
        zoom = getattr(self.app.toolsBox, "raw_zoom", 1.0)
        coords = getattr(self.app.raw, "raw_coords", [0, 0])
        x_canvas = x - coords[0]
        y_canvas = y - coords[1]
        x = int(x_canvas / zoom)
        y = int(y_canvas / zoom)

        image_orig = self.app.raw.raw[self.app.raw_id].raw
        if len(image_orig.shape) == 3:
            img = cv2.cvtColor(image_orig, cv2.COLOR_BGR2GRAY)
        else:
            img = image_orig.copy()

        h, w = img.shape
        
        # Vérifier que le point de départ est valide
        if not (0 <= x < w and 0 <= y < h):
            return
            
        ref_val = int(img[y, x])
        
        # Flood fill avec tolérance
        visited = np.zeros((h, w), dtype=bool)
        piste_points = []
        stack = [(y, x)]
        
        MAX_PIXELS = 100000
        
        while stack and len(piste_points) < MAX_PIXELS:
            cy, cx = stack.pop()
            
            if visited[cy, cx]:
                continue
                
            # Vérifier si le pixel appartient à la piste
            pixel_val = int(img[cy, cx])
            if abs(pixel_val - ref_val) > tolerance:
                continue
                
            visited[cy, cx] = True
            piste_points.append((cy, cx))
            
            # Ajouter les voisins 8-connectés
            for dy in [-1, 0, 1]:
                for dx in [-1, 0, 1]:
                    if dy == 0 and dx == 0:
                        continue
                    ny, nx = cy + dy, cx + dx
                    if (0 <= ny < h and 0 <= nx < w and 
                        not visited[ny, nx]):
                        neighbor_val = int(img[ny, nx])
                        if abs(neighbor_val - ref_val) <= tolerance:
                            stack.append((ny, nx))

        if len(piste_points) >= MAX_PIXELS:
            tk.messagebox.showwarning(
                "Tolérance trop élevée",
                f"Plus de {MAX_PIXELS} pixels trouvés.\nLa tolérance ({tolerance}) est probablement trop élevée."
            )
            return

        if len(piste_points) <= 1:
            tk.messagebox.showinfo(
                "Aucune piste",
                f"Aucune piste trouvée au point ({x}, {y}).\nValeur pixel: {ref_val}, tolérance: {tolerance}"
            )
            return

        # Sauvegarde dans l'historique pour undo
        if hasattr(self.app.toolsBox, "draw"):
            draw = self.app.toolsBox.draw
            if hasattr(draw, "_history"):
                draw._history.append((
                    self.app.raw.raw[self.app.raw_id].raw.copy(),
                    self.app.raw.raw[self.app.raw_id].draw.copy() if hasattr(self.app.raw.raw[self.app.raw_id], "draw") else None,
                    getattr(draw, "_draw_image", None).copy() if hasattr(draw, "_draw_image") else None
                ))
                if hasattr(draw, "_history_undo"):
                    draw._history_undo.clear()

        # Charger les vias du projet pour trouver le point de départ optimal
        vias = self._load_vias_from_project()
        
        # Trouver le via le plus proche de la piste
        start_py, start_px = y, x  # Par défaut, utiliser le point de clic
        
        if vias:
            min_via_dist = float('inf')
            closest_via = None
            closest_via_index = -1
            
            # Chercher le via le plus proche du POINT DE CLIC (pas de toute la piste)
            for via_index, via in enumerate(vias):
                via_x, via_y = via['center']
                
                # Calculer la distance entre ce via et le POINT DE CLIC INITIAL
                dist_to_click = np.hypot(y - via_y, x - via_x)
                
                # Si ce via est plus proche du point de clic que les précédents
                if dist_to_click < min_via_dist:
                    min_via_dist = dist_to_click
                    closest_via = via
                    closest_via_index = via_index
            
            # Si on a trouvé un via proche, placer le point vert directement sur le via
            if closest_via:
                start_px, start_py = closest_via['center']

        # Trouver le point le plus éloigné du point de départ optimal
        max_dist = 0
        end_py, end_px = start_py, start_px
        for py, px in piste_points:
            dist = np.hypot(py - start_py, px - start_px)
            if dist > max_dist:
                max_dist = dist
                end_py, end_px = py, px

        # Détecter tous les vias traversés par la piste avec un algorithme plus strict
        VIA_PROXIMITY_THRESHOLD = 12  # Distance maximum réduite pour être plus strict
        MIN_POINTS_REQUIRED = 8  # Plus de points requis pour confirmer un traversement
        traversed_vias = []
        end_via = None
        
        if vias:
            # Pour chaque via, vérifier s'il est réellement traversé par la piste
            for i, via in enumerate(vias):
                via_x, via_y = via['center']
                
                # Compter combien de points de piste sont très proches du via
                close_points = []
                for py, px in piste_points:
                    dist = np.hypot(py - via_y, px - via_x)
                    if dist <= VIA_PROXIMITY_THRESHOLD:
                        close_points.append((py, px))
                
                # Algorithme plus strict : besoin de beaucoup de points proches
                if len(close_points) >= MIN_POINTS_REQUIRED:
                    traversed_vias.append(via)
            
            # Identifier le via de fin (celui le plus proche de l'extrémité)
            if traversed_vias:
                min_end_via_dist = float('inf')
                for via in traversed_vias:
                    via_x, via_y = via['center']
                    dist_to_end = np.hypot(end_py - via_y, end_px - via_x)
                    
                    if dist_to_end < min_end_via_dist:
                        min_end_via_dist = dist_to_end
                        end_via = via
                
                # Si on a trouvé un via proche de l'extrémité, placer le point de fin sur le via
                if end_via and min_end_via_dist <= VIA_PROXIMITY_THRESHOLD:
                    end_px, end_py = end_via['center']

        # Sauvegarder le pathtracking avec les informations des vias traversés
        pathtracking_data = {
            'raw_id': self.app.raw_id,
            'start': (start_px, start_py),
            'end': (end_px, end_py),
            'piste_points': piste_points,  # Conserver les points de la piste pour le redessin
            'has_end_via': end_via is not None,  # Indiquer s'il y a un via à la fin
            'traversed_vias': [{'center': via['center'], 'id': via.get('id', i)} for i, via in enumerate(traversed_vias)],  # Vias traversés
            'start_via': closest_via,  # Via de départ (défini plus haut)
            'end_via': end_via,  # Via de fin
            'color': self.app.toolsBox.draw_color  # Couleur sélectionnée dans la toolbox
        }
        self.pathtrackings.append(pathtracking_data)
        self.save_pathtrackings_to_project()
        
        # Dessiner le pathtracking sur l'image pathtracking correspondante
        self.draw_pathtracking_on_layer(pathtracking_data)
        
        # Afficher l'image mise à jour
        self.app.displayImage()
        
        # Vérifier la visibilité du panneau
        self._check_panel_visibility()

    def draw_pathtracking_vias(self, pathtracking_data, image):
        """Dessine tous les vias traversés par un pathtracking sur l'image."""
        # Dessiner tous les vias traversés avec des couleurs différentes
        traversed_vias = pathtracking_data.get('traversed_vias', [])
        start_via = pathtracking_data.get('start_via')
        end_via = pathtracking_data.get('end_via')
        
        # Couleurs pour les vias intermédiaires (format BGR pour OpenCV)
        intermediate_colors = [
            (255, 255, 0),    # cyan (BGR)
            (0, 255, 255),    # jaune (BGR)
            (128, 0, 128),    # violet (BGR)
            (0, 165, 255),    # orange (BGR)
            (128, 128, 0),    # teal (BGR)
            (0, 128, 128),    # olive (BGR)
            (192, 192, 192),  # gris clair (BGR)
        ]
        
        # Adapter les couleurs selon le format de l'image (BGR ou BGRA)
        if len(image.shape) == 3 and image.shape[2] == 4:
            # Image BGRA : ajouter canal alpha
            intermediate_colors = [(*color, 255) for color in intermediate_colors]
            green_color = (0, 255, 0, 255)    # VERT en BGRA
            blue_color = (255, 0, 0, 255)     # BLEU en BGRA
            red_color = (0, 0, 255, 255)      # ROUGE en BGRA
        else:
            # Image BGR : utiliser couleurs normales
            green_color = (0, 255, 0)         # VERT en BGR
            blue_color = (255, 0, 0)          # BLEU en BGR
            red_color = (0, 0, 255)           # ROUGE en BGR
        
        # Dessiner TOUS les vias traversés avec des couleurs différentes
        color_index = 0
        for via in traversed_vias:
            color = intermediate_colors[color_index % len(intermediate_colors)]
            cv2.circle(image, via['center'], 7, color, -1)
            color_index += 1
        
        # Dessiner les points de départ et d'arrivée PAR-DESSUS (priorité sur les autres)
        cv2.circle(image, pathtracking_data['start'], 7, green_color, -1)    # VERT - point de départ
        
        # Choisir la couleur du point d'arrivée selon s'il y a un via ou pas
        if pathtracking_data.get('has_end_via', False):
            # Point BLEU si l'extrémité est sur un via
            cv2.circle(image, pathtracking_data['end'], 7, blue_color, -1)  # BLEU - fin sur via
        else:
            # Point ROUGE si l'extrémité n'est pas sur un via
            cv2.circle(image, pathtracking_data['end'], 7, red_color, -1)  # ROUGE - fin libre



    def save_pathtrackings_to_project(self):
        """Sauvegarde tous les pathtrackings dans le pathtrackings.json du dossier projet."""
        pathtrackings_json = os.path.join(self.app.current_project, "pathtrackings.json")
        try:
            # On ne sauvegarde que les données sérialisables (pas les piste_points)
            data = {
                "pathtrackings": [
                    {
                        "raw_id": p["raw_id"],
                        "start": p["start"],
                        "end": p["end"],
                        "has_end_via": p.get("has_end_via", False),
                        "traversed_vias": p.get("traversed_vias", []),
                        "start_via": p.get("start_via"),
                        "end_via": p.get("end_via"),
                        "color": p.get("color", "#FF0000"),  # Couleur du pathtracking (rouge par défaut)
                        "link_id": p.get("link_id"),  # ID de liaison intercouche
                        "linked_layer": p.get("linked_layer"),  # Couche liée
                        "is_intercouche": p.get("is_intercouche", False)  # Marqueur intercouche
                    }
                    for p in self.pathtrackings
                ]
            }

            with open(pathtrackings_json, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Erreur lors de la sauvegarde des pathtrackings: {e}")

    def load_pathtrackings_from_project(self):
        """Recharge les pathtrackings depuis le pathtrackings.json du dossier projet."""
        pathtrackings_json = os.path.join(self.app.current_project, "pathtrackings.json")
        try:
            with open(pathtrackings_json, "r", encoding="utf-8") as f:
                data = json.load(f)
            # Charger les pathtrackings et ajouter une couleur par défaut si manquante
            self.pathtrackings = []
            for p in data.get("pathtrackings", []):
                # Ajouter une couleur par défaut si elle n'existe pas
                if "color" not in p:
                    p["color"] = "#FF0000"  # Rouge par défaut
                # Ajouter les champs de liaison par défaut s'ils n'existent pas
                if "link_id" not in p:
                    p["link_id"] = None
                if "linked_layer" not in p:
                    p["linked_layer"] = None
                if "is_intercouche" not in p:
                    p["is_intercouche"] = False
                self.pathtrackings.append(p)
        except Exception as e:
            self.pathtrackings = []
        
        # Vérifier la visibilité du panneau après le chargement
        self._check_panel_visibility()

    def on_right_click(self, event: tk.Event):
        """
        Supprime uniquement le pathtracking le plus proche du clic sur la couche courante,
        sans toucher aux autres pathtrackings.
        """
        zoom = getattr(self.app.toolsBox, "raw_zoom", 1.0)
        coords = getattr(self.app.raw, "raw_coords", [0, 0])
        x_canvas = event.x - coords[0]
        y_canvas = event.y - coords[1]
        x = int(x_canvas / zoom)
        y = int(y_canvas / zoom)

        # Recherche du pathtracking le plus proche sur la couche courante
        closest_pathtracking = None
        closest_distance = float('inf')
        closest_index = -1

        for i, path in enumerate(self.pathtrackings):
            if path.get('raw_id', None) == self.app.raw_id:
                # Distance au point de départ
                sx, sy = path['start']
                start_dist = np.hypot(x - sx, y - sy)
                # Distance au point de fin
                ex, ey = path['end']
                end_dist = np.hypot(x - ex, y - ey)
                # Distance aux points de la piste
                piste_dist = float('inf')
                if 'piste_points' in path:
                    for py, px in path['piste_points']:
                        dist = np.hypot(x - px, y - py)
                        if dist < piste_dist:
                            piste_dist = dist
                # Distance minimale
                min_dist = min(start_dist, end_dist, piste_dist)
                if min_dist < closest_distance and min_dist <= 15:
                    closest_distance = min_dist
                    closest_pathtracking = path
                    closest_index = i

        # Suppression sélective
        if closest_pathtracking is not None:
            # Vérifier si c'est un pathtracking intercouche
            if closest_pathtracking.get('is_intercouche', False):
                link_id = closest_pathtracking.get('link_id')
                linked_layer = closest_pathtracking.get('linked_layer')
                
                # Demander confirmation pour supprimer tout le groupe lié
                if messagebox.askyesno("Supprimer pathtracking intercouche", 
                    f"Ce pathtracking est lié à la couche {linked_layer + 1}.\n"
                    f"Supprimer TOUS les pathtrackings liés ?\n"
                    f"(Distance: {closest_distance:.1f} pixels)"):
                    
                    # Supprimer tous les pathtrackings avec le même link_id
                    self.pathtrackings = [p for p in self.pathtrackings if p.get('link_id') != link_id]
                    self.save_pathtrackings_to_project()
                    
                    # Redessiner les calques des couches affectées
                    affected_layers = set()
                    for p in self.pathtrackings:
                        if p.get('link_id') == link_id:
                            affected_layers.add(p['raw_id'])
                    
                    # Ajouter les couches actuelles et liées
                    affected_layers.add(self.app.raw_id)
                    if linked_layer is not None:
                        affected_layers.add(linked_layer)
                    
                    for layer_id in affected_layers:
                        self.redraw_all_pathtrackings_on_layer(layer_id)
                    
                    self.app.displayImage()
                    # Vérifier la visibilité du panneau
                    self._check_panel_visibility()
            else:
                # Pathtracking normal
                if messagebox.askyesno("Supprimer pathtracking", f"Supprimer ce pathtracking ?\n(Distance: {closest_distance:.1f} pixels)"):
                    del self.pathtrackings[closest_index]
                    self.save_pathtrackings_to_project()
                    self.redraw_all_pathtrackings_on_layer(self.app.raw_id)
                    self.app.displayImage()
                    # Vérifier la visibilité du panneau
                    self._check_panel_visibility()

    def undo_last_pathtracking_on_current_layer(self):
        """
        Annule uniquement le dernier pathtracking de la couche courante (contrôle Z).
        """
        if not self.pathtrackings:
            tk.messagebox.showinfo("Undo", "Aucun pathtracking à annuler.")
            return

        # Indices des pathtrackings de la couche courante
        current_layer_indices = [i for i, p in enumerate(self.pathtrackings) if p['raw_id'] == self.app.raw_id]
        if not current_layer_indices:
            tk.messagebox.showinfo("Undo", "Aucun pathtracking à annuler sur cette couche.")
            return

        # Supprimer le dernier pathtracking de la couche courante
        last_index = current_layer_indices[-1]
        del self.pathtrackings[last_index]
        self.save_pathtrackings_to_project()
        self.redraw_all_pathtrackings_on_layer(self.app.raw_id)
        self.app.displayImage()
        tk.messagebox.showinfo("Undo", f"Dernier pathtracking annulé sur la couche {self.app.raw_id + 1}.")
        # Vérifier la visibilité du panneau
        self._check_panel_visibility()

    def reset_layer_to_original(self, raw_id):
        """Recharge l'image d'origine de la couche (sans pathtrackings)."""
        try:
            project_json = os.path.join(self.app.current_project, "project.json")
            data = {}
            
            # Charger le project.json s'il existe
            if os.path.exists(project_json):
                try:
                    with open(project_json, "r", encoding="utf-8") as f:
                        data = json.load(f)
                except:
                    pass
            
            # Vérifier si l'image originale existe dans le JSON
            if "original_images" in data and str(raw_id) in data["original_images"]:
                orig_path = os.path.join(self.app.current_project, data["original_images"][str(raw_id)])
                if os.path.exists(orig_path):
                    image = cv2.imread(orig_path)
                    if image is not None:
                        self.app.raw.raw[raw_id].raw = image
                        return
            
            # Si l'image originale n'existe pas, charger depuis le dossier edit
            if hasattr(self.app.raw.raw[raw_id], 'filename'):
                edit_path = os.path.join(self.app.current_project, "edit", self.app.raw.raw[raw_id].filename)
                if os.path.exists(edit_path):
                    image = cv2.imread(edit_path)
                    if image is not None:
                        self.app.raw.raw[raw_id].raw = image
                        return
                
                # En dernier recours, charger depuis le dossier raw
                raw_path = os.path.join(self.app.current_project, "raw", self.app.raw.raw[raw_id].filename)
                if os.path.exists(raw_path):
                    image = cv2.imread(raw_path)
                    if image is not None:
                        self.app.raw.raw[raw_id].raw = image
                        return
                    
        except Exception as e:
            # En cas d'erreur, afficher le message d'erreur mais ne pas planter
            tk.messagebox.showwarning("Erreur", f"Impossible de réinitialiser la couche : {e}")
            
        # Si aucune image n'a pu être chargée, ne rien faire

    def _load_vias_from_project(self):
        """Charge les vias du projet courant pour le calcul du point de départ optimal."""
        if not self.app.current_project:
            return []
            
        project_path = self.app.current_project / 'project.json'
        
        try:
            with open(project_path, 'r', encoding='utf-8') as file:
                project_data = json.load(file)
                
            # Charger les vias existants
            vias = []
            if 'vias' in project_data and project_data['vias']:
                for via_record in project_data['vias']:
                    via_data = {
                        'center': via_record['center'],
                        'radius': via_record['radius'],
                        'image_index': via_record.get('image_index', 0),
                    }
                    vias.append(via_data)
            
            return vias
                    
        except Exception as e:
            # En cas d'erreur, retourner une liste vide (pas d'erreur critique)
            return []

    def hex_to_rgb(self, hex_color):
        """Convertit une couleur hexadécimale en couleur RGB (format natif souhaité)."""
        # Retirer le # s'il est présent
        hex_color = hex_color.lstrip('#')
        
        # Convertir les composantes RGB
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        
        # Retourner en format RGB natif (255,0,0 = rouge)
        return (r, g, b)

    def display_pathtrackings_on_current_layer(self):
        """Affiche tous les pathtrackings de la couche courante."""
        if not self.app.raw.raw:
            return
            
        # Charger les pathtrackings de la couche courante
        current_layer_pathtrackings = [p for p in self.pathtrackings if p['raw_id'] == self.app.raw_id]
        
        if current_layer_pathtrackings:
            # Redessiner tous les pathtrackings sur le calque
            self.redraw_all_pathtrackings_on_layer(self.app.raw_id)
            
            # Afficher l'image mise à jour
            self.app.displayImage()

    def draw_pathtracking_on_layer(self, pathtracking_data):
        """Dessine un pathtracking sur l'image calque correspondante dans le dossier pathtracking."""
        try:
            # Construire le chemin vers l'image pathtracking correspondante
            if hasattr(self.app.raw.raw[self.app.raw_id], 'filename'):
                pathtracking_filename = self.app.raw.raw[self.app.raw_id].filename
            else:
                # Utiliser un nom par défaut basé sur l'ID
                pathtracking_filename = f"slice{self.app.raw_id:05d}.png"
            
            pathtracking_path = os.path.join(self.app.current_project, "pathtracking", pathtracking_filename)
            
            # Charger l'image pathtracking existante ou créer une image transparente
            if os.path.exists(pathtracking_path):
                pathtracking_image = cv2.imread(pathtracking_path, cv2.IMREAD_UNCHANGED)
            else:
                # Créer une image transparente de la même taille que l'image edit
                edit_path = os.path.join(self.app.current_project, "edit", pathtracking_filename)
                if os.path.exists(edit_path):
                    edit_image = cv2.imread(edit_path)
                    h, w = edit_image.shape[:2]
                    # Créer une image transparente (4 canaux : BGRA)
                    pathtracking_image = np.zeros((h, w, 4), dtype=np.uint8)
                else:
                    # Taille par défaut si l'image edit n'existe pas
                    pathtracking_image = np.zeros((1000, 1000, 4), dtype=np.uint8)
            
            # S'assurer que l'image pathtracking a 4 canaux (BGRA)
            if len(pathtracking_image.shape) == 3 and pathtracking_image.shape[2] == 3:
                # Convertir BGR en BGRA (ajouter canal alpha)
                pathtracking_image = cv2.cvtColor(pathtracking_image, cv2.COLOR_BGR2BGRA)
            elif len(pathtracking_image.shape) == 2:
                # Convertir grayscale en BGRA
                pathtracking_image = cv2.cvtColor(pathtracking_image, cv2.COLOR_GRAY2BGRA)
            
            # Obtenir la couleur du pathtracking en RGB
            pathtracking_color_rgb = self.hex_to_rgb(pathtracking_data.get('color', '#FF0000'))
            # Convertir RGB en BGR pour OpenCV
            pathtracking_color_bgr = (pathtracking_color_rgb[2], pathtracking_color_rgb[1], pathtracking_color_rgb[0])
            pathtracking_color_bgra = (*pathtracking_color_bgr, 255)  # Ajouter alpha=255 (opaque)
            
            # Dessiner les points de la piste
            if 'piste_points' in pathtracking_data:
                for py, px in pathtracking_data['piste_points']:
                    if 0 <= py < pathtracking_image.shape[0] and 0 <= px < pathtracking_image.shape[1]:
                        pathtracking_image[py, px] = pathtracking_color_bgra
            
            # Dessiner les vias et points sur l'image pathtracking
            self.draw_pathtracking_vias(pathtracking_data, pathtracking_image)
            
            # Sauvegarder l'image pathtracking mise à jour
            cv2.imwrite(pathtracking_path, pathtracking_image)
            
        except Exception as e:
            print(f"Erreur lors du dessin sur le calque pathtracking : {e}")

    def redraw_all_pathtrackings_on_layer(self, raw_id):
        """Redessine tous les pathtrackings d'une couche sur son image calque."""
        try:
            # Construire le chemin vers l'image pathtracking correspondante
            if hasattr(self.app.raw.raw[raw_id], 'filename'):
                pathtracking_filename = self.app.raw.raw[raw_id].filename
            else:
                pathtracking_filename = f"slice{raw_id:05d}.png"
            
            pathtracking_path = os.path.join(self.app.current_project, "pathtracking", pathtracking_filename)
            
            # Créer une image transparente de la même taille que l'image edit
            edit_path = os.path.join(self.app.current_project, "edit", pathtracking_filename)
            if os.path.exists(edit_path):
                edit_image = cv2.imread(edit_path)
                h, w = edit_image.shape[:2]
                # Créer une image transparente (4 canaux : BGRA)
                pathtracking_image = np.zeros((h, w, 4), dtype=np.uint8)
            else:
                # Taille par défaut si l'image edit n'existe pas
                pathtracking_image = np.zeros((1000, 1000, 4), dtype=np.uint8)
            
            # Dessiner tous les pathtrackings de cette couche
            current_layer_pathtrackings = [p for p in self.pathtrackings if p['raw_id'] == raw_id]
            for p in current_layer_pathtrackings:
                # Obtenir la couleur du pathtracking en RGB
                pathtracking_color_rgb = self.hex_to_rgb(p.get('color', '#FF0000'))
                # Convertir RGB en BGR pour OpenCV
                pathtracking_color_bgr = (pathtracking_color_rgb[2], pathtracking_color_rgb[1], pathtracking_color_rgb[0])
                pathtracking_color_bgra = (*pathtracking_color_bgr, 255)  # Ajouter alpha=255 (opaque)
                
                # Dessiner les points de la piste
                if 'piste_points' in p:
                    for py, px in p['piste_points']:
                        if 0 <= py < pathtracking_image.shape[0] and 0 <= px < pathtracking_image.shape[1]:
                            pathtracking_image[py, px] = pathtracking_color_bgra
                
                # Dessiner les vias et points sur l'image pathtracking
                self.draw_pathtracking_vias(p, pathtracking_image)
            
            # Sauvegarder l'image pathtracking mise à jour
            cv2.imwrite(pathtracking_path, pathtracking_image)
            
        except Exception as e:
            print(f"Erreur lors du redessin des pathtrackings : {e}")

    def undo_last_pathtracking(self):
        """Annule uniquement le dernier pathtracking ajouté."""
        if not self.pathtrackings:
            tk.messagebox.showinfo("Undo", "Aucun pathtracking à annuler.")
            return
        
        # Trouver le dernier pathtracking ajouté (le plus récent dans la liste)
        last_pathtracking = self.pathtrackings[-1]
        last_raw_id = last_pathtracking['raw_id']
        
        # Supprimer le dernier pathtracking
        self.pathtrackings.pop()
        self.save_pathtrackings_to_project()
        
        # Redessiner tous les pathtrackings restants sur le calque du dernier pathtracking
        self.redraw_all_pathtrackings_on_layer(last_raw_id)
        
        # Si le dernier pathtracking était sur la couche actuelle, rafraîchir l'affichage
        if last_raw_id == self.app.raw_id:
            self.app.displayImage()
        
        tk.messagebox.showinfo("Undo", f"Dernier pathtracking annulé (couche {last_raw_id + 1}).")
        # Vérifier la visibilité du panneau
        self._check_panel_visibility()

    def undo_last_pathtracking_on_current_layer(self):
        """Annule uniquement le dernier pathtracking de la couche actuelle."""
        if not self.pathtrackings:
            tk.messagebox.showinfo("Undo", "Aucun pathtracking à annuler.")
            return
        
        # Trouver tous les pathtrackings de la couche actuelle
        current_layer_pathtrackings = [i for i, p in enumerate(self.pathtrackings) if p['raw_id'] == self.app.raw_id]
        
        if not current_layer_pathtrackings:
            tk.messagebox.showinfo("Undo", "Aucun pathtracking à annuler sur cette couche.")
            return
        
        # Supprimer le dernier pathtracking de la couche actuelle
        last_index = current_layer_pathtrackings[-1]
        del self.pathtrackings[last_index]
        self.save_pathtrackings_to_project()
        
        # Redessiner tous les pathtrackings restants sur le calque
        self.redraw_all_pathtrackings_on_layer(self.app.raw_id)
        
        # Rafraîchir l'affichage
        self.app.displayImage()
        
        tk.messagebox.showinfo("Undo", f"Dernier pathtracking de la couche {self.app.raw_id + 1} annulé.")
        # Vérifier la visibilité du panneau
        self._check_panel_visibility()

    def _pathTracking_intercouche(self, x, y):
        """
        Pathtracking intercouche avec liaison bidirectionnelle complète.
        Fait le pathtracking complet sur les deux couches (points verts ET bleus/rouges).
        """
        # --- Vérification de l'étalonnage des vias ---
        if not self._check_vias_calibrated():
            tk.messagebox.showerror(
                "Vias non étalonnés",
                "Les vias ne sont pas étalonnés !\n\n"
                "Avant de faire du pathtracking intercouche, vous devez :\n"
                "1. Aller dans le menu 'Via' ou utiliser l'outil Via\n"
                "2. Étalonner les vias en cliquant sur les vias de votre circuit\n"
                "3. Sauvegarder l'étalonnage\n\n"
                "Le pathtracking intercouche nécessite absolument des vias étalonnés\n"
                "pour déterminer les points de correspondance entre les couches."
            )
            return

        # Étape 1: Trouver la couche cible la plus similaire
        edit_dir = str(self.app.current_project / "edit")
        edit_files = sorted([f for f in os.listdir(edit_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tif'))])
        ref_img_path = os.path.join(edit_dir, edit_files[self.app.raw_id])
        ref_img = cv2.imread(ref_img_path, cv2.IMREAD_GRAYSCALE)
        if ref_img is None:
            return

        ref_mean = np.mean(ref_img)
        ref_std = np.std(ref_img)

        best_score = float('inf')
        best_idx = None

        for idx, fname in enumerate(edit_files):
            if abs(idx - self.app.raw_id) <= 10:
                continue
            img_path = os.path.join(edit_dir, fname)
            img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
            if img is None or img.shape != ref_img.shape:
                continue
            mean = np.mean(img)
            std = np.std(img)
            score = np.sqrt((mean - ref_mean) ** 2 + (std - ref_std) ** 2)
            if score < best_score:
                best_score = score
                best_idx = idx

        if best_idx is None:
            return

        # Étape 2: Générer un ID unique pour lier les pathtrackings
        link_id = str(uuid.uuid4())
        
        # Étape 3: Décaler légèrement si on clique sur un via
        adjusted_x, adjusted_y = self._simple_via_offset(x, y)
        
        # Étape 4: Pathtracking sur la couche source avec position ajustée
        source_id = self.app.raw_id
        source_pathtracking = self._pathTracking_internal_with_link(adjusted_x, adjusted_y, link_id, best_idx)
        
        if source_pathtracking is None:
            return
            
        # Étape 4: Pathtracking sur la couche cible
        self.app.raw_id = best_idx
        self.app.displayImage()
        
        # Sauvegarder la tolérance originale
        old_tol = getattr(self.app.toolsBox, "path_tolerance", 10)
        self.app.toolsBox.path_tolerance = 16
        
        # Collecter les indices des vias à traiter sur la couche cible
        vias_indices_to_process = []
        
        # 1. Indice du via de départ (si c'est un via)
        if source_pathtracking.get('start_via'):
            start_via_id = source_pathtracking['start_via'].get('id')
            if start_via_id is not None:
                vias_indices_to_process.append(start_via_id)
        
        # 2. Indice du via d'arrivée (seulement si c'est un via)
        if source_pathtracking.get('has_end_via', False) and source_pathtracking.get('end_via'):
            end_via_id = source_pathtracking['end_via'].get('id')
            if end_via_id is not None:
                vias_indices_to_process.append(end_via_id)
        
        # 3. Indices de tous les vias intermédiaires traversés
        for via_data in source_pathtracking.get('traversed_vias', []):
            via_id = via_data.get('id')
            if via_id is not None:
                # Éviter les doublons
                if via_id not in vias_indices_to_process:
                    vias_indices_to_process.append(via_id)
        
        # Faire des pathtrackings automatiques récursifs sur tous les vias détectés
        self._auto_pathtrack_all_vias_recursive(vias_indices_to_process, link_id, source_id, best_idx)
        
        # Restaurer la tolérance
        self.app.toolsBox.path_tolerance = old_tol
        
        # Revenir à la couche source pour l'affichage final
        self.app.raw_id = source_id
        self.app.displayImage()
        
        # Compter tous les pathtrackings créés avec ce link_id
        all_linked_pathtrackings = self.get_linked_pathtrackings(link_id)
        source_pathtrackings = [p for p in all_linked_pathtrackings if p['raw_id'] == source_id]
        target_pathtrackings = [p for p in all_linked_pathtrackings if p['raw_id'] == best_idx]
        
        # Message de confirmation
        tk.messagebox.showinfo("Pathtrackings intercouche automatiques", 
            f"Pathtrackings créés automatiquement :\n"
            f"- Couche source ({source_id + 1}): {len(source_pathtrackings)} pathtracking(s)\n"
            f"- Couche cible ({best_idx + 1}): {len(target_pathtrackings)} pathtracking(s)\n"
            f"- Total: {len(all_linked_pathtrackings)} pathtracking(s) liés\n"
            f"- Tous les vias rencontrés ont été traités automatiquement !")

    def _pathTracking_internal_with_link(self, x, y, link_id=None, linked_layer=None):
        """
        Version de _pathTracking_internal qui supporte les liens intercouches.
        Retourne les données du pathtracking créé.
        """
        # Récupérer la tolérance depuis la toolbox
        tolerance_direct = self.app.toolsBox.path_tolerance
        
        # Forcer une mise à jour de la tolérance depuis le scale si il existe
        if hasattr(self.app.toolsBox, '_setting_scale'):
            scale_value = self.app.toolsBox._setting_scale.get()
            scale_label = self.app.toolsBox._setting_scale.cget("label").lower()
            if any(word in scale_label for word in ["tolérance", "tolerance", "tolérence", "tolerence"]):
                self.app.toolsBox.path_tolerance = scale_value
        
        tolerance = self.app.toolsBox.path_tolerance
        
        zoom = getattr(self.app.toolsBox, "raw_zoom", 1.0)
        coords = getattr(self.app.raw, "raw_coords", [0, 0])
        x_canvas = x - coords[0]
        y_canvas = y - coords[1]
        x = int(x_canvas / zoom)
        y = int(y_canvas / zoom)

        image_orig = self.app.raw.raw[self.app.raw_id].raw
        if len(image_orig.shape) == 3:
            img = cv2.cvtColor(image_orig, cv2.COLOR_BGR2GRAY)
        else:
            img = image_orig.copy()

        h, w = img.shape
        
        # Vérifier que le point de départ est valide
        if not (0 <= x < w and 0 <= y < h):
            return None
            
        ref_val = int(img[y, x])
        
        # Flood fill avec tolérance
        visited = np.zeros((h, w), dtype=bool)
        piste_points = []
        stack = [(y, x)]
        
        MAX_PIXELS = 100000
        
        while stack and len(piste_points) < MAX_PIXELS:
            cy, cx = stack.pop()
            
            if visited[cy, cx]:
                continue
                
            # Vérifier si le pixel appartient à la piste
            pixel_val = int(img[cy, cx])
            if abs(pixel_val - ref_val) > tolerance:
                continue
                
            visited[cy, cx] = True
            piste_points.append((cy, cx))
            
            # Ajouter les voisins 8-connectés
            for dy in [-1, 0, 1]:
                for dx in [-1, 0, 1]:
                    if dy == 0 and dx == 0:
                        continue
                    ny, nx = cy + dy, cx + dx
                    if (0 <= ny < h and 0 <= nx < w and 
                        not visited[ny, nx]):
                        neighbor_val = int(img[ny, nx])
                        if abs(neighbor_val - ref_val) <= tolerance:
                            stack.append((ny, nx))

        if len(piste_points) >= MAX_PIXELS:
            tk.messagebox.showwarning(
                "Tolérance trop élevée",
                f"Plus de {MAX_PIXELS} pixels trouvés.\nLa tolérance ({tolerance}) est probablement trop élevée."
            )
            return None

        if len(piste_points) <= 1:
            return None

        # Sauvegarde dans l'historique pour undo
        if hasattr(self.app.toolsBox, "draw"):
            draw = self.app.toolsBox.draw
            if hasattr(draw, "_history"):
                draw._history.append((
                    self.app.raw.raw[self.app.raw_id].raw.copy(),
                    self.app.raw.raw[self.app.raw_id].draw.copy() if hasattr(self.app.raw.raw[self.app.raw_id], "draw") else None,
                    getattr(draw, "_draw_image", None).copy() if hasattr(draw, "_draw_image") else None
                ))
                if hasattr(draw, "_history_undo"):
                    draw._history_undo.clear()

        # Charger les vias du projet pour trouver le point de départ optimal
        vias = self._load_vias_from_project()
        
        # Trouver le via le plus proche de la piste
        start_py, start_px = y, x  # Par défaut, utiliser le point de clic
        
        if vias:
            min_via_dist = float('inf')
            closest_via = None
            closest_via_index = -1
            
            # Chercher le via le plus proche du POINT DE CLIC (pas de toute la piste)
            for via_index, via in enumerate(vias):
                via_x, via_y = via['center']
                
                # Calculer la distance entre ce via et le POINT DE CLIC INITIAL
                dist_to_click = np.hypot(y - via_y, x - via_x)
                
                # Si ce via est plus proche du point de clic que les précédents
                if dist_to_click < min_via_dist:
                    min_via_dist = dist_to_click
                    closest_via = via
                    closest_via_index = via_index
            
            # Si on a trouvé un via proche, placer le point vert directement sur le via
            if closest_via:
                # Ajouter l'ID du via le plus proche
                closest_via = closest_via.copy()
                closest_via['id'] = closest_via_index
                start_px, start_py = closest_via['center']

        # Trouver le point le plus éloigné du point de départ optimal
        max_dist = 0
        end_py, end_px = start_py, start_px
        for py, px in piste_points:
            dist = np.hypot(py - start_py, px - start_px)
            if dist > max_dist:
                max_dist = dist
                end_py, end_px = py, px

        # Détecter tous les vias traversés par la piste avec un algorithme plus strict
        VIA_PROXIMITY_THRESHOLD = 12  # Distance maximum réduite pour être plus strict
        MIN_POINTS_REQUIRED = 8  # Plus de points requis pour confirmer un traversement
        traversed_vias = []
        end_via = None
        
        if vias:
            # Pour chaque via, vérifier s'il est réellement traversé par la piste
            for via_index, via in enumerate(vias):
                via_x, via_y = via['center']
                
                # Compter combien de points de piste sont très proches du via
                close_points = []
                for py, px in piste_points:
                    dist = np.hypot(py - via_y, px - via_x)
                    if dist <= VIA_PROXIMITY_THRESHOLD:
                        close_points.append((py, px))
                
                # Algorithme plus strict : besoin de beaucoup de points proches
                if len(close_points) >= MIN_POINTS_REQUIRED:
                    # Ajouter l'indice réel du via dans la liste des vias étalonnés
                    via_with_index = via.copy()
                    via_with_index['id'] = via_index
                    traversed_vias.append(via_with_index)
            
            # Identifier le via de fin (celui le plus proche de l'extrémité)
            if traversed_vias:
                min_end_via_dist = float('inf')
                for via in traversed_vias:
                    via_x, via_y = via['center']
                    dist_to_end = np.hypot(end_py - via_y, end_px - via_x)
                    
                    if dist_to_end < min_end_via_dist:
                        min_end_via_dist = dist_to_end
                        end_via = via
                
                # Si on a trouvé un via proche de l'extrémité, placer le point de fin sur le via
                if end_via and min_end_via_dist <= VIA_PROXIMITY_THRESHOLD:
                    end_px, end_py = end_via['center']

        # Sauvegarder le pathtracking avec les informations des vias traversés ET les liens
        pathtracking_data = {
            'raw_id': self.app.raw_id,
            'start': (start_px, start_py),
            'end': (end_px, end_py),
            'piste_points': piste_points,  # Conserver les points de la piste pour le redessin
            'has_end_via': end_via is not None,  # Indiquer s'il y a un via à la fin
            'traversed_vias': traversed_vias,  # Vias traversés avec leurs vrais indices
            'start_via': closest_via,  # Via de départ (défini plus haut)
            'end_via': end_via,  # Via de fin
            'color': self.app.toolsBox.draw_color,  # Couleur sélectionnée dans la toolbox
            'link_id': link_id,  # ID de liaison pour pathtracking intercouche
            'linked_layer': linked_layer,  # Couche liée
            'is_intercouche': link_id is not None  # Marqueur intercouche
        }
        self.pathtrackings.append(pathtracking_data)
        self.save_pathtrackings_to_project()
        
        # Dessiner le pathtracking sur l'image pathtracking correspondante
        self.draw_pathtracking_on_layer(pathtracking_data)
        
        # Afficher l'image mise à jour
        self.app.displayImage()
        
        # Vérifier la visibilité du panneau
        self._check_panel_visibility()
        
        return pathtracking_data

    def navigate_to_linked_layer(self, pathtracking_data):
        """
        Navigue vers la couche liée d'un pathtracking intercouche.
        """
        if not pathtracking_data.get('is_intercouche', False):
            return
            
        linked_layer = pathtracking_data.get('linked_layer')
        if linked_layer is not None and 0 <= linked_layer < len(self.app.raw.raw):
            self.app.raw_id = linked_layer
            self.app.displayImage()
            self.app.updateCounter()
            tk.messagebox.showinfo("Navigation", f"Navigation vers la couche liée {linked_layer + 1}")

    def get_linked_pathtrackings(self, link_id):
        """
        Retourne tous les pathtrackings liés par un link_id.
        """
        if not link_id:
            return []
        return [p for p in self.pathtrackings if p.get('link_id') == link_id]

    def show_intercouche_info(self):
        """
        Affiche les informations sur les pathtrackings intercouches.
        """
        intercouche_groups = {}
        for p in self.pathtrackings:
            if p.get('is_intercouche', False):
                link_id = p.get('link_id')
                if link_id not in intercouche_groups:
                    intercouche_groups[link_id] = []
                intercouche_groups[link_id].append(p)
        
        if not intercouche_groups:
            tk.messagebox.showinfo("Pathtrackings intercouches", "Aucun pathtracking intercouche trouvé.")
            return
        
        info_text = "Pathtrackings intercouches:\n\n"
        for link_id, pathtrackings in intercouche_groups.items():
            layers = set(p['raw_id'] for p in pathtrackings)
            info_text += f"Groupe {link_id[:8]}...\n"
            info_text += f"  Couches liées: {', '.join(str(l+1) for l in sorted(layers))}\n"
            info_text += f"  Nombre de pathtrackings: {len(pathtrackings)}\n\n"
        
        tk.messagebox.showinfo("Pathtrackings intercouches", info_text)

    def _find_and_track_via_by_index(self, via_index, link_id, source_id):
        """
        Trouve une piste valide sur un via spécifique par son indice dans la liste des vias étalonnés.
        Cette méthode est plus précise que _find_and_track_near_via car elle utilise 
        les coordonnées exactes du via étalonné au lieu de chercher autour de coordonnées.
        """
        # Charger les vias étalonnés du projet
        vias = self._load_vias_from_project()
        if not vias or via_index >= len(vias):
            return None
            
        # Récupérer les coordonnées exactes du via à partir de l'indice
        via = vias[via_index]
        via_x, via_y = via['center']
        
        if not self.app.raw.raw or self.app.raw_id >= len(self.app.raw.raw):
            return None
            
        image_orig = self.app.raw.raw[self.app.raw_id].raw
        if len(image_orig.shape) == 3:
            img = cv2.cvtColor(image_orig, cv2.COLOR_BGR2GRAY)
        else:
            img = image_orig.copy()
        
        h, w = img.shape
        
        # Vérifier que les coordonnées du via sont dans l'image
        if not (0 <= via_x < w and 0 <= via_y < h):
            return None
        
        # Paramètres de recherche
        search_radius = 20  # Rayon de recherche réduit car on utilise les coordonnées exactes
        tolerance = self.app.toolsBox.path_tolerance
        
        # Recherche en spirale autour du via avec les coordonnées exactes
        best_point = None
        best_score = 0
        
        # Vérifier d'abord le point central (coordonnées exactes du via étalonné)
        try:
            center_val = int(img[via_y, via_x])
            # Compter les pixels similaires autour du point central
            similar_pixels = self._count_similar_pixels_around(img, via_x, via_y, center_val, tolerance, 5)
            if similar_pixels > best_score:
                best_score = similar_pixels
                best_point = (via_x, via_y)
        except:
            pass
        
        # Recherche en spirale si le point central n'est pas suffisant
        if best_score < 10:  # Seuil minimum pour considérer une piste valide
            for radius in range(1, search_radius + 1):
                for angle in range(0, 360, 20):  # Tous les 20 degrés
                    # Calculer les coordonnées du point à tester
                    test_x = int(via_x + radius * np.cos(np.radians(angle)))
                    test_y = int(via_y + radius * np.sin(np.radians(angle)))
                    
                    # Vérifier que le point est dans l'image
                    if not (0 <= test_x < w and 0 <= test_y < h):
                        continue
                    
                    try:
                        pixel_val = int(img[test_y, test_x])
                        # Compter les pixels similaires autour de ce point
                        similar_pixels = self._count_similar_pixels_around(img, test_x, test_y, pixel_val, tolerance, 5)
                        
                        if similar_pixels > best_score:
                            best_score = similar_pixels
                            best_point = (test_x, test_y)
                    except:
                        continue
                
                # Si on a trouvé un bon point, arrêter la recherche
                if best_score >= 15:  # Seuil suffisant
                    break
        
        # Si aucun point valide n'a été trouvé, retourner None
        if best_point is None or best_score < 5:
            return None
        
        # Faire le pathtracking au meilleur point trouvé
        return self._pathTracking_internal_with_link(best_point[0], best_point[1], link_id, source_id)
    
    def _find_and_track_near_via(self, via_x, via_y, link_id, source_id):
        """
        Recherche une piste valide autour des coordonnées d'un via et fait le pathtracking.
        Utilise une recherche en spirale pour trouver le meilleur point de départ.
        """
        if not self.app.raw.raw or self.app.raw_id >= len(self.app.raw.raw):
            return None
            
        image_orig = self.app.raw.raw[self.app.raw_id].raw
        if len(image_orig.shape) == 3:
            img = cv2.cvtColor(image_orig, cv2.COLOR_BGR2GRAY)
        else:
            img = image_orig.copy()
        
        h, w = img.shape
        
        # Vérifier que les coordonnées du via sont dans l'image
        if not (0 <= via_x < w and 0 <= via_y < h):
            return None
        
        # Paramètres de recherche
        search_radius = 25  # Rayon de recherche autour du via
        tolerance = self.app.toolsBox.path_tolerance
        
        # Recherche en spirale autour du via
        best_point = None
        best_score = 0
        
        # Vérifier d'abord le point central (coordonnées exactes du via)
        try:
            center_val = int(img[via_y, via_x])
            # Compter les pixels similaires autour du point central
            similar_pixels = self._count_similar_pixels_around(img, via_x, via_y, center_val, tolerance, 5)
            if similar_pixels > best_score:
                best_score = similar_pixels
                best_point = (via_x, via_y)
        except:
            pass
        
        # Recherche en spirale si le point central n'est pas suffisant
        if best_score < 10:  # Seuil minimum pour considérer une piste valide
            for radius in range(1, search_radius + 1):
                for angle in range(0, 360, 15):  # Tous les 15 degrés
                    # Calculer les coordonnées du point à tester
                    test_x = int(via_x + radius * np.cos(np.radians(angle)))
                    test_y = int(via_y + radius * np.sin(np.radians(angle)))
                    
                    # Vérifier que le point est dans l'image
                    if not (0 <= test_x < w and 0 <= test_y < h):
                        continue
                    
                    try:
                        pixel_val = int(img[test_y, test_x])
                        # Compter les pixels similaires autour de ce point
                        similar_pixels = self._count_similar_pixels_around(img, test_x, test_y, pixel_val, tolerance, 5)
                        
                        if similar_pixels > best_score:
                            best_score = similar_pixels
                            best_point = (test_x, test_y)
                    except:
                        continue
                
                # Si on a trouvé un bon point, arrêter la recherche
                if best_score >= 20:  # Seuil suffisant
                    break
        
        # Si aucun point valide n'a été trouvé, retourner None
        if best_point is None or best_score < 5:
            return None
        
        # Faire le pathtracking au meilleur point trouvé
        return self._pathTracking_internal_with_link(best_point[0], best_point[1], link_id, source_id)

    def _count_similar_pixels_around(self, img, x, y, ref_val, tolerance, radius):
        """
        Compte le nombre de pixels similaires autour d'un point donné.
        """
        count = 0
        h, w = img.shape
        
        for dy in range(-radius, radius + 1):
            for dx in range(-radius, radius + 1):
                test_x, test_y = x + dx, y + dy
                if 0 <= test_x < w and 0 <= test_y < h:
                    try:
                        pixel_val = int(img[test_y, test_x])
                        if abs(pixel_val - ref_val) <= tolerance:
                            count += 1
                    except:
                        pass
        
        return count

    def _check_vias_calibrated(self):
        """
        Vérifie si les vias sont étalonnés dans le projet courant.
        Retourne True si les vias sont étalonnés, False sinon.
        """
        if not self.app.current_project:
            return False
            
        project_path = self.app.current_project / 'project.json'
        
        try:
            with open(project_path, 'r', encoding='utf-8') as file:
                project_data = json.load(file)
                
            # Vérifier si les vias existent et ne sont pas vides
            vias = project_data.get('vias', [])
            
            # Considérer que les vias sont étalonnés s'il y en a au moins un
            if vias and len(vias) > 0:
                # Vérifier que les vias ont les champs nécessaires
                for via in vias:
                    if not all(key in via for key in ['center', 'radius']):
                        return False
                return True
            else:
                return False
                
        except (FileNotFoundError, json.JSONDecodeError, KeyError):
            # Si le fichier n'existe pas ou est mal formé, considérer que les vias ne sont pas étalonnés
            return False

    def _create_via_visual_pathtracking(self, via_index, link_id, source_id):
        """
        Crée un pathtracking sur un via avec un décalage simple.
        """
        # Charger les vias étalonnés du projet
        vias = self._load_vias_from_project()
        if not vias or via_index >= len(vias):
            return None
            
        # Récupérer les coordonnées exactes du via à partir de l'indice
        via = vias[via_index]
        via_x, via_y = via['center']
        
        if not self.app.raw.raw or self.app.raw_id >= len(self.app.raw.raw):
            return None
        
        # Convertir les coordonnées du via vers les coordonnées canvas
        zoom = getattr(self.app.toolsBox, "raw_zoom", 1.0)
        coords = getattr(self.app.raw, "raw_coords", [0, 0])
        canvas_x = int(via_x * zoom + coords[0])
        canvas_y = int(via_y * zoom + coords[1])
        
        # Décaler simplement de 6 pixels vers la droite
        offset_canvas_x = canvas_x + 6
        offset_canvas_y = canvas_y
        
        # Faire le pathtracking avec la position décalée
        return self._pathTracking_internal_with_link(offset_canvas_x, offset_canvas_y, link_id, source_id)

    def _simple_via_offset(self, x, y):
        """
        Décale simplement de quelques pixels si on clique sur un via.
        """
        # Convertir les coordonnées canvas vers coordonnées image
        zoom = getattr(self.app.toolsBox, "raw_zoom", 1.0)
        coords = getattr(self.app.raw, "raw_coords", [0, 0])
        x_canvas = x - coords[0]
        y_canvas = y - coords[1]
        img_x = int(x_canvas / zoom)
        img_y = int(y_canvas / zoom)
        
        # Charger les vias étalonnés du projet
        vias = self._load_vias_from_project()
        if not vias:
            return x, y
        
        # Vérifier si on clique sur un via
        for via in vias:
            via_x, via_y = via['center']
            via_radius = via.get('radius', 5)
            distance = np.sqrt((img_x - via_x)**2 + (img_y - via_y)**2)
            
            # Si on clique sur le via, décaler de 6 pixels vers la droite
            if distance <= via_radius:
                offset_x = 6  # Décalage simple de 6 pixels
                new_canvas_x = x + offset_x
                return new_canvas_x, y
        
        # Si on n'a pas cliqué sur un via, retourner les coordonnées originales
        return x, y

    def _auto_pathtrack_all_vias_recursive(self, vias_indices_to_process, link_id, source_layer, target_layer):
        """
        Fait automatiquement des pathtrackings récursifs sur tous les vias trouvés.
        Continue jusqu'à ce qu'il n'y ait plus de nouveaux vias à traiter.
        """
        if not vias_indices_to_process:
            return
        
        print(f"DEBUG: Traitement des vias {vias_indices_to_process} sur couche {target_layer}")
        
        # Sauvegarder la couche actuelle
        original_layer = self.app.raw_id
        
        # S'assurer qu'on est sur la bonne couche cible
        self.app.raw_id = target_layer
        self.app.displayImage()
        
        # Traiter tous les vias de cette itération
        new_vias_found = []
        target_pathtrackings = []
        
        for via_index in vias_indices_to_process:
            print(f"DEBUG: Création pathtracking sur via {via_index}")
            # Créer un pathtracking sur ce via
            target_pathtracking = self._create_via_visual_pathtracking(via_index, link_id, source_layer)
            if target_pathtracking:
                target_pathtrackings.append(target_pathtracking)
                
                # Récupérer TOUS les vias traversés par ce pathtracking
                new_traversed_vias = target_pathtracking.get('traversed_vias', [])
                print(f"DEBUG: Vias traversés: {[v.get('id') for v in new_traversed_vias]}")
                
                # Ajouter l'ID du via de début s'il existe
                if target_pathtracking.get('start_via') and target_pathtracking['start_via'].get('id') is not None:
                    new_vias_found.append(target_pathtracking['start_via']['id'])
                
                # Ajouter l'ID du via de fin s'il existe
                if target_pathtracking.get('end_via') and target_pathtracking['end_via'].get('id') is not None:
                    new_vias_found.append(target_pathtracking['end_via']['id'])
                
                # Ajouter tous les vias intermédiaires traversés
                for via_data in new_traversed_vias:
                    if via_data.get('id') is not None:
                        new_vias_found.append(via_data['id'])
        
        # Éliminer les doublons des nouveaux vias
        new_vias_found = list(set(new_vias_found))
        print(f"DEBUG: Nouveaux vias trouvés: {new_vias_found}")
        
        # Récupérer tous les vias déjà traités avec ce link_id pour éviter les doublons
        # NE PAS inclure les vias actuellement en cours de traitement
        already_processed_vias = set()
        existing_pathtrackings = self.get_linked_pathtrackings(link_id)
        
        # Exclure les pathtrackings qu'on vient de créer dans cette session
        pathtrackings_before_session = [p for p in existing_pathtrackings if p not in target_pathtrackings]
        
        for p in pathtrackings_before_session:
            if p.get('start_via') and p['start_via'].get('id') is not None:
                already_processed_vias.add(p['start_via']['id'])
            if p.get('end_via') and p['end_via'].get('id') is not None:
                already_processed_vias.add(p['end_via']['id'])
            for via_data in p.get('traversed_vias', []):
                if via_data.get('id') is not None:
                    already_processed_vias.add(via_data['id'])
        
        print(f"DEBUG: Vias déjà traités: {already_processed_vias}")
        
        # Filtrer les nouveaux vias pour ne garder que ceux pas encore traités
        truly_new_vias = [via_id for via_id in new_vias_found if via_id not in already_processed_vias]
        print(f"DEBUG: Vias vraiment nouveaux: {truly_new_vias}")
        
        # S'il y a de nouveaux vias, faire une récursion sur la couche source
        if truly_new_vias:
            print(f"DEBUG: Récursion vers couche {source_layer}")
            # Retourner à la couche source pour traiter les nouveaux vias
            self._auto_pathtrack_all_vias_recursive(truly_new_vias, link_id, target_layer, source_layer)
        else:
            print("DEBUG: Pas de nouveaux vias, arrêt de la récursion")

    def show_pathtracking_panel(self):
        self.show_panel()
        
        # Frame principal avec scrollbar
        main_frame = tk.Frame(self.pathtracking_panel)
        main_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Canvas et scrollbar pour le scroll
        canvas = tk.Canvas(main_frame)
        scrollbar = tk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        self.scrollable_frame = tk.Frame(canvas)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Support de la molette de souris
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        canvas.bind("<MouseWheel>", _on_mousewheel)
        self.pathtracking_panel.bind("<MouseWheel>", _on_mousewheel)
        
        # Titre du panneau
        title_label = tk.Label(self.scrollable_frame, text="🎯 Pathtrackings", 
                              font=("Arial", 12, "bold"), fg="#2E7D32")
        title_label.pack(pady=(0, 10))
        
        # Mettre à jour le contenu
        self._update_pathtracking_panel()

    # Ancienne méthode _update_pathtracking_panel supprimée (remplacée par update_pathtracking_panel)
        
        print(f"DEBUG: Mise à jour du panneau avec {len(self.pathtrackings)} pathtrackings")
        
        # Nettoyer le contenu existant (sauf le titre)
        for widget in self.scrollable_frame.winfo_children()[1:]:  # Garder le titre
            widget.destroy()
        
        # Réinitialiser les variables
        self.layer_frames = {}
        
        # Grouper les pathtrackings par couche
        layers_data = {}
        for i, pathtracking in enumerate(self.pathtrackings):
            layer_id = pathtracking['raw_id']
            if layer_id not in layers_data:
                layers_data[layer_id] = []
            layers_data[layer_id].append((i, pathtracking))
        
        # Créer un dictionnaire des groupes intercouches pour la numérotation
        intercouche_groups = {}
        group_counter = 1
        for pathtracking in self.pathtrackings:
            if pathtracking.get('is_intercouche', False):
                link_id = pathtracking.get('link_id')
                if link_id and link_id not in intercouche_groups:
                    intercouche_groups[link_id] = group_counter
                    group_counter += 1
        
        # Afficher chaque couche
        for layer_id in sorted(layers_data.keys()):
            pathtrackings_list = layers_data[layer_id]
            self._create_layer_section(layer_id, pathtrackings_list, intercouche_groups)

    def _create_layer_section(self, layer_id, pathtrackings_list, intercouche_groups):
        """Crée une section pour une couche avec ses pathtrackings."""
        # Frame principal pour la couche
        layer_main_frame = tk.Frame(self.scrollable_frame, relief='raised', bd=1)
        layer_main_frame.pack(fill='x', pady=2)
        
        # Header de la couche (cliquable pour expand/collapse)
        header_frame = tk.Frame(layer_main_frame, bg='#E8F5E8', cursor='hand2')
        header_frame.pack(fill='x')
        
        # Icône expand/collapse
        is_expanded = layer_id in self.expanded_layers
        arrow = "▼" if is_expanded else "▶"
        
        # Texte du header
        layer_text = f"{arrow} Couche {layer_id + 1} ({len(pathtrackings_list)} pathtracking{'s' if len(pathtrackings_list) > 1 else ''})"
        
        header_label = tk.Label(header_frame, text=layer_text, 
                               font=("Arial", 10, "bold"), bg='#E8F5E8', 
                               anchor='w', padx=10, pady=5)
        header_label.pack(fill='x')
        
        # Bind pour toggle expand/collapse
        def toggle_layer(event, lid=layer_id):
            if lid in self.expanded_layers:
                self.expanded_layers.remove(lid)
            else:
                self.expanded_layers.add(lid)
            self._update_pathtracking_panel()
        
        header_frame.bind("<Button-1>", toggle_layer)
        header_label.bind("<Button-1>", toggle_layer)
        
        # Frame pour les pathtrackings (visible seulement si expandé)
        if is_expanded:
            pathtrackings_frame = tk.Frame(layer_main_frame)
            pathtrackings_frame.pack(fill='x', padx=10)
            
            # Afficher chaque pathtracking
            for path_num, (global_index, pathtracking) in enumerate(pathtrackings_list, 1):
                self._create_pathtracking_entry(pathtrackings_frame, global_index, pathtracking, 
                                               path_num, intercouche_groups)

    def _create_pathtracking_entry(self, parent, global_index, pathtracking, path_num, intercouche_groups):
        """Crée l'entrée pour un pathtracking individuel."""
        # Frame pour le pathtracking
        path_frame = tk.Frame(parent, relief='flat', bd=1)
        path_frame.pack(fill='x', pady=1)
        
        # Couleur de fond selon le type
        if pathtracking.get('is_intercouche', False):
            bg_color = '#FFF8E1'  # Jaune pâle pour intercouche
        else:
            bg_color = '#F5F5F5'  # Gris clair pour normal
        
        path_frame.configure(bg=bg_color)
        
        # Frame principal cliquable
        main_info_frame = tk.Frame(path_frame, bg=bg_color, cursor='hand2')
        main_info_frame.pack(fill='x', padx=5, pady=3)
        
        # Couleur du pathtracking (petit carré)
        color_hex = pathtracking.get('color', '#FF0000')
        color_frame = tk.Frame(main_info_frame, bg=color_hex, width=12, height=12, relief='solid', bd=1)
        color_frame.pack(side='left', padx=(0, 5))
        color_frame.pack_propagate(False)
        
        # Texte principal
        path_text = f"#{path_num}"
        
        # Ajouter les informations sur les vias
        via_info = []
        if pathtracking.get('start_via'):
            via_info.append("📍")
        if pathtracking.get('has_end_via', False):
            via_info.append("🎯")
        if pathtracking.get('traversed_vias'):
            via_count = len(pathtracking['traversed_vias'])
            if via_count > 0:
                via_info.append(f"⚡{via_count}")
        
        if via_info:
            path_text += f" {' '.join(via_info)}"
        
        # Ajouter info intercouche si applicable
        if pathtracking.get('is_intercouche', False):
            link_id = pathtracking.get('link_id')
            if link_id and link_id in intercouche_groups:
                group_num = intercouche_groups[link_id]
                linked_layer = pathtracking.get('linked_layer')
                if linked_layer is not None:
                    path_text += f" → Lien #{group_num} (Couche {linked_layer + 1})"
        
        path_label = tk.Label(main_info_frame, text=path_text, 
                             font=("Arial", 9), bg=bg_color, anchor='w')
        path_label.pack(side='left', fill='x', expand=True)
        
        # Bind pour navigation
        def navigate_to_pathtracking(event, layer=pathtracking['raw_id'], index=global_index):
            self._navigate_to_pathtracking(layer, index)
        
        main_info_frame.bind("<Button-1>", navigate_to_pathtracking)
        path_label.bind("<Button-1>", navigate_to_pathtracking)
        color_frame.bind("<Button-1>", navigate_to_pathtracking)
        
        # Info supplémentaire (coordonnées)
        start_x, start_y = pathtracking['start']
        end_x, end_y = pathtracking['end']
        coord_text = f"({start_x},{start_y}) → ({end_x},{end_y})"
        
        coord_label = tk.Label(main_info_frame, text=coord_text, 
                              font=("Arial", 8), fg='#666666', bg=bg_color)
        coord_label.pack(side='right')
        coord_label.bind("<Button-1>", navigate_to_pathtracking)

    def _navigate_to_pathtracking(self, layer_id, pathtracking_index):
        """Navigue vers un pathtracking spécifique."""
        # Changer vers la couche du pathtracking
        if 0 <= layer_id < len(self.app.raw.raw):
            self.app.raw_id = layer_id
            self.app.displayImage()
            self.app.updateCounter()
            
            # TODO: Optionnel - mettre en évidence le pathtracking sélectionné
            # (par exemple, avec un cercle ou une surbrillance temporaire)
            
            print(f"Navigation vers pathtracking #{pathtracking_index + 1} sur couche {layer_id + 1}")

    def close_pathtracking_panel(self):
        self.hide_panel()
        self.layer_frames = {}
        self.expanded_layers = set()

    def _check_panel_visibility(self):
        print(f"DEBUG: _check_panel_visibility appelée, pathtrackings: {len(self.pathtrackings)}")
        if self.pathtrackings:
            print("DEBUG: Ouverture du panneau de pathtrackings")
            self.show_panel()
        else:
            print("DEBUG: Fermeture du panneau de pathtrackings")
            self.hide_panel()


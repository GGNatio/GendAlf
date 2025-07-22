import tkinter as tk
from tkinter import messagebox, ttk
import json
import cv2
import numpy as np
from PIL import Image, ImageTk
from pathlib import Path
import uuid


class RXviewerVia:
    def __init__(self, parent):
        self.parent = parent
        self.current_image_index = 0
        self.detected_vias = []
        self.via_colors = [(255, 255, 0), (255, 0, 255), (0, 255, 255), (0, 255, 0), (255, 0, 0)]  # BGR colors
        self.window = None
        self.canvas_with_vias = None
        self.canvas_original = None
        self.tk_image_with_vias = None
        self.tk_image_original = None
        
        # Variables pour le zoom et déplacement
        self.zoom_factor = 1.0
        self.image_offset_x = 0
        self.image_offset_y = 0
        self.drag_start_x = 0
        self.drag_start_y = 0
        self.dragging = False
        
    def close_window(self):
        '''Ferme la fenêtre proprement en supprimant les bindings'''
        try:
            if hasattr(self, 'window') and self.window:
                # Supprimer les bindings globaux pour éviter les erreurs
                if hasattr(self, '_mousewheel_callback'):
                    self.window.unbind_all("<MouseWheel>")
                
                # Détruire la fenêtre
                self.window.destroy()
                self.window = None
        except Exception as e:
            print(f"Erreur lors de la fermeture de la fenêtre via: {e}")

    def open_via_calibration_window(self):
        """Ouvre la fenêtre d'étalonnage des vias"""
        if not self.parent.current_project or not self.parent.raw.raw:
            messagebox.showwarning("Erreur", "Aucun projet ou image chargé.")
            return
            
        self.window = tk.Toplevel(self.parent.app)
        self.window.title("Étalonnage des Vias")
        self.window.geometry("1200x700")
        self.window.grab_set()
        
        # Configurer la fermeture propre de la fenêtre
        self.window.protocol("WM_DELETE_WINDOW", self.close_window)
        
        # Frame principal avec scrollbar
        main_canvas = tk.Canvas(self.window)
        scrollbar = tk.Scrollbar(self.window, orient="vertical", command=main_canvas.yview)
        scrollable_frame = tk.Frame(main_canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: main_canvas.configure(scrollregion=main_canvas.bbox("all"))
        )
        
        main_canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        main_canvas.configure(yscrollcommand=scrollbar.set)
        
        main_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Navigation des images
        nav_frame = tk.Frame(scrollable_frame)
        nav_frame.pack(fill='x', pady=10, padx=10)
        
        tk.Button(nav_frame, text="<<", command=self.first_image, width=5).pack(side='left', padx=2)
        tk.Button(nav_frame, text="<", command=self.previous_image, width=5).pack(side='left', padx=2)
        
        self.image_label = tk.Label(nav_frame, text=f"1/{len(self.parent.raw.raw)}", font=("Arial", 12))
        self.image_label.pack(side='left', padx=20)
        
        tk.Button(nav_frame, text=">", command=self.next_image, width=5).pack(side='left', padx=2)
        tk.Button(nav_frame, text=">>", command=self.last_image, width=5).pack(side='left', padx=2)
        
        # Frame pour les deux images côte à côte
        images_frame = tk.Frame(scrollable_frame)
        images_frame.pack(fill='x', pady=10, padx=10)
        
        # Image avec vias (gauche)
        left_frame = tk.LabelFrame(images_frame, text="Avec détection des vias", font=("Arial", 10, "bold"))
        left_frame.pack(side='left', fill='both', expand=True, padx=(0, 5))
        
        self.canvas_with_vias = tk.Canvas(left_frame, bg='gray', width=550, height=450)
        self.canvas_with_vias.pack(pady=5)
        
        # Image originale (droite)
        right_frame = tk.LabelFrame(images_frame, text="Image originale", font=("Arial", 10, "bold"))
        right_frame.pack(side='right', fill='both', expand=True, padx=(5, 0))
        
        self.canvas_original = tk.Canvas(right_frame, bg='gray', width=550, height=450)
        self.canvas_original.pack(pady=5)
        
        # Paramètres
        params_frame = tk.LabelFrame(scrollable_frame, text="Paramètres de détection", font=("Arial", 10, "bold"))
        params_frame.pack(fill='x', pady=10, padx=10)
        
        tk.Label(params_frame, text="Seuil:").grid(row=0, column=0, sticky='w', padx=5, pady=2)
        self.threshold_var = tk.IntVar(value=180)
        tk.Scale(params_frame, from_=100, to=255, orient='horizontal', variable=self.threshold_var, length=120).grid(row=0, column=1, padx=5, pady=2)
        
        tk.Label(params_frame, text="Taille min:").grid(row=0, column=2, sticky='w', padx=5, pady=2)
        self.min_area_var = tk.IntVar(value=5)
        tk.Scale(params_frame, from_=3, to=30, orient='horizontal', variable=self.min_area_var, length=120).grid(row=0, column=3, padx=5, pady=2)
        
        tk.Label(params_frame, text="Taille max:").grid(row=1, column=0, sticky='w', padx=5, pady=2)
        self.max_area_var = tk.IntVar(value=100)
        tk.Scale(params_frame, from_=20, to=200, orient='horizontal', variable=self.max_area_var, length=120).grid(row=1, column=1, padx=5, pady=2)
        
        tk.Label(params_frame, text="Distance min:").grid(row=1, column=2, sticky='w', padx=5, pady=2)
        self.min_distance_var = tk.IntVar(value=10)
        tk.Scale(params_frame, from_=3, to=30, orient='horizontal', variable=self.min_distance_var, length=120).grid(row=1, column=3, padx=5, pady=2)
        
        # Option pour la détection multi-seuils
        tk.Label(params_frame, text="Multi-seuils:").grid(row=2, column=0, sticky='w', padx=5, pady=2)
        self.multi_threshold_var = tk.BooleanVar(value=True)
        tk.Checkbutton(params_frame, text="Activer", variable=self.multi_threshold_var).grid(row=2, column=1, sticky='w', padx=5, pady=2)
        
        # Zone d'informations de détection
        info_frame = tk.LabelFrame(scrollable_frame, text="Informations de détection", font=("Arial", 10, "bold"))
        info_frame.pack(fill='x', pady=5, padx=10)
        
        self.info_text = tk.Text(info_frame, height=4, width=80, wrap=tk.WORD, font=("Arial", 9))
        self.info_text.pack(pady=5, padx=5)
        
        # Ajouter les instructions d'utilisation
        instructions = ("Instructions : Shift + Clic gauche = Ajouter un via manuellement | "
                       "Shift + Clic droit = Supprimer un via | "
                       "Ctrl + Molette = Zoom | Clic droit + Glisser = Déplacer\n")
        self.info_text.insert(tk.END, instructions)
        
        # Boutons d'action
        action_frame = tk.Frame(scrollable_frame)
        action_frame.pack(fill='x', pady=10, padx=10)
        
        tk.Button(action_frame, text="Détecter les Vias", command=self.detect_vias, 
                 bg='lightblue', font=("Arial", 11)).pack(side='left', padx=5)
        tk.Button(action_frame, text="Réinitialiser", command=self.reset_detection, 
                 bg='orange', font=("Arial", 11)).pack(side='left', padx=5)
        tk.Button(action_frame, text="Reset Zoom", command=self.reset_zoom, 
                 bg='lightcyan', font=("Arial", 11)).pack(side='left', padx=5)
        tk.Button(action_frame, text="Accepter", command=self.accept_vias, 
                 bg='lightgreen', font=("Arial", 11)).pack(side='left', padx=5)
        tk.Button(action_frame, text="Annuler", command=self.close_window, 
                 bg='lightcoral', font=("Arial", 11)).pack(side='right', padx=5)
        
        # Bind scroll wheel to main canvas
        def _on_mousewheel(event):
            try:
                if main_canvas.winfo_exists():
                    main_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
            except tk.TclError:
                # Le widget n'existe plus, ignorer l'erreur
                pass
        
        # Bind scroll wheel sur les images pour navigation
        def _on_image_scroll(event):
            if event.delta > 0:
                self.previous_image()
            else:
                self.next_image()
        
        # Bind zoom avec Ctrl+molette
        def _on_zoom(event):
            if event.state & 0x0004:  # Ctrl est pressé
                if event.delta > 0:
                    self.zoom_in(event.x, event.y, event.widget)
                else:
                    self.zoom_out(event.x, event.y, event.widget)
                return "break"
        
        # Bind déplacement de l'image
        def _start_drag(event):
            self.dragging = True
            self.drag_start_x = event.x
            self.drag_start_y = event.y
        
        def _do_drag(event):
            if self.dragging:
                dx = event.x - self.drag_start_x
                dy = event.y - self.drag_start_y
                self.image_offset_x += dx
                self.image_offset_y += dy
                self.drag_start_x = event.x
                self.drag_start_y = event.y
                self.display_current_image()
        
        def _stop_drag(event):
            self.dragging = False
        
        self.window.bind_all("<MouseWheel>", _on_mousewheel)
        self.canvas_with_vias.bind("<MouseWheel>", _on_zoom)
        self.canvas_original.bind("<MouseWheel>", _on_zoom)
        
        # Stocker les références des fonctions de callback pour pouvoir les supprimer
        self._mousewheel_callback = _on_mousewheel
        self._zoom_callback = _on_zoom
        
        # Bind déplacement avec clic droit
        self.canvas_with_vias.bind("<Button-3>", _start_drag)
        self.canvas_with_vias.bind("<B3-Motion>", _do_drag)
        self.canvas_with_vias.bind("<ButtonRelease-3>", _stop_drag)
        
        self.canvas_original.bind("<Button-3>", _start_drag)
        self.canvas_original.bind("<B3-Motion>", _do_drag)
        self.canvas_original.bind("<ButtonRelease-3>", _stop_drag)
        
        # Bind pour édition manuelle des vias
        def _on_manual_edit(event):
            if event.state & 0x0001:  # Shift est pressé
                # Convertir les coordonnées du canvas vers les coordonnées de l'image
                image_x, image_y = self.canvas_to_image_coords(event.x, event.y)
                
                if event.num == 1:  # Clic gauche + Shift = Ajouter via
                    self.add_via_manually(image_x, image_y)
                elif event.num == 3:  # Clic droit + Shift = Supprimer via
                    self.remove_via_manually(image_x, image_y)
                return "break"
        
        self.canvas_with_vias.bind("<Shift-Button-1>", _on_manual_edit)
        self.canvas_with_vias.bind("<Shift-Button-3>", _on_manual_edit)
        
        # Bind navigation normale sans Ctrl
        self.canvas_with_vias.bind("<Button-4>", _on_image_scroll)
        self.canvas_with_vias.bind("<Button-5>", _on_image_scroll)
        self.canvas_original.bind("<Button-4>", _on_image_scroll)
        self.canvas_original.bind("<Button-5>", _on_image_scroll)
        
        self.display_current_image()
        
        # Charger les vias existants du projet
        self.load_existing_vias()
        
    def first_image(self):
        """Aller à la première image"""
        self.current_image_index = 0
        self.reset_zoom()
        self.image_label.config(text=f"{self.current_image_index + 1}/{len(self.parent.raw.raw)}")
        self.display_current_image()
    
    def previous_image(self):
        """Aller à l'image précédente"""
        if self.current_image_index > 0:
            self.current_image_index -= 1
            self.reset_zoom()
            self.image_label.config(text=f"{self.current_image_index + 1}/{len(self.parent.raw.raw)}")
            self.display_current_image()
    
    def next_image(self):
        """Aller à l'image suivante"""
        if self.current_image_index < len(self.parent.raw.raw) - 1:
            self.current_image_index += 1
            self.reset_zoom()
            self.image_label.config(text=f"{self.current_image_index + 1}/{len(self.parent.raw.raw)}")
            self.display_current_image()
    
    def last_image(self):
        """Aller à la dernière image"""
        self.current_image_index = len(self.parent.raw.raw) - 1
        self.reset_zoom()
        self.image_label.config(text=f"{self.current_image_index + 1}/{len(self.parent.raw.raw)}")
        self.display_current_image()
        
    def navigate_image(self, direction):
        """Navigate entre les images"""
        new_index = self.current_image_index + direction
        if 0 <= new_index < len(self.parent.raw.raw):
            self.current_image_index = new_index
            self.image_label.config(text=f"{self.current_image_index + 1}/{len(self.parent.raw.raw)}")
            self.display_current_image()
            
    def display_current_image(self):
        """Affiche l'image courante avec les vias détectés"""
        if not self.parent.raw.raw:
            return
            
        # Obtenir l'image courante
        current_image = self.parent.raw.raw[self.current_image_index].raw.copy()
        
        # Image avec vias (gauche)
        image_with_vias = current_image.copy()
        
        # Afficher tous les vias détectés (persistance)
        for i, via in enumerate(self.detected_vias):
            color = self.via_colors[i % len(self.via_colors)]
            cv2.circle(image_with_vias, tuple(via['center']), via['radius'], color, 2)
            cv2.putText(image_with_vias, str(i+1), (via['center'][0]-10, via['center'][1]-15), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
        
        # Taille du canvas
        canvas_w, canvas_h = 550, 450
        h, w = current_image.shape[:2]
        
        # Calculer la taille finale avec zoom
        final_w = int(w * self.zoom_factor)
        final_h = int(h * self.zoom_factor)
        
        # Redimensionner les images selon le zoom
        if self.zoom_factor != 1.0:
            image_with_vias = cv2.resize(image_with_vias, (final_w, final_h))
            current_image = cv2.resize(current_image, (final_w, final_h))
        
        # Calculer la zone à afficher selon l'offset
        start_x = max(0, int(-self.image_offset_x))
        start_y = max(0, int(-self.image_offset_y))
        end_x = min(final_w, start_x + canvas_w)
        end_y = min(final_h, start_y + canvas_h)
        
        # Créer une image de fond grise pour les zones vides
        display_with_vias = np.full((canvas_h, canvas_w, 3), 128, dtype=np.uint8)
        display_original = np.full((canvas_h, canvas_w, 3), 128, dtype=np.uint8)
        
        # Calculer où placer l'image dans le canvas
        paste_x = max(0, int(self.image_offset_x))
        paste_y = max(0, int(self.image_offset_y))
        
        # Extraire la partie visible de l'image
        if start_x < final_w and start_y < final_h and end_x > start_x and end_y > start_y:
            crop_with_vias = image_with_vias[start_y:end_y, start_x:end_x]
            crop_original = current_image[start_y:end_y, start_x:end_x]
            
            # Calculer les dimensions à coller
            crop_h, crop_w = crop_with_vias.shape[:2]
            paste_end_x = min(canvas_w, paste_x + crop_w)
            paste_end_y = min(canvas_h, paste_y + crop_h)
            
            if paste_end_x > paste_x and paste_end_y > paste_y:
                # Ajuster les dimensions si nécessaire
                actual_w = paste_end_x - paste_x
                actual_h = paste_end_y - paste_y
                
                if crop_w > actual_w:
                    crop_with_vias = crop_with_vias[:, :actual_w]
                    crop_original = crop_original[:, :actual_w]
                if crop_h > actual_h:
                    crop_with_vias = crop_with_vias[:actual_h, :]
                    crop_original = crop_original[:actual_h, :]
                
                # Coller les images
                display_with_vias[paste_y:paste_y + crop_with_vias.shape[0], 
                                paste_x:paste_x + crop_with_vias.shape[1]] = crop_with_vias
                display_original[paste_y:paste_y + crop_original.shape[0], 
                               paste_x:paste_x + crop_original.shape[1]] = crop_original
        
        # Convertir BGR vers RGB pour PIL
        if len(display_with_vias.shape) == 3:
            display_with_vias = cv2.cvtColor(display_with_vias, cv2.COLOR_BGR2RGB)
            display_original = cv2.cvtColor(display_original, cv2.COLOR_BGR2RGB)
        
        # Créer les images Tkinter
        self.tk_image_with_vias = ImageTk.PhotoImage(Image.fromarray(display_with_vias))
        self.tk_image_original = ImageTk.PhotoImage(Image.fromarray(display_original))
        
        # Afficher dans les canvas
        if hasattr(self, 'canvas_with_vias'):
            self.canvas_with_vias.delete("all")
            self.canvas_with_vias.create_image(0, 0, anchor=tk.NW, image=self.tk_image_with_vias)
        
        if hasattr(self, 'canvas_original'):
            self.canvas_original.delete("all")
            self.canvas_original.create_image(0, 0, anchor=tk.NW, image=self.tk_image_original)
        
    def detect_vias_at_threshold(self, gray, threshold_value):
        """Détecte les vias avec un seuil donné"""
        _, thresh = cv2.threshold(gray, threshold_value, 255, cv2.THRESH_BINARY)
        
        # Nettoyage morphologique très léger pour préserver les petits vias
        kernel = np.ones((2,2), np.uint8)
        cleaned = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
        cleaned = cv2.morphologyEx(cleaned, cv2.MORPH_OPEN, kernel)
        
        # Détection des contours
        contours, _ = cv2.findContours(cleaned, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        detected_vias = []
        for contour in contours:
            area = cv2.contourArea(contour)
            if self.min_area_var.get() <= area <= self.max_area_var.get():
                perimeter = cv2.arcLength(contour, True)
                if perimeter > 0:
                    # Calcul de la circularité
                    circularity = 4 * np.pi * area / (perimeter * perimeter)
                    
                    # Calculer l'aspect ratio pour éliminer les rectangles
                    rect = cv2.minAreaRect(contour)
                    width, height = rect[1]
                    if width > 0 and height > 0:
                        aspect_ratio = max(width, height) / min(width, height)
                    else:
                        aspect_ratio = 10
                    
                    # Critères stricts pour les vias UNIQUEMENT :
                    # - Bonne circularité (> 0.6)
                    # - Aspect ratio proche de 1 (< 1.4) pour éviter les rectangles
                    if circularity > 0.6 and aspect_ratio < 1.4:
                        M = cv2.moments(contour)
                        if M["m00"] != 0:
                            cx = int(M["m10"] / M["m00"])
                            cy = int(M["m01"] / M["m00"])
                            
                            radius = int(np.sqrt(area / np.pi))
                            via_data = {
                                'center': [cx, cy],
                                'radius': max(radius, 3),
                                'area': area,
                                'circularity': circularity,
                                'aspect_ratio': aspect_ratio,
                                'threshold': threshold_value
                            }
                            detected_vias.append(via_data)
        
        return detected_vias

    def merge_vias(self, vias_list):
        """Fusionne les vias détectés à différents seuils, en évitant les doublons"""
        if not vias_list:
            return []
            
        # Fusionner toutes les détections
        all_vias = []
        for vias in vias_list:
            all_vias.extend(vias)
        
        if not all_vias:
            return []
        
        # Trier par qualité (circularité décroissante, puis aspect ratio croissant)
        all_vias.sort(key=lambda v: (-v['circularity'], v['aspect_ratio']))
        
        # Éliminer les doublons basés sur la distance
        merged_vias = []
        min_distance = self.min_distance_var.get()
        
        for via in all_vias:
            cx, cy = via['center']
            
            # Vérifier si ce via est trop proche d'un via déjà accepté
            too_close = any(
                np.sqrt((cx - accepted['center'][0])**2 + (cy - accepted['center'][1])**2) < min_distance
                for accepted in merged_vias
            )
            
            if not too_close:
                # Ajouter les métadonnées finales
                via['id'] = str(uuid.uuid4())
                via['image_index'] = self.current_image_index
                via['image_name'] = getattr(self.parent.raw.raw[self.current_image_index], 'filename', f'image_{self.current_image_index}')
                merged_vias.append(via)
        
        return merged_vias

    def detect_vias(self):
        """Détecte les vias sur l'image courante avec une approche multi-seuils ou simple"""
        if not self.parent.raw.raw:
            return
            
        current_image = self.parent.raw.raw[self.current_image_index].raw
        gray = cv2.cvtColor(current_image, cv2.COLOR_BGR2GRAY) if len(current_image.shape) == 3 else current_image.copy()
        
        if self.multi_threshold_var.get():
            # Détection multi-seuils pour capturer tous les vias
            base_threshold = self.threshold_var.get()
            
            # Définir les seuils : un plus élevé (strict) et un plus bas (sensible)
            thresholds = [
                base_threshold + 20,  # Seuil strict (pour les vias bien contrastés)
                base_threshold,       # Seuil de base (choisi par l'utilisateur)
                base_threshold - 15   # Seuil bas (pour les vias moins contrastés)
            ]
            
            # Éviter les seuils négatifs ou trop hauts
            thresholds = [max(10, min(240, t)) for t in thresholds]
            
            print(f"Détection multi-seuils: {thresholds}")
            
            # Détecter les vias pour chaque seuil
            all_detections = []
            for threshold in thresholds:
                vias_at_threshold = self.detect_vias_at_threshold(gray, threshold)
                all_detections.append(vias_at_threshold)
                print(f"Seuil {threshold}: {len(vias_at_threshold)} vias trouvés")
            
            # Fusionner les résultats
            self.detected_vias = self.merge_vias(all_detections)
            
            messagebox.showinfo("Détection terminée", f"{len(self.detected_vias)} vias détectés (fusion multi-seuils).")
            
            # Afficher les statistiques de détection
            if self.detected_vias:
                avg_circularity = sum(v['circularity'] for v in self.detected_vias) / len(self.detected_vias)
                avg_aspect_ratio = sum(v['aspect_ratio'] for v in self.detected_vias) / len(self.detected_vias)
                thresholds_used = list(set(v.get('threshold', base_threshold) for v in self.detected_vias))
                print(f"Circularité moyenne: {avg_circularity:.2f}, Aspect ratio moyen: {avg_aspect_ratio:.2f}")
                print(f"Seuils utilisés: {sorted(thresholds_used)}")
        else:
            # Mode simple (ancien comportement)
            vias_simple = self.detect_vias_at_threshold(gray, self.threshold_var.get())
            
            # Ajouter les métadonnées et filtrer par distance
            self.detected_vias = []
            for via in vias_simple:
                cx, cy = via['center']
                
                # Vérifier distance minimale avec les autres vias
                too_close = any(
                    np.sqrt((cx - v['center'][0])**2 + (cy - v['center'][1])**2) < self.min_distance_var.get()
                    for v in self.detected_vias
                )
                
                if not too_close:
                    via['id'] = str(uuid.uuid4())
                    via['image_index'] = self.current_image_index
                    via['image_name'] = getattr(self.parent.raw.raw[self.current_image_index], 'filename', f'image_{self.current_image_index}')
                    self.detected_vias.append(via)
            
            messagebox.showinfo("Détection terminée", f"{len(self.detected_vias)} vias détectés (seuil simple).")
            
            # Afficher les statistiques de détection
            if self.detected_vias:
                avg_circularity = sum(v['circularity'] for v in self.detected_vias) / len(self.detected_vias)
                avg_aspect_ratio = sum(v['aspect_ratio'] for v in self.detected_vias) / len(self.detected_vias)
                print(f"Circularité moyenne: {avg_circularity:.2f}, Aspect ratio moyen: {avg_aspect_ratio:.2f}")
        
        self.display_current_image()
        
        # Mettre à jour la zone d'information
        self.update_detection_info()
        
    def update_detection_info(self):
        """Met à jour les informations de détection dans la zone d'information"""
        # Conserver les instructions
        instructions = ("Instructions : Shift + Clic gauche = Ajouter un via manuellement | "
                       "Shift + Clic droit = Supprimer un via | "
                       "Ctrl + Molette = Zoom | Clic droit + Glisser = Déplacer\n")
        
        self.info_text.delete(1.0, tk.END)
        self.info_text.insert(tk.END, instructions)
        
        if not self.detected_vias:
            self.info_text.insert(tk.END, "Aucun via détecté.\n")
            return
        
        # Statistiques de base
        num_vias = len(self.detected_vias)
        avg_circularity = sum(v['circularity'] for v in self.detected_vias) / num_vias
        avg_aspect_ratio = sum(v['aspect_ratio'] for v in self.detected_vias) / num_vias
        
        # Seuils utilisés
        thresholds_used = list(set(v.get('threshold', 180) for v in self.detected_vias))
        
        # Affichage des statistiques
        self.info_text.insert(tk.END, f"Nombre de vias détectés: {num_vias}\n")
        self.info_text.insert(tk.END, f"Circularité moyenne: {avg_circularity:.2f}\n")
        self.info_text.insert(tk.END, f"Aspect ratio moyen: {avg_aspect_ratio:.2f}\n")
        self.info_text.insert(tk.END, f"Seuils utilisés: {sorted(thresholds_used)}\n")
        
    def reset_detection(self):
        """Réinitialise la détection"""
        self.detected_vias = []
        self.display_current_image()
        
        # Réinitialiser la zone d'information mais garder les instructions
        instructions = ("Instructions : Shift + Clic gauche = Ajouter un via manuellement | "
                       "Shift + Clic droit = Supprimer un via | "
                       "Ctrl + Molette = Zoom | Clic droit + Glisser = Déplacer\n")
        self.info_text.delete(1.0, tk.END)
        self.info_text.insert(tk.END, instructions)
        self.info_text.insert(tk.END, "Aucune détection effectuée.\n")
        
    def accept_vias(self):
        """Accepte les vias détectés et les enregistre dans le projet"""
        if not self.detected_vias:
            messagebox.showwarning("Aucun via", "Aucun via détecté à enregistrer.")
            return
            
        print(f"Tentative de sauvegarde de {len(self.detected_vias)} vias")
        
        # Lire le fichier projet existant
        project_path = self.parent.current_project / 'project.json'
        try:
            with open(project_path, 'r', encoding='utf-8') as file:
                project_data = json.load(file)
                print(f"Fichier projet lu avec succès: {project_path}")
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de lire le fichier projet: {e}")
            print(f"ERREUR lecture fichier projet: {e}")
            return
        
        # Préserver les pathtrackings existants
        existing_pathtrackings = project_data.get('pathtrackings', [])
        print(f"Pathtrackings existants préservés: {len(existing_pathtrackings)}")
        
        # Ajouter les vias au projet
        project_data['vias'] = []
        for via in self.detected_vias:
            via_record = {
                "id": via["id"],
                "center": via["center"], 
                "radius": via["radius"],
                "area": via["area"],
                "image_index": via["image_index"],
                "image_name": via.get("image_name", "")
            }
            project_data['vias'].append(via_record)
            print(f"Via ajouté: {via_record}")
        
        # Remettre les pathtrackings
        project_data['pathtrackings'] = existing_pathtrackings
        
        # Enregistrer le fichier projet
        try:
            with open(project_path, 'w', encoding='utf-8') as file:
                json.dump(project_data, file, indent=2, ensure_ascii=False)
            
            print(f"SUCCÈS: {len(self.detected_vias)} vias sauvegardés dans {project_path}")
            print(f"Pathtrackings préservés: {len(existing_pathtrackings)}")
            
            # Recharger les vias dans l'application principale
            self.parent.loadProjectVias()
            print(f"Vias rechargés dans l'application principale")
            
            messagebox.showinfo("Succès", f"{len(self.detected_vias)} vias enregistrés dans le projet.")
            self.close_window()
            
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible d'enregistrer le projet: {e}")
            print(f"ERREUR sauvegarde projet: {e}")
    
    def zoom_in(self, x, y, widget):
        """Zoom avant centré sur la position de la souris"""
        old_zoom = self.zoom_factor
        self.zoom_factor = min(self.zoom_factor * 1.2, 5.0)  # Zoom max 5x
        
        # Ajuster l'offset pour centrer le zoom sur la position de la souris
        zoom_ratio = self.zoom_factor / old_zoom
        self.image_offset_x = x - (x - self.image_offset_x) * zoom_ratio
        self.image_offset_y = y - (y - self.image_offset_y) * zoom_ratio
        
        self.display_current_image()
    
    def zoom_out(self, x, y, widget):
        """Zoom arrière centré sur la position de la souris"""
        old_zoom = self.zoom_factor
        self.zoom_factor = max(self.zoom_factor / 1.2, 0.1)  # Zoom min 0.1x
        
        # Ajuster l'offset pour centrer le zoom sur la position de la souris
        zoom_ratio = self.zoom_factor / old_zoom
        self.image_offset_x = x - (x - self.image_offset_x) * zoom_ratio
        self.image_offset_y = y - (y - self.image_offset_y) * zoom_ratio
        
        self.display_current_image()
    
    def reset_zoom(self):
        """Remet le zoom à 1.0 et centre l'image"""
        self.zoom_factor = 1.0
        self.image_offset_x = 0
        self.image_offset_y = 0
        self.display_current_image()
        
    def canvas_to_image_coords(self, canvas_x, canvas_y):
        """Convertit les coordonnées du canvas vers les coordonnées de l'image originale"""
        # Prendre en compte l'offset et le zoom
        image_x = (canvas_x - self.image_offset_x) / self.zoom_factor
        image_y = (canvas_y - self.image_offset_y) / self.zoom_factor
        
        return int(image_x), int(image_y)
    
    def find_via_at_position(self, x, y, tolerance=15):
        """Trouve un via à la position donnée (avec tolérance)"""
        for i, via in enumerate(self.detected_vias):
            distance = np.sqrt((x - via['center'][0])**2 + (y - via['center'][1])**2)
            if distance <= tolerance:
                return i, via
        return None, None
    
    def remove_via_manually(self, image_x, image_y):
        """Supprime un via manuellement"""
        via_index, via = self.find_via_at_position(image_x, image_y)
        
        if via is not None:
            response = messagebox.askyesno(
                "Supprimer le via",
                f"Voulez-vous supprimer le via n°{via_index + 1} ?\n"
                f"Position: ({via['center'][0]}, {via['center'][1]})\n"
                f"Circularité: {via['circularity']:.2f}\n"
                f"Aspect ratio: {via['aspect_ratio']:.2f}"
            )
            
            if response:
                self.detected_vias.pop(via_index)
                self.display_current_image()
                self.update_detection_info()
                print(f"Via supprimé à la position ({image_x}, {image_y})")
        else:
            messagebox.showinfo("Aucun via", "Aucun via trouvé à cette position.")
    
    def add_via_manually(self, image_x, image_y):
        """Ajoute un via manuellement par recherche locale"""
        if not self.parent.raw.raw:
            return
            
        current_image = self.parent.raw.raw[self.current_image_index].raw
        gray = cv2.cvtColor(current_image, cv2.COLOR_BGR2GRAY) if len(current_image.shape) == 3 else current_image.copy()
        
        # Définir une zone de recherche autour du clic (50x50 pixels)
        search_radius = 25
        h, w = gray.shape[:2]
        
        # Limiter la zone de recherche aux bords de l'image
        y1 = max(0, image_y - search_radius)
        y2 = min(h, image_y + search_radius)
        x1 = max(0, image_x - search_radius)
        x2 = min(w, image_x + search_radius)
        
        # Extraire la zone de recherche
        search_area = gray[y1:y2, x1:x2]
        
        if search_area.size == 0:
            messagebox.showwarning("Erreur", "Zone de recherche invalide.")
            return
        
        # Essayer plusieurs seuils pour trouver le via
        base_threshold = self.threshold_var.get()
        thresholds_to_try = [
            base_threshold,
            base_threshold - 20,
            base_threshold - 40,
            base_threshold + 20
        ]
        
        found_via = None
        best_circularity = 0
        
        for threshold in thresholds_to_try:
            if threshold < 10 or threshold > 250:
                continue
                
            # Seuillage de la zone de recherche
            _, thresh = cv2.threshold(search_area, threshold, 255, cv2.THRESH_BINARY)
            
            # Nettoyage morphologique léger
            kernel = np.ones((2,2), np.uint8)
            cleaned = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
            cleaned = cv2.morphologyEx(cleaned, cv2.MORPH_OPEN, kernel)
            
            # Détection des contours
            contours, _ = cv2.findContours(cleaned, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for contour in contours:
                area = cv2.contourArea(contour)
                if self.min_area_var.get() <= area <= self.max_area_var.get():
                    perimeter = cv2.arcLength(contour, True)
                    if perimeter > 0:
                        circularity = 4 * np.pi * area / (perimeter * perimeter)
                        
                        # Calculer l'aspect ratio
                        rect = cv2.minAreaRect(contour)
                        width, height = rect[1]
                        if width > 0 and height > 0:
                            aspect_ratio = max(width, height) / min(width, height)
                        else:
                            aspect_ratio = 10
                        
                        # Critères pour un via valide
                        if circularity > 0.5 and aspect_ratio < 1.8:  # Critères moins stricts pour l'ajout manuel
                            M = cv2.moments(contour)
                            if M["m00"] != 0:
                                # Coordonnées relatives dans la zone de recherche
                                local_cx = int(M["m10"] / M["m00"])
                                local_cy = int(M["m01"] / M["m00"])
                                
                                # Coordonnées absolues dans l'image
                                global_cx = x1 + local_cx
                                global_cy = y1 + local_cy
                                
                                # Prendre le via le plus proche du clic et avec la meilleure circularité
                                distance_to_click = np.sqrt((global_cx - image_x)**2 + (global_cy - image_y)**2)
                                
                                if distance_to_click <= search_radius and circularity > best_circularity:
                                    # Vérifier qu'il n'y a pas déjà un via trop proche
                                    too_close = any(
                                        np.sqrt((global_cx - v['center'][0])**2 + (global_cy - v['center'][1])**2) < self.min_distance_var.get()
                                        for v in self.detected_vias
                                    )
                                    
                                    if not too_close:
                                        best_circularity = circularity
                                        radius = int(np.sqrt(area / np.pi))
                                        found_via = {
                                            'id': str(uuid.uuid4()),
                                            'center': [global_cx, global_cy],
                                            'radius': max(radius, 3),
                                            'area': area,
                                            'circularity': circularity,
                                            'aspect_ratio': aspect_ratio,
                                            'threshold': threshold,
                                            'image_index': self.current_image_index,
                                            'image_name': getattr(self.parent.raw.raw[self.current_image_index], 'filename', f'image_{self.current_image_index}')
                                        }
        
        if found_via:
            # Demander confirmation
            response = messagebox.askyesno(
                "Ajouter le via",
                f"Via détecté à la position ({found_via['center'][0]}, {found_via['center'][1]})\n"
                f"Circularité: {found_via['circularity']:.2f}\n"
                f"Aspect ratio: {found_via['aspect_ratio']:.2f}\n"
                f"Seuil utilisé: {found_via['threshold']}\n\n"
                f"Voulez-vous ajouter ce via ?"
            )
            
            if response:
                self.detected_vias.append(found_via)
                self.display_current_image()
                self.update_detection_info()
                print(f"Via ajouté manuellement à la position ({found_via['center'][0]}, {found_via['center'][1]})")
        else:
            messagebox.showinfo(
                "Aucun via détecté",
                f"Aucun via valide trouvé dans la zone autour de ({image_x}, {image_y}).\n"
                f"Essayez d'ajuster les paramètres ou de cliquer plus précisément sur le via."
            )
    
    def load_existing_vias(self):
        """Charge les vias existants du projet"""
        if not self.parent.current_project:
            return
            
        project_path = self.parent.current_project / 'project.json'
        try:
            with open(project_path, 'r', encoding='utf-8') as file:
                project_data = json.load(file)
                
            # Charger les vias existants
            if 'vias' in project_data and project_data['vias']:
                self.detected_vias = []
                for via_record in project_data['vias']:
                    via_data = {
                        'id': via_record.get('id', str(uuid.uuid4())),
                        'center': via_record['center'],
                        'radius': via_record['radius'],
                        'area': via_record.get('area', 0),
                        'circularity': via_record.get('circularity', 0.8),  # Valeur par défaut
                        'aspect_ratio': via_record.get('aspect_ratio', 1.0),  # Valeur par défaut
                        'threshold': via_record.get('threshold', 180),  # Valeur par défaut
                        'image_index': via_record.get('image_index', 0),
                        'image_name': via_record.get('image_name', '')
                    }
                    self.detected_vias.append(via_data)
                    
                print(f"Chargé {len(self.detected_vias)} vias existants du projet")
                
        except Exception as e:
            print(f"Erreur lors du chargement des vias existants: {e}")
            # Pas d'erreur critique, on continue avec une liste vide
            self.detected_vias = []

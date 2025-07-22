import tkinter as tk
from pathlib import Path
import cv2
from PIL import Image, ImageTk
import numpy as np
from skimage.metrics import structural_similarity as ssim
import json

from RXmodule.RXviewerRaws import RXviewerRaws
from RXmodule.RXviewerLabels import RXviewerLabels
from RXmodule.RXviewerToolsBox import RXviewerToolsBox


class ProjectView:
    def __init__(self, parent, bgColor, app, path):
        self.raw = RXviewerRaws(app)
        self.labels = RXviewerLabels(app)
        self.toolsBox = RXviewerToolsBox(app)
        self.raw_id = 0
        self.tk_image = None
        self.app = app
        self.raw.raw_coords = [0, 0]

        self.raw.loadImagesFromPath(path)
        self.project_path = path
        with open(path / "project.json", 'r', encoding='utf-8') as file:
            self.project_file = json.load(file)
        self.labels.addLabels(self.project_file['labels'])

        self.container = tk.Frame(parent, bg=bgColor)
        self.container.pack(side="left", expand=True, fill="both")

        self.canvas = tk.Canvas(self.container, bg=bgColor)
        self.canvas.pack(expand=True, fill="both")

        self.counter_label = tk.Label(self.container, text="0/0", bg=bgColor, fg="white")
        self.counter_label.pack()

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

    def scrollTo(self, index):
        if 0 <= index < len(self.raw.raw):
            self.raw_id = index
            self.showImage()


class RXviewerSync:
    def __init__(self, app, path1: Path, path2: Path):
        self.window = tk.Toplevel(app)
        self.window.title("RXviewer - Synchronisation automatique")
        self.window.geometry("1920x1080")
        self.window.configure(bg="#333333")
        self.window.grab_set()  

        self.view_left = ProjectView(self.window, bgColor="#222222", app=app, path=path1)
        self.view_right = ProjectView(self.window, bgColor="#222222", app=app, path=path2)

        self.window.after(100, self._compute_sync_points)  

        self.window.bind("<MouseWheel>", self._onScroll)
        self.window.bind("<Button-4>", self._onScroll)
        self.window.bind("<Button-5>", self._onScroll)

    def _compute_sync_points(self):
        raw_left = self.view_left.raw.raw
        raw_right = self.view_right.raw.raw

        if not raw_left or not raw_right:
            print("Erreur : raw manquant.")
            return

        best_score = -1
        best_pair = (0, 0)

        step_left = max(1, len(raw_left) // 20)
        step_right = max(1, len(raw_right) // 20)

        for i in range(0, len(raw_left), step_left):
            for j in range(0, len(raw_right), step_right):
                try:
                    score = self._compare_images(raw_left[i].raw, raw_right[j].raw)
                    if score > best_score:
                        best_score = score
                        best_pair = (i, j)
                except Exception as e:
                    print(f"Erreur comparaison: {e}")

        self.left_base = best_pair[0]
        self.right_base = best_pair[1]
        self.left_total = len(raw_left)
        self.right_total = len(raw_right)

        self.view_left.scrollTo(self.left_base)
        self.view_right.scrollTo(self.right_base)

    def _compare_images(self, img1, img2):
        img1_gray = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
        img2_gray = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
        img1_resized = cv2.resize(img1_gray, (256, 256))
        img2_resized = cv2.resize(img2_gray, (256, 256))
        score, _ = ssim(img1_resized, img2_resized, full=True)
        return score

    def _onScroll(self, event):
        delta = event.delta if hasattr(event, 'delta') else (120 if event.num == 4 else -120)
        step = 1 if delta < 0 else -1

        new_left = self.view_left.raw_id + step
        ratio = (self.right_total - self.right_base) / (self.left_total - self.left_base) if (self.left_total - self.left_base) != 0 else 1
        new_right = self.right_base + round((new_left - self.left_base) * ratio)
        self.view_left.scrollTo(new_left)
        self.view_right.scrollTo(new_right)

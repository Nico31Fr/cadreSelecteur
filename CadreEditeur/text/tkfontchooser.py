# -*- coding: utf-8 -*-
"""Boîte de dialogue de sélection de police avec aperçu PIL (supporte les polices embarquées)."""

from tkinter import (
    Toplevel, Listbox, StringVar, Scrollbar, Entry, Button
)
from tkinter.ttk import Frame, Label, Style
from PIL import Image, ImageFont, ImageDraw, ImageTk
from os import path, listdir
import sys


def get_app_dir():
    """Retourne le dossier contenant le script (mode normal)
       ou le .exe PyInstaller (mode frozen)."""
    if getattr(sys, 'frozen', False):
        # chemin de l'exécutable
        return path.dirname(sys.executable)
    else:
        # chemin du script .py
        return path.join(path.dirname(path.abspath(__file__)), "..", "..")

class FontChooser(Toplevel):
    """ Boîte de dialogue de sélection de police
     """
    def __init__(self, master, font_dict=None, text="Abcd", title="Choisir une police", **kwargs):
        super().__init__(master, **kwargs)
        self.title(title)
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self.quit)

        self.res = None
        self.preview_image = None

        style = Style(self)
        style.configure("prev.TLabel", background="white")
        bg = style.lookup("TLabel", "background")
        self.configure(bg=bg)

        # --- Charger les polices du dossier Fonts
        fonts_dir = path.join(get_app_dir(), "Fonts")
        self.fonts = []
        if path.isdir(fonts_dir):
            for f in listdir(str(fonts_dir)):
                if f.lower().endswith(".ttf"):
                    font_name = path.splitext(f)[0]
                    self.fonts.append(font_name)
        else:
            print(f"[AVERTISSEMENT] Dossier Fonts introuvable : {fonts_dir}")

        if not self.fonts:
            self.fonts = ["adelia"]

        self.fonts.sort()
        max_length = int(2.5 * max([len(font) for font in self.fonts])) // 3

        # --- tailles
        self.sizes = [str(i) for i in range(6, 82, 2)]

        # --- paramètres initiaux
        font_dict = font_dict or {}
        self.current_family = font_dict.get("family", self.fonts[0])
        self.current_size = str(font_dict.get("size", 20))
        self.preview_text = text[:30]

        # --- variables Tk
        self.var_family = StringVar(value=self.current_family)
        self.var_size = StringVar(value=self.current_size)
        self.font_family_list = StringVar(value=" ".join(self.fonts))
        self.font_size_list = StringVar(value=" ".join(self.sizes))

        # --- widgets principaux
        self.entry_family = Entry(self, textvariable=self.var_family, width=max_length)
        self.entry_size = Entry(self, textvariable=self.var_size, width=4)
        self.list_family = Listbox(self, listvariable=self.font_family_list, height=8, exportselection=False)
        self.list_size = Listbox(self, listvariable=self.font_size_list, height=8, width=4, exportselection=False)
        self.scroll_family = Scrollbar(self, orient='vertical', command=self.list_family.yview)
        self.scroll_size = Scrollbar(self, orient='vertical', command=self.list_size.yview)

        self.list_family.configure(yscrollcommand=self.scroll_family.set)
        self.list_size.configure(yscrollcommand=self.scroll_size.set)

        # --- aperçu via PIL
        self.preview = Label(self, relief="groove", style="prev.TLabel", anchor="center", width=40)

        # --- disposition
        self.entry_family.grid(row=0, column=0, sticky="ew", pady=(10, 1), padx=(10, 0))
        self.entry_size.grid(row=0, column=2, sticky="ew", pady=(10, 1), padx=(10, 0))
        self.list_family.grid(row=1, column=0, sticky="nsew", pady=(1, 10), padx=(10, 0))
        self.scroll_family.grid(row=1, column=1, sticky='ns', pady=(1, 10))
        self.list_size.grid(row=1, column=2, sticky="nsew", pady=(1, 10), padx=(10, 0))
        self.scroll_size.grid(row=1, column=3, sticky='ns', pady=(1, 10))
        self.preview.grid(row=2, column=0, columnspan=4, sticky="eswn", padx=10, pady=(0, 10))

        # --- boutons
        button_frame = Frame(self)
        button_frame.grid(row=3, column=0, columnspan=4, pady=(0, 10))
        Button(button_frame, text="OK", command=self.ok).grid(row=0, column=0, padx=4)
        Button(button_frame, text="Annuler", command=self.quit).grid(row=0, column=1, padx=4)

        # --- bindings
        self.list_family.bind("<<ListboxSelect>>", self.on_family_select)
        self.list_size.bind("<<ListboxSelect>>", self.on_size_select)
        self.entry_family.bind("<Return>", self.update_preview)
        self.entry_size.bind("<Return>", self.update_preview)

        # --- initialisation
        self.list_family.selection_set(0)
        self.list_size.selection_set(0)
        self.update_preview()

        self.grab_set()
        self.lift()
        self.focus_set()

    # -------------------------------------------------------
    # --- Aperçu PIL : rend la vraie police à partir du .ttf
    # -------------------------------------------------------
    def update_preview(self, _event=None):
        """ met a jour la zone de prévisualisation
        """
        family = self.var_family.get()
        try:
            size = int(self.var_size.get())
        except ValueError:
            size = 20

        font_path = path.join(get_app_dir(), "Fonts", f"{family}.ttf")
        if not path.exists(font_path):
            # fallback si non trouvé
            font_path = path.join(get_app_dir(), "Fonts", f"{self.fonts[0]}.ttf")

        try:
            font = ImageFont.truetype(font_path, size)
        except Exception as e:
            print(f"[AVERTISSEMENT] Erreur de chargement police {font_path}: {e}")
            font = ImageFont.load_default()

        # crée l'image de prévisualisation
        img = Image.new("RGB", (400, 80), "white")
        draw = ImageDraw.Draw(img)
        draw.text((10, 20), f"Aperçu : {family}", fill="black", font=font)

        self.preview_image = ImageTk.PhotoImage(img)
        self.preview.config(image=str(self.preview_image), text="")

    def on_family_select(self, _event=None):
        """Quand on sélectionne une famille de police."""
        if not self.list_family.curselection():
            return
        index = self.list_family.curselection()[0]
        family = self.list_family.get(index)
        self.var_family.set(family)
        self.update_preview()

    def on_size_select(self, _event=None):
        """Quand on sélectionne une taille."""
        if not self.list_size.curselection():
            return
        index = self.list_size.curselection()[0]
        size = self.list_size.get(index)
        self.var_size.set(size)
        self.update_preview()

    def ok(self):
        """Valide le choix."""
        self.res = {"family": self.var_family.get(), "size": int(self.var_size.get())}
        self.quit()

    def quit(self):
        """Ferme la fenêtre."""
        self.destroy()

    def get_res(self):
        """ récupère la valeur de res
        """
        return self.res


# ----------------------------------------------------------
# fonction helper comme avant : ask_font()
# ----------------------------------------------------------
def ask_font(master=None, text="Abcd", title="Choisir une police", **font_args):
    """ lance un sélecteur de police"""
    chooser = FontChooser(master, font_args, text, title)
    chooser.wait_window(chooser)
    return chooser.get_res()


# ----------------------------------------------------------
# test autonome
# ----------------------------------------------------------
if __name__ == "__main__":
    import tkinter as tk
    root = tk.Tk()

    label = Label(root, text='Police choisie :')
    label.pack(padx=10, pady=(10, 4))

    def callback():
        """ _ """
        font = ask_font(root, title="Choisir une police")
        if font:
            font_name = font['family']
            font_str = f"{font_name} {font['size']}"
            label.configure(text=f'Police choisie : {font_str}')

    Button(root, text='Sélecteur de police', command=callback).pack(padx=10, pady=(4, 10))
    root.mainloop()

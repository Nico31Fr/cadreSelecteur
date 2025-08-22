# -*- coding: utf-8 -*-
""" Module d'édition de cadre pour PiBooth
    |-> fenêtre d'édition d'un cadre  """

import tkinter as tk
from tkinter import colorchooser,messagebox
from PIL import Image, ImageTk
from re import fullmatch

from .layerimage import LayerImage
from .layertext import LayerText
from .layerexcluzone import LayerExcluZone


class ImageEditor:
    """
    Une application d'édition d'image simple permettant aux utilisateurs
    d'importer des images, d'ajouter du texte, de déplacer/redimensionner les images,
    et d'enregistrer la composition finale.
    """

    def __init__(self, root, exclusion_zone, resources_path):
        """
        Initialise l'application ImageEditor avec une fenêtre tkinter racine.

        Paramètres :
            root (tk.Tk) : La fenêtre tkinter racine.
            Exclusion_zone : liste contenant les zone à garder en transparent
        """
        self.CANVA_W, self.CANVA_H = 600, 400
        # Dimension de l'image générée
        self.IMAGE_W, self.IMAGE_H = 1800, 1200
        self.RATIO = int(self.IMAGE_W // self.CANVA_W)
        self.exclusion_zone = exclusion_zone
        self.imported_image_path = None
        self.display_imported_image = None
        self.image_imported_image = None
        self.original_image = None
        self.background_couleur = "#FFFFFF"
        self.root = root
        self.texte_background_value = tk.StringVar(value=self.background_couleur)

        # -- Pile dynamique de calques --
        self.layers = []
        self.active_layer_idx = -1

        # -- Canvas/IHM --
        self.canvas = tk.Canvas(self.root, width=self.CANVA_W, height=self.CANVA_H)
        self.canvas.pack()
        self.tk_image = None

        self.layers_frame = tk.Frame(self.root)
        self.layers_frame.pack(side='left',
                                    padx=10,
                                    pady=10,
                                    ipadx=10,
                                    ipady=10)
        self.listbox = tk.Listbox(self.layers_frame, height=5)
        self.listbox.pack(fill='x')
        self.listbox.bind("<<ListboxSelect>>", self.on_layer_select)

        # -- Boutons de gestion pile --
        btnf = tk.Frame(self.layers_frame); btnf.pack()
        tk.Button(btnf, text="Ajouter Image", command=self.add_image_layer).grid(row=0,column=0)
        tk.Button(btnf, text="Ajouter Texte", command=self.add_text_layer).grid(row=0,column=1)
        tk.Button(btnf, text="Supprimer", command=self.delete_layer).grid(row=0,column=2)
        tk.Button(btnf, text="  ˄  ", command=lambda:self.move_layer(-1)).grid(row=0,column=3)
        tk.Button(btnf, text="  ˅  ", command=lambda:self.move_layer(1)).grid(row=0,column=4)

        # -- Boutons de gestion couleur de fond --
        fondf = tk.Frame(self.layers_frame)
        fondf.pack(pady=(10, 0))
        tk.Label(fondf, text="Couleur du fond :").pack(side="left")
        self.texte_background = tk.Entry(fondf, textvariable=self.texte_background_value, width=8)
        self.texte_background.pack(side="left", padx=5)
        self.label_couleur = tk.Label(fondf, text="                  ",
                                      bg=self.background_couleur,
                                      cursor="hand2")
        self.label_couleur.pack(side="left", padx=5)
        # Ouvre le colorchooser sur clic
        self.label_couleur.bind("<Button-1>", lambda e: self.select_background_color())
        # Lier une fonction à la modification de la valeur de l'Entry
        self.texte_background_value.trace_add("write",
                                              self.on_color_entry_change)

        # Frame bouton de config du calque
        self.param_frame = tk.Frame(self.root,
                                    borderwidth=2,
                                    relief="groove",
                                    width=300,
                                    height=200,
                                    padx=10,
                                    pady=10)
        self.param_frame.pack(side='right')
        self.param_frame.pack_propagate(False)

        # -- Drag & Resize --
        self.canvas.bind("<Button-1>", self.start_drag)
        self.canvas.bind("<B1-Motion>", self.drag_drop)
        self.canvas.bind("<MouseWheel>", self.resize)
        self.start_drag_pos = None

        self.add_zone_exclu_layer()

        self.update_canvas()

    def add_image_layer(self):
        """
        Ajoute un nouveau calque image et le sélectionne.
        """
        n = len([l for l in self.layers if l.layer_type=='image'])+1
        layer = LayerImage(self.root,
                           self,
                           (self.CANVA_W,self.CANVA_H),
                           (self.IMAGE_W,self.IMAGE_H),
                           self.RATIO,
                           name=f"Image {n}")
        if layer.import_image():
            self.layers.append(layer)
            self.active_layer_idx = len(self.layers)-1
            self.refresh_listbox()
            self.update_canvas()
        else:
            del layer

    def add_text_layer(self):
        """
        Ajoute un nouveau calque texte et le sélectionne.
        """
        n = len([l for l in self.layers if l.layer_type=='text'])+1
        name = f"Texte {n}"
        layer = LayerText(self.root,
                          self,
                          (self.CANVA_W,self.CANVA_H),
                          (self.IMAGE_W,self.IMAGE_H),
                          self.RATIO,
                          name=name)
        self.layers.append(layer)
        self.active_layer_idx = len(self.layers) - 1
        self.refresh_listbox()
        self.update_canvas()

    def add_zone_exclu_layer(self):
        """
        met à jour les zone d'exclusions
        """
        name = "Zones insertion photos"
        layer = LayerExcluZone(self.root,
                               self,
                          (self.CANVA_W,self.CANVA_H),
                          (self.IMAGE_W,self.IMAGE_H),
                          self.RATIO,
                          name=name)
        layer.set_exclusion_zone(self.exclusion_zone)
        self.layers.append(layer)
        self.active_layer_idx = len(self.layers)-1
        self.refresh_listbox()
        self.update_canvas()

    def update_zone_exclu_layer(self, exclusion_zone):
        """
        Ajoute un nouveau calque zone d'exclusions
        """

        for layer in self.layers:
            if layer.layer_type == 'ZoneEx':
                layer.set_exclusion_zone(exclusion_zone)

        self.update_canvas()

    def delete_layer(self):
        """
        Supprime le calque sélectionné.
        """
        if 0 <= self.active_layer_idx < len(self.layers)\
                and  self.layers[self.active_layer_idx].layer_type != 'ZoneEx' :
            del self.layers[self.active_layer_idx]
            if self.layers:
                self.active_layer_idx = max(0, self.active_layer_idx-1)
            else:
                self.active_layer_idx = -1
            self.refresh_listbox()
            self.update_canvas()

    def move_layer(self, direction):
        """
        Fait monter/descendre le calque actif dans la pile.

        Args:
            direction (int): -1=monter, 1=descendre
        """
        idx = self.active_layer_idx
        if 0 <= idx < len(self.layers):
            new_idx = idx+direction
            if 0 <= new_idx < len(self.layers):
                self.layers[idx], self.layers[new_idx] = self.layers[new_idx], self.layers[idx]
                self.active_layer_idx = new_idx
                self.refresh_listbox()
                self.update_canvas()

    def refresh_listbox(self):
        """
        Met à jour la liste visuelle des calques.
        """
        self.listbox.delete(0,"end")
        for i, l in enumerate(self.layers):
            name = l.name + (" [actif]" if i==self.active_layer_idx else "")
            self.listbox.insert("end", name)
        self.listbox.selection_clear(0,"end")
        if self.active_layer_idx >=0:
            self.listbox.selection_set(self.active_layer_idx)
        self.layers[self.active_layer_idx].update_param_zone(self.param_frame)

    def on_layer_select(self, event):
        """
        Sélectionne le calque actif dans la liste.
        """
        idxs = self.listbox.curselection()
        if idxs:
            self.active_layer_idx = idxs[0]
            self.refresh_listbox()
            self.update_canvas()

    def start_drag(self, event):
        """
        Démarre le déplacement du calque actif.
        """
        if 0 <= self.active_layer_idx < len(self.layers):
            l = self.layers[self.active_layer_idx]
            l._drag_pos = (event.x, event.y)

    def drag_drop(self, event):
        """
        Effectue le déplacement drag&drop du calque actif.
        """
        if 0 <= self.active_layer_idx < len(self.layers):
            l = self.layers[self.active_layer_idx]
            if hasattr(l,'_drag_pos') and l._drag_pos:
                l._drag_pos = l.drag(event, l._drag_pos)
                self.update_canvas()

    def resize(self, event):
        """
        Redimensionne le calque actif (image ou texte) via la molette.
        """
        if 0 <= self.active_layer_idx < len(self.layers):
            l = self.layers[self.active_layer_idx]
            if l.layer_type == "image":
                delta = 10 if event.delta > 0 else -10
                l.resize(delta)
            elif l.layer_type == "text":
                delta = 2 if event.delta > 0 else -2
                l.resize_font(delta)
            self.update_canvas()

    def select_background_color(self):
        """ Ouvrir une boîte de dialogue de sélection de couleur """
        try:
            couleur = colorchooser.askcolor(title="Choisissez une couleur")
            if couleur[1]:
                self.background_couleur = couleur[1]
                self.update_canvas()
        except Exception as e:
            messagebox.showerror("Erreur de couleur", f"Exception inattendue : {str(e)}")

    def on_color_entry_change(self, *args):
        """
        une nouvelle valeur de couleur a été saisie, mettre à jour
        """
        try:
            if args:
                color_code = self.texte_background_value.get()
                match = fullmatch(r'^#[0-9A-Fa-f]{6}$', color_code)
                if match:
                    self.background_couleur = color_code
                    self.update_canvas()
        except Exception as e:
            messagebox.showerror("Erreur de couleur", f"Exception inattendue : {str(e)}")

    # export de l'image
    def save_image(self, out_path: str):
        """
        Ouvre une boîte de dialogue pour enregistrer l'image courante dans un fichier.
        """
        try:
            # couleur du fond
            # génère une image avec la couleur de fond sélectionnée
            image_de_font = Image.new('RGBA',
                                           (self.IMAGE_W, self.IMAGE_H),
                                           self.background_couleur)

            # évite l'effacement par le garbage collector
            image_export = image_de_font.copy()

            # superpose les calques dans l'image
            for l in reversed(self.layers):
                l.draw_on_image(image_export, export=True)

            # Enregistre le fichier image.
            extension = str('_' + str(len(self.exclusion_zone)) + '.png')
            out_path = out_path + extension
            image_export.save(out_path)

        except Exception as e:
            messagebox.showerror("Erreur d'enregistrement", f"Exception inattendue : {str(e)}")

    def update_canvas(self):
        """
        Redessine tous les calques empilés sur le canvas d’édition.
        """

        # couleur du fond
        # met à jour le label (couleur et texte)
        self.label_couleur.config(bg=self.background_couleur)
        self.texte_background.delete(0, tk.END)  # Efface le champ existant
        self.texte_background.insert(0, self.background_couleur)
        # génère une image avec la couleur sélectionnée
        display_image = Image.new('RGBA',
                                  (self.CANVA_W, self.CANVA_H),
                                  self.background_couleur)

        # évite l'effacement par le garbage collector
        temp_image = display_image.copy()

        # superpose les calques dans l'image
        for l in reversed(self.layers):
            l.draw_on_image(temp_image, export=False)

        self.tk_image = ImageTk.PhotoImage(temp_image)
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.tk_image)


# --- Pour tester/demo ---
if __name__=="__main__":
    main_root = tk.Tk()
    editor = ImageEditor(main_root, (0,0,0,0), '')
    main_root.mainloop()

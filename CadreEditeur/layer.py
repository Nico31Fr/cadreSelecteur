# -*- coding: utf-8 -*-
""" Module d'édition de cadre pour PiBooth
    |-> classe générique de gestion des calques """


class Layer:
    """
    Calque générique pour l’éditeur d’images.
    Gère la visibilité, le verrouillage, la position d’affichage,
    et définit l’interface pour les spécialisations (image, texte…).
    """

    def __init__(self, name, canva_size, image_size, ratio):
        """
        Initialise le calque.

        Args:
            name (str): Nom du calque (pour l’affichage).
            canva_size (tuple): Taille du canvas d’affichage (largeur, hauteur).
            image_size (tuple): Taille de l'image exportée (largeur, hauteur).
            ratio (int): Rapport (image_size/canva_size).
        """
        self.CANVA_W, self.CANVA_H = canva_size
        self.IMAGE_W, self.IMAGE_H = image_size
        self.RATIO = ratio
        self.display_position = (0, 0)
        self.image_position = (0, 0)
        self.visible = True
        self.locked = False
        self.layer_type = "generic"
        self.name = name

    def drag(self, event, start_pos):
        """
        Déplace le calque (drag & drop).

        Args :
            event (tk.Event) : Évènement souris Tkinter.
            start_pos (tuple) : Position de départ (x, y).
        Returns :
            tuple : Nouvelle position de départ après le déplacement.
        """
        if self.locked or not self.visible:
            return start_pos
        dx = event.x - start_pos[0]
        dy = event.y - start_pos[1]
        new_disp_x = self.display_position[0] + dx
        new_disp_y = self.display_position[1] + dy
        self.display_position = (new_disp_x, new_disp_y)
        self.image_position = (new_disp_x * self.RATIO, new_disp_y * self.RATIO)
        return (event.x, event.y)

    def draw_on_image(self, image, export=False):
        """
        Méthode à spécialiser. Dessine le calque sur l’image PIL.

        Args:
            image (PIL.Image): Image PIL sur laquelle dessiner.
            export (bool): True si l'on dessine pour export (haute rés.), False pour affichage.

        Returns :
            None
        """
        pass # À spécialiser dans les sous-classes.

    def update_param_zone(self, frame):
        """
        Méthode à spécialiser. Met à jour la zone de paramétrage du calque

        Args:
            frame (PIL.Frame): frame à mettre à jour
        Returns :
            None
        """
        pass # À spécialiser dans les sous-classes.
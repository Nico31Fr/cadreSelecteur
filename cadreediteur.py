# -*- coding: utf-8 -*-
""" Module d'édition de cadre pour PiBooth
    |→ point d'entrée de l'appli autonome """

import tkinter as tk
from CadreEditeur.imageeditorapp import ImageEditorApp


def start_cadre_editeur():
    """
    initialise une IHM et démarre l'éditeur de cadre
    """
    tk_root = tk.Tk()
    ImageEditorApp(tk_root)
    tk_root.mainloop()


if __name__ == "__main__":

    start_cadre_editeur()

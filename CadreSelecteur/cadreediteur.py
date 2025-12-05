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
    return tk_root


if __name__ == "__main__":

    root = start_cadre_editeur()
    root.mainloop()

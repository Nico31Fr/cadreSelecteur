# -*- coding: utf-8 -*-
""" Module d'édition de cadre pour PiBooth """

import tkinter as tk
from image_editor import ImageEditorApp

if __name__ == "__main__":
    tk_root = tk.Tk()
    app = ImageEditorApp(tk_root)
    tk_root.mainloop()
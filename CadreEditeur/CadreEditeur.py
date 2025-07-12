# -*- coding: utf-8 -*-
""" Module d'édition de cadre pour PiBooth """

import tkinter as tk
from image_editor import ImageEditorApp

if __name__ == "__main__":
    # Définir des zones d'exclusion
    # <mxGeometry x="20" y="420" width="110" height="160" as="geometry" />
    # <mxGeometry x="145" y="420" width="110" height="160" as="geometry" />
    # <mxGeometry x="270" y="420" width="110" height="160" as="geometry" />
    # <mxGeometry x="20" y="20" width="280" height="350" as="geometry" />
    # Y X H W
    exclusion_zones_4 = [
        (420, 20, 160, 110),
        (420, 145, 160, 110),
        (420, 270, 160, 110),
        (20, 20, 350, 280)
    ]

    # <mxGeometry x="50" y="20" width="330" height="470" as="geometry" />
    # Y X H W
    exclusion_zones_1 = [
        (50, 20, 470, 330),
    ]

    tk_root = tk.Tk()
    ImageEditorApp(tk_root, (exclusion_zones_1, exclusion_zones_4))
    tk_root.mainloop()

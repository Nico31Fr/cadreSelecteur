# -*- coding: utf-8 -*-
""" Module d'édition de cadre pour PiBooth """

import tkinter as tk

from imageeditorapp import ImageEditorApp

if __name__ == "__main__":
    # Définir des zones d'exclusion
    # <mxGeometry x="20" y="37" width="355.89" height="193" as="geometry" />
    # <mxGeometry x="390" y="37" width="195.89" height="106.23" as="geometry" />
    # <mxGeometry x="390" y="160" width="195.89" height="106.23" as="geometry" />
    # <mxGeometry x="390" y="280" width="195.89" height="106.23" as="geometry" />

    exclusion_zones_4 = [
        (20, 37, 355.89, 193),
        (390, 37, 195.89, 106.23),
        (390, 160, 195.89, 106.23),
        (390, 280, 195.89, 106.23)
    ]

    # <mxGeometry x="40" y="37" width="520" height="282" as="geometry" />
    exclusion_zones_1 = [
        (40, 37, 520, 282),
    ]

    tk_root = tk.Tk()
    ImageEditorApp(tk_root, (exclusion_zones_1, exclusion_zones_4))
    tk_root.mainloop()

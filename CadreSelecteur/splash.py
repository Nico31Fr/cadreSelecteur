# -*- coding: utf-8 -*-
""" splash screen """

from os import path
import tkinter as tk
from PIL import Image, ImageTk
import logging
from .logging_config import LOG_PATH  # noqa: F401
from .config_loader import RESOURCES_DIR
logger = logging.getLogger(__name__)


def splash():
    root = tk.Tk()
    root.overrideredirect(True)
    root.geometry("500x250+600+300")

    try:
        image = Image.open(path.join(RESOURCES_DIR, 'cadreSelecteur.png'))
        photo = ImageTk.PhotoImage(image)
        label = tk.Label(root, image=photo)
        label.image = photo
        label.pack(padx=5, pady=5)
    except Exception as e:
        logger.error(f' erreur de chargement image : {e}')
        pass

    tk.Label(
        root,
        text="Cadre Selecteur / Cadre Editeur",
        font=("Arial", 15)
    ).pack(padx=5, pady=5)

    tk.Label(
        root,
        text="Chargement en cours...\nVeuillez patienter...",
        font=("Arial", 12)
    ).pack(padx=5, pady=5)

    root.mainloop()


if __name__ == "__main__":
    splash()

# -*- coding: utf-8 -*-
""" splash screen """

from os import path
import tkinter as tk
from PIL import Image, ImageTk
import logging
from .logging_config import LOG_PATH  # noqa: F401
from .config_loader import RESOURCES_DIR

logger = logging.getLogger(__name__)


def splash(timeout_ms: int = 5000) -> None:
    """
    Affiche un écran de splash avec timeout.
    
    IMPORTANT: Cette fonction NE DOIT PAS appeler mainloop() indéfiniment
    car elle bloquerait le processus parent. À la place, elle affiche
    la fenêtre et attend avec un timeout.
    
    Args:
        timeout_ms: Timeout en millisecondes avant fermeture automatique
    """
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
        logger.error(f'Erreur de chargement image : {e}')
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
    
    # Afficher la fenêtre
    root.update()
    logger.debug(f"Splash: fenêtre affichée, timeout={timeout_ms}ms")
    
    # Attendre avec timeout et traiter les événements
    # Cela permet au process parent de nous terminer via signal
    elapsed = 0
    step = 100  # ms par itération
    
    while elapsed < timeout_ms:
        try:
            # Traiter les événements Tkinter
            root.update()
        except tk.TclError:
            # Fenêtre fermée par le parent
            logger.debug("Splash: fenêtre fermée")
            return
        
        # Attendre un peu avant la prochaine itération
        root.after(step)
        elapsed += step
    
    # Timeout atteint, fermer proprement
    logger.debug("Splash: timeout atteint, fermeture")
    try:
        root.destroy()
    except Exception as e:
        logger.warning(f"Splash: erreur lors de la destruction - {e}")


if __name__ == "__main__":
    splash()



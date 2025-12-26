# -*- coding: utf-8 -*-
""" Module de selection de cadre pour PiBooth
    |→ point d'entrée de l'appli autonome """

from multiprocessing import Process
from time import sleep

from CadreSelecteur.cadreselecteur import CadreSelecteur, check_mandatory_path
from CadreSelecteur.splash import splash

if __name__ == "__main__":
    splash_process = Process(target=lambda: splash())
    app_process = Process(target=lambda: CadreSelecteur())
    splash_process.start()

    # Vérifie les path
    check_mandatory_path()

    # start IHM
    app_process.start()

    # fermer le splash
    sleep(3)
    splash_process.terminate()
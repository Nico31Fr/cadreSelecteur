# -*- coding: utf-8 -*-
""" Module de selection de cadre pour PiBooth
    |→ point d'entrée de l'appli autonome """

from multiprocessing import Process, freeze_support
from time import sleep

from CadreSelecteur.cadreselecteur import CadreSelecteur, check_mandatory_path
from CadreSelecteur.splash import splash


def run_splash():
    splash()


def run_app():
    CadreSelecteur()


if __name__ == "__main__":
    freeze_support()  # indispensable pour Windows + PyInstaller

    splash_process = Process(target=run_splash)
    app_process = Process(target=run_app)
    splash_process.start()

    # Vérifie les path
    check_mandatory_path()

    # start IHM
    app_process.start()

    # fermer le splash sreen
    sleep(3)
    splash_process.terminate()

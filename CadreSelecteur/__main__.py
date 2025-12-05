# -*- coding: utf-8 -*-
""" Module de selection de cadre pour PiBooth
    |→ point d'entrée de l'appli autonome """

from cadreselecteur import CadreSelecteur, check_mandatory_path

if __name__ == "__main__":

    # Vérifie les path
    check_mandatory_path()

    # start IHM
    CadreSelecteur()

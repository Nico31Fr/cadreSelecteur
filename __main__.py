from CadreSelecteur import CadreSelecteur, template_path, destination_path
from CadreSelecteur import TEMPLATE_NAME_STD
from tkinter import Tk, messagebox
from os import path


if __name__ == "__main__":

    # verification de la presence des répertoire sources et dest.
    message_error = ''
    if not path.exists(template_path):
        message_error = message_error +\
                        "SOURCES :\nle repertoire :" +\
                        template_path +\
                        " n'est pas accessible\n\n"

    if not path.exists(destination_path):
        message_error = message_error + \
                        "DESTINATION:\nle repertoire :" + \
                        destination_path + \
                        " n'est pas accessible\n\n"

    # verification de la presence du template par default.
    template_dft_file = path.join(template_path,
                                  TEMPLATE_NAME_STD)
    if not path.exists(template_dft_file):
        message_error = message_error + \
                        "TEMPLATE:\nle fichier :" + \
                        template_dft_file + \
                        " n'est pas accessible\n\n"

    if message_error != '':
        messagebox.showerror(title='erreur fichiers', message=message_error)
        quit()

    # start IHM
    root = Tk()
    app = CadreSelecteur(root, template_path, destination_path)
    root.mainloop()

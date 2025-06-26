# -*- coding: utf-8 -*-
""" selecteur de cadre pour pibooth """

import os
from tkinter import Tk, Scrollbar, Canvas, Frame
from tkinter import messagebox, Label, Button, Radiobutton, StringVar
from PIL import Image, ImageTk
from shutil import copy

# taille de la fenetre
WINDOWS_SIZE = "800x600"

# repertoire avec tous les cadres / templates dispo
template_path = "C:/Temp/test/template/"
# repertoire avec le cadre / template selectionne
destination_path = "C:/Temp/test/cadre/"

# nom du template definie dans piBooth
TEMPLATE_NAME = 'template.xml'
TEMPLATE_NAME_STD = 'template_std.xml'
# nom du cadre definie dans piBooth
FRAME_NAME = 'frame.png'


class CadreSelecteur:
    """
    Class to display image thumbnails and select a template
    using radio buttons within a GUI.
    """

    def __init__(self, master, source_directory, destination_directory):
        """
        Initializes the TemplateSelector with a window
        and directory to display images.

        :param master: The Tkinter root or parent window.
        :param source_directory: The directory containing image files.
        :param destination_directory: The directory containing template files.
                for pibooth
        """
        self.master = master
        self.master.title("Sélecteur de Vignettes")
        self.source_directory = source_directory
        self.destination_directory = destination_directory
        # Set the window size
        self.master.geometry(WINDOWS_SIZE)

        # Create a frame with specific size
        self.frame = Frame(master, width=800, height=600)
        self.frame.pack(fill='both', expand=True)

        # Initialize scrollbar
        self.scrollbar = Scrollbar(self.frame, orient="vertical")
        self.scrollbar.pack(side='right', fill='y')

        # Initialize canvas for drawing
        self.canvas = Canvas(self.frame, yscrollcommand=self.scrollbar.set)
        self.canvas.pack(side='left', fill='both', expand=True)

        self.scrollbar.config(command=self.canvas.yview)

        # Create a frame to contain list of thumbnails
        self.list_frame = Frame(self.canvas)
        self.canvas.create_window((0, 0), window=self.list_frame, anchor="nw")

        # Variable to store selected image
        self.selected_image = StringVar()
        self.selected_image.set('None')

        # List and generate image thumbnails
        self.list_files_and_generate_thumbnails()

        # Create action buttons
        self.create_action_buttons()

    def list_files_and_generate_thumbnails(self):
        """
        Lists files from the specified directory
        and generates thumbnails for image files.
        """
        for filename in sorted(os.listdir(self.source_directory)):
            if filename.lower().endswith('.png'):
                self.create_thumbnail(filename)

    def create_thumbnail(self, filename):
        """
        Creates a thumbnail for the specified image file
        and displays it along with a radio button.

        :param filename: The name of the image file.
        """
        try:
            file_path = os.path.join(self.source_directory, filename)
            with Image.open(file_path) as img:
                img.thumbnail((128, 128))  # Thumbnail size
                thumbnail_img = ImageTk.PhotoImage(img)

                # Create a frame for each image and radio button
                item_frame = Frame(self.list_frame)
                item_frame.pack(side="top", fill="x", pady=5)

                radio_button = Radiobutton(item_frame,
                                           variable=self.selected_image,
                                           value=filename)
                radio_button.pack(side="left", padx=5)

                thumbnail_label = Label(item_frame, image=thumbnail_img)
                # Keep a reference to prevent garbage collection
                thumbnail_label.image = thumbnail_img
                thumbnail_label.pack(side="left", padx=5)

                text_label = Label(item_frame, text=filename)
                text_label.pack(side="left", padx=5)

        except Exception as e:
            print(f"Error processing file {filename}: {e}")

    def create_action_buttons(self):
        """
        Creates Apply and Quit buttons in the main interface.
        """
        button_frame = Frame(self.master)
        button_frame.pack(side="bottom", fill="x", pady=10)

        quit_button = Button(button_frame,
                             text="Quitter",
                             command=self.master.quit)
        quit_button.pack(side="right", padx=10)

        apply_button = Button(button_frame,
                              text="Appliquer",
                              command=self.apply_selection)
        apply_button.pack(side="right", padx=10)

    def apply_selection(self):
        """
        Function to execute when Apply button is clicked.
        Prints the selected image file to the console.
        """
        selected_file = self.selected_image.get()
        if selected_file != 'None':
            print(f"Image sélectionnée: {selected_file}")

            source_file = os.path.join(self.source_directory, selected_file)
            dest_file = os.path.join(self.destination_directory,
                                     FRAME_NAME)

            # Copier le fichier cadre
            print(f">>> Copy :{source_file}\n       to : {dest_file}")
            copy(source_file, dest_file)

            # Copier le fichier template
            source_file_tpl = source_file.replace('.png', '.xml')
            dest_file_tpl = os.path.join(self.destination_directory,
                                         TEMPLATE_NAME)

            if os.path.exists(source_file_tpl):
                print(f">>> Copy :{source_file_tpl}\n"
                      f"       to : {dest_file_tpl}")
                copy(source_file_tpl, dest_file_tpl)
            else:
                source_file_tpl = os.path.join(self.source_directory,
                                               TEMPLATE_NAME_STD)
                dest_file_tpl = os.path.join(self.destination_directory,
                                             TEMPLATE_NAME)
                print('pas de fichier frame associé au cadre,'
                      ' copy du template standard')
                print(f">>> Copy :{source_file_tpl}\n"
                      f"       to : {dest_file_tpl}")
                copy(source_file_tpl, dest_file_tpl)

        else:
            messagebox.showerror("Erreur",
                                 "Aucune image sélectionnée."
                                 " Veuillez choisir une image.")
            print("Aucune image sélectionnée.")


if __name__ == "__main__":

    # verification de la presence des répertoire sources et dest.
    message_error = ''
    if not os.path.exists(template_path):
        message_error = message_error +\
                        "SOURCES :\nle repertoire :" +\
                        template_path +\
                        " n'est pas accessible\n\n"

    if not os.path.exists(destination_path):
        message_error = message_error + \
                        "DESTINATION:\nle repertoire :" + \
                        destination_path + \
                        " n'est pas accessible\n\n"

    # verification de la presence du template par default.
    template_dft_file = os.path.join(template_path,
                                     TEMPLATE_NAME_STD)
    if not os.path.exists(template_dft_file):
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

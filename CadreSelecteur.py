# -*- coding: utf-8 -*-
""" selecteur de cadre pour pibooth """

import os
from tkinter import Tk, Scrollbar, Canvas, Frame, Toplevel
from tkinter import messagebox, Label, Button, Radiobutton, StringVar
from PIL import Image, ImageTk
from shutil import copy

# taille de la fenetre
WINDOWS_SIZE = "800x600"
# taille des vignettes
THUMBNAIL_H = 128
THUMBNAIL_L = int((THUMBNAIL_H/15)*10)

# repertoire avec tous les cadres / templates disponibles
template_path = "./Templates/"
# repertoire avec le cadre / template selectionne
destination_path = "./Cadres/"

# nom du template definie dans piBooth
TEMPLATE_NAME = 'template.xml'
TEMPLATE_NAME_STD = 'template_std.xml'
# nom du cadre definie dans piBooth
CADRE_NAME_1 = 'cadre_1.png'
CADRE_NAME_4 = 'cadre_4.png'


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
        self.master.title("Sélecteur de cadre pour piBooth V0.1")
        self.source_directory = source_directory
        self.destination_directory = destination_directory
        # Set the window size
        self.master.geometry(WINDOWS_SIZE)

        self.top_frame = Frame(master)
        self.top_frame.pack(fill='x', pady=10)

        # Create text fields
        self.text_field1 = StringVar()
        self.text_field2 = StringVar()

        # Font configuration
        label_font = ("Arial", 14, "bold")

        # Add text labels
        label1 = Label(self.top_frame,
                       text="                Cadres disponibles",
                       font=label_font)
        label1.pack(side='left', padx=5)

        label2 = Label(self.top_frame,
                       text="Cadre installé                    ",
                       font=label_font)
        label2.pack(side='right', padx=5)

        # Create a frame with specific size
        self.frame_main = Frame(master, width=800, height=600)
        self.frame_main.pack(fill='both', expand=True)
        self.master.resizable(False, False)  # Prevent window resizing

        # Initialize scrollbar for canvasSrc
        self.scrollbarSrc = Scrollbar(self.frame_main, orient="vertical")

        # Initialize canvas for drawing source
        self.canvasSrc = Canvas(self.frame_main,
                                width=450,  # Specify width for source canvas
                                yscrollcommand=self.scrollbarSrc.set)
        self.canvasSrc.pack(side='left', fill='both', expand=True)
        self.scrollbarSrc.pack(side='left', fill='y')

        self.scrollbarSrc.config(command=self.canvasSrc.yview)

        # Create a frame to contain list of thumbnails
        self.list_frameSrc = Frame(self.canvasSrc)
        self.canvasSrc.create_window((0, 0),
                                     window=self.list_frameSrc,
                                     anchor="nw")

        # Initialize canvas for drawing dest
        self.canvasDest = Canvas(self.frame_main)
        self.canvasDest.pack(side='right', fill='both', expand=True)

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
        Configures the scroll region after adding items.
        """
        self.create_dest_thumbnail()
        for filename in sorted(os.listdir(self.source_directory)):
            if filename.lower().endswith('_1.png'):
                self.create_thumbnail_list(filename)

        # Update the scroll region to encompass all content
        self.list_frameSrc.update_idletasks()
        self.canvasSrc.config(scrollregion=self.canvasSrc.bbox("all"))

    def create_dest_thumbnail(self):
        """
        Creates  thumbnail for the destination image file
        and displays it along with a radio button.

        """
        try:
            file_path_1 = os.path.join(self.destination_directory,
                                       CADRE_NAME_1)
            file_path_4 = os.path.join(self.destination_directory,
                                       CADRE_NAME_4)

            # Clear the canvas before adding a new image
            self.canvasDest.delete("all")

            with Image.open(file_path_1) as img:
                img.thumbnail((THUMBNAIL_H, THUMBNAIL_L))  # Thumbnail size
                thumbnail_img_1 = ImageTk.PhotoImage(img)

            with Image.open(file_path_4) as img:
                img.thumbnail((THUMBNAIL_H, THUMBNAIL_L))  # Thumbnail size
                thumbnail_img_4 = ImageTk.PhotoImage(img)

            if thumbnail_img_1 and thumbnail_img_4:
                # Display the image on the canvas
                img_id_1 = self.canvasDest.create_image((THUMBNAIL_H/2),
                                                        (THUMBNAIL_L/2),
                                                        image=thumbnail_img_1)
                # Display the image on the canvas
                img_id_4 = self.canvasDest.create_image((THUMBNAIL_H/2) +
                                                        THUMBNAIL_H + 20,
                                                        (THUMBNAIL_L/2),
                                                        image=thumbnail_img_4)
                # Keep a reference to prevent garbage collection
                # Keep a reference to prevent garbage collection
                self.canvasDest.image_1 = thumbnail_img_1
                self.canvasDest.image_4 = thumbnail_img_4

                # Bind click event to the image objects
                self.canvasDest.tag_bind(img_id_1,
                                         "<Button-1>",
                                         lambda e1:
                                         self.show_full_image(file_path_1))
                self.canvasDest.tag_bind(img_id_4,
                                         "<Button-1>",
                                         lambda e2:
                                         self.show_full_image(file_path_4))

        except Exception as e:
            print(f"Error processing file : {e}")

    def create_thumbnail_list(self, filename):
        """
        Creates a thumbnail for the specified image file
        and displays it along with a radio button.

        :param filename: The name of the image file.
        """
        try:
            file_path_1 = os.path.join(self.source_directory, filename)
            file_path_4 = os.path.join(self.source_directory,
                                       filename.replace('_1.png', '_4.png'))
            with Image.open(file_path_1) as img:
                img.thumbnail((THUMBNAIL_H, THUMBNAIL_L))  # Thumbnail size
                thumbnail_img_1 = ImageTk.PhotoImage(img)

            with Image.open(file_path_4) as img:
                img.thumbnail((THUMBNAIL_H, THUMBNAIL_L))  # Thumbnail size
                thumbnail_img_4 = ImageTk.PhotoImage(img)

            if thumbnail_img_1 and thumbnail_img_4:

                # Create a frame for each image and radio button
                item_frame = Frame(self.list_frameSrc)
                item_frame.pack(side="top", fill="x", pady=5)

                radio_button = Radiobutton(item_frame,
                                           variable=self.selected_image,
                                           value=filename)
                radio_button.pack(side="left", padx=5)

                thumbnail_label_1 = Label(item_frame, image=thumbnail_img_1)
                # Keep a reference to prevent garbage collection
                thumbnail_label_1.image = thumbnail_img_1
                thumbnail_label_4 = Label(item_frame, image=thumbnail_img_4)
                # Keep a reference to prevent garbage collection
                thumbnail_label_4.image = thumbnail_img_4

                # Bind click event to show full size image
                thumbnail_label_1.bind("<Button-1>",
                                       lambda e1,
                                       f=file_path_1: self.show_full_image(f))
                thumbnail_label_4.bind("<Button-1>",
                                       lambda e4,
                                       f=file_path_4: self.show_full_image(f))

                thumbnail_label_1.pack(side="left", padx=5)
                thumbnail_label_4.pack(side="left", padx=5)

                text_label = Label(item_frame,
                                   text=filename.replace('_1.png', ''))
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

            source_file_1 = os.path.join(self.source_directory, selected_file)
            dest_file_1 = os.path.join(self.destination_directory,
                                       CADRE_NAME_1)
            source_file_4 = os.path.join(self.source_directory,
                                         selected_file.replace('_1.png',
                                                               '_4.png'))
            dest_file_4 = os.path.join(self.destination_directory,
                                       CADRE_NAME_4)

            # Copier le fichier cadre
            print(f">>> Copy :{source_file_1}/{source_file_4}\n"
                  f"       to : {dest_file_1}/{dest_file_4}")
            copy(source_file_1, dest_file_1)
            copy(source_file_4, dest_file_4)

            # Copier le fichier template
            source_file_tpl = source_file_1.replace('_1.png',
                                                    '.xml')
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

            # rafraichie l'image dans dest
            self.create_dest_thumbnail()

        else:
            messagebox.showerror("Erreur",
                                 "Aucune image sélectionnée."
                                 " Veuillez choisir une image.")
            print("Aucune image sélectionnée.")

    def show_full_image(self, file_path, width=720, height=480):
        """
        Opens a new window to display the full-size image.
        """
        try:
            window = Toplevel(self.master)  # Create a Toplevel window
            window.title("Prévisualisation")
            # To ensure close action shuts the window
            # without affecting the main app
            window.protocol("WM_DELETE_WINDOW", window.destroy)

            with Image.open(file_path) as img:
                img_resized = img.resize((width, height), Image.ANTIALIAS)
                img_full = ImageTk.PhotoImage(img_resized)
                label = Label(window, image=img_full)
                label.image = img_full  # Keep a reference
                label.pack()
                window.resizable(False, False)

        except Exception as e:
            print(f"Error displaying full image: {e}")


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

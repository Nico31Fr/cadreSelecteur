# -*- coding: utf-8 -*-
""" sélecteur de cadre pour pibooth """

from os import path, listdir, remove
import tkinter as tk
from tkinter import Tk, Scrollbar, Canvas, Frame, Toplevel
from tkinter import messagebox, Label, Button, Radiobutton, StringVar
from PIL import Image, ImageTk
from PIL import UnidentifiedImageError
from PIL.ImageTk import PhotoImage
from shutil import copy
from platform import system
from pathlib import Path
import sys
import logging
from typing import cast

from . import __version__
from .CadreEditeur.imageeditorapp import ImageEditorApp
from .config_loader import (
    WINDOWS_SIZE,
    THUMBNAIL_H,
    THUMBNAIL_L,
    TEMPLATE_NAME,
    TEMPLATE_NAME_STD,
    CADRE_NAME_1,
    CADRE_NAME_4,
)
# Import du traducteur (API publique du package i18n)
from .i18n import t, set_language, get_language

logger = logging.getLogger(__name__)


def get_base_path() -> str:
    if getattr(sys, 'frozen', False):
        # Exécution depuis un .exe PyInstaller
        return path.dirname(sys.executable)
    else:
        # Exécution depuis le code source (PyCharm)
        return path.dirname(path.abspath(__file__))


def resource_path(relative_path: str) -> str:
    """
    Retourne le chemin correct vers les ressources, que l'app tourne en .py ou en .exe
    """
    # PyInstaller stocke le chemin temporaire dans l'attribut protégé _MEIPASS.
    # Utiliser getattr permet d'accéder de façon plus explicite et de fournir
    # une valeur par défaut None si l'attribut n'existe pas (mode script).
    meipass = getattr(sys, '_MEIPASS', None)
    if meipass:  # Exécutable PyInstaller
        return path.join(meipass, relative_path)
    return path.join(path.dirname(path.abspath(__file__)), relative_path)


BASE_PATH = get_base_path()
# repertoire avec tous les cadres / templates disponibles
template_path = Path(BASE_PATH) / "Templates"
# repertoire avec le cadre / template sélectionné
destination_path = Path(BASE_PATH) / "Cadres"
# repertoire avec les resources scripts
resources_path = Path(resource_path("resources"))


# configure un logger par défaut si aucune configuration n'est présente
if not logging.getLogger().hasHandlers():
    logging.basicConfig(level=logging.INFO)


class CadreSelecteur:
    """
    Sélecteur de cadres : affiche des vignettes d'images et permet
    de sélectionner un template via des boutons radio dans l'interface.
    """

    def __init__(self, start_mainloop: bool = True):
        """
        Initializes the TemplateSelector with a window
        and directory to display images.
        """

        self.apply_button = None
        self.quit_button = None
        self.add_new_border = None
        self.master = Tk()
        self.master.title(t('selector.title', version=__version__))
        self.source_directory = template_path
        self.destination_directory = destination_path
        # Set the window size
        self.master.geometry(WINDOWS_SIZE)

        # Barre supérieure : contient le sélecteur de langue aligné à droite
        self.top_bar = Frame(self.master)
        self.top_bar.pack(fill='x')

        # Frame principal pour les labels (sous la barre supérieure)
        self.top_frame = Frame(self.master)
        self.top_frame.pack(fill='x', pady=10)

        self.tk_editor = None

        # Font configuration
        label_font = ("Arial", 14, "bold")

        # Add text labels
        # Labels (stocker comme attributs pour pouvoir les rafraîchir)
        self.label1 = Label(self.top_frame,
                            text=t('selector.label.available_frames'),
                            font=label_font)
        self.label1.pack(side='left', padx=5)

        self.label2 = Label(self.top_frame,
                            text=t('selector.label.installed_frame'),
                            font=label_font)
        self.label2.pack(side='right', padx=5)

        # Create a frame with specific size
        self.frame_main = Frame(self.master, width=800, height=600)
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
        self.selected_image.set('')

        # Conserver des références PhotoImage pour éviter le GC
        self._image_refs = []

        # Pré-charger l'icône poubelle pour réutilisation (évite d'ouvrir le fichier à chaque vignette).
        try:
            icon_path_global = resources_path / "trash.png"
            # utiliser self.master explicitement (existe ici)
            with Image.open(icon_path_global) as _img:
                img = _img.resize((30, 30))
                self.trash_icon = ImageTk.PhotoImage(img.copy(), master=self.master)
                # Conserver la référence
                self._image_refs.append(self.trash_icon)
        except (FileNotFoundError, UnidentifiedImageError, OSError) as e:
            # Si l'icône est manquante ou invalide, on logge en debug et on continue
            logger.debug(f"Trash icon not available or invalid: {e}")
            self.trash_icon = None

        # List and generate image thumbnails
        self.list_files_and_generate_thumbnails()

        # Create action buttons
        self.create_action_buttons()

        # Sélecteur de langue déroulant (dans une barre tout en haut, aligné à droite)
        try:
            self.lang_btn = tk.Menubutton(self.top_bar, text=get_language(), relief='raised')
            self.lang_menu = tk.Menu(self.lang_btn, tearoff=0)
            self.lang_btn.config(menu=self.lang_menu)
            # placer à droite dans la barre supérieure
            self.lang_btn.pack(side='right', padx=4, pady=4)
            Label(self.top_bar, text=t('menu.language')).pack(side='right', padx=4, pady=4)
            # construire les entrées du menu en fonction des traductions
            self._build_lang_menu()
        except tk.TclError as e:
            # Problème d'interface tkinter (par ex. en environnement headless)
            logger.debug(f"GUI unavailable for language selector: {e}")
            self.lang_btn = None
            self.lang_menu = None
        except Exception as e:
            # Log toute autre erreur inattendue pour faciliter le diagnostic
            logger.exception("Unexpected error while creating language selector", exc_info=e)
            self.lang_btn = None
            self.lang_menu = None

        self.system = system()
        if self.system == 'Windows' or self.system == 'Darwin':
            # bind to canvas to keep binding local to widget
            self.canvasSrc.bind("<MouseWheel>", self._on_mousewheel)  # Windows et macOS
        else:  # Linux
            self.canvasSrc.bind("<Button-4>", self._on_mousewheel)
            self.canvasSrc.bind("<Button-5>", self._on_mousewheel)

        if start_mainloop:
            self.master.mainloop()

    def _on_mousewheel(self, event):
        if self.system == 'Windows':
            self.canvasSrc.yview_scroll(int(-1 * (event.delta / 120)), "units")
        elif self.system == 'Darwin':
            self.canvasSrc.yview_scroll(int(-1 * event.delta), "units")
        else:  # Linux
            if event.num == 4:
                self.canvasSrc.yview_scroll(-1, "units")
            elif event.num == 5:
                self.canvasSrc.yview_scroll(1, "units")

    def list_files_and_generate_thumbnails(self):
        """
        Parcourt le répertoire source et génère les vignettes pour les images.
        Met à jour la zone de défilement une fois les éléments ajoutés.
        """

        # Efface tous les widgets existants dans la frame
        for child in self.list_frameSrc.winfo_children():
            child.destroy()

        # Reset image references to avoid accumulation on repeated refresh
        # (we keep references only for current displayed widgets)
        self._image_refs.clear()

        self.create_dest_thumbnail()
        # protéger si le repertoire source est manquant
        if not path.exists(self.source_directory):
            messagebox.showerror(t('selector.msg.error.dir_missing_title'),
                                 t('selector.msg.error.dir_missing_message',
                                   path=self.source_directory))
            logger.error(f"Source directory not found: {self.source_directory}")
            return

        for filename in sorted(listdir(self.source_directory)):
            if filename.lower().endswith('_1.png'):
                self.create_src_thumbnail(filename)

        # Update the scroll region to encompass all content
        self.list_frameSrc.update_idletasks()
        self.canvasSrc.config(scrollregion=self.canvasSrc.bbox("all"))

    def create_dest_thumbnail(self):
        """
        Génère et affiche la vignette du cadre installé (destination).
        Affiche les deux images (cadre_1 et cadre_4) et lie le clic à la
        prévisualisation en plein écran.
        """
        try:
            file_path_1 = path.join(self.destination_directory,
                                    CADRE_NAME_1)
            file_path_4 = path.join(self.destination_directory,
                                    CADRE_NAME_4)

            # Clear the canvas before adding a new image
            self.canvasDest.delete("all")

            # vérifier la présence des fichiers avant d'ouvrir
            if not path.exists(file_path_1) or not path.exists(file_path_4):
                logger.debug(f"Destination images absentes: {file_path_1}, {file_path_4}")
                return

            with Image.open(file_path_1) as img:
                img.thumbnail((THUMBNAIL_H, THUMBNAIL_L))  # Thumbnail size
                thumbnail_img_1 = self._photoimage_from_pil(img)

            with Image.open(file_path_4) as img:
                img.thumbnail((THUMBNAIL_H, THUMBNAIL_L))  # Thumbnail size
                thumbnail_img_4 = self._photoimage_from_pil(img)

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
                # Conserver la référence pour éviter la collecte par le GC
                self.canvasDest.image_1 = thumbnail_img_1
                self.canvasDest.image_4 = thumbnail_img_4
                # Conserver aussi dans la liste globale (une seule fois)
                self._image_refs.extend([thumbnail_img_1, thumbnail_img_4])

                # Bind click event to the image objects
                # Lier le clic à la prévisualisation
                self.canvasDest.tag_bind(img_id_1, "<Button-1>", lambda e1: self.show_full_image(file_path_1))
                self.canvasDest.tag_bind(img_id_4, "<Button-1>", lambda e2: self.show_full_image(file_path_4))

        except (FileNotFoundError, UnidentifiedImageError, OSError, tk.TclError, RuntimeError) as e:
            # Erreurs d'I/O, PIL ou Tkinter lors du traitement des thumbnails
            logger.exception("Error processing destination thumbnails", exc_info=e)

    def create_src_thumbnail(self, filename):
        """
        Génère la vignette pour le fichier source `filename` et crée
        l'élément UI associé (radio, vignettes, étiquette et bouton supprimer).

        :param filename: nom du fichier image source.
        """
        try:
            file_path_1 = path.join(self.source_directory, filename)
            file_path_4 = path.join(self.source_directory,
                                    filename.replace('_1.png', '_4.png'))
            with Image.open(file_path_1) as img:
                img.thumbnail((THUMBNAIL_H, THUMBNAIL_L))  # Thumbnail size
                thumbnail_img_1 = self._photoimage_from_pil(img)

            with Image.open(file_path_4) as img:
                img.thumbnail((THUMBNAIL_H, THUMBNAIL_L))  # Thumbnail size
                thumbnail_img_4 = self._photoimage_from_pil(img)

            if thumbnail_img_1 and thumbnail_img_4:
                # Conserver les références pour éviter GC
                self._image_refs.extend([thumbnail_img_1, thumbnail_img_4])

                # Create a frame for each image and radio button
                item_frame = Frame(self.list_frameSrc)
                item_frame.pack(side="top", fill="x", pady=5)

                radio_button = Radiobutton(item_frame,
                                           variable=self.selected_image,
                                           value=filename)
                radio_button.pack(side="left", padx=5)

                # noinspection PyTypeChecker
                thumbnail_label_1 = Label(item_frame, image=thumbnail_img_1)
                # Conserver la référence pour éviter la collecte par le GC
                thumbnail_label_1.image = thumbnail_img_1
                # noinspection PyTypeChecker
                thumbnail_label_4 = Label(item_frame, image=thumbnail_img_4)
                # Conserver la référence pour éviter la collecte par le GC
                thumbnail_label_4.image = thumbnail_img_4

                # Bind click event to show full size image
                # Lier le clic à la prévisualisation
                thumbnail_label_1.bind("<Button-1>", lambda e1, f=file_path_1: self.show_full_image(f))
                thumbnail_label_4.bind("<Button-1>", lambda e4, f=file_path_4: self.show_full_image(f))

                # Utiliser l'icône poubelle préchargée si disponible
                icon_trash = None
                if self.trash_icon:
                    icon_trash = self.trash_icon
                else:
                    # Chargement de secours si la précharge à échouer
                    icon_path = resources_path / "trash.png"
                    try:
                        with Image.open(icon_path) as img_icon:
                            img2 = img_icon.resize((30, 30))
                            icon_trash = self._photoimage_from_pil(img2)
                    except (FileNotFoundError, UnidentifiedImageError, OSError) as e:
                        logger.debug(f"fallback trash icon failed: {e}")
                        icon_trash = None

                # GARDER LA RÉFÉRENCE à l'image (sinon l'image disparaît !)
                item_frame.icon_trash = icon_trash
                # Conserver la référence si présente
                if icon_trash:
                    self._image_refs.append(icon_trash)

                # Créer le bouton avec l'image
                if icon_trash:
                    bouton_supprimer = Button(item_frame,
                                              command=lambda f=filename: self.del_border(f),
                                              image=cast(tk.PhotoImage, icon_trash))
                else:
                    bouton_supprimer = Button(item_frame,
                                              command=lambda f=filename: self.del_border(f),
                                              text=t('image.button.delete'))

                bouton_supprimer.pack(side='right', padx=20, pady=20)

                thumbnail_label_1.pack(side='left', padx=5)
                thumbnail_label_4.pack(side='left', padx=5)

                text_label = Label(item_frame, text=filename.replace('_1.png', ''))
                text_label.pack(side='left', padx=5)

        except (FileNotFoundError, UnidentifiedImageError, OSError, tk.TclError, RuntimeError) as e:
            logger.exception(f"Error processing file {filename}", exc_info=e)

    def create_action_buttons(self):
        """
        Crée les boutons d'action (nouveau cadre, Appliquer, Quitter).
        """
        button_frame = Frame(self.master)
        button_frame.pack(side="bottom", fill="x", pady=10)

        self.add_new_border = Button(button_frame,
                                     text=t('selector.button.new_frame'),
                                     command=self.new_border)
        self.add_new_border.pack(side='left', padx=10)
        self.quit_button = Button(button_frame,
                                  text=t('selector.button.quit'),
                                  command=self.master.quit)
        self.quit_button.pack(side="right", padx=10)

        self.apply_button = Button(button_frame,
                                   text=t('selector.button.apply'),
                                   command=self.apply_selection)
        self.apply_button.pack(side="right", padx=10)

        # expose references for refresh
        return

    def refresh_ui_texts(self):
        """Met à jour les textes affichés selon la langue courante."""
        try:
            # fenêtre principale
            self.master.title(t('selector.title', version=__version__))
            # labels
            self.label1.config(text=t('selector.label.available_frames'))
            self.label2.config(text=t('selector.label.installed_frame'))
            # boutons
            self.add_new_border.config(text=t('selector.button.new_frame'))
            self.apply_button.config(text=t('selector.button.apply'))
            self.quit_button.config(text=t('selector.button.quit'))
            # menu langue
            if hasattr(self, 'lang_btn'):
                self.lang_btn.config(text=get_language())
                # reconstruire les entrées du menu pour prendre en compte la nouvelle langue
                try:
                    self._build_lang_menu()
                except (AttributeError, tk.TclError, RuntimeError) as e:
                    # erreurs possibles lors de la reconstruction du menu (widgets absents, Tk indisponible)
                    logger.exception("Error rebuilding language menu after language change", exc_info=e)
        except (AttributeError, tk.TclError, RuntimeError) as e:
            # erreurs attendues lorsque des widgets n'existent pas encore
            # (p.ex. refresh called early or in headless env). On loggue
            # pour debug mais on ne propage pas l'exception afin de
            # ne pas planter l'application.
            logger.exception("Error refreshing UI texts", exc_info=e)

    def change_language(self, lang_code: str):
        """Change la langue via le traducteur et rafraîchit l'IHM."""
        if set_language(lang_code):
            # met à jour les textes de l'UI
            self.refresh_ui_texts()
        else:
            messagebox.showwarning("i18n", f"Could not load language: {lang_code}")

    def _build_lang_menu(self):
        """(Re)construit le menu déroulant de sélection de langue avec les labels traduits."""
        if not hasattr(self, 'lang_menu'):
            return
        # supprimer les entrées existantes
        try:
            self.lang_menu.delete(0, 'end')
        except tk.TclError as e:
            # suppression impossible si le widget n'existe plus ou si Tk est indisponible
            logger.debug(f"Could not clear language menu: {e}")
        except Exception as e:
            logger.exception("Unexpected error when clearing language menu", exc_info=e)
        # ajouter les entrées en utilisant les traductions
        try:
            # Récupère les libellés traduits via `t()` ; si la clé n'existe pas,
            # `t()` retourne la clé. On fait un fallback lisible dans ce cas.
            label_fr = 'fr'
            label_en = 'en'

        except Exception as e:
            logger.exception("Error fetching translated labels", exc_info=e)
            label_fr = 'fr'
            label_en = 'en'

        self.lang_menu.add_command(label=label_fr, command=lambda: self.change_language('fr'))
        self.lang_menu.add_command(label=label_en, command=lambda: self.change_language('en'))

    def apply_selection(self):
        """
        Applique le cadre sélectionné : copie les fichiers _1 et _4 ainsi que
        le template associé dans le dossier de destination et rafraîchit l'affichage.
        """
        selected_file = self.selected_image.get()
        if selected_file:
            logger.info(f"Image sélectionnée: {selected_file}")

            source_file_1 = path.join(self.source_directory, selected_file)
            dest_file_1 = path.join(self.destination_directory,
                                    CADRE_NAME_1)
            source_file_4 = path.join(self.source_directory,
                                      selected_file.replace('_1.png',
                                                            '_4.png'))
            dest_file_4 = path.join(self.destination_directory,
                                    CADRE_NAME_4)

            # Copier le fichier cadre
            logger.info(f">>> Copy :{source_file_1}/{source_file_4}\n"
                        f"       to : {dest_file_1}/{dest_file_4}")
            try:
                copy(source_file_1, dest_file_1)
                copy(source_file_4, dest_file_4)
            except OSError as e:
                logger.exception("Erreur lors de la copie des fichiers cadres", exc_info=e)
                messagebox.showerror(t('selector.msg.error.copy'), f"Impossible de copier les fichiers du cadre: {e}")
                return

            # Copier le fichier template
            source_file_tpl = source_file_1.replace('_1.png',
                                                    '.xml')
            dest_file_tpl = path.join(self.destination_directory,
                                      TEMPLATE_NAME)

            try:
                if path.exists(source_file_tpl):
                    logger.info(f">>> Copy :{source_file_tpl}\n"
                                f"       to : {dest_file_tpl}")
                    copy(source_file_tpl, dest_file_tpl)
                else:
                    source_file_tpl = path.join(self.source_directory,
                                                TEMPLATE_NAME_STD)
                    dest_file_tpl = path.join(self.destination_directory,
                                              TEMPLATE_NAME)
                    logger.info('pas de fichier frame associé au cadre,'
                                ' copy du template standard')
                    logger.info(f">>> Copy :{source_file_tpl}\n"
                                f"       to : {dest_file_tpl}")
                    copy(source_file_tpl, dest_file_tpl)
            except OSError as e:
                logger.exception("Erreur lors de la copie du template", exc_info=e)
                messagebox.showerror(t('selector.msg.error.copy_template'),
                                     f"Impossible de copier le template: {e}")
                return

            # rafraichie l'image dans dest
            self.create_dest_thumbnail()

        else:
            messagebox.showerror(t('selector.msg.error.no_selection_title'),
                                 t('selector.msg.error.no_selection_message'))
            logger.warning("Aucune image sélectionnée.")

    def show_full_image(self, file_path, width=720, height=480):
        """
        Ouvre une fenêtre de prévisualisation affichant l'image en taille
        complète (redimensionnée aux dimensions fournies).
        """
        try:
            window = Toplevel(self.master)  # Create a Toplevel window
            window.title(t('selector.preview.title'))
            # To ensure close action shuts the window
            # without affecting the main app
            window.protocol("WM_DELETE_WINDOW", window.destroy)

            with Image.open(file_path) as img:
                img_resized = img.resize((width, height))
                img_full: PhotoImage = ImageTk.PhotoImage(img_resized, master=window)
                # noinspection PyTypeChecker
                label = Label(window, image=img_full)
                # Conserver la référence attachée à la fenêtre de prévisualisation
                label.image = img_full
                label.pack()
                window.resizable(False, False)

        except (FileNotFoundError, UnidentifiedImageError, OSError, tk.TclError, RuntimeError) as e:
            # Erreurs d'I/O, PIL ou Tkinter lors de la prévisualisation
            logger.exception("Error displaying full image", exc_info=e)

    def new_border(self):
        """
        Lance l'éditeur de cadres (ouvre la fenêtre d'édition) et
        minimise la fenêtre principale pendant l'édition.
        """
        self.master.iconify()

        self.tk_editor = Toplevel(self.master)

        # Lier la fonction on_closing à l'événement de fermeture de la fenêtre
        self.tk_editor.protocol("WM_DELETE_WINDOW", self.on_closing)

        ImageEditorApp(self.tk_editor,
                       template=template_path,
                       destination=destination_path,
                       standalone=False)

    def on_closing(self):
        """
        Fermeture de l'éditeur : détruit la fenêtre d'édition, restaure la
        fenêtre principale et rafraîchit la liste des vignettes.
        """
        self.tk_editor.destroy()
        self.master.deiconify()
        # List and generate image thumbnails
        self.list_files_and_generate_thumbnails()

    def del_border(self, filename):
        """
        Supprime le cadre (fichiers _1.png, _4.png, .xml) du dossier Templates.
        Refuse la suppression si c'est le dernier cadre disponible et
        affiche un message de confirmation avant suppression.
        Rafraîchir ensuite la liste.
        """

        file_1 = path.join(self.source_directory, filename)
        file_4 = path.join(
            self.source_directory,
            filename.replace('_1.png', '_4.png')
        )
        file_xml = path.join(
            self.source_directory,
            filename.replace('_1.png', '.xml')
        )

        files_to_remove = [file_1, file_4, file_xml]
        errors = []

        # Compte le nombre de cadres disponibles
        nb_cadres = len([f for f in listdir(self.source_directory)
                         if f.lower().endswith('_1.png')])
        if nb_cadres <= 1:
            messagebox.showwarning(
                t('selector.msg.warn.delete_impossible_title'),
                t('selector.msg.warn.delete_impossible_message')
            )
            return

        # Confirmation suppression
        if not messagebox.askyesno(
                t('selector.msg.confirm.delete_title'),
                t('selector.msg.confirm.delete_message', name=filename.replace('_1.png', ''))
        ):
            return  # abandon si non

        for file in files_to_remove:
            if path.exists(file):
                try:
                    remove(file)
                except OSError as e:
                    errors.append(str(e))

        if errors:
            messagebox.showerror(t('selector.msg.error.delete'),
                                 f"Erreur lors de la suppression:\n"
                                 f"{errors}")
        else:
            messagebox.showinfo(t('selector.msg.info.deleted_title'), t('selector.msg.info.deleted_message'))

        # Rafraîchir la liste
        self.list_files_and_generate_thumbnails()

    def _photoimage_from_pil(self, pil_image):
        """
        Crée et retourne un ImageTk.PhotoImage à partir d'une image PIL.
        Fait une copie et attache l'image au master de l'instance pour
        éviter des erreurs Tkinter et la collecte par le garbage collector.
        """
        try:
            return ImageTk.PhotoImage(pil_image.copy(), master=getattr(self, 'master', None))
        except (RuntimeError, tk.TclError) as e:
            # Environnements headless ou erreur Tkinter : retenter sans master
            logger.debug(f"PhotoImage with master failed: {e}; retrying without master")
            try:
                return ImageTk.PhotoImage(pil_image.copy())
            except tk.TclError as e2:
                # Errors from Tk internals when running headless or no display.
                logger.exception("Failed to create PhotoImage (even without master)", exc_info=e2)
                return None


def check_mandatory_path():
    """
    Vérifie la présence des répertoires indispensable au bon fonctionnement.
    """
    # verification de la presence des répertoire sources et dest.
    message_error = ''
    if not path.exists(template_path):
        message_error = message_error + (
            f"SOURCES :\nle repertoire : {str(template_path)} n'est pas accessible\n\n"
        )

    if not path.exists(destination_path):
        message_error = message_error + (
            f"DESTINATION:\nle repertoire : {str(destination_path)} n'est pas accessible\n\n"
        )

    # verification de la presence du template par default.
    template_dft_file = path.join(template_path,
                                  TEMPLATE_NAME_STD)
    if not path.exists(template_dft_file):
        message_error = message_error + (
            f"TEMPLATE:\nle fichier : {str(template_dft_file)} n'est pas accessible\n\n"
        )

    if message_error != '':
        messagebox.showerror(title=t('selector.msg.error.no_selection_title'), message=message_error)
        quit()


if __name__ == "__main__":

    # Vérifie les path
    check_mandatory_path()

    # start IHM
    app = CadreSelecteur()

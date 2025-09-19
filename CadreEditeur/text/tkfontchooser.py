# -*- coding: utf-8 -*-
""" Module gestion de la fenêtre de selection des polices d'écritures """

from tkinter import Toplevel, Listbox, StringVar, TclError, messagebox
from tkinter.ttk import Frame, Label, Button, Scrollbar, Style, Entry
from tkinter.font import families, Font
from typing import Any, Optional, Dict


class FontChooser(Toplevel):
    """Boîte de dialogue pour choisir une police : famille et taille uniquement, en français."""
    def __init__(self, master, font_dict=None, text="Abcd", title="Choisir une police", **kwargs):
        """
        Crée une boîte de dialogue pour choisir une police.

        Arguments :
            master : Fenêtre parente Tk ou Toplevel
            font_dict : dictionnaire contenant les options de police initiales (famille, taille)
            text : texte affiché dans l'aperçu
            title : titre de la fenêtre
            kwargs : paramètres supplémentaires pour Toplevel
        """
        Toplevel.__init__(self, master, **kwargs)
        if font_dict is None:
            font_dict = {}
        self.title(title)
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self.quit)
        self._validate_family = self.register(self.validate_font_family)
        self._validate_size = self.register(self.validate_font_size)

        # --- Variable stockant la police choisie
        self.res: Optional[Dict[str, Any]] = {}

        style = Style(self)
        style.configure("prev.TLabel", background="white")
        bg = style.lookup("TLabel", "background")
        self.configure(bg=bg)

        # --- Liste des familles disponibles
        self.fonts = list(set(families()))
        self.fonts.append("TkDefaultFont")
        self.fonts.sort()
        for i in range(len(self.fonts)):
            self.fonts[i] = self.fonts[i].replace(" ", r"\ ")
        max_length = int(2.5 * max([len(font) for font in self.fonts])) // 3

        # --- Tailles de police disponibles
        self.sizes = ["%i" % i for i in (list(range(6, 17)) + list(range(18, 82, 2)))]

        # --- Valeurs par défaut
        font_dict["family"] = font_dict.get("family", self.fonts[0].replace(r'\ ', ' '))
        font_dict["size"] = font_dict.get("size", 10)

        # --- Création des widgets
        self.font_family = StringVar(self, " ".join(self.fonts))
        self.font_size = StringVar(self, " ".join(self.sizes))
        self.var_size = StringVar(self)
        self.entry_family = Entry(self, width=max_length, validate="key",
                                  validatecommand=(self._validate_family, "%d", "%S", "%i", "%s", "%V"))
        self.entry_size = Entry(self, width=4, validate="key",
                                textvariable=self.var_size,
                                validatecommand=(self._validate_size, "%d", "%P", "%V"))
        self.list_family = Listbox(self, selectmode="browse",
                                   listvariable=self.font_family,
                                   highlightthickness=0,
                                   exportselection=False,
                                   width=max_length)
        self.list_size = Listbox(self, selectmode="browse",
                                 listvariable=self.font_size,
                                 highlightthickness=0,
                                 exportselection=False,
                                 width=4)
        scroll_family = Scrollbar(self, orient='vertical', command=self.list_family.yview)
        scroll_size = Scrollbar(self, orient='vertical', command=self.list_size.yview)
        self.preview_font = Font(self, **font_dict)
        if len(text) > 30:
            text = text[:30]
        self.preview = Label(self, relief="groove", style="prev.TLabel",
                             text=text, font=self.preview_font,
                             anchor="center")

        # --- Configuration des widgets
        self.list_family.configure(yscrollcommand=scroll_family.set)
        self.list_size.configure(yscrollcommand=scroll_size.set)

        self.entry_family.insert(0, font_dict["family"])
        self.entry_family.selection_clear()
        self.entry_family.icursor("end")
        self.entry_size.insert(0, font_dict["size"])

        try:
            i = self.fonts.index(self.entry_family.get().replace(" ", r"\ "))
        except ValueError:
            i = 0
        self.list_family.selection_clear(0, "end")
        self.list_family.selection_set(i)
        self.list_family.see(i)
        try:
            i = self.sizes.index(self.entry_size.get())
            self.list_size.selection_clear(0, "end")
            self.list_size.selection_set(i)
            self.list_size.see(i)
        except ValueError:
            pass

        self.entry_family.grid(row=0, column=0, sticky="ew",
                               pady=(10, 1), padx=(10, 0))
        self.entry_size.grid(row=0, column=2, sticky="ew",
                             pady=(10, 1), padx=(10, 0))
        self.list_family.grid(row=1, column=0, sticky="nsew",
                              pady=(1, 10), padx=(10, 0))
        self.list_size.grid(row=1, column=2, sticky="nsew",
                            pady=(1, 10), padx=(10, 0))
        scroll_family.grid(row=1, column=1, sticky='ns', pady=(1, 10))
        scroll_size.grid(row=1, column=3, sticky='ns', pady=(1, 10))

        self.preview.grid(row=2, column=0, columnspan=5, sticky="eswn",
                          padx=10, pady=(0, 10), ipadx=4, ipady=4)

        button_frame = Frame(self)
        button_frame.grid(row=3, column=0, columnspan=5, pady=(0, 10), padx=10)

        Button(button_frame, text="Ok",
               command=self.ok).grid(row=0, column=0, padx=4, sticky='ew')
        Button(button_frame, text='Annuler',
               command=self.quit).grid(row=0, column=1, padx=4, sticky='ew')

        # --- Liaisons des événements
        self.list_family.bind('<<ListboxSelect>>', self.update_entry_family)
        self.list_size.bind('<<ListboxSelect>>', self.update_entry_size, add=True)
        self.list_family.bind("<KeyPress>", self.keypress)
        self.entry_family.bind("<Return>", self.change_font_family)
        self.entry_family.bind("<Tab>", self.tab)
        self.entry_size.bind("<Return>", self.change_font_size)
        self.entry_family.bind("<Down>", self.down_family)
        self.entry_size.bind("<Down>", self.down_size)
        self.entry_family.bind("<Up>", self.up_family)
        self.entry_size.bind("<Up>", self.up_size)

        self.bind_class("TEntry", "<Control-a>", self.select_all)

        self.wait_visibility(self)
        self.grab_set()
        self.entry_family.focus_set()
        self.lift()

    @staticmethod
    def select_all(event):
        """Sélectionne tout le contenu du champ."""
        event.widget.selection_range(0, "end")

    def keypress(self, event):
        """Sélectionne la première police commençant par la lettre frappée."""
        key = event.char.lower()
        lst = [i for i in self.fonts if i[0].lower() == key]
        if lst:
            i = self.fonts.index(lst[0])
            self.list_family.selection_clear(0, "end")
            self.list_family.selection_set(i)
            self.list_family.see(i)
            self.update_entry_family()

    def up_family(self, _event):
        """Navigation vers le haut dans la liste des familles."""
        try:
            i = self.list_family.curselection()[0]
            self.list_family.selection_clear(0, "end")
            if i <= 0:
                i = len(self.fonts)
            self.list_family.see(i - 1)
            self.list_family.select_set(i - 1)
        except TclError:
            self.list_family.selection_clear(0, "end")
            i = len(self.fonts)
            self.list_family.see(i - 1)
            self.list_family.select_set(i - 1)
        self.list_family.event_generate('<<ListboxSelect>>')

    def up_size(self, _event):
        """Navigation vers le haut dans la liste des tailles."""
        try:
            s = self.var_size.get()
            if s in self.sizes:
                i = self.sizes.index(s)
            elif s:
                sizes = list(self.sizes)
                sizes.append(s)
                sizes.sort(key=lambda x: int(x))
                i = sizes.index(s)
            else:
                i = 0
            self.list_size.selection_clear(0, "end")
            if i <= 0:
                i = len(self.sizes)
            self.list_size.see(i - 1)
            self.list_size.select_set(i - 1)
        except TclError:
            i = len(self.sizes)
            self.list_size.see(i - 1)
            self.list_size.select_set(i - 1)
        self.list_size.event_generate('<<ListboxSelect>>')

    def down_family(self, _event):
        """Navigation vers le bas dans la liste des familles."""
        try:
            i = self.list_family.curselection()[0]
            self.list_family.selection_clear(0, "end")
            if i >= len(self.fonts):
                i = -1
            self.list_family.see(i + 1)
            self.list_family.select_set(i + 1)
        except TclError:
            self.list_family.selection_clear(0, "end")
            self.list_family.see(0)
            self.list_family.select_set(0)
        self.list_family.event_generate('<<ListboxSelect>>')

    def down_size(self, _event):
        """Navigation vers le bas dans la liste des tailles."""
        try:
            s = self.var_size.get()
            if s in self.sizes:
                i = self.sizes.index(s)
            else:
                sizes = list(self.sizes)
                sizes.append(s)
                sizes.sort(key=lambda x: int(x))
                i = sizes.index(s) - 1
            self.list_size.selection_clear(0, "end")
            if i < len(self.sizes) - 1:
                self.list_size.selection_set(i + 1)
                self.list_size.see(i + 1)
            else:
                self.list_size.see(0)
                self.list_size.select_set(0)
        except TclError:
            self.list_size.selection_set(0)
        self.list_size.event_generate('<<ListboxSelect>>')

    def change_font_family(self, _event=None):
        """Met à jour l'aperçu lors du changement de famille."""
        family = self.entry_family.get()
        if family.replace(" ", r"\ ") in self.fonts:
            self.preview_font.configure(family=family)

    def change_font_size(self, _event=None):
        """Met à jour l'aperçu lors du changement de taille."""
        try:
            size_str = self.var_size.get()
            size = int(size_str)
            if size < 1 or size > 300:
                raise ValueError
            self.preview_font.configure(size=size)
        except ValueError:
            self.var_size.set(str(self.preview_font.cget("size")))
            messagebox.showwarning("Taille incorrecte")

    def validate_font_size(self, d, ch, v):
        """Valide et complète la taille de police saisie."""
        l_ = [i for i in self.sizes if i[:len(ch)] == ch]
        i = None
        if l_:
            i = self.sizes.index(l_[0])
        elif ch.isdigit():
            sizes = list(self.sizes)
            sizes.append(ch)
            sizes.sort(key=lambda x: int(x))
            i = min(sizes.index(ch), len(self.sizes))
        if i is not None:
            self.list_size.selection_clear(0, "end")
            self.list_size.selection_set(i)
            deb = self.list_size.nearest(0)
            fin = self.list_size.nearest(self.list_size.winfo_height())
            if v != "forced":
                if i < deb or i > fin:
                    self.list_size.see(i)
                return True
        if d == '1':
            return ch.isdigit()
        else:
            return True

    def tab(self, event):
        """Place le curseur à la fin du champ lors de la touche Tab."""
        self.entry_family = event.widget
        self.entry_family.selection_clear()
        self.entry_family.icursor("end")
        return "break"

    def validate_font_family(self, action, modif, pos, prev_txt, v):
        """Complète ou valide le nom de police saisi."""
        if self.entry_family.selection_present():
            sel = self.entry_family.selection_get()
            txt = prev_txt.replace(sel, '')
        else:
            txt = prev_txt
        if action == "0":
            return True
        else:
            txt = txt[:int(pos)] + modif + txt[int(pos):]
            ch = txt.replace(" ", r"\ ")
            list_font = [i for i in self.fonts if i[:len(ch)] == ch]
            if list_font:
                i = self.fonts.index(list_font[0])
                self.list_family.selection_clear(0, "end")
                self.list_family.selection_set(i)
                deb = self.list_family.nearest(0)
                fin = self.list_family.nearest(self.list_family.winfo_height())
                index = self.entry_family.index("insert")
                self.entry_family.delete(0, "end")
                self.entry_family.insert(0, list_font[0].replace(r"\ ", " "))
                self.entry_family.selection_range(index + 1, "end")
                self.entry_family.icursor(index + 1)
                if v != "forced":
                    if i < deb or i > fin:
                        self.list_family.see(i)
                return True
            else:
                return False

    def update_entry_family(self, _event=None):
        """Met à jour le champ famille depuis la liste."""
        family = self.list_family.get(self.list_family.curselection()[0])
        self.entry_family.delete(0, "end")
        self.entry_family.insert(0, family)
        self.entry_family.selection_clear()
        self.entry_family.icursor("end")
        self.change_font_family()

    def update_entry_size(self, _event):
        """Met à jour le champ taille depuis la liste."""
        size = self.list_size.get(self.list_size.curselection()[0])
        self.var_size.set(size)
        self.change_font_size()

    def ok(self):
        """Valide le choix et ferme la boîte de dialogue."""
        self.res = self.preview_font.actual()
        # On ne garde que la famille et la taille
        self.res = {
            "family": self.res["family"],
            "size": self.res["size"]
        }
        self.quit()

    def get_res(self) -> Optional[Dict[str, int]]:
        """Retourne la police sélectionnée sous forme de dictionnaire."""
        return self.res

    def quit(self):
        """Ferme la fenêtre."""
        self.destroy()


def ask_font(master: Any = None,
             text: str = "Abcd",
             title: str = "Choisir une police",
             **font_args: Any) -> Optional[Dict[str, int]]:
    """
    Ouvre la boîte de dialogue de sélection de police (famille et taille).
    Retourne le résultat sous forme de dictionnaire.

    Arguments :
        master : fenêtre parente (optionnel)
        text : texte d’aperçu
        title : titre de la boîte de dialogue
        font_args : paramètres initiaux (family, size…)

    Retour :
        Dictionnaire {'family' : str, 'size' : int}
    """
    chooser = FontChooser(master, font_args, text, title)
    chooser.wait_window(chooser)
    return chooser.get_res()


if __name__ == "__main__":
    from tkinter import Tk

    root = Tk()

    label = Label(root, text='Police choisie :')
    label.pack(padx=10, pady=(10, 4))

    def callback():
        """ callback du bouton Sélecteur police"""
        font = ask_font(root, title="Choisir une police")
        if font:
            # espaces dans family à échapper
            font_name = font['family']
            font_name = str(font_name).replace(' ', r'\ ')
            font_str = f"{font_name} {font['size']}"
            label.configure(font=font_str,
                            text='Police choisie : ' + font_str.replace(r'\ ', ' '))

    Button(root, text='Sélecteur de police',
           command=callback).pack(padx=10, pady=(4, 10))
    root.mainloop()
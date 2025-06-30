import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageDraw, ImageFont, ImageTk


class ImageEditorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Éditeur d'image")

        self.canvas = tk.Canvas(root, width=800, height=600)
        self.canvas.pack()

        # Fond blanc
        self.image = Image.new('RGBA', (3600, 2400), (255, 255, 255, 255))
        self.draw = ImageDraw.Draw(self.image)
        self.tk_image = ImageTk.PhotoImage(self.image)
        self.canvas_image_id = self.canvas.create_image(0, 0, anchor=tk.NW, image=self.tk_image)

        self.text = tk.StringVar()
        tk.Entry(root, textvariable=self.text).pack()

        tk.Button(root, text="Importer une image", command=self.import_image).pack()
        tk.Button(root, text="Ajouter un texte", command=self.add_text).pack()
        tk.Button(root, text="Enregistrer l'image", command=self.save_image).pack()

        self.imported_image = None
        self.imported_image_path = None

        # Variables pour déplacer l'image importée
        self.image_position = (150, 150)
        self.image_size = [100, 100]

        # Définir quelques zones d'exclusion
        self.exclusion_zones = [
            (50, 50, 100, 100),  # Format: (x, y, width, height)
            (250, 200, 100, 50)  # Exemple de deuxième zone
        ]

        # Événements de souris pour déplacer/redimensionner
        self.canvas.bind("<B1-Motion>", self.move_image)
        self.canvas.bind("<MouseWheel>", self.resize_image)

    def import_image(self):
        self.imported_image_path = filedialog.askopenfilename()
        if self.imported_image_path:
            self.imported_image = Image.open(self.imported_image_path).convert('RGBA')
            self.imported_image = self.imported_image.resize(self.image_size)
            self.update_canvas()

    def add_text(self):
        self.draw.text((200, 150), self.text.get(), fill=(0, 0, 0, 255), font=ImageFont.load_default())
        self.update_canvas()

    def move_image(self, event):
        self.image_position = (event.x, event.y)
        self.update_canvas()

    def resize_image(self, event):
        delta = 10 if event.delta > 0 else -10
        new_width = max(10, self.image_size[0] + delta)
        new_height = max(10, self.image_size[1] + delta)
        self.image_size = [new_width, new_height]
        if self.imported_image_path:
            self.imported_image = Image.open(self.imported_image_path).convert('RGBA').resize(self.image_size)
        self.update_canvas()

    def update_canvas(self):
        temp_image = self.image.copy()

        # Coller l'image importée en assurant le masquage correct
        if self.imported_image:
            resized_image = self.imported_image.resize(self.image_size)
        #    mask = resized_image.split()[3]  # Utilisation du canal alpha
        #    mask = mask.resize(resized_image.size)  # Garantie que le masque a la bonne taille
            temp_image.paste(resized_image, self.image_position,)

        # Appliquer les zones d'exclusion : les rendre transparentes
        for zone in self.exclusion_zones:
            x, y, w, h = zone
            draw = ImageDraw.Draw(temp_image)
            draw.rectangle([x, y, x + w, y + h], fill=(255, 255, 255, 0))

        self.tk_image = ImageTk.PhotoImage(temp_image)
        self.canvas.itemconfig(self.canvas_image_id, image=self.tk_image)

    def save_image(self):
        file_path = (filedialog.asksaveasfilename(defaultextension=".png",
                                                 filetypes=[("PNG files", "*.png"), ("JPEG files", "*.jpg")]))
        if file_path:
            self.image.save(file_path)


if __name__ == "__main__":
    root = tk.Tk()
    app = ImageEditorApp(root)
    root.mainloop()
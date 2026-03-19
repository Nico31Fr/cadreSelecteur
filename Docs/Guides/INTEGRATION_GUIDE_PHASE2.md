# 📋 Guide d'Intégration: Refactorer ImageEditorApp (Phase 2)

## 🎯 Objectif

Refactorer `ImageEditorApp` pour utiliser `EditorModel` au lieu de stocker la logique métier dans la GUI.

## 🔍 Changements Requis

### 1. Initialisation

**Avant:**
```python
class ImageEditorApp:
    def __init__(self, root, template="../Templates/", destination='../Cadres/', ...):
        self.tk_root = root
        self.template = template
        self.destination = destination
        self.layers = []              # ← LOGIQUE MÉTIER DANS GUI!
        self.active_layer_idx = 0
        self.prj_name_var = tk.StringVar()      # ← Variable Tkinter
        self.selected_template = tk.StringVar()  # ← Variable Tkinter
```

**Après:**
```python
class ImageEditorApp:
    def __init__(self, root, template="../Templates/", destination='../Cadres/', ...):
        # ✅ CRÉER le modèle métier
        self.model = EditorModel(
            template_dir=template,
            destination_dir=destination,
            canvas_width=600,
            canvas_height=400,
            image_width=1800,
            image_height=1200,
        )
        
        # ✅ GUI - Variables pour la synchronisation VIEW ONLY
        self.tk_root = root
        self.prj_name_var = tk.StringVar()      # Pour Entry widget
        self.selected_template_var = tk.StringVar()  # Pour DropDown
        
        # ✅ Cache pour l'affichage canvas
        self._display_cache = None
```

### 2. Callbacks Tkinter → Modèle

**Pattern générique:**
```python
def on_user_action(self, *args):
    """Callback depuis Tkinter"""
    try:
        # 1. Récupérer input Tkinter
        user_input = self.user_input_var.get()
        
        # 2. Appeler modèle (logique métier)
        self.model.some_operation(user_input)
        
        # 3. Rafraîchir affichage
        self._refresh_display()
        
    except ValidationError as e:
        messagebox.showerror("Erreur Validation", str(e))
    except FileOperationError as e:
        messagebox.showerror("Erreur Fichier", str(e))
    except Exception as e:
        handle_exception(e, operation="on_user_action")
```

### 3. Gestion Calques

**Avant:**
```python
def add_image_layer(self):
    """Ajoute un calque image (logique métier + GUI)"""
    file_path = filedialog.askopenfilename()
    if file_path:
        layer = LayerImage(self.app1, file_path, ...)
        self.app1.layers.append(layer)
        self.app1.active_layer_idx = len(self.app1.layers) - 1
        self.refresh_layer_list()
```

**Après:**
```python
def add_image_layer(self):
    """Ajoute un calque image"""
    try:
        # 1. GUI - Sélectionner fichier
        file_path = filedialog.askopenfilename()
        if not file_path:
            return
        
        # 2. MÉTIER - Ajouter au modèle
        layer_data = {
            "type": "image",
            "path": file_path,
            "position": (0, 0),
            "size": (100, 100),
        }
        idx = self.model.add_layer(layer_data, layout="1")
        
        # 3. GUI - Rafraîchir
        self._refresh_layer_list()
        self._refresh_canvas()
        
    except ValidationError as e:
        messagebox.showerror("Erreur", str(e))
    except FileOperationError as e:
        messagebox.showerror("Erreur", str(e))
```

### 4. Sauvegarder Projet

**Avant:**
```python
def save_project(self):
    """Sauvegarde (logique métier + GUI)"""
    file_path = filedialog.asksaveasfilename(defaultextension=".json")
    if file_path:
        project_data = {
            "app1": {
                "layers": [layer.to_dict() for layer in self.app1.layers],
                "background_color": self.app1.background_couleur,
            },
            "app4": {
                "layers": [layer.to_dict() for layer in self.app4.layers],
                "background_color": self.app4.background_couleur,
            },
        }
        with open(file_path, 'w') as f:
            json.dump(project_data, f)
```

**Après:**
```python
def save_project(self):
    """Sauvegarde projet"""
    try:
        # 1. GUI - Demander fichier
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")]
        )
        if not file_path:
            return
        
        # 2. MÉTIER - Sauvegarder
        self.model.save_project(file_path)
        
        # 3. GUI - Feedback
        messagebox.showinfo(
            _t('editor.msg.info.export_ok_title'),
            _t('editor.msg.info.export_ok_message')
        )
        
    except FileOperationError as e:
        messagebox.showerror("Erreur Sauvegarde", str(e))
    except Exception as e:
        handle_exception(e, operation="save_project")
```

### 5. Charger Projet

**Avant:**
```python
def load_project(self):
    file_path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
    if file_path:
        with open(file_path) as f:
            project_data = json.load(f)
        
        # Recréer layers manuellement...
        self.app1.layers = []
        for layer_dict in project_data["app1"]["layers"]:
            if layer_dict["type"] == "image":
                layer = LayerImage.from_dict(layer_dict, self.app1, ...)
                self.app1.layers.append(layer)
        # ... 30 lignes de logique ...
```

**Après:**
```python
def load_project(self):
    """Charge un projet"""
    try:
        # 1. GUI - Sélectionner fichier
        file_path = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json")]
        )
        if not file_path:
            return
        
        # 2. MÉTIER - Charger
        self.model.load_project(file_path)
        
        # 3. GUI - Rafraîchir
        self._refresh_layer_list()
        self._refresh_canvas()
        
    except ProjectError as e:
        messagebox.showerror("Erreur Format", str(e))
    except FileOperationError as e:
        messagebox.showerror("Erreur Fichier", str(e))
```

### 6. Gestion Couleur Fond

**Avant:**
```python
def change_background_color(self):
    new_color = colorchooser.askcolor(color=self.app1.background_couleur)[1]
    if new_color:
        self.app1.background_couleur = new_color
        self.refresh_canvas()
```

**Après:**
```python
def change_background_color(self):
    """Change couleur fond"""
    try:
        # 1. GUI - Sélectionner couleur
        new_color = colorchooser.askcolor(
            color=self.model.get_background_color("1")
        )[1]
        if not new_color:
            return
        
        # 2. MÉTIER - Valider et mettre à jour
        # (Validators.is_valid_hex_color est appelé inside)
        self.model.set_background_color(new_color, layout="1")
        
        # 3. GUI - Rafraîchir
        self._refresh_canvas()
        
    except ValidationError as e:
        messagebox.showerror("Erreur Couleur", str(e))
```

### 7. Export Images

**Avant:**
```python
def export_images(self):
    path_im = self.select_directory()  # Dialogue fichier
    if path_im:
        # Logique export mélangée
        app_1.save_image(path_im)
        app_4.save_image(path_im)
        copy(template_xml, path_im + '.xml')
```

**Après:**
```python
def export_images(self):
    """Exporte frames"""
    try:
        # 1. GUI - Sélectionner répertoire
        output_dir = filedialog.askdirectory()
        if not output_dir:
            return
        
        # 2. MÉTIER - Récupérer données et template
        layers_1, bg_1 = self.model.get_frame_data_for_export("1")
        layers_4, bg_4 = self.model.get_frame_data_for_export("4")
        
        # 3. GUI (Presenter) - RENDU des layers Tkinter
        # (C'est la responsabilité du presenter de rendre les Layer objects)
        image_1 = self.app1.export_to_image(layers_1, bg_1)
        image_4 = self.app4.export_to_image(layers_4, bg_4)
        
        # 4. MÉTIER - Sauvegarder fichiers
        image_1.save(Path(output_dir) / "cadre_1.png")
        image_4.save(Path(output_dir) / "cadre_4.png")
        self.model.export_template_xml(str(Path(output_dir) / "cadre_1"))
        
        # 5. GUI - Feedback
        messagebox.showinfo("Succès", "Cadres exportés!")
        
    except FileOperationError as e:
        messagebox.showerror("Erreur Export", str(e))
```

---

## 📋 Checklist de Refactoring

### Phase 1: Initialisation
- [ ] Créer `self.model = EditorModel(...)`
- [ ] Remplacer `self.layers` par `self.model.layers_1photo/4photo`
- [ ] Remplacer `self.active_layer_idx` par `self.model.get_active_layer_idx()`
- [ ] Garder `self.prj_name_var` et `self.selected_template_var` (GUI)

### Phase 2: Callbacks Simples
- [ ] Refactorer `on_template_changed()`
- [ ] Refactorer `change_background_color()`
- [ ] Refactorer `delete_layer()`
- [ ] Refactorer `move_layer()`

### Phase 3: Opérations Fichier
- [ ] Refactorer `save_project()`
- [ ] Refactorer `load_project()`
- [ ] Refactorer `export_images()`

### Phase 4: Rendu Canvas
- [ ] Créer méthode `_refresh_canvas()` qui:
  - Récupère données du modèle
  - Crée Layer objects Tkinter
  - Affiche sur canvas
  - Met en cache

### Phase 5: Tests
- [ ] Tester chaque callback indépendamment
- [ ] Tester scenarios complets (load + edit + save)
- [ ] Vérifier que GUI respond bien

---

## 🔧 Exemple Complet: Ajouter Calque Texte

**Vue d'ensemble du flux:**

```python
# 1. UTILISATEUR clique "Ajouter Texte"
button_add_text = tk.Button(
    button_frame, 
    text=_t('image.button.add_text'),
    command=self.add_text_layer  # ← Callback
)

# 2. CALLBACK déclenché
def add_text_layer(self):
    """Ajoute un calque texte"""
    try:
        # a) GUI - Demander paramètres
        dialog = TextLayerDialog(self.tk_root)
        if not dialog.result:
            return
        
        text_content = dialog.result['text']
        font_name = dialog.result['font']
        font_size = dialog.result['size']
        
        # b) MÉTIER - Valider et ajouter au modèle
        layer_data = {
            "type": "text",
            "content": text_content,
            "font": font_name,
            "size": font_size,
            "position": (0, 0),
            "color": "#000000",
        }
        
        idx = self.model.add_layer(layer_data, layout="1")
        logger.info(f"Calque texte ajouté à l'index {idx}")
        
        # c) GUI - Rafraîchir affichages
        self._refresh_layer_list()      # Met à jour listbox
        self._refresh_canvas()           # Redessine canvas
        
    except ValidationError as e:
        messagebox.showerror("Validation", str(e))
    except Exception as e:
        handle_exception(e, operation="add_text_layer")

# 3. MODÈLE retourne l'index
# 4. GUI met à jour listbox et canvas
# 5. UTILISATEUR voit le nouveau calque!
```

---

## 💡 Bonnes Pratiques

### ✅ À Faire

```python
# ✅ Valider en priorité
try:
    self.model.operation(user_input)  # Validation dedans
except ValidationError as e:
    messagebox.showerror(...)

# ✅ Séparer GUI et métier clairement
self.model.add_layer(data)     # Métier
self._refresh_canvas()          # GUI

# ✅ Utiliser le modèle comme source de vérité
state = self.model.get_active_layer_idx("1")
```

### ❌ À Éviter

```python
# ❌ Ne pas créer d'état GUI parallèle
self.local_layers = []  # Non! Utiliser self.model.layers_1photo

# ❌ Ne pas faire de logique métier en callback
def on_click():
    # ❌ MAUVAIS: Logique métier inline
    self.layers.pop(idx)
    
    # ✅ BON: Appeler modèle
    self.model.delete_layer()

# ❌ Ne pas ignorer les exceptions
try:
    self.model.operation()
except:
    pass  # ❌ TRÈS MAUVAIS!
    
    # ✅ BON:
except FileOperationError as e:
    messagebox.showerror("Erreur", str(e))
```

---

## 🧪 Tests de Validation

Avant de mettre en production, tester:

```python
def test_integration():
    """Scénario complet"""
    root = tk.Tk()
    app = ImageEditorApp(root)
    
    # 1. Ajouter calque
    layer_data = {"type": "text", "content": "Test"}
    app.model.add_layer(layer_data)
    
    # 2. Vérifier modèle
    assert len(app.model.layers_1photo) == 1
    
    # 3. Sauvegarder
    app.model.save_project("/tmp/test.json")
    assert Path("/tmp/test.json").exists()
    
    # 4. Charger
    app.model.load_project("/tmp/test.json")
    assert len(app.model.layers_1photo) == 1
    
    root.destroy()
```

---

## 📚 Ressources

- `REFACTORING_MVP_REPORT.md` - Architecture MVP complète
- `DECOUPLING_STRATEGY.md` - Stratégie générale
- `CadreEditeur/editor_model.py` - Documentation EditorModel API
- `tests/test_models_mvc.py` - Exemples d'usage



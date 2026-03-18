from CadreSelecteur.CadreEditeur import layertext, imageeditor


class DummyStringVar:
    def __init__(self, value=''):
        self._v = value

    def set(self, v):
        self._v = v

    def get(self):
        return self._v


def test_layertext_set_text():
    # Crée une instance non initialisée et lui attribue un StringVar simulé
    obj = object.__new__(layertext.LayerText)
    obj.text = DummyStringVar('Initial')

    # Appel de la méthode corrigée
    layertext.LayerText.set_text(obj, 'Bonjour')

    assert obj.text.get() == 'Bonjour'


class DummyListbox:
    def __init__(self):
        self._items = []

    def delete(self, a, b=None):
        self._items = []

    def insert(self, *args, **kwargs):
        pass

    def selection_clear(self, a, b=None):
        pass

    def selection_set(self, idx):
        pass

    def curselection(self):
        return []


class DummyParamFrame:
    def __init__(self):
        self._children = []

    def winfo_children(self):
        return list(self._children)


class DummyLayer:
    def __init__(self):
        self.name = 'L0'
        self.layer_type = 'Texte'
        self.updated = False

    def update_param_zone(self, frame):
        self.updated = True


def test_imageeditor_refresh_listbox_guard():
    # Crée une instance non initialisée d'ImageEditor
    obj = object.__new__(imageeditor.ImageEditor)

    # Attributs nécessaires pour refresh_listbox
    obj.layers = []
    obj.active_layer_idx = -1
    obj.listbox = DummyListbox()
    obj.param_frame = DummyParamFrame()

    # Ne doit pas lever
    imageeditor.ImageEditor.refresh_listbox(obj)

    # Maintenant tester avec un calque actif
    layer = DummyLayer()
    obj.layers = [layer]
    obj.active_layer_idx = 0
    imageeditor.ImageEditor.refresh_listbox(obj)

    assert layer.updated is True

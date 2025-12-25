import os
import CadreSelecteur.cadreselecteur as cs


class DummyWidget:
    def __init__(self, *args, **kwargs):
        self._attrs = {}

    def pack(self, *a, **k):
        pass

    def pack_forget(self, *a, **k):
        pass

    def bind(self, *a, **k):
        pass

    def bind_all(self, *a, **k):
        pass

    def config(self, *a, **k):
        pass

    def create_image(self, *a, **k):
        return 1

    def tag_bind(self, *a, **k):
        pass


class DummyFrame(DummyWidget):
    def __init__(self, *a, **k):
        super().__init__()
        self._children = []

    def winfo_children(self):
        return list(self._children)


class DummyLabel(DummyWidget):
    def __init__(self, parent=None, image=None, **kwargs):
        super().__init__()
        self.image = image


class DummyButton(DummyWidget):
    def __init__(self, *a, **k):
        super().__init__()


class DummyRadiobutton(DummyWidget):
    def __init__(self, *a, **k):
        super().__init__()


class DummyCanvas(DummyWidget):
    def __init__(self, *a, **k):
        super().__init__()


def test_create_src_thumbnail_no_gui(tmp_path, monkeypatch):
    # Use a real image from the Templates folder
    tpl_dir = cs.template_path
    assert os.path.isdir(tpl_dir)
    # pick a file that ends with _1.png
    filenames = [f for f in os.listdir(tpl_dir) if f.lower().endswith('_1.png')]
    assert filenames, "Aucune image template *_1.png trouvée"
    filename = filenames[0]

    # Monkeypatch Tkinter widgets used in the module
    monkeypatch.setattr(cs, 'Frame', DummyFrame)
    monkeypatch.setattr(cs, 'Label', DummyLabel)
    monkeypatch.setattr(cs, 'Button', DummyButton)
    monkeypatch.setattr(cs, 'Radiobutton', DummyRadiobutton)
    monkeypatch.setattr(cs, 'Canvas', DummyCanvas)
    # Mock ImageTk.PhotoImage to avoid creating real Tk images in headless test environment
    monkeypatch.setattr(cs.ImageTk, 'PhotoImage', lambda *a, **kw: object())

    # Create a fake instance of CadreSelecteur
    obj = object.__new__(cs.CadreSelecteur)
    # minimal attributes required by create_src_thumbnail
    obj.source_directory = tpl_dir
    obj.list_frameSrc = DummyFrame()
    obj.selected_image = type('SV', (), {'set': lambda self, v: None, 'get': lambda self: ''})()
    obj.trash_icon = None
    obj._image_refs = []
    # Provide a dummy master to satisfy PhotoImage(master=...)
    obj.master = DummyWidget()

    # Call the function under test - should not raise
    obj.create_src_thumbnail(filename)

    # After call, _image_refs should contain at least the two thumbnails
    assert len(obj._image_refs) >= 2

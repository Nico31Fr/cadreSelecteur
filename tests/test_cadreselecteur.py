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
    # Layout actuel : Templates/<Projet>/<Projet>_1.png + _4.png
    tpl_dir = cs.template_path
    assert os.path.isdir(tpl_dir)
    # pick a project subdir containing a *_1.png
    project_dirs = [
        d for d in os.listdir(tpl_dir)
        if os.path.isdir(os.path.join(tpl_dir, d))
        and any(
            f.lower().endswith('_1.png')
            for f in os.listdir(os.path.join(tpl_dir, d))
        )
    ]
    assert project_dirs, "Aucun projet avec *_1.png trouvé dans Templates/"
    project_dir_name = project_dirs[0]

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
    obj.edit_icon = None
    # Initialiser le gestionnaire de références d'images
    from CadreSelecteur.image_ref_manager import ImageRefManager
    obj.image_ref_manager = ImageRefManager()
    # Provide a dummy master to satisfy PhotoImage(master=...)
    obj.master = DummyWidget()

    # Call the function under test - should not raise
    obj.create_src_thumbnail(project_dir_name)

    # After call, image_ref_manager should contain at least the two thumbnails
    assert obj.image_ref_manager.get_count('thumbnails') >= 2



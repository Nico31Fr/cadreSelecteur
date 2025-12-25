from PIL import Image
import CadreSelecteur.CadreEditeur.layertext as layertext_mod
from CadreSelecteur.CadreEditeur.layerimage import LayerImage
from CadreSelecteur.CadreEditeur.layertext import LayerText


class DummyStringVar:
    def __init__(self, value=''):
        self._v = value

    def set(self, v):
        self._v = v

    def get(self):
        return self._v


def test_layerimage_to_from_dict(tmp_path):
    # create a small image file
    img_path = tmp_path / "test_img.png"
    Image.new('RGBA', (10, 10), (255, 0, 0, 255)).save(img_path)

    dct = {
        "class": "LayerImage",
        "layer_type": "Image",
        "name": "Image 1",
        "display_position": (1, 2),
        "image_position": (3, 4),
        "visible": True,
        "locked": False,
        "imported_image_path": str(img_path),
        "display_imported_image_size": (10, 10),
        "image_imported_image_size": (30, 30),
    }

    obj = LayerImage.from_dict(
        dct,
        tk_parent=None,
        parent=None,
        canva_size=(600, 400),
        image_size=(1800, 1200),
        ratio=3,
    )

    assert obj.imported_image_path == str(img_path)
    assert obj.original_image is not None


def test_layertext_to_from_dict(monkeypatch):
    # monkeypatch tkinter.StringVar to avoid creating Tk root
    monkeypatch.setattr(layertext_mod.tk, 'StringVar', DummyStringVar)

    lt = LayerText(tk_parent=None, parent=None, canva_size=(600, 400), image_size=(1800, 1200), ratio=3, name='T1')
    lt.text.set('Bonjour')
    lt.font_color = '#112233'
    lt.sel_font = {"family": "Anton-Regular", "size": 24}

    d = lt.to_dict()
    nt = LayerText.from_dict(d, tk_parent=None, parent=None, canva_size=(600, 400), image_size=(1800, 1200), ratio=3)

    assert nt.text.get() == 'Bonjour'
    assert nt.font_color == '#112233' or nt.font_color is not None
    assert isinstance(nt.sel_font, dict)

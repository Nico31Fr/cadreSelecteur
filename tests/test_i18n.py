import importlib

import CadreSelecteur.config_loader as config_loader
from CadreSelecteur.i18n import translator


def test_initial_language_matches_config():
    # Reload translator to ensure it reads current config
    importlib.reload(translator)
    assert translator.get_language() == config_loader.LANGUAGE


def test_translation_lookup_and_format():
    # Ensure French translations available and formatting works
    assert translator.set_language('fr') is True
    assert translator._t('selector.button.quit') == 'Quitter'
    title = translator._t('selector.title', version='1.2.3')
    assert '1.2.3' in title


def test_missing_key_returns_key():
    translator.set_language('fr')
    assert translator._t('non.existing.key') == 'non.existing.key'


def test_set_language_switch():
    assert translator.set_language('en') is True
    assert translator._t('selector.button.quit') == 'Quit'


def test_set_unknown_language_falls_back_to_fr():
    # unknown language should fall back to fr.json per translator implementation
    translator.set_language('zz_nonexistent')
    assert translator.get_language() == 'fr'
    assert translator._t('selector.button.quit') == 'Quitter'


def test_malformed_json_handled_gracefully():
    """Créer un fichier i18n malformé et vérifier que le traducteur ne plante pas.

    Comportement attendu : set_language ne lève pas d'exception (retourne True) et
    les recherches retournent la clé (comportement sûr si le JSON est corrompu).
    """
    from pathlib import Path
    # Emplacement du dossier i18n
    i18n_dir = Path(translator.__file__).resolve().parent
    bad_file = i18n_dir / 'malformed_test.json'
    try:
        # Écrire un JSON invalide
        bad_file.write_text('{ this is : not valid json', encoding='utf-8')
        # Charger la langue correspondante
        ok = translator.set_language('malformed_test')
        assert ok is True
        # Les traductions doivent être vides -> _t doit renvoyer la clé
        assert translator._t('selector.button.quit') == 'selector.button.quit'
    finally:
        # Nettoyage
        try:
            if bad_file.exists():
                bad_file.unlink()
        except Exception:
            pass

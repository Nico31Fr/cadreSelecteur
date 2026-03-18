import importlib
from pathlib import Path

from CadreSelecteur.i18n import translator


def test_resources_have_priority_over_i18n():
    """Vérifie que `resources/fr.json` est lu en priorité par rapport à `i18n/fr.json`.

    Le test crée temporairement deux fichiers JSON distincts (resources et i18n),
    recharge le module `translator` et vérifie que la valeur retournée par
    _t() correspond au contenu de resources/fr.json.
    """
    i18n_dir = Path(translator.__file__).resolve().parent
    resources_dir = i18n_dir.parent / 'resources'

    res_file = resources_dir / 'fr.json'
    i18n_file = i18n_dir / 'fr.json'

    # Sauvegarde des contenus existants (s'ils existent)
    orig_res = None
    orig_i18n = None
    if res_file.exists():
        orig_res = res_file.read_text(encoding='utf-8')
    if i18n_file.exists():
        orig_i18n = i18n_file.read_text(encoding='utf-8')

    try:
        # Écrire des contenus distincts pour forcer la différence
        res_file.write_text('{"selector": {"button": {"quit": "RESOURCE_QUIT"}}}', encoding='utf-8')
        i18n_file.write_text('{"selector": {"button": {"quit": "I18N_QUIT"}}}', encoding='utf-8')

        # Recharger le module pour qu'il relise les fichiers
        importlib.reload(translator)

        # Charger la langue francaise explicitement
        ok = translator.set_language('fr')
        assert ok is True

        # La traduction doit provenir du fichier resources/fr.json
        assert translator._t('selector.button.quit') == 'RESOURCE_QUIT'

    finally:
        # Restauration des fichiers originaux
        try:
            if orig_res is None and res_file.exists():
                res_file.unlink()
            elif orig_res is not None:
                res_file.write_text(orig_res, encoding='utf-8')
        except Exception:
            pass
        try:
            if orig_i18n is None and i18n_file.exists():
                i18n_file.unlink()
            elif orig_i18n is not None:
                i18n_file.write_text(orig_i18n, encoding='utf-8')
        except Exception:
            pass

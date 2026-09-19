# -*- coding: utf-8 -*-
""" Module de selection de cadre pour PiBooth
    |→ point d'entrée de l'appli autonome """

import logging
import sys
from multiprocessing import freeze_support

from CadreSelecteur.cadreselecteur import CadreSelecteur, check_mandatory_path

# Présent uniquement dans le .exe PyInstaller : splash natif affiché par le
# bootloader avant même le démarrage de Python (couvre extraction + imports).
# En mode source, l'import échoue et on fonctionne sans splash.
try:
    import pyi_splash
except ImportError:
    pyi_splash = None

logger = logging.getLogger(__name__)


def close_splash() -> None:
    """
    Ferme l'écran de splash natif PyInstaller.

    No-op en mode source (pyi_splash absent) ou après une fermeture déjà faite.
    """
    global pyi_splash
    if pyi_splash is not None:
        try:
            pyi_splash.close()
        except Exception:
            logger.warning("Splash: échec de fermeture", exc_info=True)
            pyi_splash = None


def main() -> int:
    """
    Point d'entrée principal.

    Returns:
        Code de sortie (0 = succès, 1 = erreur)
    """
    # Sécurité pour Windows + PyInstaller si une librairie embarquée
    # utilise multiprocessing en interne
    freeze_support()

    # Setup logging basique si pas encore configuré
    if not logging.getLogger().hasHandlers():
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

    logger.info("=" * 60)
    logger.info("CadreSelecteur: démarrage")
    logger.info("=" * 60)

    try:
        # Vérifier les chemins obligatoires
        # (le splash natif est déjà affiché par le bootloader)
        logger.debug("Vérification des chemins...")
        check_mandatory_path()

        # Créer l'app - le chargement lourd (vignettes, imports) s'exécute
        # ici, splash encore affiché pendant ce temps
        logger.debug("App: démarrage CadreSelecteur")
        app = CadreSelecteur(start_mainloop=False)
        logger.debug("App: CadreSelecteur créé")

        # Forcer la mise à jour de la fenêtre pour la rendre visible
        app.master.update_idletasks()
        logger.debug("App: fenêtre mise à jour, lancement mainloop")

        # L'app est prête : fermer le splash natif
        close_splash()

        # Lancer l'app - BLOQUANT
        app.master.mainloop()
        logger.debug("App: fermeture propre")

    except KeyboardInterrupt:
        logger.info("Interruption utilisateur (Ctrl+C)")

    except Exception as e:
        logger.error(f"Erreur pendant le démarrage - {e}", exc_info=True)
        return 1

    finally:
        # Garantir la fermeture du splash même en cas de sortie prématurée
        close_splash()

        logger.info("=" * 60)
        logger.info("CadreSelecteur: fermé")
        logger.info("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
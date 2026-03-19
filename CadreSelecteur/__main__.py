# -*- coding: utf-8 -*-
""" Module de selection de cadre pour PiBooth
    |→ point d'entrée de l'appli autonome """

import logging
import sys
from multiprocessing import Process, freeze_support
from time import sleep

from CadreSelecteur.cadreselecteur import CadreSelecteur, check_mandatory_path
from CadreSelecteur.splash import splash

logger = logging.getLogger(__name__)



def run_splash() -> None:
    """
    Lance l'écran de splash.
    
    La fonction splash() gère elle-même le timeout et se ferme proprement.
    """
    try:
        logger.debug("Splash: démarrage")
        splash()
        logger.debug("Splash: processus terminé")
    
    except Exception as e:
        logger.error(f"Splash: erreur - {e}", exc_info=True)


def run_app() -> None:
    """
    Lance l'application principale.
    """
    try:
        logger.debug("App: démarrage CadreSelecteur")
        app = CadreSelecteur()
        logger.debug("App: CadreSelecteur créé")
        
        # Forcer la mise à jour de la fenêtre pour la rendre visible
        app.root.update_idletasks()
        logger.debug("App: fenêtre mise à jour, lancement mainloop")
        
        # Lancer l'app - BLOQUANT
        app.root.mainloop()
        logger.debug("App: fermeture propre")
    
    except Exception as e:
        logger.error(f"App: erreur - {e}", exc_info=True)


def main() -> int:
    """
    Point d'entrée principal.
    
    Returns:
        Code de sortie (0 = succès, 1 = erreur)
    """
    # Nécessaire pour Windows + PyInstaller
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
    
    # Créer les processes
    splash_process = Process(target=run_splash, name="splash")
    app_process = Process(target=run_app, name="app")
    
    try:
        # Démarrer le splash AVANT de vérifier les paths
        # (pour que l'utilisateur voie quelque chose pendant la vérification)
        logger.debug("Démarrage splash...")
        splash_process.start()
        
        # Vérifier les chemins obligatoires
        logger.debug("Vérification des chemins...")
        check_mandatory_path()
        
        # Démarrer l'app
        logger.debug("Démarrage app...")
        app_process.start()
        
        # Attendre que l'app se termine
        # (le splash se ferme automatiquement après timeout)
        app_process.join()
        logger.info("App terminée proprement")
        
    except KeyboardInterrupt:
        logger.info("Interruption utilisateur (Ctrl+C)")
    
    except Exception as e:
        logger.error(f"Erreur pendant le démarrage - {e}", exc_info=True)
        return 1
    
    finally:
        # Cleanup: s'assurer que tous les processes sont fermés
        logger.debug("Cleanup: fermeture des processes...")
        
        # Fermer le splash gracieusement
        if splash_process.is_alive():
            logger.debug("Fermeture splash (graceful)...")
            splash_process.terminate()
            
            # Attendre la fermeture (avec timeout)
            splash_process.join(timeout=2)
            
            # Force kill si toujours actif
            if splash_process.is_alive():
                logger.warning("Splash n'a pas répondu, force kill...")
                splash_process.kill()
                splash_process.join()
        
        # Fermer l'app gracieusement
        if app_process.is_alive():
            logger.debug("Fermeture app (graceful)...")
            app_process.terminate()
            
            # Attendre la fermeture (avec timeout)
            app_process.join(timeout=2)
            
            # Force kill si toujours actif
            if app_process.is_alive():
                logger.warning("App n'a pas répondu, force kill...")
                app_process.kill()
                app_process.join()
        
        logger.info("=" * 60)
        logger.info("CadreSelecteur: fermé")
        logger.info("=" * 60)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())


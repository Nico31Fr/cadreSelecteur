# ---------------------------------------
#  Makefile pour CadreSelecteur
#  Build Windows et Linux via PyInstaller
# ---------------------------------------

APP_NAME = CadreSelecteur
SPEC_FILE = CadreSelecteur.spec
DIST_DIR = dist
BUILD_DIR = build

PYINSTALLER = pyinstaller

# ---------------------------------------
# Cibles principales
# ---------------------------------------

all: clean linux

windows:
	@echo ">>> Build Windows (.exe)"
	$(PYINSTALLER) $(SPEC_FILE)

linux:
	@echo ">>> Build Linux (exécutable)"
	$(PYINSTALLER) $(SPEC_FILE)

clean:
	@echo ">>> Nettoyage des dossiers dist/ et build/"
	rm -rf $(DIST_DIR) $(BUILD_DIR)
	find . -name "__pycache__" -exec rm -rf {} +

install:
	pip install -r requirements.txt

# ---------------------------------------
# Aide
# ---------------------------------------

help:
	@echo "-----------------------------------------"
	@echo " Commandes disponibles :"
	@echo "   make windows     → compile version Windows"
	@echo "   make linux       → compile version Linux"
	@echo "   make clean       → supprime dist/ build/"
	@echo "   make install     → installe dépendances"
	@echo "-----------------------------------------"

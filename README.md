 ![IHM](CadreSelecteur/resources/cadreSelecteur.png)
# PiBooth Cadre Sélecteur

## ⚠️ Important : Installation sans Python requis !

**Vous n'avez pas besoin d'installer Python** pour utiliser cette application !
Un fichier exécutable est fourni qui fonctionne directement après extraction.

---

## 🖥️ Méthode Recommandée : Exécutable Windows (Aucune Installation Requise)

### Pour les utilisateurs de Windows qui ne connaissent pas GitHub

**Étape 1 :** Téléchargez l'archive depuis [les releases](https://github.com/Nico31Fr/cadreSelecteur/releases)

**Étape 2 :** Extraiez le fichier ZIP dans un dossier de votre choix (par exemple : C:\CadreSelecteur ou sur votre bureau)

**Étape 3 :** Double-cliquez sur l'executable `cadreSelecteur.exe` pour lancer l'application

**Étape 4 :** Utilisez l'application comme vous le feriez avec n'importe quel programme Windows classique !

### Comment utiliser l'application une fois lancée :

1. L'application affiche les cadres disponibles à gauche et le cadre sélectionné à droite
2. Cliquez sur un cadre pour le sélectionner
3. Cliquez sur "Appliquer" pour valider le choix
4. Le cadre sera utilisé lors du prochain lancement de PiBooth

---

## 🐧 Alternative : Mode Script Python (Pour utilisateurs avancés)

**Cette méthode n'est utile que si :**
- Vous êtes habitué à utiliser des scripts Python
- Vous avez déjà Python installé sur votre système (Windows, Mac ou Linux)
- Vous voulez exécuter l'application directement depuis le terminal sans executable

### Installation des dépendances :

Cette méthode nécessite d'avoir Python installé. Téléchargez Python depuis [python.org](https://www.python.org/downloads/) si vous ne l'avez pas.

```bash 
pip install -r requirements.txt
```

### Démarrage :

Ouvrez un terminal dans le répertoire de l'application et exécutez :

```bash 
python3 -m CadreSelecteur
```

**Note :** Les deux méthodes (executable et script Python) fournissent les mêmes fonctionnalités. L'executable est recommandé pour la simplicité !


## Fonctionnalités

### Démarrage de l'application

1. **Initialisation** : Lors de l'exécution, l'application vérifie la présence des répertoires et du template par défaut. Les erreurs de configuration sont signalées via un message d'erreur.

   - **Répertoires requis** :
     - `Templates` : Contenant les cadres et templates disponibles.
     - `Cadres` : Destination pour les cadres sélectionnés. (PiBooth est configuré pour venir chercher le cadre à utiliser ici)
     - `Fonts` : contient les polices utilisables dans l'outil (vous pouvez en ajouter !)

   - **Fichiers nécessaires** :
     - `template_x.xml` : Template par défaut utilisé en l'absence de fichier associé.


2. **Affichage** : L'application affiche une liste de vignettes des cadres disponibles à gauche et le cadre installé à droite.
    
    ### Interface Utilisateur

3. ![IHM](CadreSelecteur/resources/IHM_selecteur.png)

- **Cadres disponibles** : Liste et prévisualisation des cadres disponibles dans `Templates`.
- **Cadre installé** : Prévisualisation du cadre actuellement utilisé dans `Cadres`.
- **Boutons d'action** : `Appliquer` pour exécuter la sélection et `Quitter` pour fermer l'application.
- **bouton poubelle** : permet de supprimer un jeux de cadre
- 
Pour modifier le cadre que pibooth va utiliser :

1. **Sélection** :
   - Naviguez dans les miniatures affichées pour choisir un cadre. Cliquez sur le bouton radio correspondant à la gauche des vignettes.

2. **Prévisualisation** :
   - Cliquez sur une vignette pour afficher l'image dans une nouvelle fenêtre.

3. **Application** :
   - Cliquez sur le bouton `Appliquer` pour copier les fichiers sélectionnés vers le répertoire de destination (./cadres/)

# Cadre éditeur

## Interface utilisateur
![IHM](CadreSelecteur/resources/IHM_editeur.png)
### Sections principales

- **1 - Sélection de templates** : Choisissez parmi les templates disponibles pour définir les zones de cadre.
- **2 - Cadres de composition** : Deux zones d'édition (app1 et app4) pour vos compositions d'image.
- **3 - Synchronisation** : Options pour synchroniser les configurations entre les deux cadres.
- **4 - Sauvegarde et export** : Sauvegarder et charger des projets, ainsi que générer et exporter des fichiers de cadre.

#### Secteur de sélection de templates

Sélectionnez le template XML désiré dans le menu déroulant. Les zones d'exclusion seront automatiquement configurées en fonction du template choisi.

### Cadres de composition

La fenêtre principale affiche deux cadres que vous pouvez personnaliser individuellement. Chacun offre la possibilité d'importer des images, de placer du texte, et de modifier les couleurs de fond.

### Synchronisation

Utilisez les boutons fléchés pour synchroniser les propriétés de texte, d'image, ou de fond entre les deux cadres. 

### Sauvegarde et export

- **Charger/Sauvegarder un projet** : Utilisez les boutons dédiés pour sauvegarder le projet actuel dans un fichier JSON ou pour le charger depuis un fichier existant.
- **Exporter les cadres** : Sélectionnez un répertoire pour sauvegarder votre projet avec le bouton `Générer les cadres`. Cela exportera deux fichiers PNG et copiera le fichier XML de template.

### Fonctionnement du Cadre de composition

#### Principales sections

- **Canvas de prévisualisation** : Affichage en temps réel de votre composition.
- **Zone de contrôle** : Interface avec les boutons et entrées pour interagir avec votre composition.

#### Canvas de prévisualisation

Situé dans la partie supérieure de l'application, le canvas affiche votre composition comprenant l'image, le texte, et le fond.

#### Zone de contrôle

La zone de contrôle inclut les calques suivantes :

1. **Texte** :
   - **Saisie** : Entrez votre texte.
   - **Police** : Cliquez sur `Police` pour choisir le style et la taille.
   - **Couleur** : Bouton `Couleur` pour la couleur du texte.

2. **Image** :
   - **Importer** : Bouton `Image` pour sélectionner une image à importer.
   - **Effacer** : Supprime l'image importée.

3. **Couleur de fond** :
   - **Sélecteur** : Cliquez sur `couleur du fond` pour ouvrir le sélecteur de couleurs.
   - **Code couleur** : Modification directe du code hexadécimal.

4. **Calque Actif** :
   - **Image** : Sélection pour déplacer ou redimensionner l'image.
   - **Texte** : Sélection pour déplacer ou redimensionner le texte.

### Manipulation de la composition

- **Déplacement** : Sélectionnez le calque et glissez/déposez (drag and drop) le calque actif.
- **Zoom** : Utilisez la molette de la souris pour agrandir ou rétrécir le calque actif.


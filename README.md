# cadreSelecteur

Sélecteur et éditeur de cadres pour piBooth  
Version : 0.1  
Python requis : 3.11 ou supérieur

---

## Sommaire

- [Description](#description)  
- [Fonctionnalités](#fonctionnalités)  
- [Arborescence des dossiers](#arborescence-des-dossiers)  
- [Installation et dépendances](#installation-et-dépendances)  
- [Utilisation](#utilisation)  
  - [Lancer le Sélecteur de cadre](#lancer-le-sélecteur-de-cadre)  
  - [Lancer l'Éditeur de cadre autonome](#lancer-léditeur-de-cadre-autonome)  
  - [Utilisation de l’exécutable Windows](#utilisation-de-lexécutable-windows)  
- [Structure interne et développement](#structure-interne-et-développement)  
- [Exemple d’utilisation rapide](#exemple-dutilisation-rapide)  
- [Licence](#licence)  

---

## Description

`cadreSelecteur` est une application Python avec interface graphique Tkinter destinée à la gestion des **cadres/templates** pour piBooth, un logiciel de photobooth.

Elle permet de visualiser les cadres disponibles, de sélectionner et appliquer un cadre actif, de supprimer ou créer un nouveau cadre via un éditeur intégré. L’édition avancée est assurée par un module indépendant permettant la modification fine des calques d’image, texte et zones d’exclusion.

---

## Fonctionnalités

- Navigation visuelle parmi les cadres disponibles avec vignettes.  
- Sélection facile avec application instantanée du cadre actif.  
- Suppression sécurisée des cadres (protection du dernier cadre).  
- Prévisualisation du cadre en taille réelle.  
- Lancement et utilisation d’un éditeur de cadre complet avec gestion de calques, texte, images, et couleur de fond.  
- Sauvegarde, chargement et export des projets d’édition (images PNG + XML).  
- Synchronisation entre deux variantes de cadres (formats 1 et 4).  
- Gestion des zones d’exclusion dans la composition des cadres.  

---

## Arborescence des dossiers

Le projet attend la présence au minimum des dossiers suivants :

/Templates/ <-- Cadres sources (images _1.png, _4.png, fichiers .xml associés)  
/Cadres/ <-- Cadre actif copié ici pour piBooth (cadre_1.png, cadre_4.png, template.xml)  

Le dossier `CadreEditeur/` contient les modules liés à l’éditeur de cadre.

---

## Installation 

### utilisation executable Windows

1. télécharger la dernière version de l'executable disponible.
2. double cliquer sur cadreSelecteur.exe

### utilisation avec interpreteur local

1. Assure-toi d’avoir installé Python 3.11 ou supérieur :  
   [https://www.python.org/downloads/](https://www.python.org/downloads/)

2. Installer les dépendances via pip :

    ```bash
    pip install -r requirements.txt
    ```

---

## Utilisation


### Utilisation de l’exécutable Windows

Un exécutable Windows (.exe) est disponible pour les systèmes Windows.  
Tu peux simplement télécharger et lancer ce fichier sans installer Python ni les dépendances.

### Lancer le Sélecteur de cadre

```bash
 python cadreselecteur.py
```

- Affiche la liste des cadres disponibles, cadre actif et boutons d’action.  
- Sélectionne un cadre puis clique sur **Appliquer** pour le définir en actif.  
- Clique sur **Nouveau cadre** pour ouvrir l’éditeur intégré.  
- Clique sur la poubelle à côté d’un cadre pour le supprimer.  
- Double-clic sur une vignette affiche la prévisualisation en grand.  

---

## Structure interne et développement

### Modules principaux

- `main.py` — Interface principale du sélecteur de cadre.  
- `start_cadre_editeur.py` — Point d’entrée autonome pour l’éditeur.  
- `CadreEditeur/imageeditorapp.py` — Application d’édition multi-fenêtres.  
- `CadreEditeur/imageeditor.py` — Fenêtre d'édition simple, gestion des calques.  
- `CadreEditeur/layerimage.py`, `layertext.py`, `layerexcluzone.py` — Types de calques gérés.  

### Gestion des calques

Le système de calques permet de créer des compositions complexes en superposant :

- **Images importées**  
- **Texte modifiable** (police, taille, position)  
- **Zones d’exclusion** (zones transparentes ou protégées)  

Les calques peuvent être déplacés, redimensionnés et ordonnés dans la pile.

### Synchronisation entre variantes

Lors de l’édition, deux variantes sont simultanément gérées (1 et 4) avec possibilité de synchroniser certains paramètres (calques, fond, tous).

---

## Exemple d’utilisation rapide

1. **Lancer le sélecteur ou double cliquer sur l'exécutable Windows** :
    ```bash
    python main.py
    ```
    ou 
    ```bash
    python cadreselecteur.py
    ```
   
2. **Sélectionner un cadre** dans la liste à gauche, cliquer sur **Appliquer**.

3. **Visualiser le cadre actif** à droite, cliquer sur la vignette pour un aperçu en grand.

4. **Créer un nouveau cadre** en cliquant sur **Nouveau cadre**, cela ouvre l’éditeur.

5. **Ajouter des calques** dans l’éditeur : images, textes, zones d’exclusion.

6. **Personnaliser la couleur de fond** et ajuster les calques.

7. **Sauvegarder le projet** et **exporter les images et fichier XML** générés.

8. **Revenir au sélecteur**, appliquer le nouveau cadre.

---

## Licence

Aucune déclaration spécifique — libre d’utilisation et modification.

---

N’hésitez pas à contribuer, rapporter des bugs ou demander de l’aide !